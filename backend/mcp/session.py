"""
MCP Session Manager
管理 SSE 连接和客户端会话
"""
import asyncio
import uuid
from typing import Dict, Optional, Set
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class McpSession:
    """MCP 客户端会话"""
    session_id: str
    prefix: str  # MCP Server 前缀
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity = datetime.now()


class SessionManager:
    """会话管理器"""

    def __init__(self):
        self._sessions: Dict[str, McpSession] = {}
        self._prefix_sessions: Dict[str, Set[str]] = {}  # prefix -> set of session_ids
        self._lock = asyncio.Lock()

    async def create_session(self, prefix: str) -> McpSession:
        """
        创建新会话

        Args:
            prefix: MCP Server 前缀

        Returns:
            新创建的会话
        """
        async with self._lock:
            session_id = str(uuid.uuid4())
            session = McpSession(
                session_id=session_id,
                prefix=prefix
            )

            self._sessions[session_id] = session

            # 建立前缀到会话的映射
            if prefix not in self._prefix_sessions:
                self._prefix_sessions[prefix] = set()
            self._prefix_sessions[prefix].add(session_id)

            return session

    async def get_session(self, session_id: str) -> Optional[McpSession]:
        """获取会话"""
        return self._sessions.get(session_id)

    async def remove_session(self, session_id: str):
        """移除会话"""
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                # 从前缀映射中移除
                if session.prefix in self._prefix_sessions:
                    self._prefix_sessions[session.prefix].discard(session_id)
                    if not self._prefix_sessions[session.prefix]:
                        del self._prefix_sessions[session.prefix]

                # 移除会话
                del self._sessions[session_id]

    async def get_sessions_by_prefix(self, prefix: str) -> list[McpSession]:
        """
        获取指定前缀的所有会话

        Args:
            prefix: MCP Server 前缀

        Returns:
            会话列表
        """
        session_ids = self._prefix_sessions.get(prefix, set())
        return [
            self._sessions[sid]
            for sid in session_ids
            if sid in self._sessions
        ]

    async def broadcast_to_prefix(self, prefix: str, message: dict):
        """
        向指定前缀的所有会话广播消息

        Args:
            prefix: MCP Server 前缀
            message: 要广播的消息
        """
        sessions = await self.get_sessions_by_prefix(prefix)
        for session in sessions:
            try:
                await session.queue.put(message)
            except Exception as e:
                print(f"Failed to send message to session {session.session_id}: {e}")

    async def cleanup_stale_sessions(self, max_idle_seconds: int = 3600):
        """
        清理过期会话

        Args:
            max_idle_seconds: 最大空闲时间（秒）
        """
        async with self._lock:
            now = datetime.now()
            stale_sessions = [
                session_id
                for session_id, session in self._sessions.items()
                if (now - session.last_activity).total_seconds() > max_idle_seconds
            ]

            for session_id in stale_sessions:
                await self.remove_session(session_id)

            if stale_sessions:
                print(f"Cleaned up {len(stale_sessions)} stale sessions")

    def get_stats(self) -> dict:
        """获取会话统计信息"""
        return {
            "total_sessions": len(self._sessions),
            "sessions_by_prefix": {
                prefix: len(session_ids)
                for prefix, session_ids in self._prefix_sessions.items()
            }
        }


# 全局会话管理器实例
session_manager = SessionManager()
