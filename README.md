# Claude Playwright Agent

> AI-powered test automation framework with intelligent test generation, self-healing selectors, and Page Object Model support

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production--ready-success.svg)]()

**Version:** 1.0.0 | **Stars:** ⭐ | **Contributing:** 🤝 Welcome

---

## 🎯 What is Claude Playwright Agent?

Claude Playwright Agent is a sophisticated test automation framework that leverages AI and multi-agent architecture to make test creation, maintenance, and execution smarter and more efficient. Built on the Claude Agent SDK and Microsoft Playwright, it transforms how teams approach web automation.

### 🚀 Why Claude Playwright Agent?

- **🤖 AI-Powered:** Automatically generate BDD scenarios from recordings
- **🔧 Self-Healing:** AI fixes broken selectors automatically (9 healing strategies)
- **📦 Page Object Model:** Full POM support with BasePage and examples
- **🔄 Multi-Agent:** 6 specialized agents orchestrate test automation
- **🎭 Deduplication:** Smart element reuse across recordings
- **⚙️ Configurable:** 5 production-ready profiles (dev, test, prod, ci)
- **📊 Comprehensive:** 47 built-in skills across 10 epics
- **🧪 BDD Framework:** Support for Behave and pytest-bdd

---

## ✨ Key Features

### 🎬 Recording to BDD
Record user interactions and automatically generate BDD scenarios with Gherkin syntax and step definitions.

```bash
playwright codegen https://example.com --target=python
cpa ingest recordings/test.spec.js
cpa run convert
```

### 🔮 Self-Healing Selectors
AI-powered selector recovery with 9 strategies:
- Exact match, text search, role-based
- Attribute matching, structure analysis
- Sibling locators, parent-child relationships
- Fuzzy text matching, nearby elements

### 📦 Page Object Model
Complete POM implementation out of the box:
- **BasePage** class (600+ lines) with common methods
- **Example Page Objects** (Login, Dashboard, Home)
- **Flexible selectors** with fallback options
- **Business language** methods
- **Navigation flow** support

### 🎯 47 Built-in Skills
Across 10 epics:
1. **Project Management** - Init, state, config, context
2. **Recording** - Advanced, network, visual regression
3. **Ingestion** - Playwright parsing, action extraction
4. **Deduplication** - Pattern analysis, component extraction
5. **BDD** - Gherkin generation, step definitions
6. **Execution** - Test running, parallel execution
7. **Self-Healing** - Selector recovery strategies
8. **Integration** - Registry, lifecycle, discovery
9. **CLI** - Error handling, interactive prompts, help
10. **Memory & AI** - Multi-layered memory for learning

---

## 🚀 Quick Start (5 Minutes)

### 1. Installation

```bash
# Install the framework
pip install claude-playwright-agent

# Install Playwright browsers
playwright install --with-deps

# Or install from source
git clone https://github.com/ksmuvva/ai-playwright-framework.git
cd ai-playwright-framework
pip install -e .
```

### 2. Initialize Project

```bash
# Create a new test project
cpa init my-first-tests
cd my-first-tests

# Configure your API key
export GLM_API_KEY=your-api-key-here
```

### 3. Record Your First Test

```bash
# Start Playwright code generator
playwright codegen https://the-internet.herokuapp.com/login --target=python

# Perform actions:
# 1. Enter username
# 2. Enter password
# 3. Click Login
# 4. Save to recordings/login.spec.js
```

### 4. Generate & Run Tests

```bash
# Ingest the recording
cpa ingest recordings/login.spec.js

# Generate page objects (optional)
cpa generate page-objects

# Convert to BDD scenarios
cpa run convert

# Run the tests
cpa run test

# View results
open reports/index.html
```

**That's it!** You've created and executed your first AI-powered test in under 5 minutes.

---

## 📚 Documentation

### User Guides

| Guide | Description |
|-------|-------------|
| **[Quick Start Guide](docs/quick_start.md)** | Get started in 5 minutes |
| **[CLI Reference](docs/cli_reference.md)** | All 15 CLI commands documented |
| **[Page Objects Guide](docs/page_objects.md)** | Create and use page objects |
| **[Configuration Guide](config/README.md)** | Framework configuration |

### Architecture & Design

