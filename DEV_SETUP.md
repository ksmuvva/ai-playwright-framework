# Development Setup Guide

## Prerequisites

### Required Software

| Software | Minimum Version | Recommended |
|----------|----------------|-------------|
| Python | 3.10 | 3.11+ |
| Git | 2.30+ | Latest |
| Node.js | 18+ | 20 LTS (for Playwright) |
| Docker | 20+ | Latest (optional) |

### Required Accounts

- GitHub account (for repository access)
- Anthropic account (for Claude API access)
- Optional: PyPI account (for publishing)

---

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/claude-playwright-agent.git
cd claude-playwright-agent
```

### 2. Create Virtual Environment

```bash
# Using venv
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Or using pyproject.toml (recommended)
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
```

### 3. Install Dependencies

```bash
# Install development dependencies
pip install -e ".[dev]"

# This will install:
# - Core dependencies (see pyproject.toml)
# - Development tools (pytest, black, ruff, mypy)
# - Documentation tools (sphinx, mkdocs)
# - Build tools (build, twine)
```

### 4. Install Playwright Browsers

```bash
# Install Playwright Python package
pip install playwright

# Install browser binaries
playwright install chromium
playwright install firefox
playwright install webkit

# Or install all at once
playwright install --with-deps
```

### 5. Configure Environment Variables

```bash
# Create .env file
cp .env.example .env

# Edit .env with your values
# Required for development:
ANTHROPIC_API_KEY=your_api_key_here
CPA_DEV_MODE=true
CPA_LOG_LEVEL=debug

# Optional for license testing:
CPA_LICENSE_KEY=dev_license_key

# Optional for telemetry testing:
CPA_TELEMETRY_ENDPOINT=http://localhost:8000
```

### 6. Pre-commit Hooks

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run manually to test
pre-commit run --all-files
```

---

## Project Structure Setup

```bash
# Create directory structure
mkdir -p src/claude_playwright_agent/{cli,agents,tools,hooks,state,config,licensing,reporting,utils}
mkdir -p tests/{unit,integration,e2e}
mkdir -p examples
mkdir -p docs

# Create __init__.py files
find src -type d -exec touch {}/__init__.py \;

# Verify structure
tree -L 3 -I '__pycache__|*.pyc|.venv'
```

---

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Changes

- Write code following the style guide
- Add unit tests for new functionality
- Update documentation as needed

### 3. Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_tools.py

# Run with coverage
pytest --cov=src/claude_playwright_agent --cov-report=html

# Run integration tests (requires environment)
pytest tests/integration/

# Run e2e tests (requires full setup)
pytest tests/e2e/
```

### 4. Lint and Format

```bash
# Format code
black src/ tests/

# Check linting
ruff check src/ tests/

# Type checking
mypy src/

# Security check
bandit -r src/

# All at once (using pre-commit)
pre-commit run --all-files
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add BDD generation tool

- Implemented generate_feature_file tool
- Added support for Behave framework
- Included unit tests

Closes #123"
```

**Commit Message Format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
# Then create PR on GitHub
```

---

## Development Tools

### IDE Setup (VS Code)

**Recommended Extensions:**
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Python Test Explorer (littlefoxteam.vscode-python-test-adapter)
- GitLens (eamodio.gitlens)
- YAML (redhat.vscode-yaml)

**VS Code Settings (`.vscode/settings.json`):**
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "editor.formatOnSave": true,
  "editor.rulers": [88, 100],
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/.mypy_cache": true
  }
}
```

---

### PyCharm Setup

1. **Project Interpreter:** Set to `.venv`
2. **Enable pytest:** Settings → Tools → Python Integrated Tools → Testing → pytest
3. **Code Style:** Settings → Editor → Code Style → Python → Set to Black (100 char line)
4. **Inspections:** Enable Pylance/Pyright for type checking

---

## Local Testing

### Testing CLI Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Test CLI help
cpa --help
cpa --version

# Test init command
cpa init test-project --template basic

# Test record (opens browser)
cpa record --name test-recording

# Test generate
cpa generate recordings/test-recording.json

# Test run
cd test-project
cpa run
```

### Testing with Real Websites

