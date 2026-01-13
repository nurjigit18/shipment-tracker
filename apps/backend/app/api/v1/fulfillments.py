from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.warehouse import Fulfillment, SupplierFulfillment, Supplier
from ...models.user import User

router = APIRouter()


@router.get("/debug/all-relations")
async def debug_all_relations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Debug endpoint to see all supplier-fulfillment relations."""
    # Get all suppliers (filtered by organization)
    suppliers_result = await db.execute(
        select(Supplier).where(Supplier.organization_id == current_user.organization_id)
    )
    suppliers = suppliers_result.scalars().all()

    # Get all fulfillments (filtered by organization)
    fulfillments_result = await db.execute(
        select(Fulfillment).where(Fulfillment.organization_id == current_user.organization_id)
    )
    fulfillments = fulfillments_result.scalars().all()

    # Get ALL fulfillments (no filter) to see what's wrong
    all_fulfillments_result = await db.execute(select(Fulfillment))
    all_fulfillments = all_fulfillments_result.scalars().all()

    # Get all relations
    relations_result = await db.execute(select(SupplierFulfillment))
    relations = relations_result.scalars().all()

    return {
        "your_organization_id": current_user.organization_id,
        "suppliers": [{"id": s.id, "name": s.name, "is_active": s.is_active, "org_id": s.organization_id} for s in suppliers],
        "fulfillments_in_your_org": [{"id": f.id, "name": f.name, "is_active": f.is_active, "org_id": f.organization_id} for f in fulfillments],
        "ALL_fulfillments_in_database": [{"id": f.id, "name": f.name, "is_active": f.is_active, "org_id": f.organization_id} for f in all_fulfillments],
        "relations": [{"supplier_id": r.supplier_id, "fulfillment_id": r.fulfillment_id} for r in relations],
    }


@router.get("/by-supplier/{supplier_name}")
async def get_fulfillments_by_supplier(
    supplier_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get fulfillments assigned to a specific supplier."""
    print(f"🔍 Looking for fulfillments for supplier: '{supplier_name}'")
    print(f"🔍 Organization ID: {current_user.organization_id}")

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
        print(f"❌ Supplier not found: '{supplier_name}'")
        return []

    print(f"✅ Found supplier ID: {supplier.id}")

    # Get fulfillments assigned to this supplier
    result = await db.execute(
        select(Fulfillment)
        .join(SupplierFulfillment, SupplierFulfillment.fulfillment_id == Fulfillment.id)
        .where(
            SupplierFulfillment.supplier_id == supplier.id,
            Fulfillment.is_active == True
        )
        .order_by(Fulfillment.name)
    )
    fulfillments = result.scalars().all()

    print(f"📦 Found {len(fulfillments)} fulfillments")
    for f in fulfillments:
        print(f"  - {f.name} (ID: {f.id})")

    return [
        {
            "id": f.id,
            "name": f.name,
            "is_active": f.is_active,
            "created_at": f.created_at.isoformat() if f.created_at else None,
            "updated_at": f.updated_at.isoformat() if f.updated_at else None,
        }
        for f in fulfillments
    ]


@router.get("/")
async def list_fulfillments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all fulfillments for the organization."""
    result = await db.execute(
        select(Fulfillment)
        .where(
            Fulfillment.organization_id == current_user.organization_id,
            Fulfillment.is_active == True
        )
        .order_by(Fulfillment.name)
    )
    fulfillments = result.scalars().all()

    return [
        {
            "id": f.id,
            "name": f.name,
            "is_active": f.is_active,
            "created_at": f.created_at.isoformat() if f.created_at else None,
            "updated_at": f.updated_at.isoformat() if f.updated_at else None,
        }
        for f in fulfillments
    ]


@router.post("/")
async def create_fulfillment(
    name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new fulfillment center."""
    print(f"🆕 Creating fulfillment: '{name}' for organization {current_user.organization_id}")

    # Check if fulfillment with same name exists
    existing = await db.execute(
        select(Fulfillment).where(
            Fulfillment.name == name,
            Fulfillment.organization_id == current_user.organization_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Fulfillment center already exists")

    fulfillment = Fulfillment(
        name=name,
        organization_id=current_user.organization_id,
        is_active=True
    )
    db.add(fulfillment)
    await db.commit()
    await db.refresh(fulfillment)

    print(f"✅ Created fulfillment ID {fulfillment.id}: {fulfillment.name} (org_id={fulfillment.organization_id}, is_active={fulfillment.is_active})")

    return {"id": fulfillment.id, "name": fulfillment.name}


@router.post("/{fulfillment_id}/assign-to-supplier/{supplier_id}")
async def assign_fulfillment_to_supplier(
    fulfillment_id: int,
    supplier_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Assign a fulfillment center to a supplier."""
    # Verify fulfillment exists and belongs to organization
    fulfillment_result = await db.execute(
        select(Fulfillment).where(
            Fulfillment.id == fulfillment_id,
            Fulfillment.organization_id == current_user.organization_id
        )
    )
    fulfillment = fulfillment_result.scalar_one_or_none()
    if not fulfillment:
        raise HTTPException(status_code=404, detail="Fulfillment center not found")

    # Verify supplier exists and belongs to organization
    supplier_result = await db.execute(
        select(Supplier).where(
            Supplier.id == supplier_id,
            Supplier.organization_id == current_user.organization_id
        )
    )
    supplier = supplier_result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    # Check if assignment already exists
    existing = await db.execute(
        select(SupplierFulfillment).where(
            SupplierFulfillment.supplier_id == supplier_id,
            SupplierFulfillment.fulfillment_id == fulfillment_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Fulfillment already assigned to supplier")

    supplier_fulfillment = SupplierFulfillment(
        supplier_id=supplier_id,
        fulfillment_id=fulfillment_id
    )
    db.add(supplier_fulfillment)
    await db.commit()

    return {"message": "Fulfillment assigned to supplier successfully"}


@router.post("/debug/fix-fulfillment-org/{fulfillment_id}")
async def fix_fulfillment_organization(
    fulfillment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fix a fulfillment's organization_id to match current user's organization."""
    result = await db.execute(select(Fulfillment).where(Fulfillment.id == fulfillment_id))
    fulfillment = result.scalar_one_or_none()

    if not fulfillment:
        raise HTTPException(status_code=404, detail="Fulfillment not found")

    old_org = fulfillment.organization_id
    fulfillment.organization_id = current_user.organization_id
    fulfillment.is_active = True  # Also ensure it's active

    await db.commit()

    return {
        "message": "Fixed",
        "fulfillment_id": fulfillment_id,
        "old_organization_id": old_org,
        "new_organization_id": current_user.organization_id,
    }
