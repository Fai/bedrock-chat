import { test, expect } from '@playwright/test';
import { AuthHelper } from '../utils/auth';
import { BotHelper } from '../utils/bot';

test.describe('Vector Knowledge Base', () => {
  let auth: AuthHelper;
  let bot: BotHelper;

  test.beforeEach(async ({ page }) => {
    auth = new AuthHelper(page);
    bot = new BotHelper(page);
    await auth.login();
  });

  test('should create OpenSearch Serverless bot', async ({ page }) => {
    await bot.createVectorBot({
      name: 'Test OpenSearch Bot',
      description: 'E2E test bot with OpenSearch storage',
      storageType: 'OPENSEARCH_SERVERLESS'
    });

    // Verify bot appears in bot list
    await page.goto('/bot');
    await expect(page.locator('text=Test OpenSearch Bot')).toBeVisible();
  });

  test('should create S3 Vector bot with warning', async ({ page }) => {
    await bot.createVectorBot({
      name: 'Test S3 Vector Bot',
      description: 'E2E test bot with S3 Vector storage',
      storageType: 'S3_VECTOR'
    });

    // Verify S3 Vector warning was shown during creation
    await page.goto('/bot');
    await expect(page.locator('text=Test S3 Vector Bot')).toBeVisible();
  });

  test('should show storage type selector for new bots only', async ({ page }) => {
    // New bot should show storage selector
    await page.goto('/bot/new');
    await page.click('[data-testid="kb-type-vector"]');
    await expect(page.locator('[data-testid="storage-type-selector"]')).toBeVisible();

    // Create a bot first
    await bot.createVectorBot({
      name: 'Edit Test Bot',
      description: 'Bot for testing edit flow',
      storageType: 'OPENSEARCH_SERVERLESS'
    });

    // Edit existing bot should NOT show storage selector
    const botId = await page.getAttribute('[data-testid="bot-id"]', 'value');
    await page.goto(`/bot/${botId}/edit`);
    await expect(page.locator('[data-testid="storage-type-selector"]')).not.toBeVisible();
  });

  test('should enforce S3 Vector 500 token limit', async ({ page }) => {
    await page.goto('/bot/new');
    await page.click('[data-testid="kb-type-vector"]');
    await page.click('[data-testid="storage-type-s3-vector"]');

    // Try to set chunk size > 500 tokens
    await page.click('[data-testid="chunking-strategy-fixed"]');
    await page.fill('[data-testid="max-tokens-input"]', '1000');

    // Should show validation error
    await expect(page.locator('[data-testid="token-limit-error"]')).toBeVisible();
    await expect(page.locator('text=500 tokens max')).toBeVisible();
  });

  test('should disable hybrid search for S3 Vector', async ({ page }) => {
    await page.goto('/bot/new');
    await page.click('[data-testid="kb-type-vector"]');
    
    // OpenSearch should allow hybrid search
    await page.click('[data-testid="storage-type-opensearch"]');
    await expect(page.locator('[data-testid="search-type-hybrid"]')).toBeEnabled();

    // S3 Vector should disable hybrid search
    await page.click('[data-testid="storage-type-s3-vector"]');
    await expect(page.locator('[data-testid="search-type-hybrid"]')).toBeDisabled();
    await expect(page.locator('[data-testid="search-type-semantic"]')).toBeChecked();
  });
});
