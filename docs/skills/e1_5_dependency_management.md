# E1.5 - Dependency Management

**Skill:** `e1_5_dependency_management`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

The Dependency Management skill handles Python package dependencies, version constraints, and dependency resolution for test projects.

## Capabilities

- Parse dependency specifications
- Resolve version constraints
- Check for dependency conflicts
- Generate requirements files
- Validate installed dependencies

## Usage

```python
# Parse dependency
dep = parse_dependency("pytest>=7.0.0,<8.0.0")

# Check if dependency is satisfied
dep.satisfies("7.4.2")  # True

# Resolve dependencies
resolver = DependencyResolver()
resolved = resolver.resolve_dependencies(["pytest", "playwright"])
```

## Dependency Types

- **Exact**: `==1.2.3` - Exact version
- **Minimum**: `>=1.2.3` - Minimum version
- **Caret**: `^1.2.3` - Compatible with 1.x.x
- **Tilde**: `~1.2.3` - Compatible with 1.2.x
- **Wildcard**: `1.2.*` - Any patch version

## Version Constraint Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `==` | Exact version | `==1.2.3` |
| `>=` | Greater than or equal | `>=1.2.3` |
| `<=` | Less than or equal | `<=1.2.3` |
| `>` | Greater than | `>1.2.3` |
| `<` | Less than | `<1.2.3` |
| `^` | Caret (compatible) | `^1.2.3` |
| `~` | Tilde (approximate) | `~1.2.3` |

## See Also

- [E1.1 - Project Initialization](./e1_1_project_init.md)
- [E1.2 - State Management](./e1_2_state_management.md)
