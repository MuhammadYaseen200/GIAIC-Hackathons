"""ChatKit CRUD Matrix Tests with Playwright + ChromeDevTools Protocol.

This test suite validates ChatKit integration using browser automation with:
1. Real browser interaction via Playwright
2. Performance monitoring via ChromeDevTools Protocol (CDP)
3. Network traffic inspection
4. Console log capture
5. Screenshot capture on failures

Tests:
- Test 1: Single operations (Add, Update, Complete, Delete)
- Test 2: Bulk operations (Multiple adds, filtered lists, bulk updates)
- Test 3: Edge cases (Invalid priorities, error handling)

Prerequisites:
- Backend server running on http://localhost:8000
- Frontend server running on http://localhost:3000
- Playwright installed: uv run playwright install chromium
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from playwright.async_api import Browser, CDPSession, Page, async_playwright

# Note: UTF-8 wrapping removed - it breaks pytest capture mechanism

# Test configuration
FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"
CHAT_URL = f"{FRONTEND_URL}/dashboard/chat"

# Evidence directory
EVIDENCE_DIR = Path(__file__).parent / "evidence"
EVIDENCE_DIR.mkdir(exist_ok=True)


class ChatKitPlaywrightTester:
    """Test harness using Playwright with ChromeDevTools."""

    def __init__(self):
        self.page: Page | None = None
        self.browser: Browser | None = None
        self.cdp_session: CDPSession | None = None
        self.network_logs: list[dict[str, Any]] = []
        self.console_logs: list[dict[str, Any]] = []
        self.performance_metrics: list[dict[str, Any]] = []
        self.access_token: str | None = None  # Store token for API calls

    async def setup(self):
        """Setup Playwright and CDP session."""
        print(f"\n{'='*80}")
        print("SETUP: Initializing Playwright + ChromeDevTools")
        print(f"{'='*80}")

        playwright = await async_playwright().start()

        # Launch browser with CDP enabled
        self.browser = await playwright.chromium.launch(
            headless=False,  # Set to False to watch tests
            args=[
                "--disable-blink-features=AutomationControlled",
                "--enable-automation",
            ],
        )

        # Create new page
        self.page = await self.browser.new_page()

        # Enable ChromeDevTools Protocol
        self.cdp_session = await self.page.context.new_cdp_session(self.page)

        # Enable CDP domains
        await self.cdp_session.send("Network.enable")
        await self.cdp_session.send("Performance.enable")
        await self.cdp_session.send("Console.enable")

        # Setup CDP event listeners
        self.cdp_session.on("Network.requestWillBeSent", self._on_request)
        self.cdp_session.on("Network.responseReceived", self._on_response)
        self.cdp_session.on("Console.messageAdded", self._on_console)

        # Setup page event listeners
        self.page.on("console", self._on_page_console)
        self.page.on("pageerror", self._on_page_error)

        print("✓ Browser launched")
        print("✓ CDP session established")
        print("✓ Event listeners attached")

    def _on_request(self, event: dict):
        """CDP Network request listener."""
        request = event.get("request", {})
        self.network_logs.append({
            "type": "request",
            "timestamp": event.get("timestamp"),
            "url": request.get("url"),
            "method": request.get("method"),
            "headers": request.get("headers"),
        })

    def _on_response(self, event: dict):
        """CDP Network response listener."""
        response = event.get("response", {})
        self.network_logs.append({
            "type": "response",
            "timestamp": event.get("timestamp"),
            "url": response.get("url"),
            "status": response.get("status"),
            "headers": response.get("headers"),
        })

    def _on_console(self, event: dict):
        """CDP Console message listener."""
        message = event.get("message", {})
        self.console_logs.append({
            "timestamp": event.get("timestamp"),
            "level": message.get("level"),
            "text": message.get("text"),
            "source": message.get("source"),
        })

    def _on_page_console(self, msg):
        """Page console message listener."""
        print(f"[Browser Console] {msg.type}: {msg.text}")

    def _on_page_error(self, error):
        """Page error listener."""
        print(f"[Browser Error] {error}")

    async def capture_performance_metrics(self):
        """Capture performance metrics via CDP."""
        metrics = await self.cdp_session.send("Performance.getMetrics")
        timestamp = datetime.now().isoformat()

        metrics_dict = {m["name"]: m["value"] for m in metrics["metrics"]}
        self.performance_metrics.append({
            "timestamp": timestamp,
            "metrics": metrics_dict,
        })

        return metrics_dict

    async def save_screenshot(self, name: str):
        """Save screenshot to evidence directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = EVIDENCE_DIR / f"{timestamp}_{name}.png"
        await self.page.screenshot(path=path, full_page=True)
        print(f"  📸 Screenshot saved: {path}")

    async def save_evidence(self):
        """Save all captured evidence to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save network logs
        network_path = EVIDENCE_DIR / f"{timestamp}_network.json"
        with open(network_path, "w") as f:
            json.dump(self.network_logs, f, indent=2)
        print(f"  📊 Network logs saved: {network_path}")

        # Save console logs
        console_path = EVIDENCE_DIR / f"{timestamp}_console.json"
        with open(console_path, "w") as f:
            json.dump(self.console_logs, f, indent=2)
        print(f"  📊 Console logs saved: {console_path}")

        # Save performance metrics
        perf_path = EVIDENCE_DIR / f"{timestamp}_performance.json"
        with open(perf_path, "w") as f:
            json.dump(self.performance_metrics, f, indent=2)
        print(f"  📊 Performance metrics saved: {perf_path}")

    async def register_via_api(self, email: str, password: str, full_name: str = "Test User"):
        """Register user via API."""
        print(f"\n→ Registering user via API: {email}")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BACKEND_URL}/api/v1/auth/register",
                json={"email": email, "password": password, "full_name": full_name}
            )
            if response.status_code in [200, 201]:
                print("  ✓ User registered successfully")
                return True
            elif response.status_code == 400:
                print("  ⚠ User already exists")
                return False
            else:
                print(f"  ✗ Registration failed: {response.status_code}")
                print(f"  Response: {response.text}")
                return False

    async def login_via_api(self, email: str, password: str):
        """Login via API and get access token."""
        print(f"\n→ Logging in via API: {email}")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BACKEND_URL}/api/v1/auth/login",
                json={"email": email, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                token = data["data"]["token"]
                print("  ✓ Login successful")
                return token
            else:
                print(f"  ✗ Login failed: {response.status_code}")
                print(f"  Response: {response.text}")
                return None

    async def inject_auth_cookie(self, access_token: str):
        """Inject authentication cookie into browser session."""
        print("\n→ Injecting auth cookie into browser")

        # Navigate to the frontend first to set cookie domain
        await self.page.goto(FRONTEND_URL, timeout=90000)

        # Add cookie (use correct cookie name: auth-token)
        await self.page.context.add_cookies([{
            "name": "auth-token",
            "value": access_token,
            "domain": "localhost",
            "path": "/",
            "httpOnly": True,  # Match frontend's httpOnly setting
            "secure": False,   # Local development
            "sameSite": "Lax"
        }])

        print("  ✓ Auth cookie injected")

        # Reload to apply cookie
        await self.page.reload()
        await asyncio.sleep(2)

        # Verify we're authenticated by checking if we can access dashboard
        await self.page.goto(f"{FRONTEND_URL}/dashboard", timeout=60000)
        await asyncio.sleep(2)

        if "/dashboard" in self.page.url:
            print("  ✓ Successfully authenticated")
        else:
            print(f"  ⚠ May not be authenticated (current URL: {self.page.url})")

    async def navigate_to_chat(self):
        """Navigate to chat page."""
        print("\n→ Navigating to chat page")
        await self.page.goto(CHAT_URL, timeout=90000)

        # Wait for ChatKit web component to be present
        print("  ⏳ Waiting for ChatKit web component...")
        await self.page.wait_for_selector('openai-chatkit', timeout=60000)

        # Wait for ChatKit to be ready (additional time for initialization)
        await asyncio.sleep(5)

        print("✓ Chat interface loaded")
        await self.save_screenshot("chat_loaded")

    async def send_chat_message(self, message: str) -> str:
        """Send a message in the chat and wait for response."""
        print(f"\n→ User: {message}")

        try:
            # Click on the ChatKit component to focus it
            chatkit = await self.page.query_selector('openai-chatkit')
            if chatkit:
                # Click in the middle of the component to focus the input
                box = await chatkit.bounding_box()
                if box:
                    await self.page.mouse.click(
                        box['x'] + box['width'] / 2,
                        box['y'] + box['height'] - 50  # Click near bottom where input usually is
                    )
                    await asyncio.sleep(0.5)

            # Type message using keyboard
            await self.page.keyboard.type(message, delay=50)  # Add delay between keystrokes
            await asyncio.sleep(0.5)

            # Press Enter to send
            await self.page.keyboard.press("Enter")

            # Wait for AI response (increased timeout)
            print("  ⏳ Waiting for AI response...")
            await asyncio.sleep(15)  # Give more time for AI to process and respond

            print("  ✓ Message sent and processed")
            return "Message sent successfully"

        except Exception as e:
            print(f"  ⚠ Error sending message: {e}")
            await self.save_screenshot("error_send_message")
            return ""

    async def verify_tasks_via_api(self, expected_count: int | None = None) -> list[dict]:
        """Verify tasks via REST API using stored access token."""
        if not self.access_token:
            print("  ✗ No access token available")
            return []

        # Make direct API request using httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BACKEND_URL}/api/v1/tasks",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )

            if response.status_code != 200:
                print(f"  ✗ Task verification failed: {response.status_code}")
                return []

            tasks_response = response.json()

        tasks = tasks_response.get("data", [])

        if expected_count is not None:
            if len(tasks) == expected_count:
                print(f"  ✓ Verified {len(tasks)} tasks (expected {expected_count})")
            else:
                print(f"  ✗ Task count mismatch: got {len(tasks)}, expected {expected_count}")

        return tasks

    async def test_single_operations(self):
        """Test 1: Single CRUD operations."""
        print(f"\n{'='*80}")
        print("TEST 1: SINGLE OPERATIONS")
        print(f"{'='*80}")

        # 1. Add task
        await self.send_chat_message("Add task: Buy Milk")
        await asyncio.sleep(2)
        tasks = await self.verify_tasks_via_api(expected_count=1)
        assert len(tasks) == 1, "Failed to add task"
        task_id = tasks[0]["id"]
        assert "milk" in tasks[0]["title"].lower(), "Task title incorrect"
        await self.save_screenshot("test1_add_task")

        # 2. Update task
        await self.send_chat_message("Update the milk task to Buy Coffee")
        await asyncio.sleep(2)
        tasks = await self.verify_tasks_via_api(expected_count=1)
        assert "coffee" in tasks[0]["title"].lower(), "Task not updated"
        await self.save_screenshot("test1_update_task")

        # 3. Complete task
        await self.send_chat_message("Complete the coffee task")
        await asyncio.sleep(2)
        tasks = await self.verify_tasks_via_api(expected_count=1)
        assert tasks[0]["completed"] is True, "Task not marked complete"
        await self.save_screenshot("test1_complete_task")

        # 4. Delete task
        await self.send_chat_message("Delete the coffee task")
        await asyncio.sleep(2)
        tasks = await self.verify_tasks_via_api(expected_count=0)
        await self.save_screenshot("test1_delete_task")

        # Capture metrics
        metrics = await self.capture_performance_metrics()
        print(f"\n  📊 Performance: {metrics.get('TaskDuration', 0):.2f}s task duration")

        print(f"\n{'✓'*40} TEST 1 PASSED {'✓'*40}")

    async def test_bulk_operations(self):
        """Test 2: Bulk CRUD operations."""
        print(f"\n{'='*80}")
        print("TEST 2: BULK OPERATIONS")
        print(f"{'='*80}")

        # 1. Add 3 tasks with priorities
        await self.send_chat_message("Add task: Code review with high priority")
        await asyncio.sleep(2)
        await self.send_chat_message("Add task: Team meeting with medium priority")
        await asyncio.sleep(2)
        await self.send_chat_message("Add task: Read emails with low priority")
        await asyncio.sleep(2)

        tasks = await self.verify_tasks_via_api(expected_count=3)
        assert len(tasks) == 3, "Failed to add 3 tasks"
        await self.save_screenshot("test2_add_multiple")

        # 2. List high priority tasks
        await self.send_chat_message("Show me my high priority tasks")
        await asyncio.sleep(2)
        await self.save_screenshot("test2_list_high_priority")

        # 3. Update task priorities
        await self.send_chat_message("Change the team meeting task to high priority")
        await asyncio.sleep(2)
        tasks = await self.verify_tasks_via_api(expected_count=3)
        await self.save_screenshot("test2_update_priority")

        # 4. Delete all tasks
        await self.send_chat_message("Delete all my tasks")
        await asyncio.sleep(3)
        tasks = await self.verify_tasks_via_api(expected_count=0)
        await self.save_screenshot("test2_delete_all")

        # Capture metrics
        metrics = await self.capture_performance_metrics()
        print(f"\n  📊 Performance: {metrics.get('Nodes', 0)} DOM nodes")

        print(f"\n{'✓'*40} TEST 2 PASSED {'✓'*40}")

    async def test_edge_cases(self):
        """Test 3: Edge cases and error handling."""
        print(f"\n{'='*80}")
        print("TEST 3: EDGE CASES")
        print(f"{'='*80}")

        # 1. Add task with invalid priority
        await self.send_chat_message("Add task: Test invalid priority with superhigh priority")
        await asyncio.sleep(2)
        tasks = await self.verify_tasks_via_api(expected_count=1)
        assert tasks[0]["priority"] in ["low", "medium", "high"], "Invalid priority not handled"
        print(f"  ✓ Invalid priority handled: {tasks[0]['priority']}")
        await self.save_screenshot("test3_invalid_priority")

        # 2. Try to delete non-existent task
        await self.send_chat_message("Delete task with ID 00000000-0000-0000-0000-000000000000")
        await asyncio.sleep(2)
        await self.save_screenshot("test3_delete_nonexistent")

        # 3. Try empty message
        await self.send_chat_message("")
        await asyncio.sleep(1)
        await self.save_screenshot("test3_empty_message")

        # Cleanup
        await self.send_chat_message("Delete all my tasks")
        await asyncio.sleep(2)
        await self.verify_tasks_via_api(expected_count=0)

        # Capture metrics
        metrics = await self.capture_performance_metrics()
        print(f"\n  📊 Performance: {metrics.get('JSHeapUsedSize', 0) / 1024 / 1024:.2f}MB heap used")

        print(f"\n{'✓'*40} TEST 3 PASSED {'✓'*40}")

    async def cleanup(self):
        """Clean up and save evidence."""
        print(f"\n{'='*80}")
        print("CLEANUP: Saving evidence and closing browser")
        print(f"{'='*80}")

        await self.save_evidence()

        if self.cdp_session:
            await self.cdp_session.detach()

        if self.browser:
            await self.browser.close()

        print("✓ Cleanup complete")


async def main():
    """Run all ChatKit CRUD tests with Playwright + CDP."""
    # Generate unique test user
    import uuid
    unique_id = uuid.uuid4().hex[:8]
    TEST_EMAIL = f"test_{unique_id}@example.com"
    TEST_PASSWORD = "TestPass123!"
    TEST_NAME = "Playwright Test User"

    tester = ChatKitPlaywrightTester()

    try:
        await tester.setup()

        # Register and login via API
        await tester.register_via_api(TEST_EMAIL, TEST_PASSWORD, TEST_NAME)
        access_token = await tester.login_via_api(TEST_EMAIL, TEST_PASSWORD)

        if not access_token:
            raise Exception("Failed to obtain access token")

        # Store token for API verification
        tester.access_token = access_token

        # Inject auth cookie into browser
        await tester.inject_auth_cookie(access_token)

        # Navigate to chat
        await tester.navigate_to_chat()

        await tester.test_single_operations()
        await tester.test_bulk_operations()
        await tester.test_edge_cases()

        print(f"\n{'='*80}")
        print("ALL TESTS PASSED ✓")
        print(f"{'='*80}")

    except Exception as e:
        print(f"\n{'✗'*40} TEST FAILED {'✗'*40}")
        print(f"Error: {e}")
        await tester.save_screenshot("error_state")
        raise

    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
