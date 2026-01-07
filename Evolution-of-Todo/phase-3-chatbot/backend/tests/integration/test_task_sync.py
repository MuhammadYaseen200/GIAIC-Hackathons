"""Task list synchronization tests for AI chatbot integration.

Tests that task list refreshes correctly after chat operations.

Dependencies:
- Layer 6: E2E Chat Flow Tests (T-324)

ADR References:
- master-plan.md (Section 5.3 - Chat Server Action) - revalidatePath on task changes
"""

import asyncio
import time
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_TOKEN = "test_jwt_token_for_sync_tests"


@pytest_asyncio.fixture
async def test_client():
    """Create async test client with auth token."""
    transport = ASGITransport()
    async with AsyncClient(base_url=BASE_URL, transport=transport) as client:
        client.cookies.set("auth-token", TEST_TOKEN)
        yield client


class TestTaskSync:
    """Test suite for task list synchronization."""

    @pytest.mark.asyncio
    async def test_task_list_refreshes_after_add(self, test_client: AsyncClient):
        """Verify task list refreshes after adding a task via chat.

        Test Case: Task list sync after add operation.
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # Get initial task count
        tasks_response = await test_client.get(
            "/api/v1/tasks",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        if tasks_response.status_code == 200:
            initial_data = tasks_response.json()
            initial_count = len(initial_data.get("data", []))
        else:
            initial_count = 0

        # Add task via chat
        chat_response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Add task: Test sync add",
            },
        )

        assert chat_response.status_code == 200

        # Wait a moment for sync
        await asyncio.sleep(0.5)

        # Get updated task count
        updated_response = await test_client.get(
            "/api/v1/tasks",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        assert updated_response.status_code == 200
        updated_data = updated_response.json()
        updated_count = len(updated_data.get("data", []))

        # Verify task was added
        assert updated_count >= initial_count, f"Expected count >= {initial_count}, got {updated_count}"

        # Verify new task is in the list
        tasks = updated_data.get("data", [])
        new_task = [t for t in tasks if "Test sync add" in t.get("title", "")]
        assert len(new_task) > 0, "New task not found in list"

        print(f"Task sync after add: {initial_count} -> {updated_count}")

    @pytest.mark.asyncio
    async def test_task_list_refreshes_after_complete(self, test_client: AsyncClient):
        """Verify task list refreshes after completing a task via chat.

        Test Case: Task list sync after complete operation.
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # Create a pending task
        create_response = await test_client.post(
            "/api/v1/tasks",
            json={"title": "Test complete sync", "completed": False},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        if create_response.status_code != 200:
            pytest.skip("Failed to create test task")
            return

        task_id = create_response.json()["data"]["id"]

        # Get initial state
        initial_response = await test_client.get(
            f"/api/v1/tasks/{task_id}",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        initial_task = initial_response.json()["data"]

        assert initial_task.get("completed") is False, "Task should start as incomplete"

        # Complete task via chat
        chat_response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Complete task: Test complete sync",
            },
        )

        assert chat_response.status_code == 200

        # Wait for sync
        await asyncio.sleep(0.5)

        # Get updated state
        updated_response = await test_client.get(
            f"/api/v1/tasks/{task_id}",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        updated_task = updated_response.json()["data"]

        # Verify task was completed
        assert updated_task.get("completed") is True, "Task should be completed"

        print(f"Task sync after complete: {initial_task} -> {updated_task}")

    @pytest.mark.asyncio
    async def test_task_list_refreshes_after_update(self, test_client: AsyncClient):
        """Verify task list refreshes after updating a task via chat.

        Test Case: Task list sync after update operation.
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # Create a task
        create_response = await test_client.post(
            "/api/v1/tasks",
            json={"title": "Original Title", "description": "Original description"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        if create_response.status_code != 200:
            pytest.skip("Failed to create test task")
            return

        task_id = create_response.json()["data"]["id"]

        # Update task via chat
        chat_response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Rename 'Original Title' to 'Updated Title'",
            },
        )

        assert chat_response.status_code == 200

        # Wait for sync
        await asyncio.sleep(0.5)

        # Get updated task
        updated_response = await test_client.get(
            f"/api/v1/tasks/{task_id}",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        updated_task = updated_response.json()["data"]

        # Verify task was updated
        assert updated_task.get("title") == "Updated Title", "Task title should be updated"

        print(f"Task sync after update: {updated_task}")

    @pytest.mark.asyncio
    async def test_task_list_refreshes_after_delete(self, test_client: AsyncClient):
        """Verify task list refreshes after deleting a task via chat.

        Test Case: Task list sync after delete operation.
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # Create a task
        create_response = await test_client.post(
            "/api/v1/tasks",
            json={"title": "Delete me test", "completed": False},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        if create_response.status_code != 200:
            pytest.skip("Failed to create test task")
            return

        task_id = create_response.json()["data"]["id"]

        # Verify task exists
        exists_response = await test_client.get(
            f"/api/v1/tasks/{task_id}",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        assert exists_response.status_code == 200, "Task should exist before deletion"

        # Delete task via chat
        chat_response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Delete task: Delete me test",
            },
        )

        assert chat_response.status_code == 200

        # Wait for sync
        await asyncio.sleep(0.5)

        # Verify task was deleted
        deleted_response = await test_client.get(
            f"/api/v1/tasks/{task_id}",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        # Should return 404 or not exist
        assert deleted_response.status_code == 404, "Task should be deleted"

        print("Task sync after delete: task successfully removed")

    @pytest.mark.asyncio
    async def test_no_full_page_reload_required(self, test_client: AsyncClient):
        """Verify updates happen without full page reload.

        Test Case: Task updates should be reflected without full refresh.
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # Create a task
        create_response = await test_client.post(
            "/api/v1/tasks",
            json={"title": "No reload test", "completed": False},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        if create_response.status_code != 200:
            pytest.skip("Failed to create test task")
            return

        task_id = create_response.json()["data"]["id"]

        # Get task status
        status_response = await test_client.get(
            "/api/v1/tasks",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        assert status_response.status_code == 200

        # Complete task via chat (simulates what frontend would do)
        chat_response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Complete task: No reload test",
            },
        )

        assert chat_response.status_code == 200

        # Verify we can check status directly without reloading
        check_response = await test_client.get(
            f"/api/v1/tasks/{task_id}",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        check_task = check_response.json()["data"]

        assert check_task.get("completed") is True

        print("No full page reload required: updates reflected directly")

    @pytest.mark.asyncio
    async def test_multiple_operations_sync(self, test_client: AsyncClient):
        """Verify multiple operations sync correctly.

        Test Case: Rapid successive operations should all sync.
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # Perform multiple operations
        operations = [
            ("Add task: Multi 1", None),
            ("Add task: Multi 2", None),
            ("Add task: Multi 3", None),
        ]

        task_ids = []

        for message, expected_id in operations:
            response = await test_client.post(
                "/api/v1/chat",
                json={"user_id": test_user_id, "message": message},
            )
            assert response.status_code == 200

        # Wait for all syncs
        await asyncio.sleep(1)

        # Verify all tasks are present
        tasks_response = await test_client.get(
            "/api/v1/tasks",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        if tasks_response.status_code == 200:
            tasks = tasks_response.json().get("data", [])
            multi_tasks = [t for t in tasks if "Multi" in t.get("title", "")]
            assert len(multi_tasks) >= 3, f"Expected at least 3 tasks, got {len(multi_tasks)}"

            print(f"Multiple operations sync: {len(multi_tasks)} tasks synced")

    @pytest.mark.asyncio
    async def test_priority_sync(self, test_client: AsyncClient):
        """Verify priority changes sync correctly.

        Test Case: Priority changes should reflect in task list.
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # Create task with default priority
        create_response = await test_client.post(
            "/api/v1/tasks",
            json={"title": "Priority sync test"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        if create_response.status_code != 200:
            pytest.skip("Failed to create test task")
            return

        task_id = create_response.json()["data"]["id"]

        # Verify default priority
        initial_response = await test_client.get(
            f"/api/v1/tasks/{task_id}",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        initial_task = initial_response.json()["data"]
        assert initial_task.get("priority") == "medium", "Default should be medium"

        # Update priority via chat
        chat_response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Set priority of 'Priority sync test' to high",
            },
        )

        assert chat_response.status_code == 200

        # Wait for sync
        await asyncio.sleep(0.5)

        # Verify priority was updated
        updated_response = await test_client.get(
            f"/api/v1/tasks/{task_id}",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        updated_task = updated_response.json()["data"]
        assert updated_task.get("priority") == "high", "Priority should be high"

        print(f"Priority sync: medium -> high")

    @pytest.mark.asyncio
    async def test_tags_sync(self, test_client: AsyncClient):
        """Verify tag changes sync correctly.

        Test Case: Tag changes should reflect in task list.
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # Create task
        create_response = await test_client.post(
            "/api/v1/tasks",
            json={"title": "Tags sync test", "tags": []},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        if create_response.status_code != 200:
            pytest.skip("Failed to create test task")
            return

        task_id = create_response.json()["data"]["id"]

        # Verify no tags
        initial_response = await test_client.get(
            f"/api/v1/tasks/{task_id}",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        initial_task = initial_response.json()["data"]
        assert len(initial_task.get("tags", [])) == 0, "Should start with no tags"

        # Add tags via chat
        chat_response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Add tags Work, Urgent to 'Tags sync test'",
            },
        )

        assert chat_response.status_code == 200

        # Wait for sync
        await asyncio.sleep(0.5)

        # Verify tags were added
        updated_response = await test_client.get(
            f"/api/v1/tasks/{task_id}",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        updated_task = updated_response.json()["data"]
        tags = updated_task.get("tags", [])
        assert "Work" in tags, "Work tag should be present"
        assert "Urgent" in tags, "Urgent tag should be present"

        print(f"Tags sync: [] -> {tags}")


# Run tests if executed directly
async def main() -> None:
    """Run all task sync tests."""
    print("Running Task List Sync Tests...")

    async with AsyncClient(base_url=BASE_URL, transport=ASGITransport()) as client:
        client.cookies.set("auth-token", TEST_TOKEN)
        test_instance = TestTaskSync()

        await test_instance.test_task_list_refreshes_after_add(client)
        await test_instance.test_task_list_refreshes_after_complete(client)
        await test_instance.test_task_list_refreshes_after_update(client)
        await test_instance.test_task_list_refreshes_after_delete(client)
        await test_instance.test_no_full_page_reload_required(client)
        await test_instance.test_multiple_operations_sync(client)
        await test_instance.test_priority_sync(client)
        await test_instance.test_tags_sync(client)

    print("All task sync tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
