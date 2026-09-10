from __future__ import annotations
import json
import os
import uuid
from pathlib import Path
from io import BytesIO
from typing import Any, Dict, List, Optional
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from openai import OpenAI
from agent.memory import memory
from agent.state import AgentState, ToolCallState
from agent.tools import registry

DATA_ROOT = Path(
    os.getenv(
        "TABLE_AGENT_DATA",
        Path(__file__).resolve().parent / "runtime" / "datasets"
    )
)

DATA_ROOT.mkdir(parents=True, exist_ok=True)

load_dotenv()
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url=os.getenv("DEEPSEEK_BASE_URL"))
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
MAX_TOOL_STEPS = int(os.getenv("MAX_TOOL_STEPS", "5"))

SYSTEM_PROMPT = """你是一个智能表格分析 Agent。
你必须先理解用户当前问题，再决定是否需要工具。
工具可以执行真实的数据操作；如果调用工具，必须依据工具返回结果继续推理，而不是猜测结果。
你可以在同一轮连续调用多个工具。
多轮对话中要记住之前已经确认的数据集、列名、用户目标和工具结果。
如果用户使用“它/这个/刚才那个”等指代，要结合会话历史理解。
如果缺少真实表格数据，不要伪造统计结果，应明确说明缺少数据。
回答时用中文，简洁说明做了什么、工具返回什么、下一步可以做什么。
"""

class Message(BaseModel):
    role: str
    content: Any = None
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[dict] | None = None

class ChatRequest(BaseModel):
    session_id: str
    message: str
    context: Dict[str, Any] = Field(default_factory=dict)

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    agent_state: AgentState
    profile: Optional[Dict[str, Any]] = None

app = FastAPI(title="Table Agent Backend")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def _jsonable(value):
    try: json.dumps(value, ensure_ascii=False); return value
    except TypeError: return str(value)

def build_messages(session):
    messages: List[Dict[str, Any]] = [{"role":"system","content":SYSTEM_PROMPT}]
    if session.get("summary"):
        messages.append({"role":"system","content":"会话历史摘要：" + session["summary"]})
    for m in session.get("messages", []):
        item = {k:v for k,v in m.items() if k in {"role","content","name","tool_call_id","tool_calls"} and v is not None}
        messages.append(item)
    return messages

def parse_tool_call(tc):
    fn = tc.function
    raw = fn.arguments or "{}"
    try: args = json.loads(raw)
    except json.JSONDecodeError as e: raise ValueError(f"工具参数不是合法 JSON: {e}")
    return tc.id, fn.name, args

