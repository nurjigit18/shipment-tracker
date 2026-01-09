from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.warehouse import Warehouse
from ...models.user import User

router = APIRouter()


@router.get("/")
async def list_warehouses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all active warehouses for the current organization."""
    result = await db.execute(
        select(Warehouse)
        .where(
            Warehouse.organization_id == current_user.organization_id,
            Warehouse.is_active == True
        )
        .order_by(Warehouse.name)
    )
    warehouses = result.scalars().all()

    return [{"id": w.id, "name": w.name} for w in warehouses]


@router.post("/")
async def create_warehouse(
    name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new warehouse."""
    # Check if warehouse with same name exists
    existing = await db.execute(
        select(Warehouse).where(
            Warehouse.name == name,
            Warehouse.organization_id == current_user.organization_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Warehouse already exists")

    warehouse = Warehouse(
        name=name,
        organization_id=current_user.organization_id,
        is_active=True
    )
    db.add(warehouse)
    await db.commit()
    await db.refresh(warehouse)

    return {"id": warehouse.id, "name": warehouse.name}


@router.delete("/{warehouse_id}")
async def delete_warehouse(
    warehouse_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete (deactivate) a warehouse."""
    result = await db.execute(
        select(Warehouse).where(
            Warehouse.id == warehouse_id,
            Warehouse.organization_id == current_user.organization_id
        )
    )
    warehouse = result.scalar_one_or_none()

    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    warehouse.is_active = False
    await db.commit()

    return {"message": "Warehouse deleted successfully"}
