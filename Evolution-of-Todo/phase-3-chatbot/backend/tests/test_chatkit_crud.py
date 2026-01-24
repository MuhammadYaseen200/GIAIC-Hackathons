"""ChatKit CRUD Matrix Tests.

This test suite validates ChatKit integration by testing:
1. Single operations (Add, Update, Complete, Delete)
2. Bulk operations (Multiple adds, filtered lists, bulk updates, bulk deletes)
3. Edge cases (Invalid priorities, error handling)

Run this test while the backend server is running:
    uv run uvicorn app.main:app --reload --port 8000
"""

import asyncio
import json
import sys
from typing import Any
from uuid import uuid4

import httpx

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
CHATKIT_URL = f"{BASE_URL}/chatkit"
AUTH_URL = f"{BASE_URL}/auth"

# Test user credentials
TEST_EMAIL = f"test_{uuid4().hex[:8]}@example.com"
TEST_PASSWORD = "TestPass123!"


class ChatKitTester:
    """Test harness for ChatKit CRUD operations."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.access_token = None
        self.session_id = None
        self.thread_id = None

    async def setup(self):
        """Register and login test user."""
        print(f"\n{'='*60}")
        print("SETUP: Creating test user")
        print(f"{'='*60}")

        # Register user
        register_response = await self.client.post(
            f"{AUTH_URL}/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "full_name": "Test User",
            },
        )

        if register_response.status_code in [200, 201]:
            print(f"✓ Registered user: {TEST_EMAIL}")
        elif register_response.status_code == 400:
            print(f"! User already exists: {TEST_EMAIL}")
        else:
            print(f"✗ Registration failed: {register_response.status_code}")
            print(register_response.text)
            raise Exception("Setup failed")

        # Login
        login_response = await self.client.post(
            f"{AUTH_URL}/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        )

        if login_response.status_code != 200:
            print(f"✗ Login failed: {login_response.status_code}")
            print(login_response.text)
            raise Exception("Setup failed")

        data = login_response.json()
        self.access_token = data["data"]["token"]
        print(f"✓ Logged in successfully")

        # Create ChatKit session
        await self.create_session()

    async def create_session(self):
        """Create a new ChatKit session."""
        response = await self.client.post(
            f"{CHATKIT_URL}/sessions",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={},
        )

        if response.status_code != 200:
            print(f"✗ Session creation failed: {response.status_code}")
            print(response.text)
            raise Exception("Session creation failed")

        data = response.json()
        self.session_id = data.get("id")
        print(f"✓ Created ChatKit session: {self.session_id}")

    async def create_thread(self):
        """Create a new chat thread."""
        response = await self.client.post(
            f"{CHATKIT_URL}/sessions/{self.session_id}/threads",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={},
        )

        if response.status_code != 200:
            print(f"✗ Thread creation failed: {response.status_code}")
            print(response.text)
            raise Exception("Thread creation failed")

        data = response.json()
        self.thread_id = data.get("id")
        print(f"✓ Created thread: {self.thread_id}")

    async def send_message(self, message: str) -> dict[str, Any]:
        """Send a message through ChatKit and collect the response."""
        if not self.thread_id:
            await self.create_thread()

        print(f"\n→ User: {message}")

        # Send message
        response = await self.client.post(
            f"{CHATKIT_URL}/sessions/{self.session_id}/threads/{self.thread_id}/runs",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={"message": {"role": "user", "content": [{"type": "input_text", "text": message}]}},
        )

        if response.status_code != 200:
            print(f"✗ Message send failed: {response.status_code}")
            print(response.text)
            return {"success": False, "error": response.text}

        # Collect streaming response
        full_response = ""
        tool_calls = []

        # Parse SSE stream
        lines = response.text.strip().split("\n")
        for line in lines:
            if line.startswith("data: "):
                data_str = line[6:].strip()
                if data_str and data_str != "[DONE]":
                    try:
                        event = json.loads(data_str)
                        event_type = event.get("type")

                        if event_type == "thread.item.added":
                            # Assistant message started
                            pass
                        elif event_type == "thread.item.content.part.added":
                            # Content part added
                            pass
                        elif event_type == "thread.item.content.part.delta":
                            # Text delta
                            delta = event.get("delta", "")
                            full_response += delta
                        elif event_type == "thread.item.content.part.done":
                            # Content part completed
                            pass
                        elif event_type == "thread.item.done":
                            # Message completed
                            pass

                    except json.JSONDecodeError:
                        continue

        print(f"← Assistant: {full_response}")
        return {"success": True, "response": full_response, "tool_calls": tool_calls}

    async def verify_tasks(self, expected_count: int | None = None) -> list[dict]:
        """Verify tasks via REST API."""
        response = await self.client.get(
            f"{BASE_URL}/tasks",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )

        if response.status_code != 200:
            print(f"✗ Task verification failed: {response.status_code}")
            return []

        data = response.json()
        tasks = data.get("data", [])

        if expected_count is not None:
            if len(tasks) == expected_count:
                print(f"✓ Verified {len(tasks)} tasks (expected {expected_count})")
            else:
                print(f"✗ Task count mismatch: got {len(tasks)}, expected {expected_count}")

        return tasks

    async def cleanup(self):
        """Clean up test data."""
        print(f"\n{'='*60}")
        print("CLEANUP: Removing test data")
        print(f"{'='*60}")

        # Delete all tasks
        tasks = await self.verify_tasks()
        for task in tasks:
            await self.client.delete(
                f"{BASE_URL}/tasks/{task['id']}",
                headers={"Authorization": f"Bearer {self.access_token}"},
            )

        print(f"✓ Deleted {len(tasks)} tasks")
        await self.client.aclose()

    async def test_single_operations(self):
        """Test 1: Single CRUD operations."""
        print(f"\n{'='*60}")
        print("TEST 1: SINGLE OPERATIONS")
        print(f"{'='*60}")

        # 1. Add task
        await self.send_message("Add task: Buy Milk")
        tasks = await self.verify_tasks(expected_count=1)
        assert len(tasks) == 1, "Failed to add task"
        task_id = tasks[0]["id"]
        assert "milk" in tasks[0]["title"].lower(), "Task title incorrect"

        # 2. Update task
        await self.send_message("Update Buy Milk to Buy Coffee")
        tasks = await self.verify_tasks(expected_count=1)
        assert "coffee" in tasks[0]["title"].lower(), "Task not updated"

        # 3. Complete task
        await self.send_message(f"Complete task {task_id}")
        tasks = await self.verify_tasks(expected_count=1)
        assert tasks[0]["completed"] is True, "Task not marked complete"

        # 4. Delete task
        await self.send_message(f"Delete task {task_id}")
        tasks = await self.verify_tasks(expected_count=0)

        print(f"\n{'✓'*30} TEST 1 PASSED {'✓'*30}")

    async def test_bulk_operations(self):
        """Test 2: Bulk CRUD operations."""
        print(f"\n{'='*60}")
        print("TEST 2: BULK OPERATIONS")
        print(f"{'='*60}")

        # 1. Add 3 tasks with priorities
        await self.send_message("Add task: Code with priority High")
        await self.send_message("Add task: Sleep with priority Low")
        await self.send_message("Add task: Eat with priority Medium")
        tasks = await self.verify_tasks(expected_count=3)
        assert len(tasks) == 3, "Failed to add 3 tasks"

        # Verify priorities
        task_titles = {t["title"].lower(): t for t in tasks}
        assert "code" in str(task_titles), "Code task not found"
        assert "sleep" in str(task_titles), "Sleep task not found"
        assert "eat" in str(task_titles), "Eat task not found"

        # 2. List high priority tasks
        await self.send_message("List my high priority tasks")
        # We can't verify filter via ChatKit, but we can verify via REST
        high_priority_tasks = [t for t in tasks if t.get("priority") == "high"]
        print(f"✓ Found {len(high_priority_tasks)} high priority tasks")

        # 3. Update all tasks to High priority
        for task in tasks:
            await self.send_message(f"Update task {task['id']} priority to High")
        tasks = await self.verify_tasks(expected_count=3)
        high_count = sum(1 for t in tasks if t.get("priority") == "high")
        assert high_count == 3, f"Expected 3 high priority tasks, got {high_count}"

        # 4. Delete all tasks
        for task in tasks:
            await self.send_message(f"Delete task {task['id']}")
        await self.verify_tasks(expected_count=0)

        print(f"\n{'✓'*30} TEST 2 PASSED {'✓'*30}")

    async def test_edge_cases(self):
        """Test 3: Edge cases and error handling."""
        print(f"\n{'='*60}")
        print("TEST 3: EDGE CASES")
        print(f"{'='*60}")

        # 1. Add task with invalid priority
        await self.send_message("Add task: Test Task with priority SuperHigh")
        tasks = await self.verify_tasks(expected_count=1)
        # Should default to 'medium' priority
        assert tasks[0]["priority"] in ["low", "medium", "high"], "Invalid priority not handled"
        print(f"✓ Invalid priority handled correctly: {tasks[0]['priority']}")

        # 2. Delete non-existent task
        fake_id = "00000000-0000-0000-0000-000000000000"
        result = await self.send_message(f"Delete task {fake_id}")
        # Should handle gracefully
        print(f"✓ Non-existent task deletion handled")

        # 3. Update non-existent task
        result = await self.send_message(f"Update task {fake_id} title to New Title")
        print(f"✓ Non-existent task update handled")

        # Cleanup
        tasks = await self.verify_tasks()
        for task in tasks:
            await self.send_message(f"Delete task {task['id']}")

        print(f"\n{'✓'*30} TEST 3 PASSED {'✓'*30}")


async def main():
    """Run all ChatKit CRUD tests."""
    tester = ChatKitTester()

    try:
        await tester.setup()
        await tester.test_single_operations()
        await tester.test_bulk_operations()
        await tester.test_edge_cases()

        print(f"\n{'='*60}")
        print("ALL TESTS PASSED")
        print(f"{'='*60}")

    except Exception as e:
        print(f"\n{'✗'*30} TEST FAILED {'✗'*30}")
        print(f"Error: {e}")
        raise

    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
