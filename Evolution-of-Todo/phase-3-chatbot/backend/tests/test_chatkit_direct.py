"""Direct ChatKit endpoint test with detailed error tracking."""

import asyncio
import sys
import httpx
from uuid import uuid4

# Fix UTF-8 for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


async def test_chatkit_endpoint():
    """Test ChatKit endpoint directly."""
    print("="*80)
    print("DIRECT CHATKIT ENDPOINT TEST")
    print("="*80)

    BASE_URL = "http://localhost:8000/api/v1"
    unique_id = uuid4().hex[:8]
    email = f"test_{unique_id}@example.com"
    password = "TestPass123!"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Register
        print(f"\n1. Registering user: {email}")
        register_response = await client.post(
            f"{BASE_URL}/auth/register",
            json={"email": email, "password": password, "full_name": "Test User"}
        )
        print(f"   Status: {register_response.status_code}")

        # Step 2: Login
        print(f"\n2. Logging in...")
        login_response = await client.post(
            f"{BASE_URL}/auth/login",
            json={"email": email, "password": password}
        )
        if login_response.status_code != 200:
            print(f"   ✗ Login failed: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            return

        data = login_response.json()
        token = data["data"]["token"]
        print(f"   ✓ Token obtained: {token[:20]}...")

        # Step 3: Test ChatKit root endpoint
        print(f"\n3. Testing ChatKit root endpoint (GET)...")
        chatkit_root_response = await client.get(
            f"{BASE_URL}/chatkit/",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"   Status: {chatkit_root_response.status_code}")
        print(f"   Response: {chatkit_root_response.text[:200]}")

        # Step 4: Test sessions endpoint
        print(f"\n4. Creating ChatKit session (POST /chatkit/sessions)...")
        try:
            session_response = await client.post(
                f"{BASE_URL}/chatkit/sessions",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={}
            )
            print(f"   Status: {session_response.status_code}")
            print(f"   Headers: {dict(session_response.headers)}")
            print(f"   Response: {session_response.text}")

            if session_response.status_code == 200:
                print(f"\n   ✓ SUCCESS! Session created")
                return True
            else:
                print(f"\n   ✗ FAILED with status {session_response.status_code}")
                return False

        except Exception as e:
            print(f"   ✗ Exception during request: {type(e).__name__}: {e}")
            return False


if __name__ == "__main__":
    result = asyncio.run(test_chatkit_endpoint())
    print("\n" + "="*80)
    print(f"Result: {'PASS' if result else 'FAIL'}")
    print("="*80)