| Document | Description |
|----------|-------------|
| **[FRAMEWORK_ARCHITECTURE.md](FRAMEWORK_ARCHITECTURE.md)** | Complete architecture overview |
| **[SKILLS_CATALOG.md](SKILLS_CATALOG.md)** | All 47 skills reference |
| **[REQUIREMENTS.md](REQUIREMENTS.md)** | Project requirements |
| **[CHANGELOG.md](CHANGELOG.md)** | Version history |

---

## 🏗️ Architecture

### Multi-Agent System

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI Interface (cpa)                       │
├─────────────────────────────────────────────────────────────┤
│              OrchestratorAgent (Coordinator)                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │Message Queue│ │State Manager │ │Error Handler │      │
│  └──────────────┘ └──────────────┘ └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│              Specialist Agents (On-Demand)                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │IngestionAgent│ │Deduplication│ │  BDDAgent    │      │
│  └──────────────┘ └──────────────┘ └──────────────┘      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │ExecutionAgent│ │AnalysisAgent │ │              │      │
│  └──────────────┘ └──────────────┘ └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│              Tool Layer (MCP + Custom)                      │
│  ┌──────────────────────────────────────────────────┐      │
│  │  Self-Healing │ Selector Catalog │ Page Objects│      │
│  └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Configuration Profiles

**Development Profile (`dev`)** - Local development with debugging
- headless: false
- devtools: true
- logging: DEBUG

**Test Profile (`test`)** - Test environment with parallel execution
- parallel_workers: 4
- retry_failed: 2
- JSON logging

**Production Profile (`prod`)** - Production runs
- parallel_workers: 8
- logging: WARNING
- Minimal overhead

**CI/CD Profile (`ci`)** - Continuous integration
- JUnit reports
- Optimized for pipelines
- Performance monitoring

---

## 💡 Usage Examples

### Example 1: Using Page Objects

```python
from pages.login_page import LoginPage

def test_login(page):
    # Create page object
    login_page = LoginPage(page, base_url="https://example.com")

    # Navigate and login
    login_page.navigate()
    login_page.login("testuser@example.com", "password123")

    # Assertions
    login_page.assert_is_loaded()
```

### Example 2: Configuration Profiles

```bash
# Development with visual debugging
cpa --profile dev run test

# CI/CD pipeline
cpa --profile ci run test

# Production run
cpa --profile prod run test
```

### Example 3: Parallel Execution

```bash
# Run 4 tests in parallel
cpa --profile test run test

# Or configure in config/default/config.yaml
execution:
  parallel_workers: 4
```

### Example 4: Self-Healing in Action

```python
# Broken selector? No problem!
page.click("#submit-button-v2")  # Selector changed
# AI automatically tries:
# 1. Exact match
# 2. Text search
# 3. Role matching
# 4. Fuzzy text
# 5. And 5 more strategies...
```

---

## 🎯 CLI Commands

### Project Management

```bash
cpa init <project-name>          # Create new project
cpa status                       # Show project status
cpa info                         # Framework information
```

### Recording & Generation

```bash
cpa ingest <recording>           # Import recording
cpa generate page-objects        # Generate page objects
cpa deduplicate                  # Run deduplication
```

### Test Execution

```bash
cpa run test                    # Run all tests
cpa run test --tags @smoke     # Run by tag
cpa run convert                 # Generate BDD scenarios
cpa run full                    # Complete pipeline
```

### Configuration

```bash
cpa configure set <key> <value> # Set config value
cpa configure profile <name>     # Switch profile
cpa env set <key> <value>        # Set environment variable
```

### Reporting

```bash
cpa report                       # View latest report
cpa report --analyze             # With AI analysis
cpa list recordings             # List all recordings
```

**[📖 Full CLI Reference](docs/cli_reference.md)**

---

## 🔧 Configuration

The framework uses a hierarchical configuration system:

```
project-root/
├── config/
│   ├── default/
│   │   ├── config.yaml      # Main configuration
│   │   ├── pytest.ini       # Pytest settings
│   │   └── behave.ini       # Behave settings
│   └── profiles/
│       ├── dev.yaml         # Development profile
│       ├── test.yaml        # Test profile
│       ├── prod.yaml        # Production profile
│       └── ci.yaml          # CI/CD profile
```

### Example Configuration

```yaml
# config/default/config.yaml
framework:
  bdd_framework: behave      # or pytest-bdd
  default_timeout: 30000     # milliseconds

browser:
  browser: chromium          # chromium, firefox, webkit
  headless: true
  viewport:
    width: 1280
    height: 720

ai:
  provider: glm              # anthropic, openai, glm
  model: glm-4-plus
  max_tokens: 8192

execution:
  parallel_workers: 1
  retry_failed: 0
  self_healing: true

page_objects:
  output_dir: pages
  base_class: BasePage
  use_async: true
```

