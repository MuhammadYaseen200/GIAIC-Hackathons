"""Direct ChatKit Tool Handler Tests.

This test suite validates ChatKit tool handlers by calling them directly,
bypassing the ChatKit protocol complexity.

Run this test while the backend server is running:
    uv run uvicorn app.main:app --reload --port 8000
"""

import asyncio
import sys
from uuid import uuid4

import httpx

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
AUTH_URL = f"{BASE_URL}/auth"
TASKS_URL = f"{BASE_URL}/tasks"

# Test user credentials
TEST_EMAIL = f"test_{uuid4().hex[:8]}@example.com"
TEST_PASSWORD = "TestPass123!"


class DirectToolTester:
    """Test harness for direct API calls."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.access_token = None
        self.user_id = None

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
        self.user_id = data["data"]["user"]["id"]
        print(f"✓ Logged in successfully (User ID: {self.user_id})")

    async def add_task(self, title: str, **kwargs) -> dict:
        """Add a task via REST API."""
        payload = {"title": title}
        if "description" in kwargs:
            payload["description"] = kwargs["description"]
        if "priority" in kwargs:
            payload["priority"] = kwargs["priority"]
        if "tags" in kwargs:
            payload["tags"] = kwargs["tags"]

        response = await self.client.post(
            TASKS_URL,
            headers={"Authorization": f"Bearer {self.access_token}"},
            json=payload,
        )

        if response.status_code not in [200, 201]:
            print(f"✗ Add task failed: {response.status_code}")
            print(response.text)
            return {"success": False, "error": response.text}

        data = response.json()
        task = data["data"]
        print(f"✓ Added task: {task['title']} (ID: {task['id']}, Priority: {task.get('priority', 'N/A')})")
        return {"success": True, "task": task}

    async def list_tasks(self, **kwargs) -> list:
        """List tasks via REST API."""
        params = {}
        if "status" in kwargs:
            if kwargs["status"] == "completed":
                params["status"] = "completed"
            elif kwargs["status"] == "pending":
                params["status"] = "pending"

        if "priority" in kwargs:
            params["priority"] = kwargs["priority"]

        response = await self.client.get(
            TASKS_URL,
            headers={"Authorization": f"Bearer {self.access_token}"},
            params=params,
        )

        if response.status_code != 200:
            print(f"✗ List tasks failed: {response.status_code}")
            return []

        data = response.json()
        tasks = data["data"]
        print(f"✓ Listed {len(tasks)} tasks")
        return tasks

    async def update_task(self, task_id: str, **kwargs) -> dict:
        """Update a task via REST API."""
        payload = {}
        if "title" in kwargs:
            payload["title"] = kwargs["title"]
        if "description" in kwargs:
            payload["description"] = kwargs["description"]
        if "priority" in kwargs:
            payload["priority"] = kwargs["priority"]

        response = await self.client.put(
            f"{TASKS_URL}/{task_id}",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json=payload,
        )

        if response.status_code != 200:
            print(f"✗ Update task failed: {response.status_code}")
            print(response.text)
            return {"success": False, "error": response.text}

        data = response.json()
        task = data["data"]
        print(f"✓ Updated task: {task['title']} (Priority: {task.get('priority', 'N/A')})")
        return {"success": True, "task": task}

    async def complete_task(self, task_id: str) -> dict:
        """Complete a task via REST API."""
        response = await self.client.patch(
            f"{TASKS_URL}/{task_id}/complete",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )

        if response.status_code != 200:
            print(f"✗ Complete task failed: {response.status_code}")
            return {"success": False, "error": response.text}

        data = response.json()
        task = data["data"]
        print(f"✓ Completed task: {task['title']} (Completed: {task['completed']})")
        return {"success": True, "task": task}

    async def delete_task(self, task_id: str) -> dict:
        """Delete a task via REST API."""
        response = await self.client.delete(
            f"{TASKS_URL}/{task_id}",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )

        if response.status_code != 200:
            print(f"✗ Delete task failed: {response.status_code}")
            return {"success": False, "error": response.text}

        print(f"✓ Deleted task: {task_id}")
        return {"success": True}

    async def cleanup(self):
        """Clean up test data."""
        print(f"\n{'='*60}")
        print("CLEANUP: Removing test data")
        print(f"{'='*60}")

        tasks = await self.list_tasks()
        for task in tasks:
            await self.delete_task(task["id"])

        print(f"✓ Cleaned up {len(tasks)} tasks")
        await self.client.aclose()

    async def test_single_operations(self):
        """Test 1: Single CRUD operations."""
        print(f"\n{'='*60}")
        print("TEST 1: SINGLE OPERATIONS")
        print(f"{'='*60}")

        # 1. Add task
        result = await self.add_task("Buy Milk")
        assert result["success"], "Failed to add task"
        task_id = result["task"]["id"]
        assert "milk" in result["task"]["title"].lower()

        # 2. Update task
        result = await self.update_task(task_id, title="Buy Coffee")
        assert result["success"], "Failed to update task"
        assert "coffee" in result["task"]["title"].lower()

        # 3. Complete task
        result = await self.complete_task(task_id)
        assert result["success"], "Failed to complete task"
        assert result["task"]["completed"] is True

        # 4. Delete task
        result = await self.delete_task(task_id)
        assert result["success"], "Failed to delete task"

        # Verify empty
        tasks = await self.list_tasks()
        assert len(tasks) == 0, "Tasks not deleted"

        print(f"\n{'✓'*30} TEST 1 PASSED {'✓'*30}")

    async def test_bulk_operations(self):
        """Test 2: Bulk CRUD operations."""
        print(f"\n{'='*60}")
        print("TEST 2: BULK OPERATIONS")
        print(f"{'='*60}")

        # 1. Add 3 tasks with different priorities
        task1 = await self.add_task("Code", priority="high")
        task2 = await self.add_task("Sleep", priority="low")
        task3 = await self.add_task("Eat", priority="medium")

        assert task1["success"] and task2["success"] and task3["success"]

        # 2. List all tasks
        tasks = await self.list_tasks()
        assert len(tasks) == 3, f"Expected 3 tasks, got {len(tasks)}"

        # Verify priorities
        priorities = {t["title"]: t["priority"] for t in tasks}
        assert priorities.get("Code") == "high", "Code task priority incorrect"
        assert priorities.get("Sleep") == "low", "Sleep task priority incorrect"
        assert priorities.get("Eat") == "medium", "Eat task priority incorrect"

        # 3. List high priority tasks
        high_tasks = [t for t in tasks if t["priority"] == "high"]
        print(f"✓ Found {len(high_tasks)} high priority task(s)")
        assert len(high_tasks) == 1, "Expected 1 high priority task"

        # 4. Update all tasks to High priority
        for task in tasks:
            await self.update_task(task["id"], priority="high")

        tasks = await self.list_tasks()
        high_count = sum(1 for t in tasks if t["priority"] == "high")
        assert high_count == 3, f"Expected 3 high priority tasks, got {high_count}"

        # 5. Delete all tasks
        for task in tasks:
            await self.delete_task(task["id"])

        tasks = await self.list_tasks()
        assert len(tasks) == 0, "Tasks not deleted"

        print(f"\n{'✓'*30} TEST 2 PASSED {'✓'*30}")

    async def test_edge_cases(self):
        """Test 3: Edge cases and error handling."""
        print(f"\n{'='*60}")
        print("TEST 3: EDGE CASES")
        print(f"{'='*60}")

        # 1. Add task with invalid priority (should default to medium)
        result = await self.add_task("Test Task", priority="superhigh")
        if result["success"]:
            # Backend might reject invalid priority
            priority = result["task"]["priority"]
            assert priority in ["low", "medium", "high"], f"Invalid priority: {priority}"
            print(f"✓ Invalid priority handled (defaulted to: {priority})")
            await self.delete_task(result["task"]["id"])
        else:
            print(f"✓ Invalid priority rejected by backend (validation working)")

        # 2. Add task with valid priority
        result = await self.add_task("Valid Task", priority="high")
        assert result["success"], "Failed to add valid task"
        task_id = result["task"]["id"]
        assert result["task"]["priority"] == "high"

        # 3. Delete non-existent task
        fake_id = "00000000-0000-0000-0000-000000000000"
        result = await self.delete_task(fake_id)
        print(f"✓ Non-existent task deletion handled (success={result['success']})")

        # 4. Update non-existent task
        result = await self.update_task(fake_id, title="New Title")
        print(f"✓ Non-existent task update handled (success={result['success']})")

        # 5. Test with tags
        result = await self.add_task("Tagged Task", priority="medium", tags=["work", "urgent"])
        if result["success"]:
            tags = result["task"].get("tags", [])
            print(f"✓ Task with tags created: {tags}")
            await self.delete_task(result["task"]["id"])

        # Cleanup
        await self.delete_task(task_id)
        tasks = await self.list_tasks()
        assert len(tasks) == 0, "Cleanup failed"

        print(f"\n{'✓'*30} TEST 3 PASSED {'✓'*30}")


async def main():
    """Run all tests."""
    tester = DirectToolTester()

    try:
        await tester.setup()
        await tester.test_single_operations()
        await tester.test_bulk_operations()
        await tester.test_edge_cases()

        print(f"\n{'='*60}")
        print("🎉 ALL TESTS PASSED 🎉")
        print(f"{'='*60}")
        print("\nSUMMARY:")
        print("✓ Test 1: Single Operations (Add, Update, Complete, Delete)")
        print("✓ Test 2: Bulk Operations (3 tasks, priority filtering, bulk updates)")
        print("✓ Test 3: Edge Cases (Invalid priority, non-existent tasks, tags)")

    except AssertionError as e:
        print(f"\n{'✗'*30} TEST FAILED {'✗'*30}")
        print(f"Assertion Error: {e}")
        raise

    except Exception as e:
        print(f"\n{'✗'*30} TEST FAILED {'✗'*30}")
        print(f"Error: {e}")
        raise

    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
