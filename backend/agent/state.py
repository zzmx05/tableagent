from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ToolCallState(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[str] = None

class AgentState(BaseModel):
    intent: str = "chat"
    need_tool: bool = False
    tool_name: Optional[str] = None
    description: Optional[str] = None
    tool_result: Optional[Any] = None
    error: Optional[str] = None
    tool_calls: List[ToolCallState] = Field(default_factory=list)
    turn_id: Optional[str] = None
