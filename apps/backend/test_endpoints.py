import requests
import json

BASE_URL = "http://localhost:8000"

# First, login to get a fresh token
print("\n=== TESTING LOGIN ===")
login_response = requests.post(
    f"{BASE_URL}/api/v1/login",
    json={"username": "test_supplier", "password": "password123"}
)
print(f"Login Status: {login_response.status_code}")

if login_response.status_code == 200:
    data = login_response.json()
    token = data.get("access_token")
    print(f"Token received: {token[:50]}...")

    headers = {"Authorization": f"Bearer {token}"}

    # Test /api/suppliers/my-suppliers
    print("\n=== TESTING /api/suppliers/my-suppliers ===")
    response = requests.get(f"{BASE_URL}/api/suppliers/my-suppliers", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        suppliers = response.json()
        print(f"Suppliers: {json.dumps(suppliers, indent=2, ensure_ascii=False)}")
    else:
        print(f"Error: {response.text}")

    # Test /api/warehouses
    print("\n=== TESTING /api/warehouses ===")
    response = requests.get(f"{BASE_URL}/api/warehouses", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        warehouses = response.json()
        print(f"Warehouses count: {len(warehouses)}")
        print(f"First 3: {json.dumps(warehouses[:3], indent=2, ensure_ascii=False)}")
    else:
        print(f"Error: {response.text}")

    # Test /api/products/models
    print("\n=== TESTING /api/products/models ===")
    response = requests.get(f"{BASE_URL}/api/products/models", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        models = response.json()
        print(f"Product models: {json.dumps(models, indent=2, ensure_ascii=False)}")
    else:
        print(f"Error: {response.text}")

    # Test /api/products/colors
    print("\n=== TESTING /api/products/colors ===")
    response = requests.get(f"{BASE_URL}/api/products/colors", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        colors = response.json()
        print(f"Product colors: {json.dumps(colors, indent=2, ensure_ascii=False)}")
    else:
        print(f"Error: {response.text}")
else:
    print(f"Login failed: {login_response.text}")
