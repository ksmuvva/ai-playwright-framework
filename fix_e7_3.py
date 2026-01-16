#!/usr/bin/env python3
"""Fix E7.3 f-string template issues."""

import re

file_path = r"C:\Playwriht_Framework\src\claude_playwright_agent\skills\builtins\e7_3_custom_skill_support\main.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix line 445 - separate the docstring and super().__init__ call
content = re.sub(
    r'"""Initialize the agent."""\s+super\(\).__init__\(\*\*kwargs\)',
    '''"""Initialize the agent."""
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = "You are a custom skill support agent."
        super().__init__(**kwargs)''',
    content
)

# Fix the f-string braces - all the single braces need to be doubled for escaping
# In f-strings, single braces {} become actual braces, double braces {{}} become literal braces
# The template uses f'{...}' so we need to escape the inner braces

# Fix dict braces in the template - patterns like { "context_id": ... } should be {{ "context_id": ... }}
content = re.sub(
    r'return \{\{[\s\n]*"context_id": self\.context_id,',
    r'return {{\n            "context_id": self.context_id,',
    content
)

content = re.sub(
    r'"created_at": self\.created_at[\s\n]*\}\}',
    r'"created_at": self.created_at\n        }}',
    content
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed E7.3 f-string template issues")
