"""
Final comprehensive fix for all skill agents.
"""

import re
from pathlib import Path


def fix_agent_file(file_path: Path) -> bool:
    """Fix a single agent file to properly implement BaseAgent."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  [ERROR] {file_path.parent.name}/{file_path.name} - {e}")
        return False

    original_content = content
    modified = False

    # Fix 1: Fix the broken super().__init__() line with extra whitespace
    # Pattern: kwargs["system_prompt"] = '...'        super().__init__(**kwargs)
    # Pattern: kwargs["system_prompt"] = '...'    super().__init__(**kwargs)
    # Pattern: kwargs["system_prompt"] = '...'            super().__init__(**kwargs)

    patterns_to_fix = [
        (r"(kwargs\[\"system_prompt\"\] = '[^']+'\s+)(super\(\).__init__\(\*\*kwargs\))", r"\1\n        \2"),
        (r'(kwargs\["system_prompt"\] = "[^"]+"\s+)(super\(\).__init__\(\*\*kwargs\))', r"\1\n        \2"),
        (r"(kwargs\[\"system_prompt\"\] = '[^']+'\s*\n\s+)(super\(\).__init__\(\*\*kwargs\))", r"\1        \2"),
        (r'(kwargs\["system_prompt"\] = "[^"]+"\s*\n\s+)(super\(\).__init__\(\*\*kwargs\))', r"\1        \2"),
    ]

    for pattern, replacement in patterns_to_fix:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            content = new_content
            modified = True

    # Fix 2: Remove extra blank line before super() call
    content = re.sub(r"\n\n\n        super\(\).__init__\(\*\*kwargs\)", "\n\n        super().__init__(**kwargs)", content)

    # Fix 3: Ensure _context_history is initialized after super().__init__
    # Pattern: super().__init__(**kwargs) followed by something else
    if "self._context_history = []" not in content:
        content = re.sub(
            r"(        super\(\).__init__\(\*\*kwargs\)\n)(    )",
            r"\1        # Track context history\n        self._context_history = []\n",
            content
        )
        modified = True

    # Fix 4: Ensure _get_timestamp() method exists
    if "def _get_timestamp" not in content:
        # Add at end of file before any trailing code
        helper_method = '''

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
'''
        content = content.rstrip() + helper_method + "\n"
        modified = True

    # Write back if modified
    if modified or content != original_content:
        file_path.write_text(content, encoding="utf-8")
        print(f"  [FIXED] {file_path.parent.name}/{file_path.name}")
        return True

    print(f"  [OK] {file_path.parent.name}/{file_path.name}")
    return False


def main():
    """Fix all skill agent files."""
    skills_dir = Path("src/claude_playwright_agent/skills/builtins")

    print("Comprehensive fix for all skill agents...")
    print()

    fixed_count = 0
    ok_count = 0

    for agent_file in sorted(skills_dir.glob("*/main.py")):
        print(f"Checking: {agent_file.parent.name}/{agent_file.name}")
        if fix_agent_file(agent_file):
            fixed_count += 1
        else:
            ok_count += 1

    print()
    print(f"Summary: {fixed_count} fixed, {ok_count} already OK")


if __name__ == "__main__":
    main()
