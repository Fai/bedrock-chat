import { test, expect } from '@playwright/test';
import { AuthHelper } from '../utils/auth';
import { BotHelper } from '../utils/bot';

test.describe('Chat Functionality', () => {
  let auth: AuthHelper;
  let bot: BotHelper;

  test.beforeEach(async ({ page }) => {
    auth = new AuthHelper(page);
    bot = new BotHelper(page);
    await auth.login();
  });

  test('should send and receive messages', async ({ page }) => {
    await page.goto('/');
    
    // Send a message
    await page.fill('[data-testid="chat-input"]', 'Hello, how are you?');
    await page.click('[data-testid="send-button"]');

    // Wait for response
    await expect(page.locator('[data-testid="bot-response"]')).toBeVisible({ timeout: 30000 });
    
    // Verify message appears in chat history
    await expect(page.locator('[data-testid="user-message"]')).toContainText('Hello, how are you?');
  });

  test('should show typing indicator during response', async ({ page }) => {
    await page.goto('/');
    
    await page.fill('[data-testid="chat-input"]', 'Tell me a story');
    await page.click('[data-testid="send-button"]');

    // Should show typing indicator
    await expect(page.locator('[data-testid="typing-indicator"]')).toBeVisible();
    
    // Typing indicator should disappear when response arrives
    await expect(page.locator('[data-testid="bot-response"]')).toBeVisible({ timeout: 30000 });
    await expect(page.locator('[data-testid="typing-indicator"]')).not.toBeVisible();
  });

  test('should handle long messages with S3 storage', async ({ page }) => {
    await page.goto('/');
    
    // Send a very long message (>300KB trigger)
    const longMessage = 'A'.repeat(350000);
    await page.fill('[data-testid="chat-input"]', longMessage);
    await page.click('[data-testid="send-button"]');

    // Should handle large message successfully
    await expect(page.locator('[data-testid="bot-response"]')).toBeVisible({ timeout: 45000 });
    await expect(page.locator('[data-testid="user-message"]')).toContainText('A'.repeat(100)); // Partial match
  });

  test('should persist chat history', async ({ page }) => {
    await page.goto('/');
    
    // Send a message
    await page.fill('[data-testid="chat-input"]', 'Remember this message');
    await page.click('[data-testid="send-button"]');
    await expect(page.locator('[data-testid="bot-response"]')).toBeVisible({ timeout: 30000 });

    // Refresh page
    await page.reload();
    
    // Chat history should persist
    await expect(page.locator('[data-testid="user-message"]')).toContainText('Remember this message');
  });

  test('should show error for failed messages', async ({ page }) => {
    // Mock network failure
    await page.route('**/chat', route => route.abort());
    
    await page.goto('/');
    await page.fill('[data-testid="chat-input"]', 'This should fail');
    await page.click('[data-testid="send-button"]');

    // Should show error message
    await expect(page.locator('[data-testid="message-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
  });

  test('should support message retry', async ({ page }) => {
    // Mock initial failure, then success
    let callCount = 0;
    await page.route('**/chat', route => {
      callCount++;
      if (callCount === 1) {
        route.abort();
      } else {
        route.continue();
      }
    });

    await page.goto('/');
    await page.fill('[data-testid="chat-input"]', 'Retry test');
    await page.click('[data-testid="send-button"]');

    // Should show error first
    await expect(page.locator('[data-testid="message-error"]')).toBeVisible();
    
    // Click retry
    await page.click('[data-testid="retry-button"]');
    
    // Should succeed on retry
    await expect(page.locator('[data-testid="bot-response"]')).toBeVisible({ timeout: 30000 });
  });
});
