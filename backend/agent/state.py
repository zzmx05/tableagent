from pydantic import BaseModel


class AgentState(BaseModel):
    """
    Agent当前状态
    """

    intent: str

    need_tool: bool

    tool_name: str | None = None

    description: str | None = None