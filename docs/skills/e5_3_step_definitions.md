# E5.3 - Step Definitions

**Skill:** `e5_3_step_definitions`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

Generates step definition code for Gherkin scenarios using pytest-bdd or behave.

## Capabilities

- Generate step definitions
- Map steps to Playwright actions
- Support parameterized steps
- Handle step arguments

## Usage

```python
agent = StepDefinitionsAgent()
code = await agent.run("generate", {"scenario": {...}})
```

## Output

```python
from pytest_bdd import given, when, then

@given("I am on the login page")
async def login_page(page):
    await page.goto("https://example.com/login")

@when("I enter username and password")
async def enter_credentials(page, username, password):
    await page.fill("#username", username)
    await page.fill("#password", password)
```

## See Also

- [E5.1 - BDD Conversion](./e5_1_bdd_conversion.md)
- [E5.2 - Gherkin Generation](./e5_2_gherkin_generation.md)