```bash
# Run integration tests against real sites
pytest tests/integration/test_playwright_tools.py --env=real

# Test against localhost (requires running app)
pytest tests/integration/ --target=http://localhost:3000
```

### Testing License System

```bash
# Test with dev license
export CPA_LICENSE_KEY=DEV-KEY-1234
cpa license status

# Test offline mode
export CPA_OFFLINE_MODE=true
cpa run

# Test expired license
export CPA_LICENSE_KEY=EXPIRED-KEY
cpa run  # Should fail gracefully
```

---

## Debugging

### Debugging Tests

```bash
# Run with pdb
pytest --pdb

# Run with ipdb (if installed)
pip install ipdb
pytest --pdbcls=IPython.terminal.debugger:TerminalPdb --pdb
```

### Debugging CLI

```bash
# Enable verbose output
export CPA_LOG_LEVEL=DEBUG
cpa --verbose run

# Use Python debugger
python -m pdb -m claude_playwright_agent.cli.main run
```

### Debugging Agent Interactions

```bash
# Enable Claude SDK debug mode
export CLAUDE_SDK_DEBUG=true
export CPA_LOG_LEVEL=DEBUG

# Save agent conversations
export CPA_SAVE_CONVERSATIONS=true
# Conversations saved to .cpa/conversations/
```

---

## Building and Distribution

### Build Wheel

```bash
# Build wheel with bundled CLI
python scripts/build_wheel.py

# Build with specific version
python scripts/build_wheel.py --version 0.1.0

# Build and check
python -m build
twine check dist/*
```

### Test Local Install

```bash
# Install from local wheel
pip install dist/claude_playwright_agent-0.1.0-py3-none-any.whl

# Test installation
cpa --version

# Uninstall
pip uninstall claude-playwright-agent
```

---

## Docker Development

### Build Dev Container

```bash
# Build image
docker build -t cpa-dev -f docker/Dockerfile.dev .

# Run container
docker run -it --rm \
  -v $(pwd):/workspace \
  -p 8000:8000 \
  cpa-dev bash

# Or use docker-compose
docker-compose -f docker/docker-compose.dev.yml up
```

### Run Tests in Docker

```bash
docker exec -it cpa-dev pytest
```

---

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          playwright install --with-deps
      - name: Run tests
        run: pytest
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Common Issues

### Issue: Playwright browsers not found

**Solution:**
```bash
playwright install --with-deps
```

### Issue: Claude SDK not found

**Solution:**
```bash
pip install claude-agent-sdk
# The SDK bundles Claude Code CLI automatically
```

### Issue: License validation fails in dev

**Solution:**
```bash
export CPA_DEV_MODE=true
export CPA_LICENSE_KEY=DEV-KEY
```

### Issue: Pre-commit hooks not running

**Solution:**
```bash
pre-commit uninstall
pre-commit install --hook-type pre-commit --hook-type pre-push
```

---

## Resources

### Documentation

- [Claude Agent SDK Docs](https://github.com/anthropics/claude-agent-sdk-python)
- [Playwright Python Docs](https://playwright.dev/python/)
- [Behave Docs](https://behave.readthedocs.io/)

### Internal Resources

**Core Documentation:**
- `README.md` - Project overview and quick start
- `AGENT_ARCHITECTURE.md` - Complete Orchestrator + Specialist Agent architecture
- `SKILLS_CATALOG.md` - Reference for all 18 skills
- `SKILLS_ARCHITECTURE.md` - Skills system design
- `COMPONENT_SPECS.md` - Detailed component specifications
- `STATE_SCHEMA.md` - State management schema
- `SYSTEM_DESIGN.md` - System architecture and data flow

**Development Guides:**
- `SKILL_DEV_GUIDE.md` - Guide for developing custom skills
- `SDK_MAPPING.md` - Claude Agent SDK Python implementation mapping
- `EXAMPLES.md` - Development examples and workflows
- `API_DESIGN.md` - CLI and Agent API design

**Planning Documents:**
- `CONVERSION_PLAN.md` - High-level conversion plan and roadmap
- `DEV_SETUP.md` - This file

---

## Getting Help

- **Slack:** #claude-playwright-agent
- **Email:** dev@claudeplaywright.ai
- **Issues:** GitHub Issues

---

**Version:** 1.0
**Last Updated:** 2025-01-11
