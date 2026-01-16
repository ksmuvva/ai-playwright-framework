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

    # Fix the __init__ method by replacing the entire method
    # Pattern for the __init__ method
    init_pattern = r'(    def __init__\(self, \*\*kwargs\) -> None:.*?""".*?"""\n)(        super\(\).__init__\(\*\*kwargs\))'

    replacement = rf'\1        # Set a default system prompt if not provided\n        if "system_prompt" not in kwargs:\n            kwargs["system_prompt"] = {repr(system_prompt)}\n        super().__init__(**kwargs)\n        # Track context history\n        self._context_history = []'

    # Remove any incorrect indentation that might have been introduced
    content = re.sub(r'\s+super\(\).__init__\(\*\*kwargs\)\n', '        super().__init__(**kwargs)\n', content)

    # Apply the replacement
    new_content = re.sub(init_pattern, replacement, content, flags=re.DOTALL)

    if new_content == content:
        # Pattern didn't match, try alternative patterns
        # Look for simple init without docstring
        simple_init_pattern = r'(    def __init__\(self, \*\*kwargs\) -> None:\n)(        super\(\).__init__\(\*\*kwargs\))'
        simple_replacement = rf'\1        # Set a default system prompt if not provided\n        if "system_prompt" not in kwargs:\n            kwargs["system_prompt"] = {repr(system_prompt)}\n        super().__init__(**kwargs)\n        # Track context history\n        self._context_history = []'
        new_content = re.sub(simple_init_pattern, simple_replacement, content)

    # Remove any stray _context_history lines that might exist
    new_content = re.sub(r'\n        self\._context_history = \[\]\n', '\n', new_content)

    content = new_content

    # Fix 3: Add process() method before run()
    run_match = re.search(r'    async def run\(self, task: str, context: dict\[str, Any\]\) -> str:', content)
    if run_match:
        process_method = f'''    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process input data and return results.

        Args:
            input_data: Input data for processing

        Returns:
            Processing results
        """
        task = input_data.get("task", "unknown")
        context = input_data.get("context", {{}})

        # Track context history
        self._context_history.append({{
            "operation": "process",
            "task": task,
            "timestamp": self._get_timestamp()
        }})

        result = await self.run(task, context)

        return {{
            "success": True,
            "result": result,
            "agent": self.name
        }}

'''
        # Insert process() method before run()
        content = content.replace(run_match.group(0), process_method + run_match.group(0))

    # Fix 4: Add _get_timestamp() helper method at end of class
    if "_get_timestamp" not in content:
        # Find the last method and add after it
        helper_method = '''

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
'''
        # Add before last class or file end
        content = content.rstrip() + helper_method + "\n"

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
