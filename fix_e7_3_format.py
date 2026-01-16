#!/usr/bin/env python3
"""Fix E7.3 f-string template by using format() instead."""

file_path = r"C:\Playwriht_Framework\src\claude_playwright_agent\skills\builtins\e7_3_custom_skill_support\main.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the _generate_main_content method
# Use .format() instead of f-string to avoid brace escaping issues

old_method = '''    def _generate_main_content(self, skill_name: str) -> str:
        """Generate main.py content."""
        class_name = "".join(word.capitalize() for word in skill_name.split("_"))
        return f\'\'\'"""
{skill_name.replace("_", " ").title()} Skill.

This skill provides custom functionality.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


@dataclass
class {class_name}Context:
    """
    Context for {skill_name} operations.

    Attributes:
        context_id: Unique context identifier
        created_at: When context was created
    """

    context_id: str = field(default_factory=lambda: f"ctx_{{uuid.uuid4().hex[:8]}}")
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {{
            "context_id": self.context_id,
            "created_at": self.created_at,
        }}


class {class_name}Agent(BaseAgent):
    """
    {skill_name.replace("_", " ").title()} Agent.

    This agent provides custom functionality.
    """

    name = "{skill_name}"
    version = "1.0.0"
    description = "{skill_name.replace("_", " ").title()}"

    def __init__(self, **kwargs) -> None:
        """Initialize the agent."""
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = "You are a custom skill support agent."
        super().__init__(**kwargs)

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process input data and return results.

        Args:
            input_data: Input data for processing

        Returns:
            Processing results
        """
        task = input_data.get("task", "unknown")
        context = input_data.get("context", {})

        # Track context history
        self._context_history.append({
            "operation": "process",
            "task": task,
            "timestamp": self._get_timestamp()
        })

        result = await self.run(task, context)

        return {
            "success": True,
            "result": result,
            "agent": self.name
        }

    async def run(self, task: str, context: dict[str, Any]) -> str:
        """
        Execute task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the operation
        """
        # Extract execution context
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {{
                "task_id": context.get("task_id", f"task_{{uuid.uuid4().hex[:8]}}"),
                "workflow_id": context.get("workflow_id", ""),
            }}

        return f"Executed task: {{task}}"
\'\'\'\'''

# Note: This is a simplified version that avoids complex brace escaping
# The template generation will work, just with simpler placeholder syntax
new_method = '''    def _generate_main_content(self, skill_name: str) -> str:
        """Generate main.py content."""
        class_name = "".join(word.capitalize() for word in skill_name.split("_"))
        skill_title = skill_name.replace("_", " ").title()

        template = \'\'\'"""
{skill_title} Skill.

This skill provides custom functionality.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


@dataclass
class {class_name}Context:
    """
    Context for {skill_name} operations.

    Attributes:
        context_id: Unique context identifier
        created_at: When context was created
    """

    context_id: str = field(default_factory=lambda: f"ctx_{{uuid.uuid4().hex[:8]}}")
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {{
            "context_id": self.context_id,
            "created_at": self.created_at,
        }}


class {class_name}Agent(BaseAgent):
    """
    {skill_title} Agent.

    This agent provides custom functionality.
    """

    name = "{skill_name}"
    version = "1.0.0"
    description = "{skill_title}"

    def __init__(self, **kwargs) -> None:
        """Initialize the agent."""
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = "You are a custom skill support agent."
        super().__init__(**kwargs)

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
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

    async def run(self, task: str, context: dict[str, Any]) -> str:
        """
        Execute task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the operation
        """
        # Extract execution context
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {{
                "task_id": context.get("task_id", f"task_{{uuid.uuid4().hex[:8]}}"),
                "workflow_id": context.get("workflow_id", ""),
            }}

        return f"Executed task: {{task}}"
\'\'\'

        return template.format(skill_name=skill_name, skill_title=skill_title, class_name=class_name)
'''

# Only replace if we can find the old method
if old_method.split('\n')[0] in content:
    # Find the start and end of the method
    start_idx = content.find('def _generate_main_content(self, skill_name: str) -> str:')
    if start_idx != -1:
        # Find the end (next def at same or lower indentation)
        search_content = content[start_idx:]
        end_idx = search_content.find('\n    def _generate_init_content')
        if end_idx == -1:
            end_idx = search_content.find('\n\ndef ')

        if end_idx != -1:
            # Replace the method
            new_content = content[:start_idx] + new_method + '\n' + content[start_idx + end_idx:]
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("Fixed E7.3 _generate_main_content method")
        else:
            print("Could not find end of _generate_main_content method")
    else:
        print("Could not find _generate_main_content method")
else:
    print("Method already replaced or not found")
