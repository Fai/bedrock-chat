import { test, expect } from '@playwright/test';
import { AuthHelper } from '../utils/auth';
import { BotHelper } from '../utils/bot';

test.describe('SQL Knowledge Base', () => {
  let auth: AuthHelper;
  let bot: BotHelper;

  test.beforeEach(async ({ page }) => {
    auth = new AuthHelper(page);
    bot = new BotHelper(page);
    await auth.login();
  });

  test('should create SQL bot successfully', async ({ page }) => {
    await bot.createSqlBot({
      name: 'Test SQL Bot',
      description: 'E2E test bot with SQL KB',
      workgroupName: 'test-workgroup',
      databaseName: 'test_db',
      tableName: 'products'
    });

    // Verify bot appears in list
    await page.goto('/bot');
    await expect(page.locator('text=Test SQL Bot')).toBeVisible();
  });

  test('should hide vector-specific settings for SQL KB', async ({ page }) => {
    await page.goto('/bot/new');
    await page.click('[data-testid="kb-type-sql"]');

    // Should hide vector-specific settings
    await expect(page.locator('[data-testid="storage-type-selector"]')).not.toBeVisible();
    await expect(page.locator('[data-testid="chunking-configuration"]')).not.toBeVisible();
    await expect(page.locator('[data-testid="parsing-configuration"]')).not.toBeVisible();
    await expect(page.locator('[data-testid="opensearch-analyzer"]')).not.toBeVisible();

    // Should show SQL-specific settings
    await expect(page.locator('[data-testid="sql-database-config"]')).toBeVisible();
    await expect(page.locator('[data-testid="workgroup-name-input"]')).toBeVisible();
  });

  test('should validate required SQL fields', async ({ page }) => {
    await page.goto('/bot/new');
    await page.fill('[data-testid="bot-name-input"]', 'Test SQL Bot');
    await page.click('[data-testid="kb-type-sql"]');

    // Try to submit without required fields
    await page.click('[data-testid="create-bot-button"]');

    // Should show validation errors
    await expect(page.locator('[data-testid="workgroup-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="database-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="table-error"]')).toBeVisible();
  });

  test('should query SQL bot and display results', async ({ page }) => {
    // Create SQL bot first
    await bot.createSqlBot({
      name: 'Query Test Bot',
      description: 'Bot for testing SQL queries',
      workgroupName: 'test-workgroup',
      databaseName: 'test_db',
      tableName: 'products'
    });

    // Chat with the bot
    const response = await bot.chatWithBot('query-test-bot', 'Show me all products');

    // Should contain SQL results
    expect(response).toContain('SQL Query:');
    
    // Check for SQL results table
    await expect(page.locator('[data-testid="sql-results-table"]')).toBeVisible();
  });

  test('should show KB status during creation', async ({ page }) => {
    await page.goto('/bot/new');
    await page.fill('[data-testid="bot-name-input"]', 'Status Test Bot');
    await page.click('[data-testid="kb-type-sql"]');
    
    // Fill SQL config
    await page.fill('[data-testid="workgroup-name-input"]', 'test-workgroup');
    await page.fill('[data-testid="database-name-input"]', 'test_db');
    await page.fill('[data-testid="table-name-input"]', 'products');

    // Submit
    await page.click('[data-testid="create-bot-button"]');

    // Should show KB creation status
    await expect(page.locator('[data-testid="kb-status-creating"]')).toBeVisible();
    
    // Wait for completion
    await expect(page.locator('[data-testid="kb-status-active"]')).toBeVisible({ timeout: 60000 });
  });
});
