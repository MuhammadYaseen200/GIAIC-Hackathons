"""Quick OpenRouter Connection Test.

Verifies the backend can successfully communicate with OpenRouter API.
"""

import asyncio
import sys
import httpx
from uuid import uuid4

# Fix UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


async def test_openrouter_connection():
    """Test OpenRouter connection via backend API."""
    print("="*80)
    print("OPENROUTER CONNECTION TEST")
    print("="*80)

    # Test user credentials
    unique_id = uuid4().hex[:8]
    email = f"test_{unique_id}@example.com"
    password = "TestPass123!"

    BASE_URL = "http://localhost:8000/api/v1"

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Step 1: Register
        print(f"\n→ Registering user: {email}")
        register_response = await client.post(
            f"{BASE_URL}/auth/register",
            json={"email": email, "password": password, "full_name": "Test User"}
        )
        if register_response.status_code in [200, 201]:
            print("  ✓ User registered")
        else:
            print(f"  ⚠ Registration failed: {register_response.status_code}")

        # Step 2: Login
        print(f"\n→ Logging in...")
        login_response = await client.post(
            f"{BASE_URL}/auth/login",
            json={"email": email, "password": password}
        )
        if login_response.status_code == 200:
            data = login_response.json()
            token = data["data"]["token"]
            print("  ✓ Login successful")
        else:
            print(f"  ✗ Login failed: {login_response.status_code}")
            return False

        # Step 3: Create ChatKit session
        print(f"\n→ Creating ChatKit session...")
        session_response = await client.post(
            f"{BASE_URL}/chatkit/sessions",
            headers={"Authorization": f"Bearer {token}"}
        )
        if session_response.status_code == 200:
            session_data = session_response.json()
            session_id = session_data.get("id")
            print(f"  ✓ Session created: {session_id}")
        else:
            print(f"  ✗ Session creation failed: {session_response.status_code}")
            print(f"  Response: {session_response.text}")
            return False

        # Step 4: Create thread
        print(f"\n→ Creating chat thread...")
        thread_response = await client.post(
            f"{BASE_URL}/chatkit/sessions/{session_id}/threads",
            headers={"Authorization": f"Bearer {token}"}
        )
        if thread_response.status_code == 200:
            thread_data = thread_response.json()
            thread_id = thread_data.get("id")
            print(f"  ✓ Thread created: {thread_id}")
        else:
            print(f"  ✗ Thread creation failed: {thread_response.status_code}")
            print(f"  Response: {thread_response.text}")
            return False

        # Step 5: Send message to OpenRouter
        print(f"\n→ Sending test message to OpenRouter...")
        print(f"  Message: 'Add task: Buy Milk'")

        message_response = await client.post(
            f"{BASE_URL}/chatkit/sessions/{session_id}/threads/{thread_id}/runs",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "message": {
                    "role": "user",
                    "content": [{"type": "input_text", "text": "Add task: Buy Milk"}]
                }
            }
        )

        if message_response.status_code == 200:
            print(f"  ✓ Message sent successfully (HTTP 200)")

            # Parse SSE response
            response_text = message_response.text
            print(f"\n→ Parsing response...")

            lines = response_text.strip().split("\n")
            found_content = False

            for line in lines:
                if line.startswith("data: "):
                    data_str = line[6:].strip()
                    if data_str and data_str != "[DONE]":
                        try:
                            import json
                            event = json.loads(data_str)
                            event_type = event.get("type")

                            if event_type == "thread.item.content.part.delta":
                                delta = event.get("delta", "")
                                if delta:
                                    print(f"  ← {delta}")
                                    found_content = True

                        except json.JSONDecodeError:
                            continue

            if found_content:
                print(f"\n  ✓ OpenRouter responded successfully!")
                print(f"\n→ Verifying task creation...")

                # Check if task was created
                tasks_response = await client.get(
                    f"{BASE_URL}/tasks",
                    headers={"Authorization": f"Bearer {token}"}
                )

                if tasks_response.status_code == 200:
                    tasks_data = tasks_response.json()
                    tasks = tasks_data.get("data", [])
                    print(f"  Tasks in database: {len(tasks)}")

                    if len(tasks) > 0:
                        print(f"  ✓ Task created: {tasks[0]['title']}")
                        return True
                    else:
                        print(f"  ⚠ No tasks created (AI may not have called tool)")
                        return True  # Connection works, but tool calling needs investigation
                else:
                    print(f"  ⚠ Could not verify tasks: {tasks_response.status_code}")
                    return True  # Connection works
            else:
                print(f"  ⚠ No content received in response")
                return False

        else:
            print(f"  ✗ Message failed: {message_response.status_code}")
            print(f"  Response: {message_response.text}")
            return False

    return False


if __name__ == "__main__":
    result = asyncio.run(test_openrouter_connection())

    print("\n" + "="*80)
    if result:
        print("✅ OPENROUTER CONNECTION TEST PASSED")
    else:
        print("❌ OPENROUTER CONNECTION TEST FAILED")
    print("="*80)
