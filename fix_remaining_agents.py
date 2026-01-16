"""
Fix remaining indentation issues in agent files.
The main issue: lines after _context_history that have wrong indentation.
"""

from pathlib import Path


def fix_agent_file(file_path: Path) -> bool:
    """Fix indentation issues in agent file."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  [ERROR] {file_path.parent.name}/{file_path.name} - {e}")
        return False

    original_content = content
    lines = content.split('\n')
    new_lines = []
    modified = False

    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)

        # Check if this line is self._context_history = []
        if 'self._context_history = []' in line:
            # Check next few lines for lines that should be indented but aren't
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                # Skip empty lines
                if not next_line.strip():
                    new_lines.append(next_line)
                    j += 1
                    continue

                # If we hit another method definition, we're done
                if next_line.strip().startswith('def ') or next_line.strip().startswith('async def '):
                    break

                # Check if this line should be indented (has self._something =)
                if 'self._' in next_line and '=' in next_line:
                    # Check indentation
                    stripped = next_line.lstrip()
                    spaces = len(next_line) - len(stripped)

                    # If not properly indented (should be 8 spaces)
                    if spaces < 8 or spaces == 4:
                        # Fix indentation
                        new_lines.append('        ' + stripped)
                        modified = True
                        j += 1
                        continue
                    # If has extra indentation (> 8 spaces)
                    elif spaces > 8:
                        new_lines.append('        ' + stripped)
                        modified = True
                        j += 1
                        continue

                # If line has extra indentation (> 8 spaces), fix it
                stripped = next_line.lstrip()
                spaces = len(next_line) - len(stripped)
                if spaces > 8 and stripped and not stripped.startswith('#'):
                    new_lines.append('        ' + stripped)
                    modified = True
                    j += 1
                    continue

                new_lines.append(next_line)
                j += 1

            i = j - 1  # Adjust since we added lines

        i += 1

    if modified:
        content = '\n'.join(new_lines)
        file_path.write_text(content, encoding="utf-8")
        print(f"  [FIXED] {file_path.parent.name}/{file_path.name}")
        return True

    return False


def main():
    """Fix all skill agent files."""
    skills_dir = Path("src/claude_playwright_agent/skills/builtins")

    print("Fixing remaining indentation issues...")
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
    print(f"Summary: {fixed_count} fixed, {ok_count} OK")


if __name__ == "__main__":
    main()
