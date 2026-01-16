# AI Playwright Framework → Claude Agent SDK Conversion Plan

## Executive Summary

**Goal:** Transform the `ai-playwright-framework` from a TypeScript CLI tool into a production-grade Python product powered by the `claude-agent-sdk-python`.

**Target Market:** QA teams, non-technical testers, and enterprises requiring AI-powered test automation.

**Commercial Status:** This is a commercial product for sale, not a prototype.

---

## 1. Current State Analysis

### 1.1 Source: ai-playwright-framework (ksmuvva/ai-playwright-framework)

**Architecture:**
- **Language:** TypeScript/Node.js CLI tool
- **Target Output:** Python Playwright tests with Behave (BDD)
- **AI Integration:** Direct Anthropic/OpenAI API calls
- **Target Audience:** Non-technical testers who cannot code

**Core Features:**
1. **BDD Scenario Generation:** Converts recordings/requirements to Gherkin scenarios
2. **Self-Healing Locators:** AI-generated resilient selectors
3. **Smart Wait Management:** Dynamic wait strategies
4. **Test Data Generation:** AI-generated realistic test data
5. **Auto-Screenshots:** Automatic capture on failures
6. **Power Apps Support:** Specialized handling for Power Apps

**Advanced AI Features:**
- Prompt caching for cost optimization
- Streaming responses
- Function calling capabilities
- Root cause analysis for failures
- Meta-reasoning for flaky test fixes
- Failure clustering
- Auto-fix flaky tests

### 1.2 Target: claude-agent-sdk-python

**Capabilities:**
- **Python SDK for Claude Agents**
- **`query()` function** - Simple async queries
- **`ClaudeSDKClient`** - Bidirectional conversations with tools
- **In-process MCP servers** - Custom tools without subprocess overhead
- **Hooks** - Event-driven processing at agent loop points
- **Bundled Claude Code CLI**

**Key Differences from Direct API Usage:**
- Agent-based architecture (not just API calls)
- Built-in tool ecosystem (Read, Write, Bash, etc.)
- Stateful conversations with context management
- Custom tool definitions as Python functions
- Hook system for intercepting and modifying behavior

---

## 2. Architecture Design

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLI Interface (Click/Typer)                 │
├─────────────────────────────────────────────────────────────────┤
│                   Application Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Test Agent  │  │  Debug Agent │  │  Report Agent│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
├─────────────────────────────────────────────────────────────────┤
│                   Claude Agent SDK Layer                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           ClaudeSDKClient + Custom Tools                │   │
│  └─────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                   Tool Layer (MCP Servers)                      │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐         │
│  │Playwright│BDD│Self-Heal│Test│Report│Power│         │
│  │Recorder│Gen│Locators│Data│Gen│Apps│         │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘         │
├─────────────────────────────────────────────────────────────────┤
│                   Infrastructure Layer                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  License Manager  │  Config  │  State  │  Logging       │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Project Structure

```
claude-playwright-agent/
├── src/
│   ├── claude_playwright_agent/
│   │   ├── __init__.py
│   │   ├── cli/                    # CLI interface (Click/Typer)
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── commands/
│   │   │   │   ├── init.py
│   │   │   │   ├── record.py
│   │   │   │   ├── generate.py
│   │   │   │   ├── run.py
│   │   │   │   ├── debug.py
│   │   │   │   └── report.py
│   │   ├── agents/                 # Agent definitions
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── test_agent.py
│   │   │   ├── debug_agent.py
│   │   │   └── report_agent.py
│   │   ├── tools/                  # MCP Tools
│   │   │   ├── __init__.py
│   │   │   ├── playwright_tools.py
│   │   │   ├── bdd_tools.py
│   │   │   ├── locator_tools.py
│   │   │   ├── test_data_tools.py
│   │   │   ├── reporting_tools.py
│   │   │   └── power_apps_tools.py
│   │   ├── hooks/                  # Event hooks
│   │   │   ├── __init__.py
│   │   │   ├── validation.py
│   │   │   ├── licensing.py
│   │   │   └── telemetry.py
│   │   ├── state/                  # State management
│   │   │   ├── __init__.py
│   │   │   ├── session.py
│   │   │   ├── project.py
│   │   │   └── test_run.py
│   │   ├── config/                 # Configuration
│   │   │   ├── __init__.py
│   │   │   ├── settings.py
│   │   │   └── defaults.py
│   │   ├── licensing/              # License management
│   │   │   ├── __init__.py
│   │   │   ├── manager.py
│   │   │   └── validator.py
│   │   ├── reporting/              # Report generation
│   │   │   ├── __init__.py
│   │   │   ├── html.py
│   │   │   ├── json.py
│   │   │   └──── ai_analysis.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── logger.py
│   │       └── helpers.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── examples/
├── docs/
├── pyproject.toml
├── setup.py
├── LICENSE
└── README.md
```

---

## 3. Feature Mapping

### 3.1 Core Feature Conversion

