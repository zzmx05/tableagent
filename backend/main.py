from __future__ import annotations
import json, os, uuid
from typing import Any, Dict, List
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from openai import OpenAI
from agent.memory import memory
from agent.state import AgentState, ToolCallState
from agent.tools import registry

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
            memory.append(session_id, {"role":"assistant","content":answer})
            return answer, state

        for tc in msg.tool_calls:
            call_id, name, args = parse_tool_call(tc)
            call_state = ToolCallState(id=call_id, name=name, arguments=args)
            try:
                current = memory.load(session_id)
                result = registry.execute(name, args, current.get("context", {}))
                result = _jsonable(result)
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

@app.get("/")
def root(): return {"message":"Table Agent Backend Running", "mode":"model_tool_loop"}

@app.get("/sessions/{session_id}")
def get_session(session_id: str):
    s = memory.load(session_id)
    return {"session_id":session_id,"summary":s.get("summary",""),"messages":s.get("messages",[]),"context":s.get("context",{}),"last_tool_results":s.get("last_tool_results",[])}

@app.delete("/sessions/{session_id}")
def clear_session(session_id: str):
    memory.clear(session_id); return {"ok":True,"session_id":session_id}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    answer, state = run_agent_turn(req.session_id, req.message, req.context)
    return {"session_id":req.session_id,"reply":answer,"agent_state":state}