def run_agent_turn(session_id: str, user_message: str, context: Dict[str, Any]) -> tuple[str, AgentState]:
    turn_id = str(uuid.uuid4())
    if context:
        memory.update_context(session_id, context)
    memory.append(session_id, {"role":"user","content":user_message})
    state = AgentState(turn_id=turn_id)
    session = memory.load(session_id)
    messages = build_messages(session)
    tool_calls_state: List[ToolCallState] = []

    for _step in range(MAX_TOOL_STEPS):
        response = client.chat.completions.create(model=MODEL, messages=messages, tools=registry.schemas(), tool_choice="auto")
        msg = response.choices[0].message
        assistant_dump = {"role":"assistant", "content":msg.content or ""}
        if msg.tool_calls:
            assistant_dump["tool_calls"] = [{"id":tc.id,"type":"function","function":{"name":tc.function.name,"arguments":tc.function.arguments}} for tc in msg.tool_calls]
        messages.append(assistant_dump)
        memory.append(session_id, assistant_dump)

        if not msg.tool_calls:
            answer = msg.content or "已完成本轮处理。"
            state.tool_calls = tool_calls_state
            state.need_tool = bool(tool_calls_state)
            if tool_calls_state:
                state.tool_name = tool_calls_state[-1].name
                state.tool_result = tool_calls_state[-1].result
            return answer, state

        for tc in msg.tool_calls:
            call_id, name, args = parse_tool_call(tc)
            call_state = ToolCallState(id=call_id, name=name, arguments=args)
            try:
                current = memory.load(session_id)
                result = registry.execute(name, args, current.get("context", {}))
                result = _jsonable(result)
                # # Tool 执行成功后，把新的表格状态写回 Memory
                # if name == "drop_missing_values" and isinstance(result, dict):
                #     if "data" in result:
                #         memory.update_context(
                #             session_id,
                #             {
                #                 "data": result["data"]
                #             }
                #         )

                call_state.result = result
                memory.add_tool_result(session_id, {"tool":name,"arguments":args,"result":result})
                tool_msg = {"role":"tool","tool_call_id":call_id,"name":name,"content":json.dumps(result, ensure_ascii=False, default=str)}
            except Exception as e:
                call_state.error = str(e)
                tool_msg = {"role":"tool","tool_call_id":call_id,"name":name,"content":json.dumps({"error":str(e)}, ensure_ascii=False)}
            tool_calls_state.append(call_state)
            messages.append(tool_msg)
            memory.append(session_id, tool_msg)

    state.tool_calls = tool_calls_state
    state.need_tool = bool(tool_calls_state)
    state.error = "工具调用超过最大步数"
    answer = "本轮工具调用次数过多，已停止执行，请缩小任务范围后重试。"
    memory.append(session_id, {"role":"assistant","content":answer})
    return answer, state

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    encoding: str = Form("UTF-8"),
    delimiter: str = Form(","),
    has_header: bool = Form(True),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="未选择文件"
        )

    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in {".csv", ".tsv", ".xlsx", ".xls"}:
        raise HTTPException(
            status_code=400,
            detail="只支持 CSV、TSV、XLSX、XLS 文件"
        )

    # 生成唯一数据集 ID
    dataset_id = f"ds_{uuid.uuid4().hex[:12]}"

    # 读取上传文件
    raw = await file.read()

    try:
        # Excel
        if ext in {".xlsx", ".xls"}:
            df = pd.read_excel(
                BytesIO(raw)
            )

        # CSV / TSV
        else:
            sep = "\t" if ext == ".tsv" else delimiter

            df = pd.read_csv(
                BytesIO(raw),
                encoding=encoding,
                sep=sep,
                header=0 if has_header else None,
            )

            # 没有表头时自动生成列名
            if not has_header:
                df.columns = [
                    f"column_{i}"
                    for i in range(len(df.columns))
                ]

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"文件解析失败: {e}"
        )

    # 保存真实 DataFrame
    dataset_path = DATA_ROOT / f"{dataset_id}.pkl"

    df.to_pickle(dataset_path)

    # 生成前 50 行预览
    preview_df = df.head(50)
    # 转成标准 JSON 数据，NaN / NaT 会自动转换为 null
    preview = json.loads(
        preview_df.to_json(
            orient="values",
            force_ascii=False
        )
    )

    # 生成字段信息
    schema = []

    for column in df.columns:
        series = df[column]

        if pd.api.types.is_numeric_dtype(series):
            column_type = "number"
        else:
            column_type = "string"

        schema.append({
            "name": str(column),
            "type": column_type,
            "nullRate": float(series.isna().mean()),
            "uniqueCount": int(
                series.nunique(dropna=True)
            ),
            "selected": True,
        })

    # 数据集基本信息
    meta = {
        "datasetId": dataset_id,
        "fileName": file.filename,
        "fileSize": len(raw),
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "encoding": encoding,
        "delimiter": delimiter,
        "hasHeader": has_header,
        "fingerprint": dataset_id,
        "uploadedAt": pd.Timestamp.now().isoformat(),
    }

    # 数据画像
    profile = {
        "datasetId": dataset_id,
        "schema": schema,
        "previewRows": preview,
        "statistics": {
            "totalRows": int(len(df)),
            "totalColumns": int(len(df.columns)),
            "memoryUsage": int(
                df.memory_usage(deep=True).sum()
            ),
        },
    }

    return {
        "datasetId": dataset_id,
        "meta": meta,
        "profile": profile,
    }

class ProcessRequest(BaseModel):
    dataset_id: str
    process_spec: Dict[str, Any] = Field(default_factory=dict)


def build_profile_from_df(dataset_id: str, df: pd.DataFrame):
    preview_df = df.head(50)

    preview = json.loads(
        preview_df.to_json(
            orient="values",
            force_ascii=False
        )
    )

    schema = []

    for column in df.columns:
        series = df[column]

        if pd.api.types.is_numeric_dtype(series):
            column_type = "number"
        else:
            column_type = "string"

        schema.append({
            "name": str(column),
            "type": column_type,
            "nullRate": float(series.isna().mean()),
            "uniqueCount": int(series.nunique(dropna=True)),
            "selected": True,
        })

    return {
        "datasetId": dataset_id,
        "schema": schema,
        "previewRows": preview,
        "statistics": {
            "totalRows": int(len(df)),
            "totalColumns": int(len(df.columns)),
            "memoryUsage": int(
                df.memory_usage(deep=True).sum()
            ),
        },
    }


