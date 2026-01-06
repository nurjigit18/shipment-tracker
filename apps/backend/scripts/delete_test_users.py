"""
Delete test users with corrupted password hashes.
Run this before re-seeding test users.
"""

import asyncio
import sys
from pathlib import Path

# Fix for Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from sqlalchemy import delete
from app.models.user import User


async def delete_test_users():
    """Delete test users from database"""
    async with AsyncSessionLocal() as db:
        # Delete test users
        result = await db.execute(
            delete(User).where(
                User.username.in_(['test_supplier', 'test_ff', 'test_driver'])
            )
        )
        await db.commit()
        print(f'✓ Deleted {result.rowcount} test user(s)')


if __name__ == "__main__":
    print("=== Deleting Test Users ===\n")
    asyncio.run(delete_test_users())
