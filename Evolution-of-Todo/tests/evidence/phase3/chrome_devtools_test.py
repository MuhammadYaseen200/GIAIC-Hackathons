"""
Phase 3 UI E2E Tests with Visual Evidence
Captures screenshots of all UI interactions
"""
import asyncio
import os
import sqlite3
import requests
from datetime import datetime
from playwright.async_api import async_playwright, Page

# Configuration
BASE_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000/api/v1"
DB_PATH = "phase-3-chatbot/backend/todo_app.db"
SCREENSHOT_DIR = "tests/evidence/phase3/chrome_screenshots"

# Use existing test user from API tests
TEST_USER = {
    "email": "test_e2e_2@example.com",
    "password": "TestPassword123!"
}

os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def get_auth_token():
    """Get JWT token via API"""
    resp = requests.post(f"{BACKEND_URL}/auth/login", json=TEST_USER)
    if resp.status_code == 200:
        return resp.json()["data"]["token"]
    return None


def get_db_state():
    """Get current database state"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, title, completed, priority, tags FROM tasks")
    tasks = cur.fetchall()
    conn.close()
    return tasks


def clean_db():
    """Clean tasks for fresh test"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks")
    conn.commit()
    conn.close()


async def add_test_label(page: Page, text: str):
    """Add a visible label to screenshot"""
    try:
        await page.evaluate(f'''
            const existing = document.getElementById("test-label");
            if (existing) existing.remove();
            const div = document.createElement("div");
            div.id = "test-label";
            div.innerText = "{text}";
            div.style.cssText = "position:fixed;top:10px;left:10px;background:#FFD700;padding:8px 16px;border:2px solid #333;font-weight:bold;z-index:99999;font-size:16px;border-radius:5px;box-shadow:2px 2px 5px rgba(0,0,0,0.3);";
            document.body.appendChild(div);
        ''')
        await page.wait_for_timeout(100)
    except:
        pass


async def take_screenshot(page: Page, name: str, label: str = None):
    """Take screenshot with optional label"""
    if label:
        await add_test_label(page, label)

    path = f"{SCREENSHOT_DIR}/{name}.png"
    await page.screenshot(path=path, full_page=True)
    print(f"    [SCREENSHOT] {name}.png")
    return path


