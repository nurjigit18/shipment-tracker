"""
Verify migration and database structure.
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
from app.models.organization import Organization
from app.models.user import User
from app.models.shipment import Shipment


async def verify_database():
    """Verify database structure after migration"""
    async with AsyncSessionLocal() as db:
        # Check organizations
        result = await db.execute(select(Organization))
        orgs = result.scalars().all()
        print("=== Organizations ===")
        for org in orgs:
            print(f"  ID: {org.id}, Name: {org.name}")

        # Check users with organization_id
        result = await db.execute(select(User))
        users = result.scalars().all()
        print("\n=== Users ===")
        for user in users:
            print(f"  ID: {user.id}, Username: {user.username}, Org ID: {user.organization_id}")

        # Check shipments with organization_id
        result = await db.execute(select(Shipment))
        shipments = result.scalars().all()
        print("\n=== Shipments ===")
        for shipment in shipments:
            print(f"  ID: {shipment.id}, Org ID: {shipment.organization_id}")

        print(f"\nSummary: {len(orgs)} organizations, {len(users)} users, {len(shipments)} shipments")


if __name__ == "__main__":
    print("=== Verifying Database Structure ===\n")
    asyncio.run(verify_database())
