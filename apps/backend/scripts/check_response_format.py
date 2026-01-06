"""Quick test to check actual API response format"""
import asyncio
import httpx
import json

async def check():
    async with httpx.AsyncClient() as client:
        # Login
        response = await client.post(
            "http://localhost:8000/api/auth/login",
            json={"username": "test_supplier", "password": "test123"}
        )
        token = response.json()["access_token"]

        # Get shipment
        response = await client.get(
            "http://localhost:8000/api/shipments/S-2025-00123",
            headers={"Authorization": f"Bearer {token}"}
        )

        print("Response Status:", response.status_code)
        print("\nResponse JSON (formatted):")
        print(json.dumps(response.json(), indent=2))

asyncio.run(check())
