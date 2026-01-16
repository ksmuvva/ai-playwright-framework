# E4.4 - Page Object Generation

**Skill:** `e4_4_page_object_generation`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

Generates Page Object models from recordings for maintainable test code.

## Capabilities

- Generate page objects
- Create element locators
- Generate action methods
- Support inheritance

## Usage

```python
agent = PageObjectGenerationAgent()
result = await agent.run("generate", {"page": "LoginPage"})
```

## Output

```python
class LoginPage:
    def __init__(self, page):
        self.page = page
        self.username_input = page.locator("#username")
        self.password_input = page.locator("#password")
        self.login_button = page.locator("#login")

    async def login(self, username, password):
        await self.username_input.fill(username)
        await self.password_input.fill(password)
        await self.login_button.click()
```

## See Also

- [E4.3 - Component Extraction](./e4_3_component_extraction.md)
- [E4.5 - Selector Catalog](./e4_5_selector_catalog.md)
