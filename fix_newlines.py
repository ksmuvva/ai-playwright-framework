"""
Fix missing newlines before async def process.
"""

from pathlib import Path


def fix_newlines(file_path: Path) -> bool:
    """Fix missing newlines."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  [ERROR] {file_path.parent.name}/{file_path.name} - {e}")
        return False

    # Fix: Add newline before async def process if missing
    # Pattern: self._context_history = []async def process
    new_content = content.replace('self._context_history = []\n    async def process', 'self._context_history = []\n\n    async def process')

    if new_content != content:
        file_path.write_text(new_content, encoding="utf-8")
        print(f"  [FIXED] {file_path.parent.name}/{file_path.name}")
        return True

    return False


def main():
    """Fix all skill agent files."""
    skills_dir = Path("src/claude_playwright_agent/skills/builtins")

    print("Fixing missing newlines...")
    print()

    fixed_count = 0
    skipped_count = 0

    for agent_file in sorted(skills_dir.glob("*/main.py")):
        if fix_newlines(agent_file):
            fixed_count += 1
        else:
            skipped_count += 1

    print()
    print(f"Summary: {fixed_count} fixed, {skipped_count} skipped")


if __name__ == "__main__":
    main()
