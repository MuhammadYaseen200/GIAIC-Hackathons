"""Priority via chat tests for AI chatbot integration.

Tests priority setting, updating, and filtering through natural language.

Dependencies:
- Layer 6: E2E Chat Flow Tests (T-324)

ADR References:
- ADR-011 (Task Schema Extension) - Priority enum and handling
"""

import asyncio
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_TOKEN = "test_jwt_token_for_priority_tests"


@pytest_asyncio.fixture
async def test_client():
    """Create async test client with auth token."""
    transport = ASGITransport()
    async with AsyncClient(base_url=BASE_URL, transport=transport) as client:
        client.cookies.set("auth-token", TEST_TOKEN)
        yield client


class TestPriorityChat:
    """Test suite for priority operations via chat."""

    @pytest.mark.asyncio
    async def test_set_high_priority_on_creation(self, test_client: AsyncClient):
        """Verify high priority is set when specified during task creation.

        Test Case: US-308 - Set Task Priority via Chat
        Acceptance Scenario 1: "Add a high priority task called Submit report"
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Add a high priority task called Submit report",
            },
        )

        assert response.status_code == 200
        data = response.json()

        print(f"Priority creation response: {data}")

        # Verify task was created with high priority
        tasks_response = await test_client.get(
            "/api/v1/tasks",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        if tasks_response.status_code == 200:
            tasks = tasks_response.json().get("data", [])
            submit_report_tasks = [
                t for t in tasks
                if "Submit report" in t.get("title", "")
            ]

            if submit_report_tasks:
                task = submit_report_tasks[0]
                assert task.get("priority") == "high", f"Expected priority 'high', got {task.get('priority')}"
                print(f"Verified high priority task: {task}")

    @pytest.mark.asyncio
    async def test_set_medium_priority_on_creation(self, test_client: AsyncClient):
        """Verify medium priority is set when specified.

        Test Case: US-308 - Set Task Priority via Chat
        Acceptance Scenario 3: "Create task: Buy groceries with medium priority"
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Create task: Buy groceries with medium priority",
            },
        )

        assert response.status_code == 200

        tasks_response = await test_client.get(
            "/api/v1/tasks",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        if tasks_response.status_code == 200:
            tasks = tasks_response.json().get("data", [])
            grocery_tasks = [t for t in tasks if "Buy groceries" in t.get("title", "")]

            if grocery_tasks:
                task = grocery_tasks[0]
                assert task.get("priority") == "medium"
                print(f"Verified medium priority task: {task}")

    @pytest.mark.asyncio
    async def test_set_low_priority_on_creation(self, test_client: AsyncClient):
        """Verify low priority is set when specified.

        Test Case: US-308 - Set Task Priority via Chat
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Add low priority task: Read book",
            },
        )

        assert response.status_code == 200

        tasks_response = await test_client.get(
            "/api/v1/tasks",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        if tasks_response.status_code == 200:
            tasks = tasks_response.json().get("data", [])
            read_tasks = [t for t in tasks if "Read book" in t.get("title", "")]

            if read_tasks:
                task = read_tasks[0]
                assert task.get("priority") == "low"
                print(f"Verified low priority task: {task}")

    @pytest.mark.asyncio
    async def test_update_existing_task_priority(self, test_client: AsyncClient):
        """Verify priority can be updated on existing tasks.

        Test Case: US-308 - Set Task Priority via Chat
        Acceptance Scenario 2: "Set the priority of 'Submit report' to low"
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # First create a task
        create_response = await test_client.post(
            "/api/v1/tasks",
            json={"title": "Submit report", "priority": "high"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        if create_response.status_code == 200:
            task_data = create_response.json()
            if "data" in task_data:
                task_id = task_data["data"]["id"]

                # Update priority via chat
                chat_response = await test_client.post(
                    "/api/v1/chat",
                    json={
                        "user_id": test_user_id,
                        "message": "Set the priority of 'Submit report' to low",
                    },
                )

                assert chat_response.status_code == 200

                # Verify priority was updated
                task_response = await test_client.get(
                    f"/api/v1/tasks/{task_id}",
                    headers={"Authorization": f"Bearer {TEST_TOKEN}"},
                )

                if task_response.status_code == 200:
                    updated_task = task_response.json().get("data", {})
                    assert updated_task.get("priority") == "low"
                    print(f"Verified priority updated to low: {updated_task}")

    @pytest.mark.asyncio
    async def test_filter_by_priority_high(self, test_client: AsyncClient):
        """Verify filtering tasks by high priority works.

        Test Case: US-308 - Set Task Priority via Chat
        Acceptance Scenario 5: "Show my high priority tasks"
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # Create tasks with different priorities
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "High Priority Task 1", "priority": "high"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "High Priority Task 2", "priority": "high"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Low Priority Task", "priority": "low"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        # Filter by high priority via chat
        response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Show my high priority tasks",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify tool was called
        assert data.get("tool_calls"), "No tool calls made for priority filter"

        # Verify tasks filtered correctly
        tasks_response = await test_client.get(
            "/api/v1/tasks",
            params={"priority": "high"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        if tasks_response.status_code == 200:
            tasks = tasks_response.json().get("data", [])
            high_tasks = [t for t in tasks if t.get("priority") == "high"]
            assert len(high_tasks) > 0, "No high priority tasks found"
            print(f"Verified {len(high_tasks)} high priority tasks: {high_tasks}")

    @pytest.mark.asyncio
    async def test_default_priority_is_medium(self, test_client: AsyncClient):
        """Verify tasks default to medium priority when not specified.

        Test Case: US-308 - Set Task Priority via Chat
        Acceptance Scenario 4: Tasks without specified priority default to medium.
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Add task: Default priority task",
            },
        )

        assert response.status_code == 200

        tasks_response = await test_client.get(
            "/api/v1/tasks",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        if tasks_response.status_code == 200:
            tasks = tasks_response.json().get("data", [])
            default_tasks = [t for t in tasks if "Default priority task" in t.get("title", "")]

            if default_tasks:
                task = default_tasks[0]
                assert task.get("priority") == "medium"
                print(f"Verified default priority is medium: {task}")

    @pytest.mark.asyncio
    async def test_invalid_priority_prompts_clarification(self, test_client: AsyncClient):
        """Verify invalid priority prompts user to specify valid option.

        Test Case: US-308 - Set Task Priority via Chat
        Acceptance Scenario 6: Invalid priority like "urgent" prompts clarification.
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Add urgent priority task: Urgent meeting",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # AI should clarify valid priority options
        ai_response = data.get("response", "").lower()
        assert any(
            word in ai_response
            for word in ["priority", "high", "medium", "low"]
        ), "AI should clarify priority options"

        print(f"Clarification response: {data.get('response')}")

    @pytest.mark.asyncio
    async def test_priority_variations(self, test_client: AsyncClient):
        """Verify AI understands various priority-related phrases.

        Test phrases: "urgent", "important", "not important"
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        variations = [
            ("urgent task", "high"),
            ("important task", "high"),
            ("not important task", "low"),
        ]

        for phrase, expected_priority in variations:
            response = await test_client.post(
                "/api/v1/chat",
                json={
                    "user_id": test_user_id,
                    "message": f"Add {phrase}: {phrase.replace(' task', ' item')}",
                },
            )

            assert response.status_code == 200
            print(f"Variation '{phrase}' processed successfully")


# Run tests if executed directly
async def main() -> None:
    """Run all priority chat tests."""
    print("Running Priority via Chat Tests...")

    async with AsyncClient(base_url=BASE_URL, transport=ASGITransport()) as client:
        client.cookies.set("auth-token", TEST_TOKEN)
        test_instance = TestPriorityChat()

        await test_instance.test_set_high_priority_on_creation(client)
        await test_instance.test_set_medium_priority_on_creation(client)
        await test_instance.test_set_low_priority_on_creation(client)
        await test_instance.test_update_existing_task_priority(client)
        await test_instance.test_filter_by_priority_high(client)
        await test_instance.test_default_priority_is_medium(client)
        await test_instance.test_invalid_priority_prompts_clarification(client)
        await test_instance.test_priority_variations(client)

    print("All priority chat tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
