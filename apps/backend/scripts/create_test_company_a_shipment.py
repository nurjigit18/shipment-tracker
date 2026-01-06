"""
Create a test shipment for Test Company A to test multi-tenant isolation.
"""

import asyncio
import sys
from pathlib import Path

# Fix for Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.shipment import Shipment
from app.models.organization import Organization


async def create_test_shipment():
    """Create test shipment for Test Company A"""
    async with AsyncSessionLocal() as db:
        # Get Test Company A organization
        result = await db.execute(
            select(Organization).where(Organization.name == "Test Company A")
        )
        test_org = result.scalar_one_or_none()

        if not test_org:
            print("ERROR: Test Company A not found.")
            return

        shipment_id = "S-2025-00999"

        # Check if shipment already exists
        result = await db.execute(select(Shipment).where(Shipment.id == shipment_id))
        existing = result.scalar_one_or_none()

        if existing:
            print(f"Test shipment {shipment_id} already exists (Org ID: {existing.organization_id})")
            return

        # Create test shipment for Test Company A
        bags_data = [
            {"bag_id": "B-A1", "sizes": {"S": 5, "M": 10}},
            {"bag_id": "B-A2", "sizes": {"L": 8}},
        ]

        total_bags = len(bags_data)
        total_pieces = sum(sum(bag["sizes"].values()) for bag in bags_data)

        shipment = Shipment(
            id=shipment_id,
            supplier="Test Supplier A",
            warehouse="Warehouse A",
            route_type="VIA_FF",
            current_status=None,
            bags_data=bags_data,
            total_bags=total_bags,
            total_pieces=total_pieces,
            organization_id=test_org.id,
        )

        db.add(shipment)
        await db.commit()

        print(f"Created test shipment: {shipment_id}")
        print(f"  Organization: Test Company A (ID: {test_org.id})")
        print(f"  Supplier: {shipment.supplier}")
        print(f"  Total bags: {total_bags}")
        print(f"  Total pieces: {total_pieces}")


if __name__ == "__main__":
    print("=== Creating Test Company A Shipment ===\n")
    asyncio.run(create_test_shipment())
