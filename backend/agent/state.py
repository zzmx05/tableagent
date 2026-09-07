from pydantic import BaseModel
from typing import Optional


class AgentState(BaseModel):
    """
    Agent 当前状态。
    """

    intent: str

    need_tool: bool

    tool_name: Optional[str] = None

    description: Optional[str] = None

    tool_result: Optional[dict] = None

    error: Optional[str] = None