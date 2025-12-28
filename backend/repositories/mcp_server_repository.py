"""
MCP 服务数据访问层（Repository）
封装所有 MCP 服务相关的数据库操作
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, update, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.db_models import McpServerDB


class McpServerRepository:
    """MCP 服务仓储类"""

    def __init__(self, session: AsyncSession):
        """
        初始化 MCP 服务仓储

        Args:
            session: 数据库会话
        """
        self.session = session

    async def get_all(self) -> List[McpServerDB]:
        """
        获取所有 MCP 服务

        Returns:
            List[McpServerDB]: MCP 服务列表
        """
        result = await self.session.execute(
            select(McpServerDB).order_by(McpServerDB.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, server_id: int) -> Optional[McpServerDB]:
        """
        根据 ID 获取 MCP 服务

        Args:
            server_id: MCP 服务 ID

        Returns:
            Optional[McpServerDB]: MCP 服务对象，不存在则返回 None
        """
        result = await self.session.execute(
            select(McpServerDB).where(McpServerDB.id == server_id)
        )
        return result.scalar_one_or_none()

    async def get_by_prefix(self, prefix: str) -> Optional[McpServerDB]:
        """
        根据前缀获取 MCP 服务

        Args:
            prefix: MCP 前缀

        Returns:
            Optional[McpServerDB]: MCP 服务对象，不存在则返回 None
        """
        result = await self.session.execute(
            select(McpServerDB).where(McpServerDB.prefix == prefix)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        name: str,
        prefix: str,
        description: str,
        combination_ids: list
    ) -> McpServerDB:
        """
        创建 MCP 服务

        Args:
            name: MCP 服务名称
            prefix: MCP 前缀（唯一标识）
            description: MCP 服务描述
            combination_ids: 组合 ID 列表

        Returns:
            McpServerDB: 创建的 MCP 服务对象
        """
        db_obj = McpServerDB(
            name=name,
            prefix=prefix,
            description=description,
            combination_ids=combination_ids,
            status="active",
        )

        self.session.add(db_obj)
        await self.session.flush()  # 刷新以获取 ID
        await self.session.refresh(db_obj)  # 刷新以获取所有字段

        return db_obj

    async def update(
        self,
        server_id: int,
        name: Optional[str] = None,
        prefix: Optional[str] = None,
        description: Optional[str] = None,
        combination_ids: Optional[list] = None
    ) -> Optional[McpServerDB]:
        """
        更新 MCP 服务

        Args:
            server_id: MCP 服务 ID
            name: 新名称（可选）
            prefix: 新前缀（可选）
            description: 新描述（可选）
            combination_ids: 新组合 ID 列表（可选）

        Returns:
            Optional[McpServerDB]: 更新后的 MCP 服务对象
        """
        # 构建更新字典
        updates = {"updated_at": datetime.now()}
        if name is not None:
            updates["name"] = name
        if prefix is not None:
            updates["prefix"] = prefix
        if description is not None:
            updates["description"] = description
        if combination_ids is not None:
            updates["combination_ids"] = combination_ids

        # 执行更新
        result = await self.session.execute(
            update(McpServerDB)
            .where(McpServerDB.id == server_id)
            .values(**updates)
            .returning(McpServerDB)
        )

        await self.session.flush()
        return result.scalar_one_or_none()

    async def delete(self, server_id: int) -> bool:
        """
        删除 MCP 服务

        Args:
            server_id: MCP 服务 ID

        Returns:
            bool: 删除成功返回 True，否则返回 False
        """
        result = await self.session.execute(
            delete(McpServerDB).where(McpServerDB.id == server_id)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def toggle_status(self, server_id: int) -> Optional[McpServerDB]:
        """
        切换 MCP 服务状态（active <-> inactive）

        Args:
            server_id: MCP 服务 ID

        Returns:
            Optional[McpServerDB]: 更新后的 MCP 服务对象
        """
        # 先获取当前状态
        server = await self.get_by_id(server_id)
        if not server:
            return None

        # 切换状态
        new_status = "inactive" if server.status == "active" else "active"

        # 更新状态
        result = await self.session.execute(
            update(McpServerDB)
            .where(McpServerDB.id == server_id)
            .values(status=new_status, updated_at=datetime.now())
            .returning(McpServerDB)
        )

        await self.session.flush()
        return result.scalar_one_or_none()

    async def search(self, keyword: str) -> List[McpServerDB]:
        """
        搜索 MCP 服务（按名称、前缀或描述）

        Args:
            keyword: 搜索关键词

        Returns:
            List[McpServerDB]: 匹配的 MCP 服务列表
        """
        search_pattern = f"%{keyword}%"

        result = await self.session.execute(
            select(McpServerDB)
            .where(
                or_(
                    McpServerDB.name.like(search_pattern),
                    McpServerDB.prefix.like(search_pattern),
                    McpServerDB.description.like(search_pattern)
                )
            )
            .order_by(McpServerDB.created_at.desc())
        )

        return list(result.scalars().all())

    async def check_prefix_exists(self, prefix: str, exclude_id: Optional[int] = None) -> bool:
        """
        检查 MCP 前缀是否已存在

        Args:
            prefix: 要检查的前缀
            exclude_id: 要排除的 ID（用于更新时检查）

        Returns:
            bool: 存在返回 True，否则返回 False
        """
        query = select(McpServerDB).where(McpServerDB.prefix == prefix)

        if exclude_id is not None:
            query = query.where(McpServerDB.id != exclude_id)

        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
