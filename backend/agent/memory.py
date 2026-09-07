from typing import Dict, List


class ConversationMemory:
    """
    简单的会话记忆管理器。

    当前版本：
    使用 Python 内存保存不同 session 的历史消息。

    后续可以替换成 Redis / PostgreSQL 等持久化存储。
    """

    def __init__(self):
        self.sessions: Dict[str, List[dict]] = {}

    def get_history(self, session_id: str) -> List[dict]:
        """
        获取某个 session 的历史消息。
        """

        return self.sessions.get(session_id, []).copy()

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str
    ):
        """
        添加一条消息。
        """

        if session_id not in self.sessions:
            self.sessions[session_id] = []

        self.sessions[session_id].append(
            {
                "role": role,
                "content": content
            }
        )

    def clear(self, session_id: str):
        """
        清除指定 session 的历史。
        """

        self.sessions.pop(session_id, None)


memory = ConversationMemory()