@app.post("/process")
def process_dataset(req: ProcessRequest):
    dataset_id = req.dataset_id

    dataset_path = DATA_ROOT / f"{dataset_id}.pkl"

    if not dataset_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"找不到数据集: {dataset_id}"
        )

    df = pd.read_pickle(dataset_path)
    input_rows = len(df)
    process_spec = req.process_spec or {}

    # 1. 缺失值处理
    missing = process_spec.get("missing") or {}
    strategy = missing.get("strategy")

    if strategy == "drop":
        column = missing.get("column")

        if column:
            df = df.dropna(subset=[column])
        else:
            df = df.dropna()

    # 2. 列选择
    selected_columns = process_spec.get("select")

    if selected_columns:
        existing_columns = [
            column
            for column in selected_columns
            if column in df.columns
        ]

        df = df[existing_columns]

    # 3. 筛选表达式
    filter_expression = process_spec.get("filter")

    if filter_expression:
        try:
            df = df.query(filter_expression)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"筛选表达式执行失败: {e}"
            )

    # 保存处理后的真实 DataFrame
    df.to_pickle(dataset_path)

    profile = build_profile_from_df(
        dataset_id,
        df
    )

    return {
        "runId": f"run_{uuid.uuid4().hex[:12]}",
        "status": "success",
        "inputRows": int(input_rows),
        "outputRows": int(len(df)),
        "affectedColumns": [],
        "missingChanges": [],
        "profile": profile,
    }

@app.get("/")
def root(): return {"message":"Table Agent Backend Running", "mode":"model_tool_loop"}

@app.get("/sessions/{session_id}")
def get_session(session_id: str):
    s = memory.load(session_id)
    return {"session_id":session_id,"summary":s.get("summary",""),"messages":s.get("messages",[]),"context":s.get("context",{}),"last_tool_results":s.get("last_tool_results",[])}

@app.delete("/sessions/{session_id}")
def clear_session(session_id: str):
    memory.clear(session_id); return {"ok":True,"session_id":session_id}

def _load_profile(dataset_id: str | None):
    if not dataset_id:
        return None
    dataset_path = DATA_ROOT / f"{dataset_id}.pkl"
    if not dataset_path.exists():
        return None
    df = pd.read_pickle(dataset_path)
    return build_profile_from_df(dataset_id, df)


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    answer, state = run_agent_turn(req.session_id, req.message, req.context)
    dataset_id = (req.context or {}).get("dataset_id")
    return {
        "session_id": req.session_id,
        "reply": answer,
        "agent_state": state,
        "profile": _load_profile(dataset_id),
    }

@app.get("/datasets/{dataset_id}/preview")
def get_dataset_preview(dataset_id: str):
    dataset_path = DATA_ROOT / f"{dataset_id}.pkl"

    if not dataset_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"找不到数据集: {dataset_id}"
        )

    df = pd.read_pickle(dataset_path)

    profile = build_profile_from_df(
        dataset_id,
        df
    )

    return profile


class ExportRequest(BaseModel):
    dataset_id: str
    format: str = "csv"
    encoding: str = "UTF-8"
    delimiter: str = ","
    null_representation: str = ""


@app.post("/export")
def export_dataset(req: ExportRequest):
    dataset_path = DATA_ROOT / f"{req.dataset_id}.pkl"
    if not dataset_path.exists():
        raise HTTPException(status_code=404, detail=f"找不到数据集: {req.dataset_id}")

    df = pd.read_pickle(dataset_path)
    if req.null_representation != "":
        df = df.fillna(req.null_representation)

    fmt = (req.format or "csv").lower()
    if fmt == "xlsx":
        buf = BytesIO()
        df.to_excel(buf, index=False)
        buf.seek(0)
        filename = f"{req.dataset_id}.xlsx"
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return StreamingResponse(
            buf,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    sep = "\t" if req.delimiter == "\\t" else req.delimiter
    buf = BytesIO()
    text = df.to_csv(index=False, sep=sep)
    buf.write(text.encode(req.encoding, errors="replace"))
    buf.seek(0)
    filename = f"{req.dataset_id}.csv"
    return StreamingResponse(
        buf,
        media_type="text/csv; charset=" + req.encoding,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )