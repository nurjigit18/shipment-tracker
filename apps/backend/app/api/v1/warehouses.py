from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.warehouse import Warehouse, Supplier, SupplierWarehouse
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


@router.get("/by-supplier/{supplier_name}")
async def get_warehouses_by_supplier(
    supplier_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get warehouses assigned to a specific supplier."""
    # First find the supplier
    supplier_result = await db.execute(
        select(Supplier).where(
            Supplier.name == supplier_name,
            Supplier.organization_id == current_user.organization_id,
            Supplier.is_active == True
        )
    )
    supplier = supplier_result.scalar_one_or_none()
    if not supplier:
        return []

    # Get warehouses assigned to this supplier
    result = await db.execute(
        select(Warehouse)
        .join(SupplierWarehouse, SupplierWarehouse.warehouse_id == Warehouse.id)
        .where(
            SupplierWarehouse.supplier_id == supplier.id,
            Warehouse.is_active == True
        )
        .order_by(Warehouse.name)
    )
    warehouses = result.scalars().all()

    return [{"id": w.id, "name": w.name} for w in warehouses]


@router.post("/create-and-assign")
async def create_warehouse_and_assign_to_supplier(
    name: str,
    supplier_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new warehouse and assign it to a supplier in one step."""
    # Find the supplier
    supplier_result = await db.execute(
        select(Supplier).where(
            Supplier.name == supplier_name,
            Supplier.organization_id == current_user.organization_id,
            Supplier.is_active == True
        )
    )
    supplier = supplier_result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    # Check if warehouse already exists for this organization
    existing = await db.execute(
        select(Warehouse).where(
            Warehouse.name == name,
            Warehouse.organization_id == current_user.organization_id
        )
    )
    warehouse = existing.scalar_one_or_none()

    if warehouse:
        # Warehouse exists, just check if it's already assigned to this supplier
        relation_check = await db.execute(
            select(SupplierWarehouse).where(
                SupplierWarehouse.supplier_id == supplier.id,
                SupplierWarehouse.warehouse_id == warehouse.id
            )
        )
        if relation_check.scalar_one_or_none():
            # Already assigned
            return {"id": warehouse.id, "name": warehouse.name, "message": "Warehouse already assigned to supplier"}

        # Assign existing warehouse to supplier
        supplier_warehouse = SupplierWarehouse(
            supplier_id=supplier.id,
            warehouse_id=warehouse.id
        )
        db.add(supplier_warehouse)
        await db.commit()
        return {"id": warehouse.id, "name": warehouse.name, "message": "Existing warehouse assigned to supplier"}

    # Create new warehouse
    warehouse = Warehouse(
        name=name,
        organization_id=current_user.organization_id,
        is_active=True
    )
    db.add(warehouse)
    await db.flush()  # Get the ID without committing

    # Assign to supplier
    supplier_warehouse = SupplierWarehouse(
        supplier_id=supplier.id,
        warehouse_id=warehouse.id
    )
    db.add(supplier_warehouse)
    await db.commit()
    await db.refresh(warehouse)

    return {"id": warehouse.id, "name": warehouse.name, "message": "Warehouse created and assigned to supplier"}


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
