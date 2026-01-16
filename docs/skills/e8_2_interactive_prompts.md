# E8.2 - Interactive Prompts

**Skill:** `e8_2_interactive_prompts`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

Provides interactive user prompts for input, confirmations, and multi-step wizards.

## Capabilities

- Prompt for user input
- Request confirmations
- Run interactive wizards
- Collect user preferences

## Usage

```python
agent = InteractivePromptsAgent()

# Simple prompt
response = await agent.run("prompt", {
    "question": "Enter test URL:",
    "default": "https://example.com"
})

# Confirmation
confirmed = await agent.run("confirm", {
    "message": "Continue with test execution?"
})
```

## See Also

- [E8.1 - Error Handling](./e8_1_error_handling.md)
- [E8.3 - CLI Help](./e8_3_cli_help.md)