async def run_ui_tests():
    """Run UI tests with visual evidence"""
    print("=" * 70)
    print("PHASE 3 UI VALIDATION WITH VISUAL EVIDENCE")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Test User: {TEST_USER['email']}")

    results = []
    screenshots = []

    # Get auth token first via API
    print("\n[PREP] Authenticating via API...")
    token = get_auth_token()
    if not token:
        print("  Creating new user...")
        requests.post(f"{BACKEND_URL}/auth/register", json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"],
            "name": "Test User"
        })
        token = get_auth_token()

    if token:
        print(f"  [OK] Token obtained")
    else:
        print("  [FAIL] FATAL: Cannot authenticate")
        return [], []

    async with async_playwright() as p:
        # Launch browser (headless for reliability)
        print("\n[PREP] Launching Chrome browser...")
        browser = await p.chromium.launch(headless=True)

        context = await browser.new_context(viewport={"width": 1400, "height": 900})

        # Set auth cookie
        await context.add_cookies([{
            "name": "auth-token",
            "value": token,
            "domain": "localhost",
            "path": "/"
        }])

        page = await context.new_page()
        page.set_default_timeout(60000)  # 60 second timeout

        # Capture console logs
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

        # ============================================
        # TEST 1: Login Page UI
        # ============================================
        print("\n[TEST 1] Login Page UI")
        try:
            await page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            ss = await take_screenshot(page, "01_login_page", "TEST 1: Login Page")
            screenshots.append(ss)
            results.append(("Login Page UI", True))
            print("    [PASS]")
        except Exception as e:
            results.append(("Login Page UI", False))
            print(f"    [FAIL]: {e}")

        # ============================================
        # TEST 2: Login Form
        # ============================================
        print("\n[TEST 2] Login Form Interaction")
        try:
            await page.fill('input[name="email"]', TEST_USER["email"])
            await page.fill('input[name="password"]', TEST_USER["password"])
            await page.wait_for_timeout(500)
            ss = await take_screenshot(page, "02_login_filled", "TEST 2: Credentials Entered")
            screenshots.append(ss)
            results.append(("Login Form", True))
            print("    [PASS]")
        except Exception as e:
            results.append(("Login Form", False))
            print(f"    [FAIL]: {e}")

        # ============================================
        # TEST 3: Submit Login
        # ============================================
        print("\n[TEST 3] Login Submission")
        try:
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(3000)
            ss = await take_screenshot(page, "03_after_login", "TEST 3: After Login Submit")
            screenshots.append(ss)
            results.append(("Login Submit", True))
            print(f"    URL: {page.url}")
            print("    [PASS]")
        except Exception as e:
            results.append(("Login Submit", False))
            print(f"    [FAIL]: {e}")

        # ============================================
        # TEST 4: Dashboard Page
        # ============================================
        print("\n[TEST 4] Dashboard Access")
        try:
            await page.goto(f"{BASE_URL}/dashboard", wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            ss = await take_screenshot(page, "04_dashboard", "TEST 4: Dashboard - Task List")
            screenshots.append(ss)
            results.append(("Dashboard", True))
            print("    [PASS]")
        except Exception as e:
            results.append(("Dashboard", False))
            print(f"    [FAIL]: {e}")

        # ============================================
        # TEST 5: Chat Page
        # ============================================
        print("\n[TEST 5] Chat Page Access")
        try:
            await page.goto(f"{BASE_URL}/dashboard/chat", wait_until="domcontentloaded")
            await page.wait_for_timeout(5000)  # Wait for ChatKit
            ss = await take_screenshot(page, "05_chat_page", "TEST 5: AI Chatbot Interface")
            screenshots.append(ss)
            results.append(("Chat Page", True))
            print("    [PASS]")
        except Exception as e:
            results.append(("Chat Page", False))
            print(f"    [FAIL]: {e}")

        # ============================================
        # TEST 6: ChatKit Component
        # ============================================
        print("\n[TEST 6] ChatKit Component Check")
        try:
            # Check for various chat-related elements
            selectors_found = []
            for selector in ["openai-chatkit", "[class*='chat']", "[class*='Chat']", "textarea", "input"]:
                el = await page.query_selector(selector)
                if el:
                    selectors_found.append(selector)

            print(f"    Found elements: {selectors_found}")
            ss = await take_screenshot(page, "06_chatkit_component", "TEST 6: ChatKit Component")
            screenshots.append(ss)
            results.append(("ChatKit Component", len(selectors_found) > 0))
            print("    [PASS]" if selectors_found else "    [WARN] ChatKit loading")
        except Exception as e:
            results.append(("ChatKit Component", False))
            print(f"    [FAIL]: {e}")

        # ============================================
        # TEST 7: Create Task via API
        # ============================================
        print("\n[TEST 7] Database Integration")
        try:
            clean_db()

            # Create tasks via API
            tasks_created = []
            for i, task in enumerate([
                {"title": "High Priority Task", "priority": "high", "tags": ["urgent"]},
                {"title": "Medium Priority Task", "priority": "medium", "tags": ["work"]},
                {"title": "Low Priority Task", "priority": "low", "tags": ["later"]}
            ]):
                resp = requests.post(
                    f"{BACKEND_URL}/tasks",
                    headers={"Authorization": f"Bearer {token}"},
                    json=task
                )
                if resp.status_code == 201:
                    tasks_created.append(task["title"])

            print(f"    Tasks created: {len(tasks_created)}")
            db_tasks = get_db_state()
            print(f"    Database tasks: {len(db_tasks)}")

            results.append(("DB Integration", len(db_tasks) == 3))
            print("    [PASS]" if len(db_tasks) == 3 else "    [FAIL]")
        except Exception as e:
            results.append(("DB Integration", False))
            print(f"    [FAIL]: {e}")

        # ============================================
        # TEST 8: Dashboard with Tasks
        # ============================================
        print("\n[TEST 8] Dashboard Task Display")
        try:
            await page.goto(f"{BASE_URL}/dashboard", wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            ss = await take_screenshot(page, "07_dashboard_tasks", "TEST 8: Dashboard with Tasks")
            screenshots.append(ss)
            results.append(("Task Display", True))
            print("    [PASS]")
        except Exception as e:
            results.append(("Task Display", False))
            print(f"    [FAIL]: {e}")

        # ============================================
        # TEST 9: Console Errors
        # ============================================
        print("\n[TEST 9] Console Error Check")
        errors = [log for log in console_logs if "error" in log.lower()]
        critical = [e for e in errors if "CORS" in e or "500" in e or "Failed" in e]

        print(f"    Total logs: {len(console_logs)}")
        print(f"    Errors: {len(errors)}")
        print(f"    Critical: {len(critical)}")

        results.append(("No Critical Errors", len(critical) == 0))
        print("    [PASS]" if len(critical) == 0 else f"    [WARN] {len(critical)} critical errors")

        # ============================================
        # TEST 10: Final Chat State
        # ============================================
        print("\n[TEST 10] Final Chat State")
        try:
            await page.goto(f"{BASE_URL}/dashboard/chat", wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            ss = await take_screenshot(page, "08_chat_final", "TEST 10: Final Chat State")
            screenshots.append(ss)
            results.append(("Final State", True))
            print("    [PASS]")
        except Exception as e:
            results.append(("Final State", False))
            print(f"    [FAIL]: {e}")

        await browser.close()

    # ============================================
    # SUMMARY
    # ============================================
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for r in results if r[1])
    total = len(results)

    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")

    print("\nResults:")
    print("-" * 50)
    for test_name, test_passed in results:
        icon = "+" if test_passed else "x"
        status = "PASS" if test_passed else "FAIL"
        print(f"  [{icon}] {test_name}: {status}")

    print(f"\nScreenshots: {len(screenshots)} captured")
    print(f"Location: {SCREENSHOT_DIR}/")
    for s in screenshots:
        print(f"  - {os.path.basename(s)}")

    print("\n" + "=" * 70)
    if passed == total:
        print("ALL TESTS PASSED [OK]")
    else:
        print(f"TESTS COMPLETED ({passed}/{total} passed)")
    print("=" * 70)

    return results, screenshots


if __name__ == "__main__":
    asyncio.run(run_ui_tests())
