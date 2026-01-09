from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.warehouse import ProductModel, ProductColor
from ...models.user import User

router = APIRouter()


@router.get("/models")
async def list_product_models(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all product models for the organization."""
    result = await db.execute(
        select(ProductModel)
        .where(ProductModel.organization_id == current_user.organization_id)
        .order_by(ProductModel.name)
    )
    models = result.scalars().all()

    return [{"id": m.id, "name": m.name} for m in models]


@router.post("/models")
async def create_product_model(
    name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new product model."""
    # Check if model with same name exists
    existing = await db.execute(
        select(ProductModel).where(
            ProductModel.name == name,
            ProductModel.organization_id == current_user.organization_id
        )
    )
    if existing.scalar_one_or_none():
        # Return existing model instead of error
        model = existing.scalar_one()
        return {"id": model.id, "name": model.name}

    model = ProductModel(
        name=name,
        organization_id=current_user.organization_id
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)

    return {"id": model.id, "name": model.name}


@router.get("/colors")
async def list_product_colors(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all product colors for the organization."""
    result = await db.execute(
        select(ProductColor)
        .where(ProductColor.organization_id == current_user.organization_id)
        .order_by(ProductColor.name)
    )
    colors = result.scalars().all()

    return [{"id": c.id, "name": c.name} for c in colors]


@router.post("/colors")
async def create_product_color(
    name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new product color."""
    # Check if color with same name exists
    existing = await db.execute(
        select(ProductColor).where(
            ProductColor.name == name,
            ProductColor.organization_id == current_user.organization_id
        )
    )
    if existing.scalar_one_or_none():
        # Return existing color instead of error
        color = existing.scalar_one()
        return {"id": color.id, "name": color.name}

    color = ProductColor(
        name=name,
        organization_id=current_user.organization_id
    )
    db.add(color)
    await db.commit()
    await db.refresh(color)

    return {"id": color.id, "name": color.name}
