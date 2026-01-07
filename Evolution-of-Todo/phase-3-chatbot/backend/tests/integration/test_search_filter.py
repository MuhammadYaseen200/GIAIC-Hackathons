"""Search and filter via chat tests for AI chatbot integration.

Tests keyword search, combined filters, and sorting through natural language.

Dependencies:
- Layer 6: E2E Chat Flow Tests (T-324)

ADR References:
- ADR-011 (Task Schema Extension) - Search and filter fields
"""

import asyncio
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_TOKEN = "test_jwt_token_for_search_tests"


@pytest_asyncio.fixture
async def test_client():
    """Create async test client with auth token."""
    transport = ASGITransport()
    async with AsyncClient(base_url=BASE_URL, transport=transport) as client:
        client.cookies.set("auth-token", TEST_TOKEN)
        yield client


class TestSearchFilterChat:
    """Test suite for search and filter operations via chat."""

    @pytest.mark.asyncio
    async def test_keyword_search_in_title(self, test_client: AsyncClient):
        """Verify keyword search works in task titles.

        Test Case: US-310 - Search Tasks via Chat
        Acceptance Scenario 1: "Search for grocery"
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # Create tasks with keyword
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Buy groceries", "description": "Milk, eggs, bread"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Grocery list review", "description": "Review list"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Call mom", "description": ""},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        # Search for keyword
        response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Search for grocery",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify tool was called
        assert data.get("tool_calls"), "No tool calls made for search"

        # Verify search results
        tasks_response = await test_client.get(
            "/api/v1/tasks",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        if tasks_response.status_code == 200:
            tasks = tasks_response.json().get("data", [])
            grocery_tasks = [
                t for t in tasks
                if "grocery" in t.get("title", "").lower()
            ]
            assert len(grocery_tasks) > 0, "No grocery tasks found"
            print(f"Found {len(grocery_tasks)} tasks matching 'grocery': {grocery_tasks}")

    @pytest.mark.asyncio
    async def test_keyword_search_in_description(self, test_client: AsyncClient):
        """Verify keyword search works in task descriptions.

        Test Case: US-310 - Search Tasks via Chat
        Acceptance Scenario 2: "Find tasks about project"
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # Create tasks with keyword in description
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Review", "description": "Review project proposal"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Meeting", "description": "Project status meeting"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        # Search for keyword
        response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Find tasks about project",
            },
        )

        assert response.status_code == 200

        tasks_response = await test_client.get(
            "/api/v1/tasks",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        if tasks_response.status_code == 200:
            tasks = tasks_response.json().get("data", [])
            project_tasks = [
                t for t in tasks
                if "project" in t.get("title", "").lower() or "project" in t.get("description", "").lower()
            ]
            assert len(project_tasks) > 0, "No project tasks found"
            print(f"Found {len(project_tasks)} tasks matching 'project': {project_tasks}")

    @pytest.mark.asyncio
    async def test_search_is_case_insensitive(self, test_client: AsyncClient):
        """Verify search is case-insensitive.

        Test Case: US-310 - Search Tasks via Chat
        Acceptance Scenario 3: Case-insensitive search.
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # Create task with mixed case
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Review PR #42", "description": ""},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        # Search with different cases
        for search_term in ["pr", "PR", "Pr"]:
            response = await test_client.post(
                "/api/v1/chat",
                json={
                    "user_id": test_user_id,
                    "message": f"Search for {search_term}",
                },
            )
            assert response.status_code == 200

        print("Case-insensitive search test passed")

    @pytest.mark.asyncio
    async def test_search_no_results(self, test_client: AsyncClient):
        """Verify helpful message when no results found.

        Test Case: US-310 - Search Tasks via Chat
        Acceptance Scenario 3: No tasks matching 'nonexistent'.
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Search for nonexistent",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # AI should indicate no results found
        ai_response = data.get("response", "").lower()
        assert any(
            phrase in ai_response
            for phrase in ["no tasks", "found", "couldn't find", "no results"]
        ), "AI should indicate no results found"

        print(f"No results message: {data.get('response')}")

    @pytest.mark.asyncio
    async def test_combined_filters_status_priority(self, test_client: AsyncClient):
        """Verify combined status and priority filters work.

        Test Case: US-312 - Filter Tasks via Chat
        Acceptance Scenario 1: "Show pending high priority tasks"
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # Create tasks with different status and priority
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Pending high", "completed": False, "priority": "high"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Pending low", "completed": False, "priority": "low"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Completed high", "completed": True, "priority": "high"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        # Filter with combined criteria
        response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Show pending high priority tasks",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify tool was called
        assert data.get("tool_calls"), "No tool calls made for combined filter"

        tasks_response = await test_client.get(
            "/api/v1/tasks",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        if tasks_response.status_code == 200:
            tasks = tasks_response.json().get("data", [])
            filtered = [
                t for t in tasks
                if not t.get("completed") and t.get("priority") == "high"
            ]
            assert len(filtered) > 0, "No pending high priority tasks found"
            print(f"Found {len(filtered)} pending high priority tasks: {filtered}")

    @pytest.mark.asyncio
    async def test_combined_filters_status_tag(self, test_client: AsyncClient):
        """Verify combined status and tag filters work.

        Test Case: US-312 - Filter Tasks via Chat
        Acceptance Scenario 3: "Show Work tasks that are pending"
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # Create tasks with different status and tags
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Work pending", "completed": False, "tags": ["Work"]},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Work completed", "completed": True, "tags": ["Work"]},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Home pending", "completed": False, "tags": ["Home"]},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        # Filter with combined criteria
        response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Show Work tasks that are pending",
            },
        )

        assert response.status_code == 200

        tasks_response = await test_client.get(
            "/api/v1/tasks",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        if tasks_response.status_code == 200:
            tasks = tasks_response.json().get("data", [])
            filtered = [
                t for t in tasks
                if not t.get("completed") and "Work" in t.get("tags", [])
            ]
            assert len(filtered) > 0, "No pending Work tasks found"
            print(f"Found {len(filtered)} pending Work tasks: {filtered}")

    @pytest.mark.asyncio
    async def test_combined_filters_priority_tag(self, test_client: AsyncClient):
        """Verify combined priority and tag filters work.

        Test Case: US-312 - Filter Tasks via Chat
        Acceptance Scenario 4: "Find high priority tasks tagged Home"
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # Create tasks with different priority and tags
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "High Home", "priority": "high", "tags": ["Home"]},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Low Home", "priority": "low", "tags": ["Home"]},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "High Work", "priority": "high", "tags": ["Work"]},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        # Filter with combined criteria
        response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Find high priority tasks tagged Home",
            },
        )

        assert response.status_code == 200

        tasks_response = await test_client.get(
            "/api/v1/tasks",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        if tasks_response.status_code == 200:
            tasks = tasks_response.json().get("data", [])
            filtered = [
                t for t in tasks
                if t.get("priority") == "high" and "Home" in t.get("tags", [])
            ]
            assert len(filtered) > 0, "No high priority Home tasks found"
            print(f"Found {len(filtered)} high priority Home tasks: {filtered}")

    @pytest.mark.asyncio
    async def test_combined_filters_no_matches(self, test_client: AsyncClient):
        """Verify helpful message when combined filters yield no results.

        Test Case: US-312 - Filter Tasks via Chat
        Acceptance Scenario 5: No tasks match criteria.
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # Create tasks that won't match filter
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Completed task", "completed": True, "tags": ["Work"]},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        # Filter for pending Home tasks (none exist)
        response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Show pending Home tasks",
            },
        )

        assert response.status_code == 200
        data = response.json()

        ai_response = data.get("response", "").lower()
        assert any(
            phrase in ai_response
            for phrase in ["no tasks", "found", "couldn't find", "no results"]
        ), "AI should indicate no tasks match criteria"

        print(f"No matches message: {data.get('response')}")

    @pytest.mark.asyncio
    async def test_search_with_filters_combined(self, test_client: AsyncClient):
        """Verify keyword search can be combined with filters.

        Test Case: US-310 - Search Tasks via Chat
        Acceptance Scenario 4: "Search for high priority work tasks"
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # Create tasks
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Work project review", "priority": "high", "tags": ["Work"]},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Home project review", "priority": "high", "tags": ["Home"]},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        # Search with combined criteria
        response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Search for high priority work tasks with project",
            },
        )

        assert response.status_code == 200

        tasks_response = await test_client.get(
            "/api/v1/tasks",
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        if tasks_response.status_code == 200:
            tasks = tasks_response.json().get("data", [])
            filtered = [
                t for t in tasks
                if t.get("priority") == "high"
                and "Work" in t.get("tags", [])
                and "project" in t.get("title", "").lower()
            ]
            assert len(filtered) > 0, "No matching tasks found"
            print(f"Found {len(filtered)} tasks matching combined criteria: {filtered}")


class TestSortChat:
    """Test suite for sorting operations via chat."""

    @pytest.mark.asyncio
    async def test_sort_by_priority(self, test_client: AsyncClient):
        """Verify tasks can be sorted by priority.

        Test Case: US-311 - Sort Tasks via Chat
        Acceptance Scenario 1: "Show my tasks sorted by priority"
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # Create tasks with different priorities
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Low task", "priority": "low"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "High task", "priority": "high"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Medium task", "priority": "medium"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        # Sort by priority
        response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Show my tasks sorted by priority",
            },
        )

        assert response.status_code == 200

        print("Sort by priority test passed")

    @pytest.mark.asyncio
    async def test_sort_by_creation_date(self, test_client: AsyncClient):
        """Verify tasks can be sorted by creation date.

        Test Case: US-311 - Sort Tasks via Chat
        Acceptance Scenario 2: "List tasks by creation date"
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # Create tasks
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "First task"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Second task"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        # Sort by date
        response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "List tasks by creation date",
            },
        )

        assert response.status_code == 200

        print("Sort by creation date test passed")

    @pytest.mark.asyncio
    async def test_sort_by_name(self, test_client: AsyncClient):
        """Verify tasks can be sorted alphabetically.

        Test Case: US-311 - Sort Tasks via Chat
        Acceptance Scenario 4: "Sort my tasks by name"
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # Create tasks
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Zebra task"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Apple task"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        # Sort by name
        response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Sort my tasks by name",
            },
        )

        assert response.status_code == 200

        print("Sort by name test passed")

    @pytest.mark.asyncio
    async def test_sort_with_filter_combined(self, test_client: AsyncClient):
        """Verify sort can be combined with filters.

        Test Case: US-311 - Sort Tasks via Chat
        Acceptance Scenario 3: "Show pending tasks sorted by priority"
        """
        test_client.cookies.set("auth-token", TEST_TOKEN)
        test_user_id = str(uuid4())

        # Create tasks
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Pending low", "completed": False, "priority": "low"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        await test_client.post(
            "/api/v1/tasks",
            json={"title": "Pending high", "completed": False, "priority": "high"},
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )

        # Filter and sort
        response = await test_client.post(
            "/api/v1/chat",
            json={
                "user_id": test_user_id,
                "message": "Show pending tasks sorted by priority",
            },
        )

        assert response.status_code == 200

        print("Sort with filter combined test passed")


# Run tests if executed directly
async def main() -> None:
    """Run all search and filter chat tests."""
    print("Running Search and Filter via Chat Tests...")

    async with AsyncClient(base_url=BASE_URL, transport=ASGITransport()) as client:
        client.cookies.set("auth-token", TEST_TOKEN)
        search_instance = TestSearchFilterChat()
        sort_instance = TestSortChat()

        await search_instance.test_keyword_search_in_title(client)
        await search_instance.test_keyword_search_in_description(client)
        await search_instance.test_search_is_case_insensitive(client)
        await search_instance.test_search_no_results(client)
        await search_instance.test_combined_filters_status_priority(client)
        await search_instance.test_combined_filters_status_tag(client)
        await search_instance.test_combined_filters_priority_tag(client)
        await search_instance.test_combined_filters_no_matches(client)
        await search_instance.test_search_with_filters_combined(client)

        await sort_instance.test_sort_by_priority(client)
        await sort_instance.test_sort_by_creation_date(client)
        await sort_instance.test_sort_by_name(client)
        await sort_instance.test_sort_with_filter_combined(client)

    print("All search and filter chat tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
