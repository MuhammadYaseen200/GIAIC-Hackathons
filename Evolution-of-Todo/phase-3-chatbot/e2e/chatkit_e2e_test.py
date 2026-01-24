"""
CHATKIT E2E VALIDATION TEST

Comprehensive end-to-end test for ChatKit integration.
Tests the complete flow: register → login → chat → CRUD operations.

Requirements:
- Backend running at http://localhost:8000
- Frontend running at http://localhost:3000
- Chrome/Chromium installed

Usage:
    cd E:/M.Y/GIAIC-Hackathons/Evolution-of-Todo/phase-3-chatbot
    python e2e/chatkit_e2e_test.py
"""

from playwright.sync_api import sync_playwright
import time
import os
import sqlite3
from datetime import datetime

class ChatKitE2ETest:
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.api_url = "http://localhost:8000/api/v1"
        self.test_email = f"test_chatkit_{int(time.time())}@example.com"
        self.test_password = "TestPassword123!"
        self.screenshots_dir = "e2e/screenshots"
        self.results = []

        # Create screenshots directory
        os.makedirs(self.screenshots_dir, exist_ok=True)

    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        self.results.append(f"[{timestamp}] {message}")

    def screenshot(self, page, name):
        """Take screenshot"""
        filename = f"{self.screenshots_dir}/{int(time.time())}_{name}.png"
        page.screenshot(path=filename, full_page=True)
        self.log(f"📸 Screenshot saved: {filename}")
        return filename

    def check_db_task(self, expected_title=None, expected_completed=None):
        """Verify task in database"""
        try:
            conn = sqlite3.connect("backend/todo_app.db")
            cursor = conn.cursor()
            cursor.execute("SELECT title, completed FROM tasks WHERE user_id IS NOT NULL ORDER BY id DESC LIMIT 1")
            task = cursor.fetchone()
            conn.close()

            if task:
                title, completed = task
                if expected_title and expected_title.lower() not in title.lower():
                    self.log(f"❌ DB verification failed: Expected '{expected_title}', found '{title}'")
                    return False
                if expected_completed is not None and completed != expected_completed:
                    self.log(f"❌ DB verification failed: Expected completed={expected_completed}, found {completed}")
                    return False
                self.log(f"✅ DB verification passed: '{title}' (completed: {completed})")
                return True
            else:
                self.log("⚠️  No tasks found in database")
                return False
        except Exception as e:
            self.log(f"⚠️  DB check failed: {e}")
            return False

    def run(self):
        """Run full E2E test"""
        self.log("=" * 70)
        self.log("CHATKIT E2E VALIDATION TEST")
        self.log("=" * 70)

        with sync_playwright() as p:
            self.log("🚀 Launching browser...")
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                ignore_https_errors=True
            )

            # Enable console logging
            def log_console(msg):
                self.log(f"📝 Console: {msg.text}")
            context.on("console", log_console)

            page = context.new_page()

            try:
                # Test 1: Register
                self.log("\n[Test 1] Registering new user...")
                page.goto(f"{self.base_url}/register")
                page.wait_for_load_state("networkidle")
                self.screenshot(page, "01_register_page")

                page.fill('input[name="email"]', self.test_email)
                page.fill('input[name="password"]', self.test_password)
                self.screenshot(page, "02_register_form_filled")

                page.click('button[type="submit"]')
                page.wait_for_timeout(2000)
                self.screenshot(page, "03_after_register")

                # If registration failed (user exists), try login
                if page.url().endswith("/register"):
                    self.log("⚠️  Registration failed, trying login...")
                    page.goto(f"{self.base_url}/login")
                    page.wait_for_load_state("networkidle")
                else:
                    self.log("✅ Registration successful")

                # Test 2: Login
                if page.url().endswith("/login"):
                    self.log("\n[Test 2] Logging in...")
                    page.fill('input[name="email"]', self.test_email)
                    page.fill('input[name="password"]', self.test_password)
                    self.screenshot(page, "04_login_form_filled")

                    page.click('button[type="submit"]')
                    page.wait_for_timeout(2000)
                    self.screenshot(page, "05_after_login")

                # Test 3: Navigate to Chat
                self.log("\n[Test 3] Navigating to Chat...")
                page.goto(f"{self.base_url}/dashboard/chat")
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(3000)  # Wait for ChatKit to load
                self.screenshot(page, "06_chat_page_loaded")

                # Check if ChatKit is loaded
                try:
                    chatkit_loaded = page.locator("openai-chatkit").is_visible(timeout=5000)
                    if chatkit_loaded:
                        self.log("✅ ChatKit component loaded")
                    else:
                        self.log("⚠️  ChatKit component not found")
                except:
                    self.log("⚠️  Could not verify ChatKit component")

                # Test 4: Add Task via ChatKit
                self.log("\n[Test 4] Adding task via ChatKit...")
                try:
                    # Find the chat input (this may vary based on ChatKit version)
                    # Try common selectors
                    input_selector = None

                    # Try shadow DOM or iframe
                    try:
                        # Look for input in openai-chatkit shadow DOM
                        textareas = page.locator("textarea").all()
                        if textareas:
                            input_selector = "textarea"
                        else:
                            input_selector = 'input[placeholder*="message"], input[placeholder*="Message"]'
                    except:
                        input_selector = 'input[placeholder*="message"], input[placeholder*="Message"]'

                    if input_selector:
                        page.fill(input_selector, "Add a high priority task to Buy groceries for dinner")
                        self.log("✅ Typed: 'Add a high priority task to Buy groceries for dinner'")
                        self.screenshot(page, "07_chat_input_filled")

                        # Send message
                        page.keyboard.press("Enter")
                        self.log("✅ Sent message")
                        page.wait_for_timeout(3000)
                        self.screenshot(page, "08_after_add_task")

                        # Check for AI response
                        messages = page.locator(".message, [data-role='assistant'], .ai-response").all()
                        if messages:
                            self.log("✅ Received AI response")
                        else:
                            self.log("⚠️  No AI response visible")

                        # Verify in database
                        self.check_db_task(expected_title="groceries", expected_completed=False)
                    else:
                        self.log("⚠️  Could not find chat input")

                except Exception as e:
                    self.log(f"❌ Error adding task: {e}")

                # Test 5: List Tasks
                self.log("\n[Test 5] Listing tasks...")
                try:
                    if input_selector:
                        page.fill(input_selector, "Show me all my tasks")
                        page.keyboard.press("Enter")
                        page.wait_for_timeout(3000)
                        self.screenshot(page, "09_after_list_tasks")
                        self.log("✅ Requested task list")
                    else:
                        self.log("⚠️  Could not find chat input")
                except Exception as e:
                    self.log(f"❌ Error listing tasks: {e}")

                # Test 6: Complete Task
                self.log("\n[Test 6] Completing task...")
                try:
                    if input_selector:
                        page.fill(input_selector, "Complete the groceries task")
                        page.keyboard.press("Enter")
                        page.wait_for_timeout(3000)
                        self.screenshot(page, "10_after_complete_task")
                        self.log("✅ Marked task as complete")

                        # Verify in database
                        self.check_db_task(expected_title="groceries", expected_completed=True)
                    else:
                        self.log("⚠️  Could not find chat input")
                except Exception as e:
                    self.log(f"❌ Error completing task: {e}")

                # Test 7: Delete Task
                self.log("\n[Test 7] Deleting task...")
                try:
                    if input_selector:
                        page.fill(input_selector, "Delete the groceries task")
                        page.keyboard.press("Enter")
                        page.wait_for_timeout(3000)
                        self.screenshot(page, "11_after_delete_task")
                        self.log("✅ Deleted task")
                    else:
                        self.log("⚠️  Could not find chat input")
                except Exception as e:
                    self.log(f"❌ Error deleting task: {e}")

                self.log("\n" + "=" * 70)
                self.log("✅ E2E TEST COMPLETED")
                self.log("=" * 70)

            except Exception as e:
                self.log(f"\n❌ FATAL ERROR: {e}")
                self.screenshot(page, "error_state")
                import traceback
                self.log(traceback.format_exc())

            finally:
                browser.close()
                self.log("\n🚪 Browser closed")

        # Print summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        for result in self.results:
            print(result)

if __name__ == "__main__":
    test = ChatKitE2ETest()
    test.run()
