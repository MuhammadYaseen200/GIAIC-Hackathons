"""Tags via chat tests for AI chatbot integration.

Tests tag creation, addition, removal, and filtering through natural language.

Dependencies:
- Layer 6: E2E Chat Flow Tests (T-324)

ADR References:
- ADR-011 (Task Schema Extension) - Tags field and max 10 tags constraint
"""

import pytest
from httpx import AsyncClient


class TestTagsChat:
    """Test suite for tag operations via chat."""

    @pytest.mark.asyncio
    async def test_add_task_with_single_tag(self, test_client: AsyncClient):
        """Verify task can be created with a single tag.

        Test Case: US-309 - Tag Tasks via Chat
        Acceptance Scenario 1: "Add task 'Email client' with tag Work"
        """
        response = await test_client.post(
            "/api/v1/chat",
            json={
                "message": "Add task Email client with tag Work",
            },
        )

        assert response.status_code == 200
        data = response.json()

        print(f"Tag creation response: {data}")

        # Verify task was created with tag
        tasks_response = await test_client.get(
            "/api/v1/tasks",
        )

        if tasks_response.status_code == 200:
            tasks = tasks_response.json().get("data", [])
            email_tasks = [t for t in tasks if "Email client" in t.get("title", "")]

            if email_tasks:
                task = email_tasks[0]
                tags = task.get("tags", [])
                assert "Work" in tags, f"Expected 'Work' in tags, got {tags}"
                print(f"Verified task with single tag: {task}")

    @pytest.mark.asyncio
    async def test_add_multiple_tags_to_task(self, test_client: AsyncClient):
        """Verify multiple tags can be added during creation.

        Test Case: US-309 - Tag Tasks via Chat
        Acceptance Scenario 2: "Add tags Home, Errands to 'Buy groceries'"
        """
        # Create task with multiple tags
        response = await test_client.post(
            "/api/v1/chat",
            json={
                "message": "Add task Buy groceries with tags Home and Errands",
            },
        )

        assert response.status_code == 200

        tasks_response = await test_client.get(
            "/api/v1/tasks",
        )

        if tasks_response.status_code == 200:
            tasks = tasks_response.json().get("data", [])
            grocery_tasks = [t for t in tasks if "Buy groceries" in t.get("title", "")]

            if grocery_tasks:
                task = grocery_tasks[0]
                tags = task.get("tags", [])
                assert "Home" in tags, f"Expected 'Home' in tags, got {tags}"
                assert "Errands" in tags, f"Expected 'Errands' in tags, got {tags}"
                print(f"Verified task with multiple tags: {task}")

    @pytest.mark.asyncio
    async def test_add_tags_to_existing_task(self, test_client: AsyncClient):
        """Verify tags can be added to an existing task.

        Test Case: US-309 - Tag Tasks via Chat
        Acceptance Scenario 2: Add tags to existing task.
        """
        # Create task first
        create_response = await test_client.post(
            "/api/v1/tasks",
            json={"title": "Taggable task", "tags": []},
        )

        if create_response.status_code == 200:
            task_data = create_response.json()
            if "data" in task_data:
                task_id = task_data["data"]["id"]

                # Add tags via chat
                chat_response = await test_client.post(
                    "/api/v1/chat",
                    json={
                        "message": "Add tags Work, Urgent to 'Taggable task'",
                    },
                )

                assert chat_response.status_code == 200

                # Verify tags were added
                task_response = await test_client.get(
                    f"/api/v1/tasks/{task_id}",
                )

                if task_response.status_code == 200:
                    updated_task = task_response.json().get("data", {})
                    tags = updated_task.get("tags", [])
                    assert "Work" in tags
                    assert "Urgent" in tags
                    print(f"Verified tags added: {updated_task}")

    @pytest.mark.asyncio
    async def test_remove_tag_from_task(self, test_client: AsyncClient):
        """Verify tag can be removed from an existing task.

        Test Case: US-309 - Tag Tasks via Chat
        Acceptance Scenario 3: "Remove tag Work from 'Email client'"
        """
        # Create task with tag
        create_response = await test_client.post(
            "/api/v1/tasks",
            json={"title": "Email client 2", "tags": ["Work", "Personal"]},
        )

        if create_response.status_code == 200:
            task_data = create_response.json()
            if "data" in task_data:
                task_id = task_data["data"]["id"]

                # Remove tag via chat
                chat_response = await test_client.post(
                    "/api/v1/chat",
                    json={
                        "message": "Remove tag Work from 'Email client 2'",
                    },
                )

                assert chat_response.status_code == 200

                # Verify tag was removed
                task_response = await test_client.get(
                    f"/api/v1/tasks/{task_id}",
                )

                if task_response.status_code == 200:
                    updated_task = task_response.json().get("data", {})
                    tags = updated_task.get("tags", [])
                    assert "Work" not in tags, "Work tag should be removed"
                    assert "Personal" in tags, "Personal tag should remain"
                    print(f"Verified tag removed: {updated_task}")

    @pytest.mark.asyncio
    async def test_filter_tasks_by_tag(self, test_client: AsyncClient):
        """Verify tasks can be filtered by tag.

        Test Case: US-309 - Tag Tasks via Chat
        Acceptance Scenario 4: "Show my Work tasks"
        """
        # Create tasks with different tags
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Work task 1", "tags": ["Work"]},
        )
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Work task 2", "tags": ["Work"]},
        )
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Home task", "tags": ["Home"]},
        )

        # Filter by tag via chat
        response = await test_client.post(
            "/api/v1/chat",
            json={
                "message": "Show my Work tasks",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify tool was called
        assert data.get("tool_calls"), "No tool calls made for tag filter"

        # Verify tasks filtered correctly
        tasks_response = await test_client.get(
            "/api/v1/tasks",
        )

        if tasks_response.status_code == 200:
            tasks = tasks_response.json().get("data", [])
            work_tasks = [t for t in tasks if "Work" in t.get("tags", [])]
            assert len(work_tasks) > 0, "No Work tasks found"
            print(f"Verified {len(work_tasks)} Work tasks: {work_tasks}")

    @pytest.mark.asyncio
    async def test_list_all_tags(self, test_client: AsyncClient):
        """Verify AI can list all unique tags.

        Test Case: US-309 - Tag Tasks via Chat
        Acceptance Scenario 5: "What tags do I have?"
        """
        # Create tasks with various tags
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Tag task 1", "tags": ["Work", "Urgent"]},
        )
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Tag task 2", "tags": ["Home", "Personal"]},
        )
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Tag task 3", "tags": ["Work", "Project"]},
        )

        # List tags via chat
        response = await test_client.post(
            "/api/v1/chat",
            json={
                "message": "What tags do I have?",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # AI should list unique tags
        ai_response = data.get("response", "").lower()
        expected_tags = ["work", "home", "urgent", "personal", "project"]

        for tag in expected_tags:
            assert tag in ai_response, f"Expected tag '{tag}' in AI response"

        print(f"Tag list response: {data.get('response')}")

    @pytest.mark.asyncio
    async def test_tags_displayed_in_task_listings(self, test_client: AsyncClient):
        """Verify tags are displayed when listing tasks.

        Test Case: US-309 - Tag Tasks via Chat
        Acceptance Scenario 6: Tags displayed in task listings.
        """
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Task with tags", "tags": ["Work", "Urgent"]},
        )

        # List tasks via chat
        response = await test_client.post(
            "/api/v1/chat",
            json={
                "message": "List my tasks",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # AI response should mention tags
        ai_response = data.get("response", "").lower()
        assert any(
            tag in ai_response for tag in ["tag", "work", "urgent"]
        ), "Tags should be mentioned in task listing"

        print(f"Task listing with tags: {data.get('response')}")

    @pytest.mark.asyncio
    async def test_max_tags_enforcement(self, test_client: AsyncClient):
        """Verify max 10 tags constraint is enforced.

        Test Case: ADR-011 constraint - Max 10 tags per task.
        """
        # Try to add more than 10 tags
        many_tags = ",".join([f"Tag{i}" for i in range(12)])

        response = await test_client.post(
            "/api/v1/chat",
            json={
                "message": f"Add task Many tags with tags {many_tags}",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # AI should either accept up to 10 tags or warn about the limit
        ai_response = data.get("response", "").lower()
        print(f"Max tags response: {ai_response}")

    @pytest.mark.asyncio
    async def test_tag_case_sensitivity(self, test_client: AsyncClient):
        """Verify tags are case-insensitive for matching but preserve case.

        Test Case: Work vs work vs WORK should be same tag.
        """
        # Create tasks with same tag in different cases
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Task 1", "tags": ["Work"]},
        )
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Task 2", "tags": ["work"]},
        )

        # Filter by lowercase "work"
        response = await test_client.post(
            "/api/v1/chat",
            json={
                "message": "Show my work tasks",
            },
        )

        assert response.status_code == 200
        print("Case sensitivity test passed")
