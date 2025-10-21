import { Page, expect } from '@playwright/test';

export class BotHelper {
  constructor(private page: Page) {}

  async createVectorBot(options: {
    name: string;
    description: string;
    storageType: 'OPENSEARCH_SERVERLESS' | 'S3_VECTOR';
    files?: string[];
  }) {
    // Navigate to bot creation
    await this.page.goto('/bot/new');
    await this.page.waitForSelector('[data-testid="bot-create-form"]');

    // Fill basic info
    await this.page.fill('[data-testid="bot-name-input"]', options.name);
    await this.page.fill('[data-testid="bot-description-input"]', options.description);

    // Select Vector KB type
    await this.page.click('[data-testid="kb-type-vector"]');

    // Select storage type
    if (options.storageType === 'S3_VECTOR') {
      await this.page.click('[data-testid="storage-type-s3-vector"]');
      // Verify S3 Vector warning appears
      await expect(this.page.locator('[data-testid="s3-vector-warning"]')).toBeVisible();
    } else {
      await this.page.click('[data-testid="storage-type-opensearch"]');
    }

    // Upload files if provided
    if (options.files?.length) {
      const fileInput = this.page.locator('[data-testid="file-upload-input"]');
      await fileInput.setInputFiles(options.files);
      
      // Wait for files to be processed
      for (const file of options.files) {
        await expect(this.page.locator(`[data-testid="uploaded-file-${file}"]`)).toBeVisible();
      }
    }

    // Submit form
    await this.page.click('[data-testid="create-bot-button"]');
    
    // Wait for success
    await this.page.waitForSelector('[data-testid="bot-created-success"]', { timeout: 30000 });
  }

  async createSqlBot(options: {
    name: string;
    description: string;
    workgroupName: string;
    databaseName: string;
    tableName: string;
  }) {
    await this.page.goto('/bot/new');
    await this.page.waitForSelector('[data-testid="bot-create-form"]');

    // Fill basic info
    await this.page.fill('[data-testid="bot-name-input"]', options.name);
    await this.page.fill('[data-testid="bot-description-input"]', options.description);

    // Select SQL KB type
    await this.page.click('[data-testid="kb-type-sql"]');

    // Fill SQL configuration
    await this.page.fill('[data-testid="workgroup-name-input"]', options.workgroupName);
    await this.page.fill('[data-testid="database-name-input"]', options.databaseName);
    await this.page.fill('[data-testid="table-name-input"]', options.tableName);

    // Submit
    await this.page.click('[data-testid="create-bot-button"]');
    await this.page.waitForSelector('[data-testid="bot-created-success"]', { timeout: 30000 });
  }

  async deleteBot(botId: string) {
    await this.page.goto(`/bot/${botId}/edit`);
    await this.page.click('[data-testid="delete-bot-button"]');
    await this.page.click('[data-testid="confirm-delete-button"]');
    await this.page.waitForSelector('[data-testid="bot-deleted-success"]');
  }

  async chatWithBot(botId: string, message: string) {
    await this.page.goto(`/bot/${botId}`);
    await this.page.waitForSelector('[data-testid="chat-interface"]');
    
    // Send message
    await this.page.fill('[data-testid="chat-input"]', message);
    await this.page.click('[data-testid="send-button"]');
    
    // Wait for response
    await this.page.waitForSelector('[data-testid="bot-response"]', { timeout: 30000 });
    
    return await this.page.textContent('[data-testid="bot-response"]:last-child');
  }
}
