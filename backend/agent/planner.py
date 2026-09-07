"""Compatibility planner. The primary planner is now the LLM tool-calling loop.
Kept only for callers that still import plan()."""
from agent.state import AgentState
def plan(user_message: str) -> AgentState:
    return AgentState(intent="chat", need_tool=False, description="LLM agent loop decides whether tools are needed")

# from agent.state import AgentState


# def plan(user_message: str) -> AgentState:
#     """
#     根据用户输入判断任务类型，
#     并决定是否需要调用工具。
#     """
#     message = user_message.lower()

#     # 删除空值
#     if (
#         "删除空值" in message
#         or "删除缺失值" in message
#         or "去除空值" in message
#         or "去除缺失值" in message
#         or "删除为空" in message
#     ):

#         return AgentState(
#             intent="data_clean",
#             need_tool=True,
#             tool_name="drop_missing_values",
#             description="删除表格中的空值记录"
#         )

#     # 数据统计
#     if (
#         "统计" in message
#         or "多少行" in message
#         or "多少列" in message
#         or "数据量" in message
#         or "缺失情况" in message
#     ):

#         return AgentState(
#             intent="data_analysis",
#             need_tool=True,
#             tool_name="get_table_statistics",
#             description="统计表格基本信息"
#         )

#     # 普通聊天
#     return AgentState(
#         intent="chat",
#         need_tool=False,
#         description="普通对话"
#     )