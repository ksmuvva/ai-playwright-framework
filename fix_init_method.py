"""
Comprehensive fix for __init__ method in all skill agent files.
Reconstructs the __init__ method properly.
"""

import re
from pathlib import Path


def fix_init_method(file_path: Path) -> bool:
    """Fix the __init__ method properly."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  [ERROR] {file_path.parent.name}/{file_path.name} - {e}")
        return False

    original_content = content

    # Pattern to match the entire __init__ method up to the next method
    # We need to find __init__, extract its body, and reconstruct it properly

    # Find the __init__ method
    init_match = re.search(
        r'(    def __init__\(self, \*\*kwargs\) -> None:.*?""".*?"""\n)(.*?)(?=\n    (async )?def |\nclass |\Z)',
        content,
        re.DOTALL
    )

    if not init_match:
        print(f"  [SKIP] {file_path.parent.name}/{file_path.name} - no __init__ found")
        return False

    init_def = init_match.group(1)  # The def line and docstring
    init_body_raw = init_match.group(2)  # The body of __init__

    # Check if already fixed
    if 'self._context_history = []' in init_body_raw and 'if "system_prompt" not in kwargs:' in init_body_raw:
        # Check if indentation is correct
        lines = init_body_raw.split('\n')
        all_correct = True
        for line in lines:
            if line.strip() and not line.startswith('#') and not line.strip().startswith('kwargs['):
                if line and not line[0] in (' ', '\t'):
                    all_correct = False
                    break
        if all_correct:
            print(f"  [OK] {file_path.parent.name}/{file_path.name}")
            return False

    # Extract all the attribute assignments from the original body
    # These are lines like: self._something = value
    attribute_lines = []
    for line in init_body_raw.split('\n'):
        stripped = line.strip()
        if stripped.startswith('self._') and '=' in stripped:
            attribute_lines.append(stripped)

    # Reconstruct the __init__ method
    new_init_body = '''        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = "You are a agent for the Playwright test automation framework. You help users with tasks and operations."
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
'''

    # Add any original attribute assignments (properly indented)
    for attr_line in attribute_lines:
        if '_context_history' not in attr_line:  # Skip _context_history as we already added it
            new_init_body += f'        {attr_line}\n'

    # Replace the old __init__ with the new one
    new_content = content[:init_match.start()] + init_def + new_init_body + '\n' + content[init_match.end():]

    if new_content != original_content:
        file_path.write_text(new_content, encoding="utf-8")
        print(f"  [FIXED] {file_path.parent.name}/{file_path.name}")
        return True

    print(f"  [OK] {file_path.parent.name}/{file_path.name}")
    return False


def main():
    """Fix all skill agent files."""
    skills_dir = Path("src/claude_playwright_agent/skills/builtins")

    print("Fixing __init__ methods in all skill agents...")
    print()

    fixed_count = 0
    skipped_count = 0

    for agent_file in sorted(skills_dir.glob("*/main.py")):
        print(f"Checking: {agent_file.parent.name}/{agent_file.name}")
        if fix_init_method(agent_file):
            fixed_count += 1
        else:
            skipped_count += 1

    print()
    print(f"Summary: {fixed_count} fixed, {skipped_count} skipped")


if __name__ == "__main__":
    main()
