from agent.state import AgentState



def plan(user_message:str)->AgentState:
    """
    简单规则版Planner

    后续这里替换成LLM Agent Planner
    """


    message = user_message.lower()


    # 数据清洗
    if (
        "删除" in message
        or "清洗" in message
        or "空值" in message
        or "缺失" in message
    ):

        return AgentState(

            intent="data_clean",

            need_tool=True,

            tool_name="data_clean",

            description=
            "用户需要进行数据清洗操作"

        )


    # 数据统计

    elif (
        "统计" in message
        or "平均" in message
        or "数量" in message
    ):

        return AgentState(

            intent="data_analysis",

            need_tool=True,

            tool_name="statistics",

            description=
            "用户需要数据统计"

        )


    # 普通聊天

    else:

        return AgentState(

            intent="chat",

            need_tool=False,

            description=
            "普通对话"

        )