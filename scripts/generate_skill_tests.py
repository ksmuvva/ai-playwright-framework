#!/usr/bin/env python
"""
Generate unit test templates for skills.

This script generates unit test files for all skills based on their
main.py structure. It reads each skill file and creates a corresponding
test file with appropriate test cases.

Usage:
    python scripts/generate_skill_tests.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def generate_test_for_skill(skill_path: Path) -> str:
    """Generate test file content for a skill."""
    # Read the skill file
    skill_main = skill_path / "main.py"
    if not skill_main.exists():
        return None

    # Read skill content to extract class name and info
    with open(skill_main) as f:
        content = f.read()

    # Extract skill name from path
    skill_name = skill_path.name
    skill_class = None

    # Find the agent class
    for line in content.split("\n"):
        if "class " in line and "Agent" in line and "BaseAgent" in line:
            # Extract class name
            class_start = line.find("class ") + 6
            class_end = line.find("(")
            if class_end > class_start:
                skill_class = line[class_start:class_end]
                break

    if not skill_class:
        skill_class = skill_class_name_from_path(skill_name)

    # Generate test file
    test_content = f'''"""Unit tests for {skill_name} skill."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from claude_playwright_agent.skills.builtins.{skill_name} import (
    {skill_class},
)
from claude_playwright_agent.agents.base import BaseAgent


class Test{skill_class}:
    """Test suite for {skill_class}."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return {skill_class}()

    @pytest.mark.unit
    def test_agent_inherits_from_base_agent(self, agent):
        """Verify agent inherits from BaseAgent."""
        assert isinstance(agent, BaseAgent)

    @pytest.mark.unit
    def test_agent_has_required_attributes(self, agent):
        """Verify agent has required attributes."""
        assert hasattr(agent, "name")
        assert hasattr(agent, "version")
        assert hasattr(agent, "description")
        assert agent.name == "{skill_name}"
        assert agent.version == "1.0.0"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_valid_task(self, agent):
        """Test running agent with valid task."""
        context = {{
            "task_type": "test_task",
        }}

        result = await agent.run("test_task", context)

        assert result is not None
        assert isinstance(result, str)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_with_invalid_task_type(self, agent):
        """Test running agent with invalid task type."""
        context = {{}}

        result = await agent.run("invalid_task_type", context)

        assert "unknown task type" in result.lower()

    @pytest.mark.unit
    def test_context_tracking_initialized(self, agent):
        """Test that context tracking is initialized."""
        assert hasattr(agent, "_context_history")
        assert isinstance(agent._context_history, list)

    @pytest.mark.unit
    def test_get_context_history(self, agent):
        """Test getting context history."""
        history = agent.get_context_history()
        assert isinstance(history, list)
'''

    return test_content


def skill_class_name_from_path(skill_name: str) -> str:
    """Generate class name from skill directory name."""
    # Convert e3_1_ingestion_agent to E3_1IngestionAgent
    parts = skill_name.split("_")
    epic = parts[0].upper() + "_" + parts[1]
    name_parts = "".join(p.capitalize() for p in parts[2:])
    return f"{epic}{name_parts}Agent"


def main():
    """Generate test files for all skills."""
    skills_dir = Path("src/claude_playwright_agent/skills/builtins")
    tests_dir = Path("tests/skills/builtins")

    # Ensure tests directory exists
    tests_dir.mkdir(parents=True, exist_ok=True)

    # Find all skill directories
    skill_dirs = sorted([d for d in skills_dir.iterdir() if d.is_dir() and not d.name.startswith("_")])

    print(f"Found {len(skill_dirs)} skill directories")

    for skill_dir in skill_dirs:
        skill_name = skill_dir.name
        test_file = tests_dir / f"{skill_name}_test.py"

        # Skip if test already exists
        if test_file.exists():
            print(f"  [SKIP] {skill_name} - test already exists")
            continue

        # Generate test content
        test_content = generate_test_for_skill(skill_dir)

        if test_content:
            # Write test file
            with open(test_file, "w") as f:
                f.write(test_content)
            print(f"  [OK] {skill_name} - test created")
        else:
            print(f"  [FAIL] {skill_name} - could not generate test")

    print("\\nTest generation complete!")


if __name__ == "__main__":
    main()
