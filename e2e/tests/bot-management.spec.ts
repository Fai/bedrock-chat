import { test, expect } from '@playwright/test';
import { AuthHelper } from '../utils/auth';
import { BotHelper } from '../utils/bot';

test.describe('Bot Management', () => {
  let auth: AuthHelper;
  let bot: BotHelper;

  test.beforeEach(async ({ page }) => {
    auth = new AuthHelper(page);
    bot = new BotHelper(page);
    await auth.login();
  });

  test('should list all user bots', async ({ page }) => {
    // Create a test bot first
    await bot.createVectorBot({
      name: 'List Test Bot',
      description: 'Bot for testing list functionality',
      storageType: 'OPENSEARCH_SERVERLESS'
    });

    // Navigate to bot list
    await page.goto('/bot');
    
    // Should show the created bot
    await expect(page.locator('[data-testid="bot-list"]')).toBeVisible();
    await expect(page.locator('text=List Test Bot')).toBeVisible();
  });

  test('should edit bot details', async ({ page }) => {
    // Create bot
    await bot.createVectorBot({
      name: 'Edit Test Bot',
      description: 'Original description',
      storageType: 'OPENSEARCH_SERVERLESS'
    });

    // Navigate to edit
    await page.goto('/bot');
    await page.click('[data-testid="edit-bot-button"]:first-child');

    // Edit details
    await page.fill('[data-testid="bot-name-input"]', 'Updated Bot Name');
    await page.fill('[data-testid="bot-description-input"]', 'Updated description');
    
    // Save changes
    await page.click('[data-testid="save-bot-button"]');
    await expect(page.locator('[data-testid="bot-updated-success"]')).toBeVisible();

    // Verify changes
    await page.goto('/bot');
    await expect(page.locator('text=Updated Bot Name')).toBeVisible();
  });

  test('should delete bot with confirmation', async ({ page }) => {
    // Create bot
    await bot.createVectorBot({
      name: 'Delete Test Bot',
      description: 'Bot to be deleted',
      storageType: 'OPENSEARCH_SERVERLESS'
    });

    // Navigate to bot list
    await page.goto('/bot');
    
    // Click delete button
    await page.click('[data-testid="delete-bot-button"]:first-child');
    
    // Should show confirmation dialog
    await expect(page.locator('[data-testid="delete-confirmation"]')).toBeVisible();
    await expect(page.locator('text=Delete Test Bot')).toBeVisible();
    
    // Confirm deletion
    await page.click('[data-testid="confirm-delete-button"]');
    
    // Should show success message
    await expect(page.locator('[data-testid="bot-deleted-success"]')).toBeVisible();
    
    // Bot should be removed from list
    await expect(page.locator('text=Delete Test Bot')).not.toBeVisible();
  });

  test('should cancel bot deletion', async ({ page }) => {
    // Create bot
    await bot.createVectorBot({
      name: 'Cancel Delete Bot',
      description: 'Bot deletion to be cancelled',
      storageType: 'OPENSEARCH_SERVERLESS'
    });

    await page.goto('/bot');
    await page.click('[data-testid="delete-bot-button"]:first-child');
    
    // Cancel deletion
    await page.click('[data-testid="cancel-delete-button"]');
    
    // Dialog should close, bot should remain
    await expect(page.locator('[data-testid="delete-confirmation"]')).not.toBeVisible();
    await expect(page.locator('text=Cancel Delete Bot')).toBeVisible();
  });

  test('should show bot status badges', async ({ page }) => {
    await page.goto('/bot');
    
    // Should show status badges for bots
    await expect(page.locator('[data-testid="bot-status-badge"]')).toBeVisible();
    
    // Common statuses
    const possibleStatuses = ['AVAILABLE', 'CREATING', 'FAILED'];
    const statusVisible = await Promise.all(
      possibleStatuses.map(status => 
        page.locator(`[data-testid="status-${status.toLowerCase()}"]`).isVisible()
      )
    );
    
    // At least one status should be visible
    expect(statusVisible.some(Boolean)).toBe(true);
  });

  test('should filter bots by status', async ({ page }) => {
    await page.goto('/bot');
    
    // Should have filter dropdown
    await expect(page.locator('[data-testid="bot-filter"]')).toBeVisible();
    
    // Filter by AVAILABLE status
    await page.selectOption('[data-testid="bot-filter"]', 'AVAILABLE');
    
    // Should only show available bots
    const statusBadges = page.locator('[data-testid="bot-status-badge"]');
    const count = await statusBadges.count();
    
    for (let i = 0; i < count; i++) {
      await expect(statusBadges.nth(i)).toContainText('AVAILABLE');
    }
  });

  test('should search bots by name', async ({ page }) => {
    // Create multiple bots
    await bot.createVectorBot({
      name: 'Search Bot Alpha',
      description: 'First search test bot',
      storageType: 'OPENSEARCH_SERVERLESS'
    });
    
    await bot.createVectorBot({
      name: 'Search Bot Beta',
      description: 'Second search test bot',
      storageType: 'S3_VECTOR'
    });

    await page.goto('/bot');
    
    // Search for specific bot
    await page.fill('[data-testid="bot-search-input"]', 'Alpha');
    
    // Should show only matching bot
    await expect(page.locator('text=Search Bot Alpha')).toBeVisible();
    await expect(page.locator('text=Search Bot Beta')).not.toBeVisible();
  });
});