| Current Feature | Implementation Strategy | Tool/Agent |
|----------------|------------------------|------------|
| **BDD Generation** | Convert to Agent tool that takes recordings → Gherkin | `bdd_tools.py` |
| **Self-Healing Locators** | Agent tool that generates multiple fallback strategies | `locator_tools.py` |
| **Test Data Generation** | Agent tool for realistic data generation | `test_data_tools.py` |
| **Smart Wait Management** | Built into Playwright tools with AI-powered wait strategies | `playwright_tools.py` |
| **Auto-Screenshots** | Hook that captures on test failure | `hooks/validation.py` |
| **Power Apps Support** | Specialized tool for Power Apps selectors | `power_apps_tools.py` |
| **Root Cause Analysis** | Dedicated Debug Agent with analysis tools | `debug_agent.py` |
| **Flaky Test Detection** | Report Agent with clustering analysis | `report_agent.py` |
| **Meta-Reasoning** | Agent-level planning with multiple turns | All Agents |

### 3.2 New Capabilities Enabled by Agent SDK

| Feature | Description |
|---------|-------------|
| **Interactive Debugging** | Bidirectional conversation during failures |
| **Self-Healing Tests** | Agent can fix broken tests autonomously |
| **Test Evolution** | Agent learns from test runs and improves |
| **Multi-Agent Orchestration** | Specialized agents for different tasks |
| **Session State** | Persistent context across test runs |
| **Custom Tool Ecosystem** | Users can define their own tools |

---

## 4. Productization Strategy

### 4.1 Licensing Model

**Tiered Licensing:**

| Tier | Features | Target |
|------|----------|--------|
| **Starter** ($99/month) | - 1 user<br>- 100 tests/month<br>- Basic BDD generation<br>- Email support | Individual testers |
| **Professional** ($499/month) | - 5 users<br>- 1000 tests/month<br>- All AI features<br>- Priority support<br>- Self-healing locators | Small teams |
| **Enterprise** (Custom) | - Unlimited users<br>- Unlimited tests<br>- On-premise option<br>- Custom integrations<br>- Dedicated support<br>- SLA guarantee | Large organizations |

**License Enforcement:**
- Hardware-locked license keys
- Usage metering and reporting
- Graceful degradation when expired
- Online activation with offline mode

### 4.2 Distribution

1. **PyPI Package:** `claude-playwright-agent`
2. **Docker Images:** For enterprise deployment
3. **Install Script:** `curl https://install.claudeplaywright.ai | sh`
4. **VS Code Extension:** IDE integration

### 4.3 Monetization Features

- **Usage Analytics Dashboard:** Track test generation, execution stats
- **Team Management:** Seat-based user management
- **API Access:** RESTful API for CI/CD integration
- **Cloud Execution:** Optional cloud test runner
- **Custom AI Models:** Fine-tuned models for specific domains

---

## 5. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)

**Goal:** Set up project infrastructure and basic Agent integration

**Tasks:**
1. Initialize Python project with proper structure
2. Set up development environment (poetry/pip, pre-commit, CI/CD)
3. Implement basic CLI with Click/Typer
4. Create base Agent class wrapping ClaudeSDKClient
5. Implement license manager stub
6. Set up logging and configuration

**Deliverables:**
- Working CLI skeleton
- Basic Agent that can respond to queries
- License validation framework

### Phase 2: Core Tools (Weeks 5-8)

**Goal:** Implement essential Playwright and BDD tools

**Tasks:**
1. Implement Playwright tools (record, playback, screenshot)
2. Implement BDD generation tool (recordings → Gherkin)
3. Implement locator tools (self-healing selectors)
4. Implement test data generation tool
5. Create Test Agent with tool integration
6. Add hooks for validation and screenshots

**Deliverables:**
- Functional test generation
- Self-healing locators
- Basic BDD scenarios

### Phase 3: Advanced Features (Weeks 9-12)

**Goal:** Add AI-powered advanced features

**Tasks:**
1. Implement Debug Agent with root cause analysis
2. Implement Report Agent with failure clustering
3. Add meta-reasoning capabilities
4. Implement flaky test detection and auto-fix
5. Add Power Apps specialized support
6. Create AI-powered test improvement suggestions

**Deliverables:**
- Intelligent debugging
- Automated test fixing
- Comprehensive reporting

### Phase 4: Productization (Weeks 13-16)

**Goal:** Make it a sellable product

**Tasks:**
1. Complete license manager with enforcement
2. Add telemetry and usage tracking
3. Create user documentation and tutorials
4. Build website and marketing materials
5. Set up payment processing (Stripe)
6. Implement customer support workflow
7. Create onboarding flow
8. Add first-run wizard

**Deliverables:**
- Licensed product
- Documentation
- Sales website
- Support infrastructure

### Phase 5: Testing & QA (Weeks 17-18)

**Goal:** Ensure product quality

**Tasks:**
1. Comprehensive unit tests
2. Integration tests with real websites
3. Performance testing
4. Security audit
5. User acceptance testing with beta customers
6. Bug fixes and polish

**Deliverables:**
- Stable release candidate
- Test coverage report
- Security audit results

### Phase 6: Launch (Week 19+)

