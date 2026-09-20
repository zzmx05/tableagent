from __future__ import annotations
import json
import os
import uuid
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
from dataset_manager import dataset_manager

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
    process_spec: Optional[Dict[str, Any]] = None

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

    dataset_manager.create_dataset(df, dataset_id=dataset_id)

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

    if not dataset_manager.exists(dataset_id):
        raise HTTPException(
            status_code=404,
            detail=f"找不到数据集: {dataset_id}"
        )

    df = dataset_manager.load_version(dataset_id)
    input_rows = len(df)
    process_spec = req.process_spec or {}

    # 1. 缺失值处理
    missing = process_spec.get("missing") or {}
    strategy = missing.get("strategy")
    column = missing.get("column")

    if strategy == "drop":
        if column:
            if column not in df.columns:
                raise HTTPException(
                    status_code=400,
                    detail=f"缺失值处理失败：找不到列 {column}"
                )

            df = df.dropna(subset=[column])
        else:
            df = df.dropna()


    elif strategy == "fill_const":
        value = missing.get("value")

        if column:
            if column not in df.columns:
                raise HTTPException(
                    status_code=400,
                    detail=f"缺失值处理失败：找不到列 {column}"
                )

            df[column] = df[column].fillna(value)

        else:
            df = df.fillna(value)


    elif strategy == "fill_mean":
        if not column:
            raise HTTPException(
                status_code=400,
                detail="均值填充必须指定 column"
            )

        if column not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"找不到列 {column}"
            )

        if not pd.api.types.is_numeric_dtype(df[column]):
            raise HTTPException(
                status_code=400,
                detail=f"{column} 不是数值列，不能使用均值填充"
            )

        df[column] = df[column].fillna(
            df[column].mean()
        )


    elif strategy == "fill_median":
        if not column:
            raise HTTPException(
                status_code=400,
                detail="中位数填充必须指定 column"
            )

        if column not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"找不到列 {column}"
            )

        if not pd.api.types.is_numeric_dtype(df[column]):
            raise HTTPException(
                status_code=400,
                detail=f"{column} 不是数值列，不能使用中位数填充"
            )

        df[column] = df[column].fillna(
            df[column].median()
        )


    elif strategy == "fill_mode":
        if not column:
            raise HTTPException(
                status_code=400,
                detail="众数填充必须指定 column"
            )

        if column not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"找不到列 {column}"
            )

        mode = df[column].mode(dropna=True)

        if mode.empty:
            raise HTTPException(
                status_code=400,
                detail=f"{column} 无法计算众数"
            )

        df[column] = df[column].fillna(
            mode.iloc[0]
        )

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
    version_info = dataset_manager.save_new_version(
        dataset_id,
        df,
        operation_name="process",
        parameters=process_spec,
    )
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
        "inputVersion": version_info["input_version"],
        "outputVersion": version_info["output_version"],
        "operationId": version_info["operation_id"],
        "profile": profile,
    }

class RollbackRequest(BaseModel):
    version: str

