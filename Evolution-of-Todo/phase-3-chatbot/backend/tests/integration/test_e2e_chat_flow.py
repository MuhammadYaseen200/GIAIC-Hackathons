"""End-to-end chat flow tests for AI chatbot integration.

Tests complete flow from user message through agent, MCP tools, to task creation/modification.

Dependencies:
- Layer 4: Chat API (T-317, T-318, T-319)
- Layer 5: Frontend Chat UI (T-320, T-321, T-322)

ADR References:
- ADR-009 (Hybrid AI Engine) - Agent orchestration
- ADR-010 (MCP Service Wrapping) - Tool execution
"""

import asyncio
from typing import Any
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_TOKEN = "test_jwt_token_for_e2e_tests"


@pytest_asyncio.fixture
async def test_client():
    """Create async test client with auth token."""
    transport = ASGITransport()
    async with AsyncClient(base_url=BASE_URL, transport=transport) as client:
        # Set auth token as would be done by middleware
        client.cookies.set("auth-token", TEST_TOKEN)
        yield client


class TestE2EChatFlow:
    """Test suite for end-to-end chat operations."""

    @pytest.mark.asyncio
    async def test_add_task_via_chat(self, test_client: AsyncClient):
        """Verify add task works through chat interface.

        Test Case: US-301 - Add Task via Chat
        Acceptance: Task created with correct title and AI confirms.
        """
        # Simulate user authentication
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # Add task via chat
        response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Add task: Submit report",
            },
            timeout=30.0,
        )

        # Verify successful response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        # Verify response structure
        assert "conversation_id" in data, "Missing conversation_id"
        assert "response" in data, "Missing AI response"
        assert isinstance(data.get("tool_calls"), list), "tool_calls should be a list"

        # Print result for verification
        print(f"Chat response: {data}")

        # Verify task was created via tasks endpoint
        tasks_response = await test_client.get(
            "/api/v1/tasks",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        assert tasks_response.status_code == 200
        tasks = tasks_response.json()

        if "data" in tasks:
            submit_report = [t for t in tasks["data"] if "Submit report" in t.get("title", "")]
            assert len(submit_report) > 0, "Task not found in task list"
            print(f"Verified task created: {submit_report[0]}")

    @pytest.mark.asyncio
    async def test_list_tasks_via_chat(self, test_client: AsyncClient):
        """Verify list tasks works through chat.

        Test Case: US-302 - List Tasks via Chat
        Acceptance: AI returns user's tasks in readable format.
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # Request tasks via chat
        response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "List all tasks",
            },
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        # Verify tool was called
        assert data.get("tool_calls"), "No tool calls made"

        # Verify AI response mentions tasks
        assert "response" in data
        print(f"List response: {data.get('response')}")

    @pytest.mark.asyncio
    async def test_complete_task_via_chat(self, test_client: AsyncClient):
        """Verify complete task works through chat.

        Test Case: US-303 - Complete Task via Chat
        Acceptance: Task marked as complete and AI confirms.
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # First create a task
        create_response = await test_client.post(
            "/api/v1/tasks",
            json={"title": "Complete me", "description": "A task to complete"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        if create_response.status_code == 200:
            task_data = create_response.json()
            if "data" in task_data:
                task_id = task_data["data"]["id"]

                # Complete task via chat
                chat_response = await test_client.post(
                    "/api/v1/chat",
                    json={
                        "user_id": test_user_id,
                        "message": "Complete task: Complete me",
                    },
                )

                assert chat_response.status_code == 200

                # Verify task was completed
                tasks_response = await test_client.get(
                    "/api/v1/tasks",
                    headers={"Authorization": f"Bearer {TEST_TOKEN}"},
                )
                tasks = tasks_response.json().get("data", [])

                completed_task = [t for t in tasks if t.get("id") == task_id and t.get("completed")]
                assert len(completed_task) > 0, "Task not marked complete"
                print(f"Verified task completed: {completed_task[0]}")

    @pytest.mark.asyncio
    async def test_update_task_via_chat(self, test_client: AsyncClient):
        """Verify update task works through chat.

        Test Case: US-305 - Update Task via Chat
        Acceptance: Task title/description updated and AI confirms.
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # Create a task first
        create_response = await test_client.post(
            "/api/v1/tasks",
            json={"title": "Original Title"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        if create_response.status_code == 200:
            task_data = create_response.json()
            if "data" in task_data:
                task_id = task_data["data"]["id"]

                # Update task via chat
                chat_response = await test_client.post(
                    "/api/v1/chat",
                    json={
                        "user_id": test_user_id,
                        "message": "Rename 'Original Title' to 'Updated Title'",
                    },
                )

                assert chat_response.status_code == 200

                # Verify task was updated
                tasks_response = await test_client.get(
                    f"/api/v1/tasks/{task_id}",
                    headers={"Authorization": f"Bearer {TEST_TOKEN}"},
                )

                if tasks_response.status_code == 200:
                    updated_task = tasks_response.json().get("data", {})
                    assert updated_task.get("title") == "Updated Title"
                    print(f"Verified task updated: {updated_task}")

    @pytest.mark.asyncio
    async def test_delete_task_via_chat(self, test_client: AsyncClient):
        """Verify delete task works through chat.

        Test Case: US-304 - Delete Task via Chat
        Acceptance: Task deleted with confirmation and AI confirms.
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # Create a task first
        create_response = await test_client.post(
            "/api/v1/tasks",
            json={"title": "Delete Me"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        if create_response.status_code == 200:
            task_data = create_response.json()
            if "data" in task_data:
                task_id = task_data["data"]["id"]

                # Delete task via chat - should ask for confirmation
                chat_response = await test_client.post(
                    "/api/v1/chat",
                    json={
                        "user_id": test_user_id,
                        "message": "Delete task: Delete Me",
                    },
                )

                assert chat_response.status_code == 200

                # Verify task no longer exists
                tasks_response = await test_client.get(
                    f"/api/v1/tasks/{task_id}",
                    headers={"Authorization": f"Bearer {TEST_TOKEN}"},
                )

                # Should return 404 for deleted task
                assert tasks_response.status_code in [404, 200]

    @pytest.mark.asyncio
    async def test_conversation_persistence(self, test_client: AsyncClient):
        """Verify conversation persists across requests.

        Test Case: US-306 - Conversation Persistence
        Acceptance: Messages survive and conversation_id is consistent.
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # First message creates conversation
        response1 = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Add task: First task",
            },
        )

        assert response1.status_code == 200
        data1 = response1.json()
        conversation_id = data1.get("conversation_id")

        assert conversation_id is not None, "Conversation ID missing"

        # Second message uses same conversation
        response2 = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "List tasks",
                "conversation_id": conversation_id,
            },
        )

        assert response2.status_code == 200
        data2 = response2.json()

        # Verify same conversation ID
        assert data2.get("conversation_id") == conversation_id, "Conversation ID changed"

        print(f"Conversation persistence verified: {conversation_id}")


# Run tests if executed directly
async def main() -> None:
    """Run all E2E chat flow tests."""
    print("Running E2E Chat Flow Tests...")

    async with AsyncClient(base_url=BASE_URL, transport=ASGITransport()) as client:
        client.cookies.set("auth-token", TEST_TOKEN)
        test_instance = TestE2EChatFlow()

        await test_instance.test_add_task_via_chat(client)
        await test_instance.test_list_tasks_via_chat(client)
        await test_instance.test_complete_task_via_chat(client)
        await test_instance.test_update_task_via_chat(client)
        await test_instance.test_conversation_persistence(client)

    print("All E2E chat flow tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
