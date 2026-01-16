# E1.1 - Project Initialization

**Skill:** `e1_1_cli_interface`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

The Project Initialization skill provides the foundational functionality for initializing new Playwright testing projects. It handles project scaffolding, configuration file generation, and initial setup of the project structure.

## Capabilities

- **Project Scaffolding**: Create new project directories with proper structure
- **Configuration Generation**: Automatically generate configuration files (pytest.ini, pyproject.toml, etc.)
- **Interactive CLI**: Provide an interactive command-line interface for project setup
- **Template Support**: Use predefined templates for different project types
- **Dependency Setup**: Configure required Python dependencies

## Usage

### Basic Usage

```python
from claude_playwright_agent.skills import SkillLoader

loader = SkillLoader(project_path=Path.cwd(), include_builtins=True)
skill = loader.load_skill("path/to/e1_1_cli_interface/skill.yaml")

agent = skill.agent_class()
result = await agent.run("init_project", {
    "project_name": "my_test_project",
    "project_path": "/path/to/project"
})
```

### CLI Command

```bash
cpa init my_test_project
```

## Available Tasks

| Task | Description | Context Required |
|------|-------------|------------------|
| `init_project` | Initialize a new project | `project_name`, `project_path` |
| `create_config` | Create configuration files | `config_type` |
| `setup_structure` | Create directory structure | `structure_type` |
| `install_deps` | Install dependencies | None |

## Configuration

The skill can be configured via `skill.yaml`:

```yaml
# Optional configuration
default_project_type: "standard"
templates_dir: ".cpa/templates"
include_examples: true
```

## Context Tracking

This skill tracks the following context:

- `project_name`: Name of the project being initialized
- `project_path`: Full path to the project directory
- `config_files`: List of configuration files created
- `initialization_steps`: Steps completed during initialization

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `ProjectExistsError` | Project directory already exists | Use `--force` flag to overwrite |
| `InvalidProjectName` | Project name contains invalid characters | Use alphanumeric names and underscores only |
| `DependencyError` | Failed to install dependencies | Check network connection and Python environment |

## Examples

### Example 1: Initialize a Standard Project

```python
context = {
    "project_name": "ecommerce_tests",
    "project_path": "/Users/dev/tests",
    "project_type": "standard",
    "include_examples": True
}

result = await agent.run("init_project", context)
print(result)  # "Project ecommerce_tests initialized successfully"
```

### Example 2: Create Custom Configuration

```python
context = {
    "config_type": "pytest",
    "options": {
        "asyncio_mode": "auto",
        "testpaths": ["tests"],
        "python_files": ["test_*.py"]
    }
}

result = await agent.run("create_config", context)
```

## Dependencies

None (this is a foundational skill)

## Troubleshooting

**Issue**: "Permission denied when creating project directory"
- **Solution**: Ensure you have write permissions to the parent directory

**Issue**: "Python dependencies installation failed"
- **Solution**: Check your pip configuration and internet connection

**Issue**: "Configuration file already exists"
- **Solution**: The skill will skip existing files unless `--force` is used

## See Also

- [E1.2 - State Management](./e1_2_state_management.md)
- [E1.3 - Configuration Management](./e1_3_config_management.md)
- [Project Initialization Guide](../guides/project_setup.md)
