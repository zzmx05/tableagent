"""OpenClaw-inspired local session memory.

A session owns its transcript and mutable working context. The model is not
the source of truth for state: this store is. This mirrors the useful part of
OpenClaw's design (gateway-owned sessions + durable transcript) without
connecting this project to OpenClaw.
"""
from __future__ import annotations
import json, os, threading, time, uuid
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(os.getenv("TABLE_AGENT_RUNTIME", Path(__file__).resolve().parents[1] / "runtime"))
SESSION_DIR = ROOT / "sessions"
SESSION_DIR.mkdir(parents=True, exist_ok=True)

class ConversationMemory:
    def __init__(self, max_messages: int = 40):
        self.max_messages = max_messages
        self._lock = threading.RLock()

    def _path(self, session_id: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_id)
        return SESSION_DIR / f"{safe}.json"

    def _default(self, session_id: str) -> Dict[str, Any]:
        now = time.time()
        return {"session_id": session_id, "created_at": now, "updated_at": now,
                "summary": "", "messages": [], "context": {}, "last_tool_results": []}

    def load(self, session_id: str) -> Dict[str, Any]:
        with self._lock:
            p = self._path(session_id)
            if not p.exists(): return self._default(session_id)
            try: return json.loads(p.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError): return self._default(session_id)

    def save(self, session: Dict[str, Any]) -> None:
        with self._lock:
            session["updated_at"] = time.time()
            p = self._path(session["session_id"])
            tmp = p.with_suffix(".tmp")
            tmp.write_text(json.dumps(session, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            tmp.replace(p)

    def append(self, session_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        session = self.load(session_id)
        session["messages"].append(message)
        # Keep a bounded transcript in active context. Older content is retained
        # in summary rather than silently disappearing.
        if len(session["messages"]) > self.max_messages:
            old = session["messages"][:-self.max_messages]
            session["messages"] = session["messages"][-self.max_messages:]
            compact = " ".join(str(m.get("content", "")) for m in old if m.get("content"))
            if compact:
                session["summary"] = (session.get("summary", "") + " " + compact)[-6000:]
        self.save(session)
        return session

    def update_context(self, session_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        session = self.load(session_id)
        session["context"].update(context or {})
        self.save(session)
        return session

    def add_tool_result(self, session_id: str, result: Any) -> Dict[str, Any]:
        session = self.load(session_id)
        session["last_tool_results"] = (session.get("last_tool_results", []) + [result])[-10:]
        self.save(session)
        return session

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._path(session_id).unlink(missing_ok=True)

memory = ConversationMemory()

# from typing import Dict, List


# class ConversationMemory:
#     """
#     简单的会话记忆管理器。

#     当前版本：
#     使用 Python 内存保存不同 session 的历史消息。

#     后续可以替换成 Redis / PostgreSQL 等持久化存储。
#     """

#     def __init__(self):
#         self.sessions: Dict[str, List[dict]] = {}

#     def get_history(self, session_id: str) -> List[dict]:
#         """
#         获取某个 session 的历史消息。
#         """

#         return self.sessions.get(session_id, []).copy()

#     def add_message(
#         self,
#         session_id: str,
#         role: str,
#         content: str
#     ):
#         """
#         添加一条消息。
#         """

#         if session_id not in self.sessions:
#             self.sessions[session_id] = []

#         self.sessions[session_id].append(
#             {
#                 "role": role,
#                 "content": content
#             }
#         )

#     def clear(self, session_id: str):
#         """
#         清除指定 session 的历史。
#         """

#         self.sessions.pop(session_id, None)


# memory = ConversationMemory()