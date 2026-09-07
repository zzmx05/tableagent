import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dotenv import load_dotenv
import os

from openai import OpenAI
from agent.planner import plan
from agent.state import AgentState
from agent.memory import memory

from tools.table_tools import (
    get_table_statistics,
    drop_missing_values
)


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

def execute_tool(
    tool_name: str,
    context: dict
):
    """
    Tool Router

    根据 Planner 指定的 tool_name
    调用对应工具。
    """

    if tool_name == "get_table_statistics":

        # 当前用于测试
        # 后续从真正上传的 DataFrame 获取

        data = context.get("data")

        if data is None:
            return {
                "message": "当前没有上传表格"
            }

        df = pd.DataFrame(data)

        return get_table_statistics(df)


    if tool_name == "drop_missing_values":

        data = context.get("data")

        if data is None:
            return {
                "message": "当前没有上传表格"
            }

        df = pd.DataFrame(data)

        column = context.get("column")

        new_df, result = drop_missing_values(
            df,
            column
        )

        return {
            "result": result,
            "data": new_df.to_dict(
                orient="records"
            )
        }


    raise ValueError(
        f"未知工具: {tool_name}"
    )

@app.post(
    "/chat",
    response_model=ChatResponse
)
def chat(req:ChatRequest):
    # 保存用户消息
    memory.add_message(
        req.session_id,
        "user",
        req.message
    )

    # Planner
    state = plan(req.message)

    # Tool执行
    if state.need_tool:

        try:

            tool_result = execute_tool(
                state.tool_name,
                req.context
            )

            state.tool_result = tool_result

        except Exception as e:

            state.error = str(e)

    messages = [
        {
            "role":"system",
            "content":f"""
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

            任务描述：
            {state.description}

            工具执行结果：
            {state.tool_result}

            工具错误：
            {state.error}

            请根据以上信息回答用户。

            如果工具已经执行成功，
            请直接解释执行结果。

            如果工具没有执行，
            请正常回答用户。
            """
        }
    ]


    # 加入历史消息
    history = memory.get_history(
    req.session_id
    )
    for item in history:
        messages.append(item)


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

    memory.add_message(
        req.session_id,
        "assistant",
        answer
    )

    return {
        "session_id":req.session_id,
        "reply":answer,
        "agent_state":state
        }