**Goal:** Product launch

**Tasks:**
1. PyPI release
2. Website launch
3. Marketing campaign
4. Customer outreach
5. Support team training
6. Collect feedback and iterate

**Deliverables:**
- Live product
- First customers
- Feedback loop

---

## 6. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Claude API Cost** | High | - Implement aggressive prompt caching<br>- Streaming for early termination<br>- Offer customer API keys option |
| **Competition** | Medium | - Focus on non-technical user experience<br>- Build unique features (Power Apps, self-healing)<br>- Create strong integration ecosystem |
| **SDK Limitations** | Medium | - Build abstraction layer for potential SDK changes<br>- Implement fallback to direct API calls<br>- Contribute to SDK if needed |
| **License Cracking** | Medium | - Server-side validation when possible<br>- Regular key rotation<br>- Make license checking async and non-blocking |
| **User Adoption** | High | - Excellent documentation and tutorials<br>- Free tier for trial<br>- Active community building<br>- Responsive support |
| **Claude API Outages** | Medium | - Graceful degradation<br>- Clear communication<br>- Caching of common patterns |

---

## 7. Technical Decisions

### 7.1 CLI Framework

**Decision:** Use **Click** over Typer

**Rationale:**
- More mature ecosystem
- Better for complex CLI structures
- Larger community
- More examples for similar tools

### 7.2 State Management

**Decision:** Use **SQLite** for local state + **JSON** for session data

**Rationale:**
- SQLite: Persistent data (projects, history, metrics)
- JSON: Session data, test runs (ephemeral)
- No external dependencies
- Easy backup and migration

### 7.3 License Validation

**Decision:** Hybrid approach

**Rationale:**
- Online: Cryptographic validation with server
- Offline: Time-limited grace period with local key validation
- Balances user experience with piracy prevention

### 7.4 Packaging

**Decision:** Multiple formats

1. **PyPI wheel** - Standard Python installation
2. **Docker image** - Enterprise deployment
3. **Standalone binary** - Using PyInstaller for non-Python users

---

## 8. Next Steps

1. **Review this plan** with stakeholders
2. **Finalize licensing model** and pricing
3. **Set up legal** (terms of service, privacy policy)
4. **Initialize repository** with proper structure
5. **Begin Phase 1** implementation

---

## 9. Success Metrics

### Technical Metrics
- Test generation success rate: >95%
- Self-healing success rate: >80%
- Average test generation time: <30 seconds
- Agent response time: <5 seconds

### Business Metrics
- Monthly active users
- Conversion rate (trial → paid)
- Customer churn rate
- Net Promoter Score
- Monthly recurring revenue

### Product Metrics
- Tests generated per user per month
- Average project size (number of tests)
- Feature usage distribution
- Support ticket volume

---

## Appendix: Code Sketches

### A. Basic Tool Definition

```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("record_playwright", "Record browser actions and generate test code", {})
async def record_playwright(args):
    """Record browser interactions using Playwright"""
    # Implementation
    return {
        "content": [{"type": "text", "text": "Recording started..."}]
    }

server = create_sdk_mcp_server(
    name="playwright-tools",
    version="1.0.0",
    tools=[record_playwright]
)
```

### B. Test Agent

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

class TestAgent:
    def __init__(self, config):
        self.options = ClaudeAgentOptions(
            system_prompt="""You are an AI test automation expert.
            Generate BDD scenarios from user requirements and recordings.""",
            mcp_servers=config.mcp_servers,
            allowed_tools=config.allowed_tools
        )

    async def generate_tests(self, recording_data):
        async with ClaudeSDKClient(options=self.options) as client:
            await client.query(f"Generate BDD tests from: {recording_data}")
            async for msg in client.receive_response():
                # Process response
                pass
```

### C. License Hook

```python
from claude_agent_sdk import HookMatcher

async def validate_license(input_data, tool_use_id, context):
    """Validate license before allowing tool use"""
    if not LicenseManager.is_valid():
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "License expired or invalid"
            }
        }
    return {}

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="*", hooks=[validate_license])
        ]
    }
)
```

---

## 10. Detailed Documentation

This document provides the high-level conversion plan. For detailed technical specifications, see:

| Document | Purpose |
|----------|---------|
| **[AGENT_ARCHITECTURE.md](AGENT_ARCHITECTURE.md)** | Complete Orchestrator-based architecture with implementation code |
| **[SKILLS_CATALOG.md](SKILLS_CATALOG.md)** | Complete reference for all 18 skills |
| **[STATE_SCHEMA.md](STATE_SCHEMA.md)** | State management schema (state.json) |
| **[SKILL_DEV_GUIDE.md](SKILL_DEV_GUIDE.md)** | Guide for developing custom skills |
| **[SDK_MAPPING.md](SDK_MAPPING.md)** | Claude Agent SDK Python implementation mapping |
| **[EXAMPLES.md](EXAMPLES.md)** | Development examples and workflows |

---

**Document Version:** 1.1
**Last Updated:** 2025-01-11
**Status:** Draft for Review
