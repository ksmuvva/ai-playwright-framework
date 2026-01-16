"""
Script to fix the broken line where super().__init__(**kwargs) was put on same line as string.
"""

from pathlib import Path


def fix_broken_line(file_path: Path) -> bool:
    """Fix the broken line where super() call was appended to string."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  [ERROR] {file_path.name} - {e}")
        return False

    original_content = content

    # Fix the broken line pattern:
    # kwargs["system_prompt"] = '...'        super().__init__(**kwargs)
    # Should be:
    # kwargs["system_prompt"] = '...'
    #         super().__init__(**kwargs)

    import re

    # Pattern 1: Single quote string with super() on same line
    pattern1 = r"(kwargs\[\"system_prompt\"\] = '[^']+')(\s+super\(\).__init__\(\*\*kwargs\))"
    replacement1 = r'\1\n        \2'

    # Pattern 2: Double quote string with super() on same line
    pattern2 = r'(kwargs\["system_prompt"\] = "[^"]+")(\s+super\(\).__init__\(\*\*kwargs\))'
    replacement2 = r'\1\n        \2'

    new_content = re.sub(pattern1, replacement1, content)
    new_content = re.sub(pattern2, replacement2, new_content)

    if new_content != original_content:
        file_path.write_text(new_content, encoding="utf-8")
        print(f"  [FIXED] {file_path.parent.name}/{file_path.name}")
        return True

    return False


def main():
    """Fix all skill agent files."""
    skills_dir = Path("src/claude_playwright_agent/skills/builtins")

    print("Fixing broken super().__init__() calls...")
    print()

    fixed_count = 0
    skipped_count = 0

    for agent_file in sorted(skills_dir.glob("*/main.py")):
        print(f"Checking: {agent_file.parent.name}/{agent_file.name}")
        if fix_broken_line(agent_file):
            fixed_count += 1
        else:
            skipped_count += 1

    print()
    print(f"Summary: {fixed_count} fixed, {skipped_count} skipped")


if __name__ == "__main__":
    main()