@app.post("/datasets/{dataset_id}/rollback")
def rollback_dataset(
    dataset_id: str,
    req: RollbackRequest,
):
    if not dataset_manager.exists(dataset_id):
        raise HTTPException(
            status_code=404,
            detail=f"找不到数据集: {dataset_id}",
        )

    try:
        metadata = dataset_manager.rollback_version(
            dataset_id,
            req.version,
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    df = dataset_manager.load_version(dataset_id)

    return {
        "status": "success",
        "datasetId": dataset_id,
        "currentVersion": metadata["current_version"],
        "profile": build_profile_from_df(dataset_id, df),
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
    if not dataset_manager.exists(dataset_id):
        return None
    df = dataset_manager.load_version(dataset_id)
    return build_profile_from_df(dataset_id, df)

def build_process_spec_from_state(
    state: AgentState
) -> Dict[str, Any]:
    spec: Dict[str, Any] = {}

    for call in state.tool_calls or []:
        if getattr(call, "error", None):
            continue

        name = call.name
        args = call.arguments or {}

        if name == "fill_missing_values":
            spec["missing"] = {
                "strategy": "fill_const",
                "column": args.get("column"),
                "value": args.get("value"),
            }

        elif name == "drop_missing_values":
            spec["missing"] = {
                "strategy": "drop",
                "column": args.get("column"),
            }

        elif name == "filter_rows":
            spec["filter"] = args.get("expression")

    return spec

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    answer, state = run_agent_turn(req.session_id,req.message,req.context)
    dataset_id = (req.context or {}).get("dataset_id")
    process_spec = build_process_spec_from_state(state)
    return {
        "session_id": req.session_id,
        "reply": answer,
        "agent_state": state,
        # Chat 不提交数据
        "profile": None,
        # 返回规划结果
        "process_spec": process_spec or None,
    }

@app.get("/datasets/{dataset_id}/preview")
def get_dataset_preview(dataset_id: str):
    if not dataset_manager.exists(dataset_id):
        raise HTTPException(
            status_code=404,
            detail=f"找不到数据集: {dataset_id}"
        )

    df = dataset_manager.load_version(dataset_id)

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
    if not dataset_manager.exists(req.dataset_id):
        raise HTTPException(status_code=404, detail=f"找不到数据集: {req.dataset_id}")

    df = dataset_manager.load_version(req.dataset_id)
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

@app.get("/datasets/{dataset_id}/versions")
def get_dataset_versions(dataset_id: str):
    if not dataset_manager.exists(dataset_id):
        raise HTTPException(
            status_code=404,
            detail=f"找不到数据集: {dataset_id}",
        )

    return {
        "datasetId": dataset_id,
        "currentVersion": dataset_manager.get_current_version(dataset_id),
        "versions": dataset_manager.list_versions(dataset_id),
    }

# # fix
# class FixRequest(BaseModel):
#     dataset_id: str
#     process_spec: Dict[str, Any]
#     error_message: str

# class FixResponse(BaseModel):
#     explanation: str
#     patch: Dict[str, Any]

# @app.post("/fix", response_model=FixResponse)
# def fix_process(req: FixRequest):

#     if not dataset_manager.exists(req.dataset_id):
#         raise HTTPException(
#             status_code=404,
#             detail=f"找不到数据集: {req.dataset_id}"
#         )

#     df = dataset_manager.load_version(
#         req.dataset_id
#     )

#     schema = [
#         {
#             "name": str(column),
#             "dtype": str(df[column].dtype),
#         }
#         for column in df.columns
#     ]

#     prompt = f"""
# 你是表格数据处理修复器。

# 当前数据字段：
# {json.dumps(schema, ensure_ascii=False)}

# 当前 process_spec：
# {json.dumps(req.process_spec, ensure_ascii=False)}

# 执行错误：
# {req.error_message}

# 你的任务是修复 process_spec。

# 只返回 JSON：

# {{
#   "explanation": "为什么失败以及如何修复",
#   "patch": {{
#   }}
# }}

# patch 只包含需要修改的字段。
# 不要执行数据操作。
# 不要虚构不存在的列。
# """

#     response = client.chat.completions.create(
#         model=MODEL,
#         messages=[
#             {
#                 "role": "system",
#                 "content":
#                     "你是表格处理参数修复器，只输出合法 JSON。"
#             },
#             {
#                 "role": "user",
#                 "content": prompt,
#             },
#         ],
#         response_format={
#             "type": "json_object"
#         },
#     )

#     raw = response.choices[0].message.content

#     try:
#         result = json.loads(raw)
#     except Exception:
#         raise HTTPException(
#             status_code=500,
#             detail="Fix 模型返回了无效 JSON"
#         )

#     return {
#         "explanation":
#             result.get("explanation", ""),
#         "patch":
#             result.get("patch", {}),
#     }