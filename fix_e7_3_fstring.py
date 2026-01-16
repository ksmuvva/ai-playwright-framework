#!/usr/bin/env python3
"""Fix E7.3 f-string template issues properly."""

import re

file_path = r"C:\Playwriht_Framework\src\claude_playwright_agent\skills\builtins\e7_3_custom_skill_support\main.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and fix the _generate_main_content method
in_method = False
in_fstring = False
fixed_lines = []

for i, line in enumerate(lines):
    line_num = i + 1

    # Start of the f-string
    if line_num == 398:
        in_fstring = True
        fixed_lines.append(line)
        continue

    # End of the f-string
    if line_num == 498:
        in_fstring = False
        fixed_lines.append(line)
        continue

    # Inside the f-string, need to escape braces
    if in_fstring:
        # Line 422: Fix the lambda f-string
        if 'context_id: str = field(default_factory=lambda: f"ctx_' in line:
            # Need: {{uuid.uuid4().hex[:8]}} -> {{{{uuid.uuid4().hex[:8]}}}}
            line = line.replace('f"ctx_{uuid.uuid4().hex[:8]}"', 'f"ctx_{{{{uuid.uuid4().hex[:8]}}}}"')

        # Lines 427-430: The dict literal - already has {{ and }} which is correct
        # But check if they're properly formatted
        if line.strip() == 'return {':
            line = line.replace('return {', 'return {{')
        elif line.strip() == '}':
            # Check context - if it's closing the dict, ensure it's }}
            if i > 0 and 'return' in lines[i-2]:
                line = line.replace('}', '}}')

        # Lines 461, 464-476: Dict literals and braces in the generated code
        # These need to have their braces escaped
        if 'input_data.get("task", "unknown")' in line:
            # This is fine - no braces
            pass
        elif 'input_data.get("context", {})' in line:
            # Replace {} with {{}}
            line = line.replace('{})', '}}{{}})')
        elif '"operation": "process"' in line:
            # This is in a dict, need to escape braces
            if line.strip().startswith('self._'):
                # Line 464-468: opening {
                line = line.replace('{', '{{')
            elif line.strip() == '}':
                # Closing }
                line = line.replace('}', '}}')
        elif '"task": task' in line:
            if '"success": True' in line:
                # Line 472-476: dict with multiple keys
                line = line.replace('{', '{{')
            elif line.strip() == '}':
                line = line.replace('}', '}}')

        # Lines 492-495: execution_context dict
        if 'execution_context = {' in line:
            line = line.replace('execution_context = {', 'execution_context = {{')
        elif '"task_id": context.get("task_id", f"task_' in line:
            # Line 493: f-string with braces
            line = line.replace('f"task_{uuid.uuid4().hex[:8]}"', 'f"task_{{{{uuid.uuid4().hex[:8]}}}}"')
        elif line.strip() == '}':
            # Check if it's closing the execution_context
            if i > 0 and 'workflow_id' in lines[i-1]:
                line = line.replace('}', '}}')

        # Line 497: return f-string
        if 'return f"Executed task: {task}"' in line:
            line = line.replace('return f"Executed task: {task}"', 'return f"Executed task: {{{{task}}}}"')

    fixed_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print("Fixed E7.3 f-string template")
