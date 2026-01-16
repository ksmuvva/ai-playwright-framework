"""
Script to fix all skill agents to properly implement BaseAgent.

This script:
1. Adds default system_prompt in __init__
2. Implements process() method
3. Adds _context_history tracking
"""

import re
from pathlib import Path


def fix_agent_file(file_path: Path) -> bool:
    """Fix a single agent file to properly implement BaseAgent."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  [ERROR] {file_path.name} - {e}")
        return False

    # Skip if already has process method
    if "async def process(self, input_data:" in content:
        print(f"  [SKIP] {file_path.parent.name}/{file_path.name} - already has process() method")
        return False

    # Check if it inherits from BaseAgent
    if "BaseAgent" not in content:
        print(f"  [SKIP] {file_path.parent.name}/{file_path.name} - doesn't inherit from BaseAgent")
        return False

    # Extract class name
    class_match = re.search(r"class (\w+)\(BaseAgent\)", content)
    if not class_match:
        print(f"  [SKIP] {file_path.parent.name}/{file_path.name} - no BaseAgent class found")
        return False

    class_name = class_match.group(1)

    # Generate system prompt based on class name and description
    desc_match = re.search(r'description = "([^"]+)"', content)
    description = desc_match.group(1) if desc_match else class_name

    system_prompt = f"You are a {description} agent for the Playwright test automation framework. You help users with {description.lower()} tasks and operations."

    # Fix 1: Update __init__ to provide default system_prompt

    if 'if "system_prompt" not in kwargs:' in content:
        # Already has the check, skip
        pass
    else:
        # Find the __init__ method and add the system_prompt check
        init_match = re.search(r'(def __init__\(self, \*\*kwargs\) -> None:.*?""".*?"""\n)(        super\(\).__init__\(\*\*kwargs\))', content, re.DOTALL)
        if init_match:
            old_init = init_match.group(0)
            new_init = init_match.group(1) + '        # Set a default system prompt if not provided\n        if "system_prompt" not in kwargs:\n            kwargs["system_prompt"] = ' + repr(system_prompt) + '\n        ' + init_match.group(2)
            content = content.replace(old_init, new_init)

    # Fix 2: Add _context_history initialization
    if "self._context_history = []" not in content:
        # Find where to add it (after super().__init__(**kwargs))
        super_match = re.search(r"(        super\(\).__init__\(\*\*kwargs\)\n)", content)
        if super_match:
            old_super = super_match.group(1)
            new_super = old_super + "        self._context_history = []\n"
            content = content.replace(old_super, new_super)

    # Fix 3: Add process() method
    # Find the run() method and add process() before it
    run_match = re.search(r'(    async def run\(self, task: str, context: dict\[str, Any\]) -> str:', content)
    if run_match:
        indent = "    "
        process_method = f'''{indent}async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
{indent}    """
{indent}    Process input data and return results.

{indent}    Args:
{indent}        input_data: Input data for processing

{indent}    Returns:
{indent}        Processing results
{indent}    """
{indent}    task = input_data.get("task", "unknown")
{indent}    context = input_data.get("context", {{}})

{indent}    # Track context history
{indent}    self._context_history.append({{
{indent}        "operation": "process",
{indent}        "task": task,
{indent}        "timestamp": self._get_timestamp()
{indent}}})

{indent}    result = await self.run(task, context)

{indent}    return {{
{indent}        "success": True,
{indent}        "result": result,
{indent}        "agent": self.name
{indent}    }}

'''

        # Insert process() method before run()
        content = content.replace(run_match.group(0), process_method + run_match.group(0))

    # Fix 4: Add _get_timestamp() helper method if needed
    if "def _get_timestamp" not in content:
        # Add it at the end of the class
        helper_method = '\n    def _get_timestamp(self) -> str:\n        """Get current timestamp."""\n        from datetime import datetime\n        return datetime.now().isoformat()\n'
        # Find the last method in the class
        last_method_end = content.rfind('    def ')
        if last_method_end > 0:
            # Find the end of this method (next class or end of file)
            rest = content[last_method_end:]
            # Look for end of method (empty line at class level)
            method_end_match = re.search(r'\n\n(?=\nclass |\nif __name__|\Z)', rest, re.DOTALL)
            if method_end_match:
                insert_pos = last_method_end + method_end_match.end()
                content = content[:insert_pos] + helper_method + content[insert_pos:]

    # Write back
    file_path.write_text(content, encoding="utf-8")
    print(f"  [FIXED] {file_path.parent.name}/{file_path.name}")
    return True


def main():
    """Fix all skill agent files."""
    skills_dir = Path("src/claude_playwright_agent/skills/builtins")

    print("Fixing all skill agents to properly implement BaseAgent...")
    print()

    fixed_count = 0
    skipped_count = 0

    for agent_file in sorted(skills_dir.glob("*/main.py")):
        print(f"Processing: {agent_file.parent.name}/{agent_file.name}")
        if fix_agent_file(agent_file):
            fixed_count += 1
        else:
            skipped_count += 1

    print()
    print(f"Summary: {fixed_count} fixed, {skipped_count} skipped")


if __name__ == "__main__":
    main()
