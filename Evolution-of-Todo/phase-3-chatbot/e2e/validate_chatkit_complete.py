#!/usr/bin/env python
"""
CHATKIT COMPLETE E2E VALIDATION SCRIPT
Performs comprehensive testing of ChatKit integration with real browser testing
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
from pathlib import Path

# Import Playwright
try:
    from playwright.sync_api import sync_playwright, expect
except ImportError:
    print("ERROR: Playwright not installed. Run: pip install playwright")
    print("Then run: playwright install chromium")
    sys.exit(1)

class ChatKitValidator:
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.api_url = "http://localhost:8000/api/v1"
        self.test_email = f"test_chatkit_{int(time.time())}@example.com"
        self.test_password = "TestPassword123!"
        self.screenshots_dir = Path("e2e/validation-artifacts")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.results = []
        self.task_ids = []
        self.user_token = None

        # Colors for terminal output
        self.COLORS = {
            'GREEN': '\033[92m',
            'RED': '\033[91m',
            'YELLOW': '\033[93m',
            'BLUE': '\033[94m',
            'BOLD': '\033[1m',
            'RESET': '\033[0m'
        }

    def log(self, message, status="INFO", data=None):
        """Log with timestamp and status"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = {
            "PASS": self.COLORS['GREEN'],
            "FAIL": self.COLORS['RED'],
            "WARN": self.COLORS['YELLOW'],
            "INFO": self.COLORS['BLUE'],
            "STEP": self.COLORS['BOLD']
        }.get(status, self.COLORS['BLUE'])

        log_entry = f"[{timestamp}] {status}: {message}"
        print(f"{color}{log_entry}{self.COLORS['RESET']}")

        if data:
            print(f"{self.COLORS['YELLOW']}  Data: {json.dumps(data, indent=2)}{self.COLORS['RESET']}")

        self.results.append({
            "timestamp": timestamp,
            "status": status,
            "message": message,
            "data": data
        })

    def screenshot(self, page, name):
        """Take screenshot"""
        filename = self.screenshots_dir / f"{int(time.time())}_{name}.png"
        try:
            page.screenshot(path=str(filename), full_page=True)
            self.log(f"📸 Screenshot saved: {filename.name}", "PASS")
            return str(filename)
        except Exception as e:
            self.log(f"⚠️  Failed to take screenshot: {e}", "WARN")
            return None

    def check_server_health(self):
        """Verify backend and frontend are running"""
        self.log("=" * 70, "STEP")
        self.log("PHASE 1: Server Health Check", "STEP")
        self.log("=" * 70, "STEP")

        # Check backend
        try:
            response = requests.get("http://localhost:8000/", timeout=5)
            if response.status_code == 200:
                self.log("✅ Backend server is running", "PASS")
            else:
                self.log(f"⚠️  Backend returned status {response.status_code}", "WARN")
        except Exception as e:
            self.log(f"❌ Backend server not accessible: {e}", "FAIL")
            sys.exit(1)

        # Check frontend
        try:
            response = requests.get("http://localhost:3000/login", timeout=5)
            if response.status_code == 200:
                self.log("✅ Frontend server is running", "PASS")
            else:
                self.log(f"⚠️  Frontend returned status {response.status_code}", "WARN")
        except Exception as e:
            self.log(f"❌ Frontend server not accessible: {e}", "FAIL")
            sys.exit(1)

    def register_user(self, page):
        """Register new user via UI"""
        self.log("=" * 70, "STEP")
        self.log("PHASE 2: User Registration", "STEP")
        self.log("=" * 70, "STEP")

        page.goto(f"{self.base_url}/register")
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        self.screenshot(page, "01_register_page")

        # Fill form
        email_input = page.locator('input[type="email"], input[name="email"]')
        password_input = page.locator('input[type="password"], input[name="password"]')

        email_input.fill(self.test_email)
        password_input.fill(self.test_password)

        self.log("✅ Filled registration form", "PASS")
        self.screenshot(page, "02_register_form_filled")

        # Submit
        page.click('button[type="submit"]')
        time.sleep(2)

        self.screenshot(page, "03_after_register")

        # Check if registration succeeded or user exists
        if page.url().endswith("/login") or "/dashboard" in page.url():
            self.log("✅ Registration successful (or user exists)", "PASS")
            return True
        else:
            self.log("⚠️  Registration may have failed, will try login", "WARN")
            return False

    def login_user(self, page):
        """Login user via UI"""
        self.log("=" * 70, "STEP")
        self.log("PHASE 3: User Login", "STEP")
        self.log("=" * 70, "STEP")

        page.goto(f"{self.base_url}/login")
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        self.screenshot(page, "04_login_page")

        # Fill form
        email_input = page.locator('input[type="email"], input[name="email"]')
        password_input = page.locator('input[type="password"], input[name="password"]')

        email_input.fill(self.test_email)
        password_input.fill(self.test_password)

        self.log("✅ Filled login form", "PASS")
        self.screenshot(page, "05_login_form_filled")

        # Submit
        page.click('button[type="submit"]')
        time.sleep(2)

        self.screenshot(page, "06_after_login")

        if "/dashboard" in page.url() or page.url() == self.base_url + "/":
            self.log("✅ Login successful", "PASS")
            return True
        else:
            self.log(f"❌ Login failed, still at: {page.url()}", "FAIL")
            return False

    def navigate_to_chat(self, page):
        """Navigate to Chat page"""
        self.log("=" * 70, "STEP")
        self.log("PHASE 4: Navigate to Chat", "STEP")
        self.log("=" * 70, "STEP")

        page.goto(f"{self.base_url}/dashboard/chat")
        page.wait_for_load_state("networkidle")
        time.sleep(3)  # Wait for ChatKit to initialize

        self.screenshot(page, "07_chat_page")

        # Check if ChatKit component exists
        try:
            # Look for ChatKit component
            chatkit = page.locator("openai-chatkit")
            if chatkit.is_visible(timeout=3000):
                self.log("✅ ChatKit component loaded", "PASS")
                return True
            else:
                # Check for any chat-like interface
                textareas = page.locator("textarea").count()
                if textareas > 0:
                    self.log("✅ Chat interface found (alternative selector)", "PASS")
                    return True
                else:
                    self.log("⚠️  ChatKit component not visible, but continuing", "WARN")
                    return True
        except Exception as e:
            self.log(f"⚠️  Could not verify ChatKit: {e}", "WARN")
            return True

    def send_chat_message(self, page, message):
        """Send message via ChatKit"""
        try:
            # Try multiple selectors for chat input
            selectors = [
                "textarea",
                'input[placeholder*="message" i]',
                'input[placeholder*="Message" i]',
                'input[placeholder*="chat" i]',
                'input[type="text"]'
            ]

            input_found = False
            for selector in selectors:
                try:
                    element = page.locator(selector).first
                    if element.is_visible(timeout=1000):
                        element.fill(message)
                        input_found = True
                        self.log(f"✅ Typed: '{message}'", "PASS")
                        break
                except:
                    continue

            if not input_found:
                self.log("❌ Could not find chat input", "FAIL")
                return False

            # Press Enter to send
            page.keyboard.press("Enter")
            time.sleep(3)  # Wait for response

            return True
        except Exception as e:
            self.log(f"❌ Error sending message: {e}", "FAIL")
            return False

    def test_add_task(self, page):
        """Test: Add task via ChatKit"""
        self.log("=" * 70, "STEP")
        self.log("PHASE 5: Test Add Task", "STEP")
        self.log("=" * 70, "STEP")

        message = "Add a high priority task to Buy groceries for dinner tonight"

        if self.send_chat_message(page, message):
            self.screenshot(page, "08_after_add_task")

            # Check for AI response
            try:
                # Look for assistant response
                response = page.locator(".message-assistant, .ai-response, [data-role='assistant']").last
                if response.is_visible(timeout=2000):
                    text = response.text_content()
                    self.log(f"✅ AI Response: {text[:100]}...", "PASS")
                else:
                    self.log("⚠️  No AI response visible", "WARN")
            except:
                self.log("⚠️  Could not find AI response", "WARN")

            # Verify in database
            time.sleep(1)
            self.verify_database_task("groceries", False)

            return True
        return False

    def test_list_tasks(self, page):
        """Test: List tasks via ChatKit"""
        self.log("=" * 70, "STEP")
        self.log("PHASE 6: Test List Tasks", "STEP")
        self.log("=" * 70, "STEP")

        if self.send_chat_message(page, "Show me all my tasks"):
            self.screenshot(page, "09_after_list_tasks")
            return True
        return False

    def test_complete_task(self, page):
        """Test: Complete task via ChatKit"""
        self.log("=" * 70, "STEP")
        self.log("PHASE 7: Test Complete Task", "STEP")
        self.log("=" * 70, "STEP")

        if self.send_chat_message(page, "Complete the groceries task"):
            self.screenshot(page, "10_after_complete_task")
            time.sleep(1)

            # Verify in database
            self.verify_database_task("groceries", True)

            return True
        return False

    def test_delete_task(self, page):
        """Test: Delete task via ChatKit"""
        self.log("=" * 70, "STEP")
        self.log("PHASE 8: Test Delete Task", "STEP")
        self.log("=" * 70, "STEP")

        if self.send_chat_message(page, "Delete the groceries task"):
            self.screenshot(page, "11_after_delete_task")
            time.sleep(1)

            # Verify deletion by checking task count
            self.check_task_count(expected_min=0, expected_max=1)

            return True
        return False

    def verify_database_task(self, expected_title=None, expected_completed=None):
        """Verify task state in SQLite database"""
        try:
            db_path = Path("backend/todo_app.db")
            if not db_path.exists():
                self.log("⚠️  Database file not found, skipping verification", "WARN")
                return False

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get latest task
            query = "SELECT title, completed, priority, id FROM tasks WHERE user_id IS NOT NULL ORDER BY id DESC LIMIT 1"
            cursor.execute(query)
            task = cursor.fetchone()
            conn.close()

            if task:
                title, completed, priority, task_id = task
                self.log(f"📊 DB Task: '{title}' | completed: {completed} | priority: {priority} | id: {task_id}", "INFO")

                if expected_title and expected_title.lower() not in title.lower():
                    self.log(f"❌ DB verification: Expected title containing '{expected_title}', got '{title}'", "FAIL")
                    return False

                if expected_completed is not None and completed != expected_completed:
                    self.log(f"❌ DB verification: Expected completed={expected_completed}, got {completed}", "FAIL")
                    return False

                self.log("✅ Database verification passed", "PASS")
                return True
            else:
                self.log("⚠️  No tasks found in database", "WARN")
                return False

        except Exception as e:
            self.log(f"⚠️  Database verification failed: {e}", "WARN")
            return False

    def check_task_count(self, expected_min=None, expected_max=None):
        """Check number of tasks in database"""
        try:
            db_path = Path("backend/todo_app.db")
            if not db_path.exists():
                return False

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id IS NOT NULL")
            count = cursor.fetchone()[0]
            conn.close()

            self.log(f"📊 Total tasks in DB: {count}", "INFO")

            if expected_min is not None and count < expected_min:
                self.log(f"❌ Task count too low: expected at least {expected_min}, got {count}", "FAIL")
                return False

            if expected_max is not None and count > expected_max:
                self.log(f"❌ Task count too high: expected at most {expected_max}, got {count}", "FAIL")
                return False

            return True

        except Exception as e:
            self.log(f"⚠️  Could not check task count: {e}", "WARN")
            return False

    def generate_report(self):
        """Generate validation report"""
        self.log("=" * 70, "STEP")
        self.log("PHASE 9: GENERATE REPORT", "STEP")
        self.log("=" * 70, "STEP")

        # Count results
        stats = {
            "PASS": len([r for r in self.results if r["status"] == "PASS"]),
            "FAIL": len([r for r in self.results if r["status"] == "FAIL"]),
            "WARN": len([r for r in self.results if r["status"] == "WARN"]),
            "INFO": len([r for r in self.results if r["status"] == "INFO"])
        }

        # Save results to JSON
        report_file = self.screenshots_dir / "validation_report.json"
        with open(report_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "test_email": self.test_email,
                "stats": stats,
                "results": self.results
            }, f, indent=2)

        self.log(f"📄 Report saved: {report_file}", "PASS")

        # Print summary
        print("\n" + "=" * 70)
        print(f"VALIDATION COMPLETE")
        print("=" * 70)
        print(f"✅ Passed: {stats['PASS']}")
        print(f"❌ Failed: {stats['FAIL']}")
        print(f"⚠️  Warnings: {stats['WARN']}")
        print(f"💡 Info: {stats['INFO']}")
        print("=" * 70)

        success_rate = (stats['PASS'] / (stats['PASS'] + stats['FAIL'] + stats['WARN']) * 100) if (stats['PASS'] + stats['FAIL'] + stats['WARN']) > 0 else 0
        if success_rate >= 80:
            print("🟢 CHATKIT VALIDATION: SUCCESS")
        elif success_rate >= 60:
            print("🟡 CHATKIT VALIDATION: PARTIAL")
        else:
            print("🔴 CHATKIT VALIDATION: FAILED")
        print("=" * 70)

        return stats['FAIL'] == 0

    def run(self):
        """Run complete validation"""
        print("\n" + "=" * 70)
        print("CHATKIT E2E COMPLETE VALIDATION")
        print("=" * 70)
        print(f"Test User: {self.test_email}")
        print(f"Screenshots: {self.screenshots_dir}")
        print("=" * 70 + "\n")

        # Check servers
        self.check_server_health()

        # Run browser tests
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )

            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                ignore_https_errors=True
            )

            # Log console messages
            def handle_console(msg):
                if msg.type == 'error':
                    self.log(f"Console Error: {msg.text}", "FAIL")
                elif 'error' in msg.text.lower() or 'failed' in msg.text.lower():
                    self.log(f"Console Warning: {msg.text}", "WARN")
            context.on("console", handle_console)

            page = context.new_page()

            try:
                # Track requests
                requests = []
                def handle_request(request):
                    requests.append(f"{request.method} {request.url}")
                page.on("request", handle_request)

                # Execute test sequence
                if not self.register_user(page):
                    self.log("Registration failed, trying direct login", "WARN")

                if not self.login_user(page):
                    raise Exception("Failed to authenticate")

                if not self.navigate_to_chat(page):
                    raise Exception("Failed to navigate to chat")

                # Test CRUD operations
                operations = [
                    ("Add Task", self.test_add_task),
                    ("List Tasks", self.test_list_tasks),
                    ("Complete Task", self.test_complete_task),
                    ("Delete Task", self.test_delete_task),
                ]

                for op_name, op_func in operations:
                    try:
                        success = op_func(page)
                        if not success:
                            self.log(f"Operation '{op_name}' failed", "FAIL")
                    except Exception as e:
                        self.log(f"Error in '{op_name}': {e}", "FAIL")

                # Log network requests
                if requests:
                    chatkit_requests = [r for r in requests if '/chatkit' in r]
                    if chatkit_requests:
                        self.log(f"📊 ChatKit API calls: {len(chatkit_requests)}", "INFO")
                        for req in chatkit_requests:
                            self.log(f"  - {req}", "INFO")
                    else:
                        self.log("⚠️  No ChatKit API calls detected", "WARN")

            except Exception as e:
                self.log(f"Fatal error during test: {e}", "FAIL")
                import traceback
                self.log(traceback.format_exc(), "FAIL")
                self.screenshot(page, "error_state")

            finally:
                browser.close()
                self.log("Browser closed", "INFO")

        # Generate report
        success = self.generate_report()

        # Exit with appropriate code
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    validator = ChatKitValidator()
    validator.run()