**[📖 Complete Configuration Guide](config/README.md)**

---

## 📦 Page Objects

The framework includes a complete Page Object Model implementation:

### BasePage Features

```python
from pages.base_page import BasePage

class MyPage(BasePage):
    # Navigation
    page.goto(path)
    page.reload()
    page.go_back()

    # Element interaction (with self-healing)
    page.click(selector)
    page.fill(selector, value)

    # Assertions
    page.assert_url(expected_url)
    page.assert_visible(selector)
    page.assert_text(selector, text)

    # Screenshots
    page.screenshot(name)
```

### Example Page Objects Included

- **LoginPage** - Login functionality
- **DashboardPage** - User dashboard
- **HomePage** - Landing page with search

**[📖 Page Objects Guide](docs/page_objects.md)**

---

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines.

### Development Setup

```bash
# Clone repository
git clone https://github.com/ksmuvva/ai-playwright-framework.git
cd ai-playwright-framework

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src/claude_playwright_agent --cov-report=html
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Add docstrings
- Write tests for new features

---

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_base_page.py

# Run with coverage
pytest --cov=src/claude_playwright_agent

# Run by marker
pytest -m "not slow"
```

### Test Structure

```
tests/
├── integration/     # Integration tests
├── agents/          # Agent tests
├── deduplication/   # Deduplication tests
└── page_objects/    # Page object tests
```

---

## 📊 Project Statistics

- **Languages:** Python, TypeScript
- **Lines of Code:** ~99,000
- **Test Coverage:** Target 80%+
- **Documentation:** 4 comprehensive guides
- **Configuration Profiles:** 5 production-ready
- **Built-in Skills:** 47 across 10 epics
- **Agents:** 6 specialized agents
- **Page Objects:** 1 BasePage + 3 examples

---

## 🗺️ Roadmap

### ✅ Completed (v1.0.0)

- [x] Multi-agent architecture (6 agents)
- [x] Configuration system (5 profiles)
- [x] Page Object Model (BasePage + examples)
- [x] Self-healing selectors (9 strategies)
- [x] BDD generation (Behave + pytest-bdd)
- [x] Comprehensive documentation (4 guides)
- [x] CLI interface (15 commands)

### 🔄 In Progress

- [ ] Enhanced component extraction (12 component types)
- [ ] AnalysisAgent optimization
- [ ] Working examples & tutorials
- [ ] CI/CD templates

### 📋 Planned

- [ ] Visual test editor
- [ ] Cloud execution support
- [ ] Team collaboration features
- [ ] Advanced reporting dashboard

---

## ❓ FAQ

### Q: What LLM providers are supported?

**A:** Anthropic Claude, OpenAI GPT-4, and GLM 4.7.

### Q: Can I use this with existing Playwright tests?

**A:** Yes! You can ingest existing Playwright recordings and generate BDD scenarios.

### Q: How does self-healing work?

**A:** When a selector fails, AI tries 9 different strategies to find the element, including text search, role matching, fuzzy matching, and more.

### Q: Do I need to know Python to use this?

**A:** For basic usage, no. You can record tests and generate BDD scenarios without coding. For advanced features, Python knowledge helps.

### Q: Is this free?

**A:** Yes! This is an open-source framework (MIT License). You only need API keys for the LLM provider of your choice.

**[📖 More FAQ](docs/faq.md)**

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with amazing open-source tools:

- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python) by Anthropic
- [Playwright](https://playwright.dev/python/) by Microsoft
- [Click](https://click.palletsprojects.com/) by Pallets
- [Behave](https://behave.readthedocs.io/) BDD testing framework
- [Pytest](https://docs.pytest.org/) Testing framework

---

## 📞 Support

- **Documentation:** [docs/](docs/)
- **Issues:** https://github.com/ksmuvva/ai-playwright-framework/issues
- **Discussions:** https://github.com/ksmuvva/ai-playwright-framework/discussions

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=ksmuvva/ai-playwright-framework&type=Date)](https://star-history.com/#ksmuvva/ai-playwright-framework&Date)

---

**Made with ❤️ by the Claude Playwright Agent team**

*© 2025 Claude Playwright Agent. All rights reserved.*
