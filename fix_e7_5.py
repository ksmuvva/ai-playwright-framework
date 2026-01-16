#!/usr/bin/env python3
"""Fix E7.5 syntax error."""

import re

file_path = r"C:\Playwriht_Framework\src\claude_playwright_agent\skills\builtins\e7_5_discovery_documentation\main.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the syntax error at line 78 - missing 'class' keyword
# Pattern: @dataclass followed by newline and spaces then " SkillDocumentation:"
content = re.sub(
    r'(@dataclass\n) +SkillDocumentation:',
    r'\1class SkillDocumentation:',
    content
)

# Also fix the field(default_factory=dict) error at line 102
content = re.sub(
    r'generation_context: dict\[str, Any\] = field\(default_factory=dict\)',
    r'generation_context: dict[str, Any] = field(default_factory=lambda: {})',
    content
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed E7.5 syntax errors")
