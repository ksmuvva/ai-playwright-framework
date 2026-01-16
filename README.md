# Claude Playwright Agent

> AI-powered test automation framework powered by Claude Agent SDK

**Status:** In Development | **Version:** 0.1.0 | **License:** Proprietary

---

## Overview

Claude Playwright Agent transforms test automation by leveraging AI to generate, execute, and maintain tests. Built on the Claude Agent SDK, it enables non-technical testers to create robust, self-healing test automation using natural language.

### Key Features

- **AI-Powered Test Generation:** Convert recordings or requirements into BDD scenarios
- **Self-Healing Locators:** AI automatically fixes broken selectors
- **Intelligent Debugging:** Root cause analysis and auto-fix suggestions
- **Smart Wait Management:** AI-optimized wait strategies
- **Test Data Generation:** Realistic test data on demand
- **Failure Clustering:** Group and analyze similar failures
- **Multi-Agent Architecture:** Specialized agents for different tasks
- **Power Apps Support:** Specialized handling for Microsoft Power Apps

---

## Quick Start

### Installation

```bash
# Install via pip
pip install claude-playwright-agent

# Install Playwright browsers
playwright install --with-deps

# Initialize your project
cpa init my-tests
```

### First Test

```bash
# Start recording
cpa record --name login-flow --url https://example.com/login

# Generate BDD tests
cpa generate recordings/login-flow.json

# Run tests
cd my-tests
cpa run
```

---

## Documentation

- [User Guide](https://docs.claudeplaywright.ai)
- [API Reference](https://docs.claudeplaywright.ai/api)
- [Examples](https://docs.claudeplaywright.ai/examples)
- [CLI Reference](https://docs.claudeplaywright.ai/cli)

---

## Pricing

| Tier | Price | Features |
|------|-------|----------|
| **Starter** | $99/month | 1 user, 100 tests/month, basic features |
| **Professional** | $499/month | 5 users, 1,000 tests/month, all AI features |
| **Enterprise** | Custom | Unlimited users, on-premise, SLA |

Get started with a free trial at [claudeplaywright.ai](https://claudeplaywright.ai)

---

## Requirements

- Python 3.10+
- Claude API account
- Modern web browser (Chromium, Firefox, or WebKit)

---

## Development

See [DEV_SETUP.md](DEV_SETUP.md) for development instructions.

```bash
# Clone repository
git clone https://github.com/your-org/claude-playwright-agent.git

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src/claude_playwright_agent --cov-report=html
```

---

## Architecture

**Orchestrator-Based Architecture** with specialist agents:

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLI Interface (cpa)                         │
├─────────────────────────────────────────────────────────────────┤
│                   Orchestrator Agent (Daemon)                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │Orchestrate  │ │ CLI Handler │ │State Mgr    │ │Error Handler││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
├─────────────────────────────────────────────────────────────────┤
│                   Specialist Agents (On-Demand)                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │ Ingestion   │ │Deduplicatn  │ │BDD Conv.    │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│  ┌─────────────┐ ┌─────────────┐                               │
│  │ Execution   │ │ Analysis    │                               │
│  └─────────────┘ └─────────────┘                               │
├─────────────────────────────────────────────────────────────────┤
│                   Tool Layer (MCP)                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           Microsoft Playwright MCP (External)            │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           Custom Tools (In-Process)                      │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Documentation

### Planning & Architecture

| Document | Description |
|----------|-------------|
| **[PROJECT_TASKS.md](PROJECT_TASKS.md)** | Complete project tasks breakdown (~557 tasks, 9 epics) |
| **[CONVERSION_PLAN.md](CONVERSION_PLAN.md)** | High-level conversion plan and roadmap |
| **[AGENT_ARCHITECTURE.md](AGENT_ARCHITECTURE.md)** | Complete Orchestrator + Specialist Agent architecture |
| **[SYSTEM_DESIGN.md](SYSTEM_DESIGN.md)** | System architecture and data flow |
| **[SKILLS_ARCHITECTURE.md](SKILLS_ARCHITECTURE.md)** | Skills system design and patterns |

### Technical Specifications

| Document | Description |
|----------|-------------|
| **[SKILLS_CATALOG.md](SKILLS_CATALOG.md)** | Reference for all 18 skills across agents |
| **[COMPONENT_SPECS.md](COMPONENT_SPECS.md)** | Detailed component specifications |
| **[STATE_SCHEMA.md](STATE_SCHEMA.md)** | State management schema design |
| **[API_DESIGN.md](API_DESIGN.md)** | CLI and Agent API design |
| **[TOOL_SPECIFICATIONS.md](TOOL_SPECIFICATIONS.md)** | MCP tool specifications |

### Development Guides

| Document | Description |
|----------|-------------|
| **[SKILL_DEV_GUIDE.md](SKILL_DEV_GUIDE.md)** | Guide for developing custom skills |
| **[SDK_MAPPING.md](SDK_MAPPING.md)** | Mapping to Claude Agent SDK Python |
| **[EXAMPLES.md](EXAMPLES.md)** | Development examples and workflows |
| **[DEV_SETUP.md](DEV_SETUP.md)** | Development environment setup |

---

## License

Proprietary software. All rights reserved.

See [LICENSE](LICENSE) for details.

---

## Support

- **Documentation:** https://docs.claudeplaywright.ai
- **Email:** support@claudeplaywright.ai
- **Slack:** #claude-playwright-agent
- **Issues:** https://github.com/your-org/claude-playwright-agent/issues

---

## Acknowledgments

Built with:
- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python) by Anthropic
- [Playwright](https://playwright.dev/python/) by Microsoft
- [Click](https://click.palletsprojects.com/) by Pallets

---

## Copyright

© 2025 Claude Playwright Agent. All rights reserved.
