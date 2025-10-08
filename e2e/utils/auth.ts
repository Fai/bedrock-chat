import { Page } from '@playwright/test';

export class AuthHelper {
  constructor(private page: Page) {}

  async login(email: string = 'test@example.com', password: string = 'TestPassword123!') {
    await this.page.goto('/');
    
    // Wait for auth form
    await this.page.waitForSelector('[data-testid="auth-form"]');
    
    // Fill login form
    await this.page.fill('[data-testid="email-input"]', email);
    await this.page.fill('[data-testid="password-input"]', password);
    
    // Submit
    await this.page.click('[data-testid="sign-in-button"]');
    
    // Wait for successful login (dashboard or chat page)
    await this.page.waitForSelector('[data-testid="main-layout"]', { timeout: 10000 });
  }

  async logout() {
    await this.page.click('[data-testid="user-menu"]');
    await this.page.click('[data-testid="logout-button"]');
    await this.page.waitForSelector('[data-testid="auth-form"]');
  }

  async isLoggedIn(): Promise<boolean> {
    try {
      await this.page.waitForSelector('[data-testid="main-layout"]', { timeout: 2000 });
      return true;
    } catch {
      return false;
    }
  }
}
