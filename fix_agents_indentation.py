"""
Fix indentation issues in all skill agent files.
The main issue: extra spaces/lines before/after super().__init__(**kwargs)
"""

import re
from pathlib import Path


def fix_agent_indentation(file_path: Path) -> bool:
    """Fix indentation issues in agent __init__ method."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  [ERROR] {file_path.parent.name}/{file_path.name} - {e}")
        return False

    original_content = content
    modified = False

    # Fix 1: Remove extra indentation before super().__init__(**kwargs)
    # Pattern: any line with super().__init__(**kwargs) that has more than 8 spaces
    lines = content.split('\n')
    new_lines = []

    for i, line in enumerate(lines):
        # Check if this line contains super().__init__(**kwargs)
        if 'super().__init__(**kwargs)' in line:
            # Count leading spaces
            stripped = line.lstrip()
            spaces = len(line) - len(stripped)

            # If there are more than 8 spaces (2 levels of indentation), fix it
            if spaces > 8:
                # Fix to 8 spaces
                new_line = '        ' + stripped
                new_lines.append(new_line)
                modified = True
                continue

        # Check for lines with only whitespace that should be removed before super()
        # Pattern: empty lines followed by super().__init__(**kwargs) with wrong indent
        if i > 0 and line.strip() == '':
            # Check if next line has super().__init__(**kwargs)
            if i + 1 < len(lines) and 'super().__init__(**kwargs)' in lines[i + 1]:
                next_line = lines[i + 1]
                next_stripped = next_line.lstrip()
                next_spaces = len(next_line) - len(next_stripped)

                # If the next line has too much indentation, remove this empty line
                # and fix the next line
                if next_spaces > 8:
                    # Skip adding this empty line
                    # Fix the next line instead
                    lines[i + 1] = '        ' + next_stripped
                    modified = True
                    continue

        new_lines.append(line)

    if modified:
        content = '\n'.join(new_lines)

    # Fix 2: Ensure we have exactly: super().__init__(**kwargs) followed by _context_history
    # Look for the pattern and fix if needed
    init_pattern = r'(if "system_prompt" not in kwargs:\s+kwargs\["system_prompt"\] = [^\n]+\n)\s*super\(\).__init__\(\*\*kwargs\)\s*(?:#\s*Track context history\s*\n\s*self\._context_history = \[\]\s*\n)?'

    def replace_init(match):
        result = match.group(1)
        result += '        super().__init__(**kwargs)\n'
        result += '        # Track context history\n'
        result += '        self._context_history = []\n'
        return result

    new_content = re.sub(init_pattern, replace_init, content, flags=re.DOTALL)
    if new_content != content:
        content = new_content
        modified = True

    # Fix 3: Remove duplicate _context_history initializations
    content = re.sub(r'(\n        self\._context_history = \[\]\n){2,}', r'\1', content)

    # Write back if modified
    if modified or content != original_content:
        file_path.write_text(content, encoding="utf-8")
        print(f"  [FIXED] {file_path.parent.name}/{file_path.name}")
        return True

    return False


def main():
    """Fix all skill agent files."""
    skills_dir = Path("src/claude_playwright_agent/skills/builtins")

    print("Fixing indentation issues in all skill agents...")
    print()

    fixed_count = 0
    skipped_count = 0

    for agent_file in sorted(skills_dir.glob("*/main.py")):
        print(f"Checking: {agent_file.parent.name}/{agent_file.name}")
        if fix_agent_indentation(agent_file):
            fixed_count += 1
        else:
            skipped_count += 1

    print()
    print(f"Summary: {fixed_count} fixed, {skipped_count} skipped")


if __name__ == "__main__":
    main()
