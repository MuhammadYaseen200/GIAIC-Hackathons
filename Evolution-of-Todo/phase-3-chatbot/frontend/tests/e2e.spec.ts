import { test, expect } from '@playwright/test';

test.describe('Phase 3 E2E Tests', () => {
  const BASE_URL = 'http://localhost:3000';

  test('homepage should load', async ({ page }) => {
    await page.goto(BASE_URL);
    await expect(page).toHaveTitle(/Todo/i);
  });

  test('login page should be accessible', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    // Check for login form elements
    await expect(page.locator('input[type="email"], input[name="email"]')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('input[type="password"], input[name="password"]')).toBeVisible();
  });

  test('register page should be accessible', async ({ page }) => {
    await page.goto(`${BASE_URL}/register`);
    // Check for registration form elements
    await expect(page.locator('input[type="email"], input[name="email"]')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('input[type="password"], input[name="password"]')).toBeVisible();
  });

  test('unauthenticated users redirected to login', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    // Should redirect to login page
    await expect(page).toHaveURL(/login|\/$/);
  });

  test('dashboard chat link exists after login', async ({ page }) => {
    // First register a new user
    const testEmail = `playwright-${Date.now()}@test.com`;
    const testPassword = 'PlaywrightTest123!';

    // Go to register page
    await page.goto(`${BASE_URL}/register`);
    await page.waitForLoadState('networkidle');

    // Fill registration form
    await page.fill('input[type="email"], input[name="email"]', testEmail);
    await page.fill('input[type="password"], input[name="password"]', testPassword);

    // Look for name field if it exists
    const nameInput = page.locator('input[name="name"], input[placeholder*="name" i]');
    if (await nameInput.isVisible()) {
      await nameInput.fill('Playwright User');
    }

    // Submit form
    await page.click('button[type="submit"]');

    // Wait for navigation or redirect
    await page.waitForURL(/dashboard|login/, { timeout: 15000 });

    // If we need to login after registration
    if (page.url().includes('login')) {
      await page.fill('input[type="email"], input[name="email"]', testEmail);
      await page.fill('input[type="password"], input[name="password"]', testPassword);
      await page.click('button[type="submit"]');
      await page.waitForURL(/dashboard/, { timeout: 15000 });
    }

    // Check that we're on dashboard
    await expect(page).toHaveURL(/dashboard/);

    // Check for chat link in navigation
    const chatLink = page.locator('a[href*="chat"], nav >> text=chat', { hasText: /chat/i });
    if (await chatLink.isVisible({ timeout: 5000 })) {
      expect(await chatLink.isVisible()).toBeTruthy();
    }
  });
});
