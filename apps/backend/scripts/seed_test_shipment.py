"""
Seed script to create a test shipment.

Creates a sample shipment for testing:
- Shipment ID: S-2025-00123
- Supplier: Нарселя
- Warehouse: Казань
- Route: VIA_FF
- 3 bags with different sizes

Usage:
    python scripts/seed_test_shipment.py
"""

import asyncio
import sys
from pathlib import Path

# Fix for Windows: Use selector event loop instead of proactor
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.shipment import Shipment
from app.models.organization import Organization


async def seed_test_shipment():
    """Create test shipment if it doesn't exist"""
    async with AsyncSessionLocal() as db:
        # Get Default Company organization
        result = await db.execute(
            select(Organization).where(Organization.name == "Default Company")
        )
        default_org = result.scalar_one_or_none()

        if not default_org:
            print("ERROR: Default Company not found. Please run migration first.")
            return

        shipment_id = "S-2025-00123"

        # Check if shipment already exists
        result = await db.execute(select(Shipment).where(Shipment.id == shipment_id))
        existing = result.scalar_one_or_none()

        if existing:
            print(f"✓ Test shipment {shipment_id} already exists")
            return

        # Create test shipment
        bags_data = [
            {"bag_id": "B-1", "sizes": {"S": 10, "M": 20, "L": 15}},
            {"bag_id": "B-2", "sizes": {"M": 12, "XL": 4}},
            {"bag_id": "B-3", "sizes": {"S": 5, "M": 7, "L": 8}},
        ]

        # Calculate totals
        total_bags = len(bags_data)
        total_pieces = sum(sum(bag["sizes"].values()) for bag in bags_data)

        shipment = Shipment(
            id=shipment_id,
            supplier="Нарселя",
            warehouse="Казань",
            route_type="VIA_FF",
            current_status=None,  # No status yet - ready for first confirmation
            bags_data=bags_data,
            total_bags=total_bags,
            total_pieces=total_pieces,
            organization_id=default_org.id,
        )

        db.add(shipment)
        await db.commit()

        print(f"✓ Created test shipment: {shipment_id}")
        print(f"  Organization: Default Company")
        print(f"  Supplier: {shipment.supplier}")
        print(f"  Warehouse: {shipment.warehouse}")
        print(f"  Total bags: {total_bags}")
        print(f"  Total pieces: {total_pieces}")
        print("\nYou can now test status updates with test users!")


if __name__ == "__main__":
    print("=== Seeding Test Shipment ===\n")
    asyncio.run(seed_test_shipment())
