#!/usr/bin/env python3
"""Fix E7.2 field naming conflict."""

file_path = r"C:\Playwriht_Framework\src\claude_playwright_agent\skills\builtins\e7_2_manifest_parser\main.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all field( with dataclass_field(
content = content.replace('field(', 'dataclass_field(')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed E7.2 field naming conflict")
