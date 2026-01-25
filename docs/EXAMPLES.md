# Examples

Practical examples for common testing scenarios.

## Example 1: Login Test

### Recording
```javascript
await page.goto('https://example.com/login');
await page.fill('#email', 'user@example.com');
await page.fill('#password', 'Secret123!');
await page.click('#submit-button');
```

### Generated BDD
```gherkin
Feature: Login
  Scenario: Successful login
    Given I am on the login page
    When I enter valid credentials
    Then I should see the dashboard
```

### Run It
```bash
cpa ingest recordings/login.spec.js
cpa run convert
behave features/login.feature
```

## Example 2: Shopping Cart

### Recording
```javascript
await page.goto('https://shop.example.com');
await page.click('.product:first-child');
await page.click('button:has-text("Add to Cart")');
await page.click('text=Cart');
await page.assert_visible('.cart-item');
```

### Generated BDD
```gherkin
Feature: Shopping Cart
  Scenario: Add item to cart
    Given I am on the products page
    When I add a product to cart
    Then the item should be in my cart
```

## Example 3: Form Validation

### Recording
```javascript
await page.goto('https://example.com/contact');
await page.fill('#name', '');
await page.click('#submit');
await page.assert_visible('#error-message');
```

### Generated BDD
```gherkin
Feature: Contact Form
  Scenario: Submit with empty required field
    Given I am on the contact page
    When I submit without filling name
    Then I should see an error message
```

## Example 4: API Testing

```python
# tests/api_test.py
from claude_playwright_agent.agents.api_agent import APITestingAgent

async def test_api():
    agent = APITestingAgent()

    result = await agent.validate_api(
        method='GET',
        url='https://api.example.com/users',
        expected_status=200,
        expected_schema={
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'name': {'type': 'string'}
                }
            }
        }
    )

    assert result.success
```

## Example 5: Page Objects

```python
# pages/login_page.py
from pages.base_page import BasePage

class LoginPage(BasePage):
    def __init__(self, page, base_url="https://example.com"):
        super().__init__(page, base_url)

    def navigate(self):
        self.page.goto(f"{self.base_url}/login")

    def login(self, email, password):
        self.page.fill('#email', email)
        self.page.fill('#password', password)
        self.page.click('#submit')

    def assert_is_logged_in(self):
        self.page.assert_visible('.dashboard')

# Use it
def test_login(page):
    login = LoginPage(page)
    login.navigate()
    login.login('user@example.com', 'pass123')
    login.assert_is_logged_in()
```

## Example 6: Parallel Execution

```bash
# Run 4 tests in parallel
cpa run test --parallel 4

# Or configure in config.yaml
execution:
  parallel_workers: 4
```

## Example 7: Self-Healing in Action

```python
# Selector changed from #submit to #login-button
# AI automatically tries:
# 1. Exact match
# 2. Text search ("Submit", "Login")
# 3. Role matching (button)
# 4. Attribute matching (type="submit")
# ...and 5 more strategies
```

## Example 8: Tags for Organization

```gherkin
Feature: User Authentication
  @smoke @critical
  Scenario: Login with valid credentials
    Given I am on the login page
    When I enter valid credentials
    Then I should be logged in

  @regression
  Scenario: Login with invalid credentials
    Given I am on the login page
    When I enter invalid credentials
    Then I should see an error
```

Run by tag:
```bash
cpa run test --tags @smoke
cpa run test --tags @critical
```

## Example 9: Data Tables

```gherkin
Feature: Search
  Scenario Outline: Search for products
    Given I am on the search page
    When I search for "<term>"
    Then I should see results

    Examples: Search terms
      | term         |
      | laptop       |
      | phone        |
      | tablet       |
```

## Example 10: Visual Regression

```python
from claude_playwright_agent.agents.visual_regression_agent import VisualRegressionAgent

async def test_visual():
    agent = VisualRegressionAgent()

    # Capture baseline
    await agent.capture_baseline('dashboard', 'https://example.com/dashboard')

    # Compare on subsequent runs
    result = await agent.compare('dashboard', 'https://example.com/dashboard')

    assert result.passed, f"Visual changes detected: {result.diffs}"
```
