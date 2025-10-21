import { test, expect } from '@playwright/test';
import { AuthHelper } from '../utils/auth';

test.describe('Authentication', () => {
  test('should login successfully', async ({ page }) => {
    const auth = new AuthHelper(page);
    
    await auth.login();
    
    // Verify user is logged in
    await expect(page.locator('[data-testid="main-layout"]')).toBeVisible();
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  });

  test('should logout successfully', async ({ page }) => {
    const auth = new AuthHelper(page);
    
    await auth.login();
    await auth.logout();
    
    // Verify user is logged out
    await expect(page.locator('[data-testid="auth-form"]')).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    const auth = new AuthHelper(page);
    
    await page.goto('/');
    await page.fill('[data-testid="email-input"]', 'invalid@example.com');
    await page.fill('[data-testid="password-input"]', 'wrongpassword');
    await page.click('[data-testid="sign-in-button"]');
    
    // Verify error message
    await expect(page.locator('[data-testid="auth-error"]')).toBeVisible();
  });

  test('should redirect to login when accessing protected route', async ({ page }) => {
    await page.goto('/bot/new');
    
    // Should redirect to login
    await expect(page.locator('[data-testid="auth-form"]')).toBeVisible();
  });
});
