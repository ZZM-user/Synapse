# backend/api/combinations.py
"""
组合管理 API 路由
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Path, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import verify_token
from core.database import get_db
from models.combination import Combination, CombinationCreate, CombinationUpdate
from repositories.combination_repository import CombinationRepository

# 路由器级别添加鉴权依赖，所有端点都需要认证
router = APIRouter(
    prefix="/api/v1/combinations",
    tags=["combinations"],
    dependencies=[Depends(verify_token)]
)


@router.get("", response_model=list[Combination])
async def get_combinations(db: AsyncSession = Depends(get_db)):
    """
    获取所有组合列表
    """
    repo = CombinationRepository(db)
    db_combinations = await repo.get_all()
    return [Combination.from_orm(c) for c in db_combinations]


@router.get("/{combination_id}", response_model=Combination)
async def get_combination(
    combination_id: int = Path(..., description="组合 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    根据 ID 获取单个组合
    """
    repo = CombinationRepository(db)
    db_combination = await repo.get_by_id(combination_id)

    if not db_combination:
        raise HTTPException(status_code=404, detail=f"组合 ID {combination_id} 不存在")

    return Combination.from_orm(db_combination)


@router.post("", response_model=Combination, status_code=201)
async def create_combination(
    combination: CombinationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建新组合
    """
    repo = CombinationRepository(db)

    # 创建组合
    db_combination = await repo.create(
        name=combination.name,
        description=combination.description,
        endpoints=[ep.model_dump() for ep in combination.endpoints]
    )

    await db.commit()
    return Combination.from_orm(db_combination)


@router.put("/{combination_id}", response_model=Combination)
async def update_combination(
    combination_id: int = Path(..., description="组合 ID"),
    combination_update: CombinationUpdate = None,
    db: AsyncSession = Depends(get_db)
):
    """
    更新组合信息
    """
    repo = CombinationRepository(db)

    # 检查组合是否存在
    existing = await repo.get_by_id(combination_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"组合 ID {combination_id} 不存在")

    # 更新组合
    db_combination = await repo.update(
        combination_id=combination_id,
        name=combination_update.name,
        description=combination_update.description,
        endpoints=[ep.model_dump() for ep in combination_update.endpoints] if combination_update.endpoints else None
    )

    await db.commit()

    if not db_combination:
        raise HTTPException(status_code=404, detail=f"组合 ID {combination_id} 不存在")

    return Combination.from_orm(db_combination)


@router.patch("/{combination_id}/status", response_model=Combination)
async def toggle_combination_status(
    combination_id: int = Path(..., description="组合 ID"),
    status: str = Query(..., description="新状态：active 或 inactive"),
    db: AsyncSession = Depends(get_db)
):
    """
    切换组合状态（启用/停用）
    """
    if status not in ["active", "inactive"]:
        raise HTTPException(status_code=400, detail="状态值必须为 'active' 或 'inactive'")

    repo = CombinationRepository(db)

    # 检查组合是否存在
    existing = await repo.get_by_id(combination_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"组合 ID {combination_id} 不存在")

    # 手动更新状态（因为 toggle_status 会切换，而我们这里需要设置特定值）
    db_combination = await repo.update(
        combination_id=combination_id,
        name=None,
        description=None,
        endpoints=None
    )

    # 直接设置状态
    existing.status = status
    existing.updated_at = datetime.now()
    await db.flush()
    await db.commit()
    await db.refresh(existing)

    return Combination.from_orm(existing)


@router.delete("/{combination_id}", status_code=204)
async def delete_combination(
    combination_id: int = Path(..., description="组合 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    删除组合
    """
    repo = CombinationRepository(db)

    success = await repo.delete(combination_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"组合 ID {combination_id} 不存在")

    await db.commit()
    return None
