# E3.5 - Native Playwright Integration

**Skill:** `e3_5_ingestion_logging`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

The Native Playwright Integration skill provides direct integration with native Playwright test formats and APIs.

## Capabilities

- Generate Playwright test code
- Support Playwright test runner
- Handle Playwright fixtures
- Support trace viewing
- Generate page object models

## Usage

```python
native = NativePlaywrightAgent()

# Generate Playwright test
test_code = await native.run("generate_test", {
    "actions": [...actions...],
    "test_name": "login_test"
})

# Generate fixture code
fixture = await native.run("generate_fixture", {
    "fixture_name": "authenticated_page"
})
```

## Generated Test Format

```typescript
import { test, expect } from '@playwright/test';

test('login test', async ({ page }) => {
  await page.goto('https://example.com');
  await page.click('#login-button');
  await expect(page).toHaveURL(/.*dashboard/);
});
```

## See Also

- [E3.1 - Recording Ingestion](./e3_1_parsing.md)
- [E3.4 - Playwright Support](./e3_4_playwright_support.md)
