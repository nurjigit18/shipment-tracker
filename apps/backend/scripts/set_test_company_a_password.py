"""
Set password for test_companyA_supplier user.
"""

import asyncio
import sys
from pathlib import Path

# Fix for Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User


async def set_password():
    """Set password for test_companyA_supplier"""
    async with AsyncSessionLocal() as db:
        # Find user
        result = await db.execute(
            select(User).where(User.username == "test_companyA_supplier")
        )
        user = result.scalar_one_or_none()

        if not user:
            print("ERROR: test_companyA_supplier not found")
            return

        # Set password
        password_hash = get_password_hash("test123")
        await db.execute(
            update(User)
            .where(User.username == "test_companyA_supplier")
            .values(password_hash=password_hash)
        )
        await db.commit()

        print(f"Password set for user: test_companyA_supplier")
        print(f"  User ID: {user.id}")
        print(f"  Organization ID: {user.organization_id}")
        print(f"  Password: test123")


if __name__ == "__main__":
    print("=== Setting Password for Test Company A User ===\n")
    asyncio.run(set_password())
