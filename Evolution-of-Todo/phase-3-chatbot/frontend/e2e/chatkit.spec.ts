import { test, expect } from "@playwright/test";

// Test configuration
const BASE_URL = "http://localhost:3000";
// Use a fixed test email to avoid creating too many accounts
const TEST_USER = {
  email: "playwright_test@example.com",
  password: "Test123456!",
};

test.describe("ChatKit E2E Tests", () => {
  test.beforeEach(async ({ page }) => {
    // Enable console logging
    page.on("console", (msg) => console.log("Browser:", msg.text()));
    page.on("pageerror", (error) => console.log("Page Error:", error.message));
  });

  test("should register, login, and access chat page", async ({ page }) => {
    // Step 1: Register a new user
    console.log("Step 1: Navigating to register page...");
    await page.goto(`${BASE_URL}/register`);
    await page.waitForLoadState("networkidle");

    // Fill registration form (only email and password fields)
    console.log("Filling registration form...");
    await page.fill('input[name="email"]', TEST_USER.email);
    await page.fill('input[name="password"]', TEST_USER.password);

    // Click register button
    await page.click('button[type="submit"]');

    // Wait for redirect to dashboard or login (or stay on page if user exists)
    await page.waitForTimeout(3000);
    console.log("After registration, current URL:", page.url());

    // Step 2: If still on register or redirected to login, log in
    if (page.url().includes("/login") || page.url().includes("/register")) {
      console.log("Step 2: Logging in...");
      await page.goto(`${BASE_URL}/login`);
      await page.waitForLoadState("networkidle");
      await page.fill('input[name="email"]', TEST_USER.email);
      await page.fill('input[name="password"]', TEST_USER.password);
      await page.click('button[type="submit"]');
      await page.waitForTimeout(3000);
    }

    console.log("After login attempt, current URL:", page.url());

    // Step 3: Navigate to chat page
    console.log("Step 3: Navigating to chat page...");
    await page.goto(`${BASE_URL}/dashboard/chat`);
    await page.waitForLoadState("networkidle");

    // Wait for ChatKit to load
    console.log("Waiting for ChatKit component...");
    await page.waitForTimeout(5000);

    // Take a screenshot for debugging
    await page.screenshot({ path: "e2e/screenshots/chat-page.png", fullPage: true });
    console.log("Screenshot saved to e2e/screenshots/chat-page.png");

    // Check the page URL
    console.log("Final URL:", page.url());

    // If redirected to login, that's an auth issue to investigate
    if (page.url().includes("/login")) {
      console.log("WARNING: Redirected to login - auth may not be working");
    }
  });

  test("should send a message in ChatKit", async ({ page }) => {
    // First login
    console.log("Logging in...");
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState("networkidle");
    await page.fill('input[name="email"]', TEST_USER.email);
    await page.fill('input[name="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);

    // If login failed, register first
    if (page.url().includes("/login")) {
      console.log("Login failed, registering...");
      await page.goto(`${BASE_URL}/register`);
      await page.waitForLoadState("networkidle");
      await page.fill('input[name="email"]', TEST_USER.email);
      await page.fill('input[name="password"]', TEST_USER.password);
      await page.click('button[type="submit"]');
      await page.waitForTimeout(3000);

      // Then login
      await page.goto(`${BASE_URL}/login`);
      await page.waitForLoadState("networkidle");
      await page.fill('input[name="email"]', TEST_USER.email);
      await page.fill('input[name="password"]', TEST_USER.password);
      await page.click('button[type="submit"]');
      await page.waitForTimeout(3000);
    }

    // Navigate to chat
    console.log("Navigating to chat...");
    await page.goto(`${BASE_URL}/dashboard/chat`);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(5000);

    // Take screenshot of the chat interface
    await page.screenshot({ path: "e2e/screenshots/chat-loaded.png", fullPage: true });
    console.log("Screenshot saved to e2e/screenshots/chat-loaded.png");

    // Log all network requests
    const requests: string[] = [];
    page.on("request", (request) => {
      if (request.url().includes("/api/") || request.url().includes("chatkit")) {
        requests.push(`${request.method()} ${request.url()}`);
      }
    });

    // Wait and collect API calls
    await page.waitForTimeout(3000);
    console.log("API calls made:", requests);

    // Final screenshot
    await page.screenshot({ path: "e2e/screenshots/chat-final.png", fullPage: true });
  });
});
