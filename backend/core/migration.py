"""
数据迁移模块
负责从 JSON 文件自动迁移数据到数据库
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.db_models import CombinationDB, McpServerDB
from .config import MigrationConfig


class DataMigrator:
    """
    数据迁移器
    负责将现有 JSON 文件数据迁移到数据库
    """

    def __init__(
        self,
        session: AsyncSession,
        config: MigrationConfig,
        data_dir: Path
    ):
        """
        初始化数据迁移器

        Args:
            session: 数据库会话
            config: 迁移配置
            data_dir: 数据目录路径
        """
        self.session = session
        self.config = config
        self.data_dir = Path(data_dir)
        self.combinations_file = self.data_dir / "combinations.json"
        self.mcp_servers_file = self.data_dir / "mcp_servers.json"

    async def should_migrate(self) -> bool:
        """
        判断是否需要执行迁移

        Returns:
            bool: True 表示需要迁移，False 表示不需要
        """
        # 检查是否启用迁移
        if not self.config.enabled:
            print("⏭️  数据迁移已禁用（migration.enabled = false）")
            return False

        # 检查 JSON 文件是否存在
        has_json = self.combinations_file.exists() or self.mcp_servers_file.exists()
        if not has_json:
            print("⏭️  未找到 JSON 文件，跳过迁移")
            return False

        # 检查数据库是否已有数据
        result = await self.session.execute(select(CombinationDB).limit(1))
        has_data = result.first() is not None

        if has_data:
            print("⏭️  数据库已有数据，跳过迁移")
            return False

        print("✅ 检测到 JSON 文件且数据库为空，准备执行迁移...")
        return True

    async def migrate(self):
        """执行数据迁移（JSON → 数据库）"""
        print("🚀 开始数据迁移...")

        try:
            # 迁移 Combinations
            combinations_count = 0
            if self.combinations_file.exists():
                combinations_count = await self._migrate_combinations()

            # 迁移 MCP Servers
            servers_count = 0
            if self.mcp_servers_file.exists():
                servers_count = await self._migrate_mcp_servers()

            # 提交事务
            await self.session.commit()

            print(f"✅ 数据迁移完成！")
            print(f"   - 组合: {combinations_count} 条")
            print(f"   - MCP 服务: {servers_count} 条")

            # 备份 JSON 文件
            if self.config.backup_json:
                self._backup_json_files()

        except Exception as e:
            await self.session.rollback()
            print(f"❌ 数据迁移失败: {e}")
            raise

    async def _migrate_combinations(self) -> int:
        """
        迁移组合数据

        Returns:
            int: 迁移成功的记录数
        """
        print(f"📦 正在迁移组合数据: {self.combinations_file}")

        with open(self.combinations_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        combinations = data.get("combinations", {})
        migrated_count = 0

        for id_str, comb_data in combinations.items():
            try:
                comb_id = int(id_str)

                # 检查是否已存在
                result = await self.session.execute(
                    select(CombinationDB).where(CombinationDB.id == comb_id)
                )
                existing = result.scalar_one_or_none()

                if existing:
                    if self.config.on_conflict == "skip":
                        print(f"  ⏭️  组合 {comb_id} 已存在，跳过")
                        continue
                    elif self.config.on_conflict == "fail":
                        raise ValueError(f"组合 {comb_id} 已存在")

                # 创建数据库记录
                db_obj = CombinationDB(
                    id=comb_id,
                    name=comb_data["name"],
                    description=comb_data.get("description", ""),
                    status=comb_data.get("status", "active"),
                    endpoints=comb_data.get("endpoints", []),
                    created_at=datetime.fromisoformat(comb_data["createdAt"]),
                    updated_at=datetime.fromisoformat(comb_data["updatedAt"]),
                )

                if existing and self.config.on_conflict == "overwrite":
                    # 合并（更新）
                    await self.session.merge(db_obj)
                    print(f"  🔄 组合 {comb_id} 已更新")
                else:
                    # 新增
                    self.session.add(db_obj)
                    print(f"  ✅ 组合 {comb_id} 已添加")

                migrated_count += 1

            except Exception as e:
                error_msg = f"迁移组合 {id_str} 失败: {e}"
                print(f"  ❌ {error_msg}")
                if self.config.on_conflict == "fail":
                    raise ValueError(error_msg) from e

        return migrated_count

    async def _migrate_mcp_servers(self) -> int:
        """
        迁移 MCP 服务数据

        Returns:
            int: 迁移成功的记录数
        """
        print(f"📦 正在迁移 MCP 服务数据: {self.mcp_servers_file}")

        with open(self.mcp_servers_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 注意：MCP servers 的 JSON 结构可能是 servers 字段
        servers = data.get("servers", data.get("mcp_servers", {}))
        migrated_count = 0

        for id_str, server_data in servers.items():
            try:
                server_id = int(id_str)

                # 检查是否已存在
                result = await self.session.execute(
                    select(McpServerDB).where(McpServerDB.id == server_id)
                )
                existing = result.scalar_one_or_none()

                if existing:
                    if self.config.on_conflict == "skip":
                        print(f"  ⏭️  MCP 服务 {server_id} 已存在，跳过")
                        continue
                    elif self.config.on_conflict == "fail":
                        raise ValueError(f"MCP 服务 {server_id} 已存在")

                # 创建数据库记录
                db_obj = McpServerDB(
                    id=server_id,
                    name=server_data["name"],
                    prefix=server_data["prefix"],
                    description=server_data.get("description", ""),
                    status=server_data.get("status", "active"),
                    combination_ids=server_data.get("combination_ids", []),
                    created_at=datetime.fromisoformat(server_data["createdAt"]),
                    updated_at=datetime.fromisoformat(server_data["updatedAt"]),
                )

                if existing and self.config.on_conflict == "overwrite":
                    await self.session.merge(db_obj)
                    print(f"  🔄 MCP 服务 {server_id} 已更新")
                else:
                    self.session.add(db_obj)
                    print(f"  ✅ MCP 服务 {server_id} 已添加")

                migrated_count += 1

            except Exception as e:
                error_msg = f"迁移 MCP 服务 {id_str} 失败: {e}"
                print(f"  ❌ {error_msg}")
                if self.config.on_conflict == "fail":
                    raise ValueError(error_msg) from e

        return migrated_count

    def _backup_json_files(self):
        """备份 JSON 文件"""
        backup_dir = Path(self.config.backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 备份 combinations.json
        if self.combinations_file.exists():
            backup_path = backup_dir / f"combinations_{timestamp}.json"
            shutil.copy2(self.combinations_file, backup_path)
            print(f"💾 已备份: {backup_path}")

        # 备份 mcp_servers.json
        if self.mcp_servers_file.exists():
            backup_path = backup_dir / f"mcp_servers_{timestamp}.json"
            shutil.copy2(self.mcp_servers_file, backup_path)
            print(f"💾 已备份: {backup_path}")


async def auto_migrate_if_needed(
    session: AsyncSession,
    config: MigrationConfig,
    data_dir: Path
) -> bool:
    """
    自动检测并执行数据迁移（如果需要）

    Args:
        session: 数据库会话
        config: 迁移配置
        data_dir: 数据目录

    Returns:
        bool: True 表示执行了迁移，False 表示未执行
    """
    migrator = DataMigrator(session, config, data_dir)

    if await migrator.should_migrate():
        await migrator.migrate()
        return True

    return False
