"""
组合数据访问层（Repository）
封装所有组合相关的数据库操作
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, update, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.db_models import CombinationDB


class CombinationRepository:
    """组合仓储类"""

    def __init__(self, session: AsyncSession):
        """
        初始化组合仓储

        Args:
            session: 数据库会话
        """
        self.session = session

    async def get_all(self) -> List[CombinationDB]:
        """
        获取所有组合

        Returns:
            List[CombinationDB]: 组合列表
        """
        result = await self.session.execute(
            select(CombinationDB).order_by(CombinationDB.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, combination_id: int) -> Optional[CombinationDB]:
        """
        根据 ID 获取组合

        Args:
            combination_id: 组合 ID

        Returns:
            Optional[CombinationDB]: 组合对象，不存在则返回 None
        """
        result = await self.session.execute(
            select(CombinationDB).where(CombinationDB.id == combination_id)
        )
        return result.scalar_one_or_none()

    async def create(self, name: str, description: str, endpoints: list) -> CombinationDB:
        """
        创建组合

        Args:
            name: 组合名称
            description: 组合描述
            endpoints: 端点列表

        Returns:
            CombinationDB: 创建的组合对象
        """
        db_obj = CombinationDB(
            name=name,
            description=description,
            endpoints=endpoints,
            status="active",
        )

        self.session.add(db_obj)
        await self.session.flush()  # 刷新以获取 ID
        await self.session.refresh(db_obj)  # 刷新以获取所有字段

        return db_obj

    async def update(
        self,
        combination_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        endpoints: Optional[list] = None
    ) -> Optional[CombinationDB]:
        """
        更新组合

        Args:
            combination_id: 组合 ID
            name: 新名称（可选）
            description: 新描述（可选）
            endpoints: 新端点列表（可选）

        Returns:
            Optional[CombinationDB]: 更新后的组合对象
        """
        # 构建更新字典
        updates = {"updated_at": datetime.now()}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if endpoints is not None:
            updates["endpoints"] = endpoints

        # 执行更新
        result = await self.session.execute(
            update(CombinationDB)
            .where(CombinationDB.id == combination_id)
            .values(**updates)
            .returning(CombinationDB)
        )

        await self.session.flush()
        return result.scalar_one_or_none()

    async def delete(self, combination_id: int) -> bool:
        """
        删除组合

        Args:
            combination_id: 组合 ID

        Returns:
            bool: 删除成功返回 True，否则返回 False
        """
        result = await self.session.execute(
            delete(CombinationDB).where(CombinationDB.id == combination_id)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def toggle_status(self, combination_id: int) -> Optional[CombinationDB]:
        """
        切换组合状态（active <-> inactive）

        Args:
            combination_id: 组合 ID

        Returns:
            Optional[CombinationDB]: 更新后的组合对象
        """
        # 先获取当前状态
        combination = await self.get_by_id(combination_id)
        if not combination:
            return None

        # 切换状态
        new_status = "inactive" if combination.status == "active" else "active"

        # 更新状态
        result = await self.session.execute(
            update(CombinationDB)
            .where(CombinationDB.id == combination_id)
            .values(status=new_status, updated_at=datetime.now())
            .returning(CombinationDB)
        )

        await self.session.flush()
        return result.scalar_one_or_none()

    async def search(self, keyword: str) -> List[CombinationDB]:
        """
        搜索组合（按名称或描述）

        Args:
            keyword: 搜索关键词

        Returns:
            List[CombinationDB]: 匹配的组合列表
        """
        search_pattern = f"%{keyword}%"

        result = await self.session.execute(
            select(CombinationDB)
            .where(
                or_(
                    CombinationDB.name.like(search_pattern),
                    CombinationDB.description.like(search_pattern)
                )
            )
            .order_by(CombinationDB.created_at.desc())
        )

        return list(result.scalars().all())
