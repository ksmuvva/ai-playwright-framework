# E3.4 - Playwright Support

**Skill:** `e3_4_selector_analysis`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

The Playwright Support skill provides specialized handling for Playwright-specific features, including advanced selectors, locators, and browser APIs.

## Capabilities

- Handle Playwright locators
- Support custom selectors
- Process browser context APIs
- Handle frame and iframe operations
- Support network interception

## Usage

```python
support = PlaywrightSupportAgent()

# Convert to Playwright locator
locator = await support.run("to_locator", {
    "selector": "#login-button"
})

# Handle frame operations
result = await support.run("handle_frame", {
    "frame_selector": "iframe#app-frame",
    "action": {...}
})
```

## Playwright Selector Types

| Type | Syntax | Example |
|------|--------|---------|
| CSS | `css=selector` | `css=#button` |
| Text | `text=text` | `text=Submit` |
| XPath | `xpath=expression` | `xpath=//button` |
| React | `_react=Component` | `_react=SubmitButton` |
| Vue | `_vue=Component` | `_vue=SubmitButton` |

## See Also

- [E3.1 - Recording Ingestion](./e3_1_parsing.md)
- [E3.5 - Native Playwright](./e3_5_native.md)
