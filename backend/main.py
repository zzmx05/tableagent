from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dotenv import load_dotenv
import os

from openai import OpenAI
from agent.planner import plan
from agent.state import AgentState


# 加载.env
load_dotenv()


client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL")
)


app = FastAPI(
    title="Table Agent Backend"
)


# 允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求格式
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    session_id: str
    message: str
    history: list[Message] = []
    context: dict = {}


# 返回格式
class ChatResponse(BaseModel):
    session_id: str
    reply: str
    agent_state: AgentState


@app.get("/")
def root():
    return {
        "message":"Table Agent Backend Running"
    }



@app.post(
    "/chat",
    response_model=ChatResponse
)
def chat(req:ChatRequest):
    state = plan(req.message)

    messages = [
        {
            "role":"system",
            "content":
            """
            你是一个智能表格分析Agent。

            你的职责：
            1. 理解用户的数据分析需求
            2. 给出解释
            3. 判断是否需要调用工具

            当前任务状态:
            意图:
            {state.intent}

            是否需要工具:
            {state.need_tool}

            工具:
            {state.tool_name}

            请根据任务回答用户。
            """
        }
    ]


    # 加入历史消息
    for item in req.history:
        messages.append(
            {
                "role":item.role,
                "content":item.content
            }
        )


    # 当前消息

    messages.append(
        {
            "role":"user",
            "content":req.message
        }
    )



    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages
    )


    answer = (
        response
        .choices[0]
        .message
        .content
    )


    return {
        "session_id":req.session_id,
        "reply":answer,
        "agent_state":state
        }