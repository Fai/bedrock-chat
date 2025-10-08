# E2E Tests for Bedrock Chat

Automated end-to-end tests using Playwright to verify the complete user journey across all Knowledge Base types.

## Setup

1. **Install dependencies:**
   ```bash
   cd e2e
   npm install
   npx playwright install
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your test configuration
   ```

3. **Start frontend development server:**
   ```bash
   cd ../frontend
   npm run dev
   ```

## Running Tests

### All tests
```bash
npm test
```

### Specific test suite
```bash
npx playwright test auth.spec.ts
npx playwright test vector-kb.spec.ts
npx playwright test sql-kb.spec.ts
```

### Interactive mode
```bash
npm run test:ui
```

### Debug mode
```bash
npm run test:debug
```

### Headed mode (see browser)
```bash
npm run test:headed
```

## Test Structure

### Test Suites

1. **Authentication (`auth.spec.ts`)**
   - Login/logout functionality
   - Protected route access
   - Error handling

2. **Vector Knowledge Base (`vector-kb.spec.ts`)**
   - OpenSearch Serverless bot creation
   - S3 Vector bot creation with warnings
   - Storage type selector behavior
   - Token limit enforcement
   - Search type restrictions

3. **SQL Knowledge Base (`sql-kb.spec.ts`)**
   - SQL bot creation
   - Conditional UI rendering
   - Field validation
   - Query execution and results display

4. **Chat Functionality (`chat.spec.ts`)**
   - Message sending/receiving
   - Typing indicators
   - Large message handling (S3 storage)
   - Chat history persistence
   - Error handling and retry

5. **Bot Management (`bot-management.spec.ts`)**
   - Bot listing and filtering
   - Bot editing and deletion
   - Status badges
   - Search functionality

### Helper Classes

- **`AuthHelper`**: Authentication utilities
- **`BotHelper`**: Bot creation and management utilities

## Test Data Requirements

### For SQL KB Tests
- Test Redshift workgroup: `test-workgroup`
- Test database: `test_db`
- Test table: `products` with columns:
  - `id` (primary key)
  - `content` (text content)
  - `metadata` (JSON metadata)
  - `embedding` (vector field)

### Test Files
Place test files in `e2e/fixtures/` for file upload tests:
- `test-document.pdf`
- `test-document.txt`

## Data Test IDs

The tests rely on `data-testid` attributes in the frontend components. Key test IDs:

### Authentication
- `auth-form`
- `email-input`
- `password-input`
- `sign-in-button`
- `auth-error`

### Bot Creation
- `bot-create-form`
- `bot-name-input`
- `bot-description-input`
- `kb-type-vector`
- `kb-type-sql`
- `storage-type-selector`
- `storage-type-opensearch`
- `storage-type-s3-vector`
- `create-bot-button`

### SQL Configuration
- `sql-database-config`
- `workgroup-name-input`
- `database-name-input`
- `table-name-input`

### Chat Interface
- `chat-interface`
- `chat-input`
- `send-button`
- `user-message`
- `bot-response`
- `typing-indicator`
- `sql-results-table`

### Bot Management
- `bot-list`
- `edit-bot-button`
- `delete-bot-button`
- `bot-status-badge`
- `bot-filter`
- `bot-search-input`

## CI/CD Integration

Tests run automatically on:
- Push to `main` or `v3` branches
- Pull requests to `main` or `v3`

GitHub Actions workflow: `.github/workflows/e2e.yml`

## Troubleshooting

### Common Issues

1. **Tests timing out**
   - Increase timeouts in `playwright.config.ts`
   - Check if backend services are running

2. **Authentication failures**
   - Verify test user credentials in `.env`
   - Check if Cognito is configured correctly

3. **Element not found**
   - Verify `data-testid` attributes exist in components
   - Check if UI has changed

4. **Network errors**
   - Ensure frontend dev server is running
   - Check API endpoints are accessible

### Debug Tips

1. **Run with headed browser:**
   ```bash
   npm run test:headed
   ```

2. **Use debug mode:**
   ```bash
   npm run test:debug
   ```

3. **Check test reports:**
   ```bash
   npm run test:report
   ```

4. **Screenshot on failure:**
   Screenshots are automatically captured on test failures in `test-results/`

## Contributing

When adding new features:

1. Add appropriate `data-testid` attributes to components
2. Create corresponding E2E tests
3. Update this README with new test IDs
4. Ensure tests pass in CI/CD

## Test Coverage

Current test coverage includes:
- ✅ Authentication flows
- ✅ Vector KB creation (OpenSearch + S3 Vector)
- ✅ SQL KB creation and querying
- ✅ Chat functionality
- ✅ Bot management operations
- ✅ UI conditional rendering
- ✅ Validation and error handling

Future additions:
- [ ] Agent functionality
- [ ] Bot store features
- [ ] Multi-user scenarios
- [ ] Performance testing
