from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.warehouse import Supplier
from ...models.user_supplier import UserSupplier
from ...models.user import User

router = APIRouter()


@router.get("/my-suppliers")
async def get_my_suppliers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get suppliers assigned to the current user."""
    result = await db.execute(
        select(Supplier)
        .join(UserSupplier)
        .where(
            UserSupplier.user_id == current_user.id,
            Supplier.is_active == True
        )
        .order_by(Supplier.name)
    )
    suppliers = result.scalars().all()

    return [
        {
            "id": s.id,
            "name": s.name,
            "is_active": s.is_active,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }
        for s in suppliers
    ]


@router.get("/")
async def list_suppliers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all suppliers for the organization (admin only)."""
    result = await db.execute(
        select(Supplier)
        .where(
            Supplier.organization_id == current_user.organization_id,
            Supplier.is_active == True
        )
        .order_by(Supplier.name)
    )
    suppliers = result.scalars().all()

    return [
        {
            "id": s.id,
            "name": s.name,
            "is_active": s.is_active,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }
        for s in suppliers
    ]


@router.post("/")
async def create_supplier(
    name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new supplier."""
    # Check if supplier with same name exists
    existing = await db.execute(
        select(Supplier).where(
            Supplier.name == name,
            Supplier.organization_id == current_user.organization_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Supplier already exists")

    supplier = Supplier(
        name=name,
        organization_id=current_user.organization_id,
        is_active=True
    )
    db.add(supplier)
    await db.commit()
    await db.refresh(supplier)

    return {"id": supplier.id, "name": supplier.name}


@router.post("/{supplier_id}/assign")
async def assign_supplier_to_user(
    supplier_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Assign a supplier to a user."""
    # Verify supplier exists and belongs to organization
    result = await db.execute(
        select(Supplier).where(
            Supplier.id == supplier_id,
            Supplier.organization_id == current_user.organization_id
        )
    )
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    # Check if assignment already exists
    existing = await db.execute(
        select(UserSupplier).where(
            UserSupplier.user_id == user_id,
            UserSupplier.supplier_id == supplier_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Supplier already assigned to user")

    user_supplier = UserSupplier(
        user_id=user_id,
        supplier_id=supplier_id
    )
    db.add(user_supplier)
    await db.commit()

    return {"message": "Supplier assigned successfully"}
