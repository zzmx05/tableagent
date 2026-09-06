from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dotenv import load_dotenv
import os

from openai import OpenAI


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
class ChatRequest(BaseModel):
    message: str


# 返回格式
class ChatResponse(BaseModel):
    reply: str



@app.get("/")
def root():
    return {
        "message":"Table Agent Backend Running"
    }



@app.post("/chat",
          response_model=ChatResponse)
def chat(req:ChatRequest):

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role":"system",
                "content":
                """
                你是一个智能表格分析助手。
                帮助用户理解、清洗和处理数据。
                """
            },
            {
                "role":"user",
                "content":req.message
            }
        ]
    )


    answer = response.choices[0].message.content


    return {
        "reply":answer
    }