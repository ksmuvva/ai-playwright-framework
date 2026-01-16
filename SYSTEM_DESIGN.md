# System Design: AI Playwright Automation Agent

## Document Information

| Field | Value |
|-------|-------|
| **Project** | AI Playwright Automation Agent |
| **Version** | 1.0 |
| **Date** | 2025-01-11 |
| **Status** | Design |
| **Author** | Claude Planning |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [Architecture](#3-architecture)
4. [Component Design](#4-component-design)
5. [Data Flow](#5-data-flow)
6. [Integration Points](#6-integration-points)
7. [Technology Stack](#7-technology-stack)
8. [User Stories & Requirements](#8-user-stories--requirements)
9. [Implementation Tasks](#9-implementation-tasks)
10. [Security Considerations](#10-security-considerations)
11. [Deployment](#11-deployment)

---

## 1. Executive Summary

### 1.1 Purpose

The AI Playwright Automation Agent is an intelligent CLI tool that automates the creation and execution of test automation frameworks. It combines:
- **Microsoft Playwright MCP** for browser automation
- **Claude Agent SDK Python** for AI reasoning
- **Custom tools** for BDD conversion and framework management
- **Claude Skills** for extensible capabilities

### 1.2 Key Value Propositions

| Feature | Benefit |
|---------|---------|
| Zero-code framework setup | Non-technical users can create professional test frameworks |
| AI-powered BDD conversion | Recorded scripts become maintainable Gherkin scenarios |
| Self-healing locators | Tests adapt to UI changes automatically |
| Intelligent reporting | AI analyzes failures and suggests fixes |
| Skill extensibility | Users can add custom capabilities via Claude Skills |

### 1.3 Target Users

1. **QA Engineers** - Need to create tests quickly without coding
2. **Manual Testers** - Transition to automation without learning to code
3. **DevOps Engineers** - Integrate AI-generated tests into CI/CD
4. **Product Owners** - Verify functionality through natural language

---

## 2. System Overview

### 2.1 High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INTERACTION                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. User runs CLI: cpa init my-project                                  │
│     └── Creates empty Playwright Python framework                       │
│                                                                          │
│  2. User runs: npx playwright codegen                                   │
│     └── Records browser actions (generates script)                      │
│                                                                          │
│  3. User runs: cpa ingest recordings/login.js                           │
│     └── AI converts to BDD scenarios                                    │
│     └── Scenarios integrated into framework                             │
│                                                                          │
│  4. User runs: cpa run                                                  │
│     └── Executes BDD tests                                              │
│     └── AI generates intelligent report                                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Core Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | **Framework Initialization** | Creates folder structure with Behave/pytest-bdd setup |
| 2 | **Recording Ingestion** | Converts Playwright codegen output to BDD scenarios |
| 3 | **Test Execution** | Runs BDD scenarios with Playwright step definitions |
| 4 | **Intelligent Reporting** | AI-analyzed test results with clustering and insights |
| 5 | **Claude Skills** | Extensible skills system for custom workflows |

---

## 3. Architecture

### 3.1 System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              CLI LAYER (Click)                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │   init   │  │  ingest  │  │   run    │  │  report  │  │  skills  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└──────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           ORCHESTRATION LAYER                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      Agent Orchestrator                               │   │
│  │  - Manages agent lifecycle                                           │   │
│  │  - Routes tasks to appropriate agents                                │   │
│  │  - Coordinates multi-agent workflows                                 │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                            AGENT LAYER (Claude SDK)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Framework    │  │  Conversion  │  │   Execution  │  │   Analysis   │     │
│  │   Agent      │  │    Agent     │  │    Agent     │  │    Agent     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘     │
└──────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                              TOOL LAYER (MCP)                                │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    CUSTOM MCP TOOLS (In-Process)                      │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │ BDD         │  │ Framework   │  │ Report      │  │   Skill     │  │    │
│  │  │ Converter   │  │ Generator   │  │ Analyzer    │  │  Manager    │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │             EXTERNAL MCP SERVERS (Subprocess)                        │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │           Microsoft Playwright MCP                            │   │    │
│  │  │  • browser_navigate  • browser_click  • browser_fill          │   │    │
│  │  │  • browser_snapshot   • browser_screenshot  • browser_run_code│   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           FRAMEWORK LAYER                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Behave  │  │pytest-bdd│  │Playwright│  │  Pages   │  │ Reports  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Claude Agent SDK Framework                           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         ClaudeSDKClient                             │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │  │   query()   │  │ receive()   │  │   tools     │                 │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Custom Agents                               │   │
│  │                                                                     │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │   │
│  │  │  FrameworkAgent │  │ ConversionAgent │  │ ExecutionAgent  │     │   │
│  │  │                 │  │                 │  │                 │     │   │
│  │  │ • init()        │  │ • ingest()      │  │ • run()         │     │   │
│  │  │ • create()      │  │ • convert()     │  │ • execute()     │     │   │
│  │  │ • configure()   │  │ • generate()    │  │ • report()      │     │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘     │   │
│  │                                                                     │   │
│  │  ┌─────────────────┐  ┌─────────────────┐                          │   │
│  │  │ AnalysisAgent   │  │   SkillAgent    │                          │   │
│  │  │                 │  │                 │                          │   │
│  │  │ • analyze()     │  │ • invoke()      │                          │   │
│  │  │ • cluster()     │  │ • extend()      │                          │   │
│  │  │ • suggest()     │  │ • manage()      │                          │   │
│  │  └─────────────────┘  └─────────────────┘                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Component Design

### 4.1 CLI Components

#### 4.1.1 Command Structure

```python
# CLI Entry Point
claude-playwright-agent (cpa)
│
├── init          # Initialize new framework
├── ingest        # Ingest Playwright recording
├── run           # Execute BDD tests
├── report        # Generate AI report
├── skills        # Manage Claude Skills
│   ├── list
│   ├── create
│   ├── update
│   └── delete
└── config        # Configuration management
```

#### 4.1.2 Command: `cpa init`

```bash
cpa init <project-name> [OPTIONS]

Options:
  --framework       BDD framework [behave|pytest-bdd] (default: behave)
  --language        Language [python|typescript] (default: python)
  --template        Template [basic|advanced|ecommerce] (default: basic)
  --with-screenshots Enable auto-screenshots
  --with-videos     Enable video recording
  --with-reports    Enable HTML reports
```

**Creates:**
```
project-name/
├── .cpa/                    # CPA configuration
│   ├── config.yaml
│   └── skills/              # Custom skills
├── features/                # BDD feature files
│   └── .gitkeep
├── steps/                   # Step definitions
│   └── __init__.py
├── pages/                   # Page objects
│   └── __init__.py
├── tests/                   # Test files
│   └── __init__.py
├── reports/                 # Test reports
│   └── .gitkeep
├── test_data/               # Test data fixtures
│   └── .gitkeep
├── recordings/              # Playwright recordings
│   └── .gitkeep
├── conftest.py             # Pytest/Behave configuration
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
└── README.md              # Project documentation
```

#### 4.1.3 Command: `cpa ingest`

```bash
cpa ingest <recording-file> [OPTIONS]

Options:
  --feature-name      Name for the feature file (default: extracted from recording)
  --scenario-name     Name for the scenario (default: extracted from recording)
  --tags              Comma-separated tags (e.g., @smoke,@regression)
  --with-pages        Generate page objects
  --self-healing      Enable self-healing locators
```

**Process:**
1. Parse Playwright codegen output
2. Extract user actions and intent
3. Generate Gherkin scenario
4. Create step definitions
5. Optional: Generate page objects
6. Integrate into framework

#### 4.1.4 Command: `cpa run`

```bash
cpa run [OPTIONS] [FILTERS]

Options:
  --tags              Run scenarios by tags
  --feature           Run specific feature
  --browser           Browser [chromium|firefox|webkit]
  --headless          Run headless (default: true)
  --parallel          Number of parallel workers
  --self-heal         Enable self-healing during execution
  --ai-report         Generate AI report after run
```

#### 4.1.5 Command: `cpa skills`

```bash
# List available skills
cpa skills list

# Create new skill
cpa skills create <skill-name>

# Execute skill
cpa skills run <skill-name> [args]

# Update skill
cpa skills update <skill-name>
```

### 4.2 Agent Components

#### 4.2.1 FrameworkAgent

**Responsibility:** Framework initialization and configuration

**Tools:**
- `create_directory_structure` - Creates folder hierarchy
- `generate_config_files` - Generates conftest.py, requirements.txt
- `setup_behave` - Configures Behave framework
- `setup_pytest_bdd` - Configures pytest-bdd framework
- `create_templates` - Creates template files

**System Prompt:**
```
You are a test automation framework architect. Create well-structured,
maintainable test frameworks following industry best practices.

Focus on:
- Clean separation of concerns (features, steps, pages, data)
- Reusable components (page objects, step libraries)
- Clear documentation
- Scalable structure
```

#### 4.2.2 ConversionAgent

**Responsibility:** Convert Playwright recordings to BDD

**Tools:**
- `parse_playwright_script` - Parse codegen output
- `extract_user_actions` - Extract meaningful actions
- `generate_gherkin` - Generate feature file
- `generate_step_definitions` - Generate Python steps
- `generate_page_objects` - Generate page object classes
- `optimize_locators` - Create resilient locators

**System Prompt:**
```
You are a BDD expert. Convert Playwright scripts into clear,
maintainable Gherkin scenarios.

Focus on:
- Business language, not technical details
- Reusable step definitions
- Clear scenario names
- Appropriate use of Background and Scenario Outline
```

#### 4.2.3 ExecutionAgent

**Responsibility:** Execute tests and coordinate with Playwright MCP

**Tools:**
- `load_feature_files` - Load BDD features
- `execute_scenario` - Execute single scenario
- `capture_screenshot` - Capture failure screenshots
- `log_step` - Log step execution
- `handle_failure` - Handle test failures

**System Prompt:**
```
You are a test execution coordinator. Execute BDD scenarios
reliably and capture detailed results.

Focus on:
- Reliable execution
- Clear logging
- Proper failure handling
- Detailed reporting
```

#### 4.2.4 AnalysisAgent

**Responsibility:** Analyze results and generate reports

**Tools:**
- `parse_results` - Parse test results
- `cluster_failures` - Group similar failures
- `analyze_root_cause` - Identify root causes
- `generate_report` - Generate HTML/JSON report
- `suggest_fixes` - Suggest test fixes

**System Prompt:**
```
You are a test analysis expert. Analyze test results and provide
actionable insights.

Focus on:
- Identifying patterns in failures
- Root cause analysis
- Actionable recommendations
- Clear executive summaries
```

### 4.3 MCP Tool Components

#### 4.3.1 Custom MCP Tools (In-Process)

**BDD Converter Tools:**

```python
@tool("parse_playwright_recording", "Parse Playwright codegen output", {
    "recording_path": str
})
async def parse_playwright_recording(args):
    """Parse Playwright recording file"""
    pass

@tool("generate_feature_file", "Generate Gherkin feature file", {
    "actions": list,
    "feature_name": str,
    "scenario_name": str
})
async def generate_feature_file(args):
    """Generate .feature file"""
    pass

@tool("generate_step_definitions", "Generate Python step definitions", {
    "feature_file": str,
    "framework": str
})
async def generate_step_definitions(args):
    """Generate steps.py file"""
    pass
```

**Framework Generator Tools:**

```python
@tool("create_project_structure", "Create project folder structure", {
    "project_name": str,
    "template": str
})
async def create_project_structure(args):
    """Create folder structure"""
    pass

@tool("generate_conftest", "Generate conftest.py", {
    "framework": str,
    "options": dict
})
async def generate_conftest(args):
    """Generate configuration"""
    pass
```

**Report Analyzer Tools:**

```python
@tool("analyze_test_results", "Analyze test results JSON", {
    "results_path": str
})
async def analyze_test_results(args):
    """Analyze and cluster results"""
    pass

@tool("generate_html_report", "Generate HTML report", {
    "analysis": dict,
    "template": str
})
async def generate_html_report(args):
    """Generate report HTML"""
    pass
```

#### 4.3.2 Microsoft Playwright MCP Integration

**Configuration:**
```python
options = ClaudeAgentOptions(
    mcp_servers={
        "playwright": {
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@microsoft/playwright-mcp"]
        }
    },
    allowed_tools=[
        "mcp__playwright__browser_navigate",
        "mcp__playwright__browser_click",
        "mcp__playwright__browser_fill",
        "mcp__playwright__browser_snapshot",
        "mcp__playwright__browser_screenshot",
        "mcp__playwright__browser_run_code"
    ]
)
```

**Available Playwright MCP Tools:**

| Tool | Description | Usage |
|------|-------------|-------|
| `browser_navigate` | Navigate to URL | Load pages |
| `browser_click` | Click element | Interactions |
| `browser_fill` | Fill form fields | Input |
| `browser_snapshot` | Get accessibility tree | Page analysis |
| `browser_screenshot` | Capture screenshot | Documentation |
| `browser_run_code` | Run Playwright code | Advanced actions |

### 4.4 Claude Skills Integration

#### 4.4.1 Skills Architecture

```
.cpa/skills/
├── core/                    # Core skills (built-in)
│   ├── self-healing.skill
│   ├── visual-testing.skill
│   └── api-testing.skill
├── custom/                  # User skills
│   └── .gitkeep
└── shared/                  # Shared skill libraries
    └── .gitkeep
```

#### 4.4.2 Skill Definition Format

```yaml
# skill: self-healing.skill
name: Self-Healing Locator
version: 1.0.0
description: Automatically heal broken locators during test execution

triggers:
  - event: TestFailure
    condition: "error contains 'Element not found'"

actions:
  - name: AnalyzeFailedLocator
    agent: ConversionAgent
    tools:
      - browser_snapshot
      - analyze_dom

  - name: GenerateHealedLocator
    agent: ConversionAgent
    prompt: |
      Generate alternative locators for element: {failed_locator}
      Page context: {page_snapshot}

  - name: ApplyHealedLocator
    action: RetryTest
    with_healed_locator: true

metadata:
  author: "CPA Team"
  category: "reliability"
  tags: ["self-healing", "locators", "automation"]
```

#### 4.4.3 Skill Manager

```python
class SkillManager:
    """Manages Claude Skills lifecycle"""

    def list_skills(self) -> List[Skill]:
        """List all available skills"""
        pass

    def create_skill(self, name: str, config: dict) -> Skill:
        """Create new skill"""
        pass

    def invoke_skill(self, name: str, context: dict) -> dict:
        """Invoke skill by name"""
        pass

    def register_trigger(self, skill: str, trigger: Trigger):
        """Register skill trigger"""
        pass
```

---

## 5. Data Flow

### 5.1 Framework Initialization Flow

```
User                    CLI                   FrameworkAgent          File System
 │                       │                          │                      │
 │ cpa init myproj       │                          │                      │
 │──────────────────────>│                          │                      │
 │                       │ parse arguments           │                      │
 │                       │                          │                      │
 │                       │ create_project()          │                      │
 │                       │─────────────────────────>│                      │
 │                       │                          │ create directories   │
 │                       │                          │─────────────────────>│
 │                       │                          │                      │
 │                       │                          │ generate_config()     │
 │                       │                          │─────────────────────>│
 │                       │                          │                      │
 │                       │                          │ create_templates()    │
 │                       │                          │─────────────────────>│
 │                       │                          │                      │
 │ Framework created ✓    │                          │                      │
 │<──────────────────────│                          │                      │
 │                       │                          │                      │
```

### 5.2 Recording Ingestion Flow

```
User                    CLI                   ConversionAgent          File System
 │                       │                          │                      │
 │ cpa ingest rec.js     │                          │                      │
 │──────────────────────>│                          │                      │
 │                       │ load recording            │                      │
 │                       │                          │                      │
 │                       │ parse_playwright_script() │                      │
 │                       │─────────────────────────>│                      │
 │                       │                          │ parse JS output       │
 │                       │                          │ extract actions       │
 │                       │                          │                      │
 │                       │                          │ generate_gherkin()    │
 │                       │                          │─────────────────────>│
 │                       │                          │                      │
 │                       │                          │ generate_steps()      │
 │                       │                          │─────────────────────>│
 │                       │                          │                      │
 │ Ingested 3 scenarios  │                          │                      │
 │<──────────────────────│                          │                      │
 │                       │                          │                      │
```

### 5.3 Test Execution Flow

```
User                    CLI                   ExecutionAgent           Playwright MCP
 │                       │                          │                         │
 │ cpa run               │                          │                         │
 │──────────────────────>│                          │                         │
 │                       │ load features             │                         │
 │                       │                          │                         │
 │                       │ for each scenario:        │                         │
 │                       │─────────────────────────>│                         │
 │                       │                          │                         │
 │                       │                          │ browser_navigate()       │
 │                       │                          │────────────────────────>│
 │                       │                          │                         │
 │                       │                          │ browser_snapshot()       │
 │                       │                          │────────────────────────>│
 │                       │                          │                         │
 │                       │                          │ browser_click()          │
 │                       │                          │────────────────────────>│
 │                       │                          │                         │
 │                       │                          │ browser_screenshot()     │
 │                       │                          │────────────────────────>│
 │                       │                          │                         │
 │ 15 passed, 2 failed   │                          │                         │
 │<──────────────────────│                          │                         │
 │                       │                          │                         │
 │ cpa report            │                          │                         │
 │──────────────────────>│                          │                         │
 │                       │                          │                         │
```

### 5.4 Skill Invocation Flow

```
Event                   SkillManager              Agent                    Tools
 │                          │                         │                        │
 │ TestFailure              │                         │                        │
 │─────────────────────────>│                         │                        │
 │                          │ find matching skills     │                        │
 │                          │                         │                        │
 │                          │ invoke SelfHealingSkill │                        │
 │                          │────────────────────────>│                        │
 │                          │                         │                        │
 │                          │                         │ browser_snapshot()      │
 │                          │                         │───────────────────────>│
 │                          │                         │                        │
 │                          │                         │ analyze_failure()       │
 │                          │                         │───────────────────────>│
 │                          │                         │                        │
 │                          │                         │ generate_healed_locator()│
 │                          │                         │───────────────────────>│
 │                          │                         │                        │
 │ Healed locator applied   │                         │                        │
 │<─────────────────────────│                         │                        │
```

---

## 6. Integration Points

### 6.1 Microsoft Playwright MCP

**Connection Method:** stdio subprocess

**Configuration:**
```python
mcp_servers={
    "playwright": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@microsoft/playwright-mcp"],
        "env": {
            "HEADLESS": "true"
        }
    }
}
```

**Tool Mapping:**

| CPA Feature | Playwright MCP Tool | Purpose |
|-------------|---------------------|---------|
| Page Load | `browser_navigate` | Navigate to URLs |
| Interaction | `browser_click` | Click elements |
| Input | `browser_fill` | Fill forms |
| Analysis | `browser_snapshot` | Get page state |
| Documentation | `browser_screenshot` | Capture screenshots |
| Custom | `browser_run_code` | Run Playwright code |

### 6.2 Claude Agent SDK

**Integration Pattern:**

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from claude_agent_sdk import tool, create_sdk_mcp_server

# Custom tools (in-process)
custom_server = create_sdk_mcp_server(
    name="cpa-tools",
    version="1.0.0",
    tools=[parse_playwright, generate_feature, ...]
)

# Agent options
options = ClaudeAgentOptions(
    system_prompt=AGENT_SYSTEM_PROMPT,
    mcp_servers={
        "cpa-tools": custom_server,           # In-process
        "playwright": {                        # External
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@microsoft/playwright-mcp"]
        }
    },
    allowed_tools=[
        "mcp__cpa-tools__*",
        "mcp__playwright__*"
    ]
)

# Create agent
async with ClaudeSDKClient(options=options) as agent:
    await agent.query(user_request)
    async for response in agent.receive_response():
        print(response)
```

### 6.3 BDD Framework Integration

**Behave Integration:**

```python
# features/steps/common.py - Generated by CPA
from playwright.sync_api import Page, expect

@given('I am on the login page')
def step_login_page(context):
    context.page.goto(context.config.userdata['base_url'])

@when('I enter "{username}" in the email field')
def step_enter_email(context, username):
    context.page.fill('input[name="email"]', username)

@then('I should be redirected to the dashboard')
def step_dashboard(context):
    expect(context.page).to_have_url('*/dashboard')
```

**pytest-bdd Integration:**

```python
# tests/test_login.py - Generated by CPA
from pytest_bdd import scenario, given, when, then
from playwright.sync_api import Page

@scenario('../features/login.feature', 'Successful login')
def test_successful_login():
    pass

@given('I am on the login page')
def i_am_on_login_page(page: Page):
    page.goto('/login')

@when('I enter valid credentials')
def i_enter_credentials(page: Page):
    page.fill('input[name="email"]', 'user@example.com')
    page.fill('input[name="password"]', 'password123')

@then('I should see the dashboard')
def i_see_dashboard(page: Page):
    assert page.url == '/dashboard'
```

---

## 7. Technology Stack

### 7.1 Core Technologies

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Language** | Python | 3.10+ | Core runtime |
| **Agent Framework** | Claude Agent SDK | latest | AI agent framework |
| **Browser Automation** | Playwright Python | 1.40+ | Browser control |
| **BDD Framework** | Behave / pytest-bdd | latest | BDD test execution |
| **CLI Framework** | Click | 8.1+ | Command-line interface |
| **Config Management** | Pydantic Settings | 2.5+ | Configuration |
| **Async Runtime** | AnyIO | latest | Async operations |

### 7.2 External Dependencies

| Dependency | Purpose |
|------------|---------|
| **Microsoft Playwright MCP** | Browser automation via MCP |
| **Node.js/npx** | Run Playwright MCP server |
| **Claude API** | AI reasoning |

### 7.3 Development Tools

| Tool | Purpose |
|------|---------|
| pytest | Testing |
| black | Code formatting |
| ruff | Linting |
| mypy | Type checking |
| pre-commit | Pre-commit hooks |

---

## 8. User Stories & Requirements

### 8.1 Epic 1: Framework Initialization

**US-1.1: Create Empty Framework**

> As a QA engineer, I want to create a new test automation framework with a single command, so that I don't have to manually set up folder structures and configuration files.

**Acceptance Criteria:**
- [ ] `cpa init my-project` creates complete folder structure
- [ ] Framework includes features/, steps/, pages/, test_data/, reports/ folders
- [ ] Generates conftest.py with default configuration
- [ ] Creates requirements.txt with all dependencies
- [ ] Generates README.md with project documentation
- [ ] Supports `--framework` option (behave, pytest-bdd)
- [ ] Supports `--template` option (basic, advanced)

**US-1.2: Configure Framework**

> As a QA engineer, I want to configure my framework settings, so that tests run with my preferred options.

**Acceptance Criteria:**
- [ ] Creates `.cpa/config.yaml` with default settings
- [ ] Supports browser selection (chromium, firefox, webkit)
- [ ] Supports headless/headed mode
- [ ] Supports base URL configuration
- [ ] Supports timeout configuration
- [ ] Supports parallel execution settings

---

### 8.2 Epic 2: Recording Ingestion

**US-2.1: Parse Playwright Recording**

> As a QA engineer, I want to ingest a Playwright codegen recording, so that I can convert it to BDD scenarios.

**Acceptance Criteria:**
- [ ] `cpa ingest recording.js` parses the Playwright script
- [ ] Extracts all user actions (click, fill, navigate)
- [ ] Identifies page elements and their selectors
- [ ] Captures test intent and flow
- [ ] Handles complex actions (dropdowns, file uploads)

**US-2.2: Generate BDD Scenarios**

> As a QA engineer, I want the AI to convert my recording into Gherkin scenarios, so that I have readable, maintainable test cases.

**Acceptance Criteria:**
- [ ] Generates feature file with proper Gherkin syntax
- [ ] Creates meaningful scenario names
- [ ] Uses business language in step definitions
- [ ] Extracts reusable steps
- [ ] Adds appropriate tags (@smoke, @regression)
- [ ] Generates step definitions in Python
- [ ] Maps steps to Playwright actions

**US-2.3: Generate Page Objects**

> As a QA engineer, I want page objects generated automatically, so that I have maintainable element locators.

**Acceptance Criteria:**
- [ ] Creates page object classes
- [ ] Extracts element locators
- [ ] Creates methods for common interactions
- [ ] Organizes by page/feature
- [ ] Supports self-healing locators

---

### 8.3 Epic 3: Test Execution

**US-3.1: Run All Tests**

> As a QA engineer, I want to run all tests with a single command, so that I can verify my application quickly.

**Acceptance Criteria:**
- [ ] `cpa run` executes all scenarios
- [ ] Shows progress indicators
- [ ] Displays real-time results
- [ ] Supports filtering by tags
- [ ] Supports filtering by feature file
- [ ] Generates output report

**US-3.2: Run Specific Tests**

> As a QA engineer, I want to run specific tests or scenarios, so that I can focus on what I'm developing.

**Acceptance Criteria:**
- [ ] `cpa run --tags @smoke` runs only tagged scenarios
- [ ] `cpa run --feature login.feature` runs specific feature
- [ ] `cpa run --scenario "Login with valid credentials"` runs specific scenario
- [ ] Supports multiple filters

**US-3.3: Self-Healing Execution**

> As a QA engineer, I want tests to automatically heal broken locators, so that my tests don't fail due to minor UI changes.

**Acceptance Criteria:**
- [ ] `cpa run --self-heal` enables self-healing
- [ ] Detects locator failures
- [ ] Attempts alternative locators
- [ ] Logs healing attempts
- [ ] Updates healed locators in page objects

---

### 8.4 Epic 4: Reporting and Analysis

**US-4.1: Generate Test Report**

> As a QA engineer, I want an HTML report of test results, so that I can share outcomes with stakeholders.

**Acceptance Criteria:**
- [ ] `cpa report` generates HTML report
- [ ] Includes pass/fail statistics
- [ ] Shows execution time
- [ ] Includes screenshots for failures
- [ ] Shows feature/scenario breakdown
- [ ] Provides drill-down into failures

**US-4.2: AI Failure Analysis**

> As a QA engineer, I want AI analysis of test failures, so that I can understand root causes quickly.

**Acceptance Criteria:**
- [ ] Analyzes failure patterns
- [ ] Clusters similar failures
- [ ] Identifies root causes
- [ ] Suggests fixes
- [ ] Highlights flaky tests
- [ ] Provides executive summary

---

### 8.5 Epic 5: Claude Skills

**US-5.1: List Available Skills**

> As a QA engineer, I want to see available skills, so that I can discover capabilities.

**Acceptance Criteria:**
- [ ] `cpa skills list` shows all skills
- [ ] Displays skill name and description
- [ ] Shows skill triggers
- [ ] Indicates built-in vs custom skills

**US-5.2: Create Custom Skill**

> As a QA engineer, I want to create custom skills, so that I can extend agent capabilities.

**Acceptance Criteria:**
- [ ] `cpa skills create my-skill` creates skill template
- [ ] Prompts for skill configuration
- [ ] Generates YAML skill file
- [ ] Registers skill in framework

**US-5.3: Invoke Skill**

> As a QA engineer, I want to manually invoke skills, so that I can use them on demand.

**Acceptance Criteria:**
- [ ] `cpa skills run my-skill` invokes skill
- [ ] Passes context to skill
- [ ] Shows skill output
- [ ] Logs skill execution

---

## 9. Implementation Tasks

### Phase 1: Foundation (Week 1-2)

#### Sprint 1.1: Project Setup
| Task ID | Task | Estimate | Dependencies |
|---------|------|----------|--------------|
| T-1.1.1 | Initialize Python project with pyproject.toml | 2h | - |
| T-1.1.2 | Set up directory structure | 1h | T-1.1.1 |
| T-1.1.3 | Configure pre-commit hooks | 1h | T-1.1.1 |
| T-1.1.4 | Set up CI/CD pipeline | 2h | T-1.1.1 |
| T-1.1.5 | Create base Agent class | 3h | T-1.1.2 |

#### Sprint 1.2: CLI Framework
| Task ID | Task | Estimate | Dependencies |
|---------|------|----------|--------------|
| T-1.2.1 | Implement Click CLI skeleton | 2h | T-1.1.1 |
| T-1.2.2 | Implement `cpa --help` and `cpa --version` | 1h | T-1.2.1 |
| T-1.2.3 | Create command routing | 2h | T-1.2.1 |
| T-1.2.4 | Implement configuration loading | 2h | T-1.2.1 |

### Phase 2: Framework Creation (Week 3-4)

#### Sprint 2.1: Framework Generation
| Task ID | Task | Estimate | Dependencies |
|---------|------|----------|--------------|
| T-2.1.1 | Create FrameworkAgent | 4h | T-1.1.5 |
| T-2.1.2 | Implement `create_project_structure` tool | 3h | T-2.1.1 |
| T-2.1.3 | Implement `generate_conftest` tool | 3h | T-2.1.1 |
| T-2.1.4 | Implement `cpa init` command | 3h | T-2.1.2, T-2.1.3 |
| T-2.1.5 | Create templates (basic, advanced) | 4h | T-2.1.2 |

#### Sprint 2.2: Behave Integration
| Task ID | Task | Estimate | Dependencies |
|---------|------|----------|--------------|
| T-2.2.1 | Create Behave configuration | 2h | T-2.1.3 |
| T-2.2.2 | Generate Behave step templates | 3h | T-2.2.1 |
| T-2.2.3 | Create page object templates | 2h | T-2.1.2 |
| T-2.2.4 | Test `cpa init` with Behave | 3h | T-2.1.4 |

### Phase 3: Recording Ingestion (Week 5-6)

#### Sprint 3.1: Playwright Parser
| Task ID | Task | Estimate | Dependencies |
|---------|------|----------|--------------|
| T-3.1.1 | Create ConversionAgent | 3h | T-1.1.5 |
| T-3.1.2 | Implement `parse_playwright_script` tool | 5h | T-3.1.1 |
| T-3.1.3 | Implement `extract_user_actions` tool | 4h | T-3.1.2 |
| T-3.1.4 | Add support for complex actions | 4h | T-3.1.3 |

#### Sprint 3.2: BDD Generation
| Task ID | Task | Estimate | Dependencies |
|---------|------|----------|--------------|
| T-3.2.1 | Implement `generate_gherkin` tool | 4h | T-3.1.3 |
| T-3.2.2 | Implement `generate_step_definitions` tool | 5h | T-3.2.1 |
| T-3.2.3 | Implement `generate_page_objects` tool | 3h | T-3.2.1 |
| T-3.2.4 | Implement `cpa ingest` command | 3h | T-3.2.1, T-3.2.2 |
| T-3.2.5 | Test ingestion with sample recording | 3h | T-3.2.4 |

### Phase 4: Test Execution (Week 7-8)

#### Sprint 4.1: Playwright MCP Integration
| Task ID | Task | Estimate | Dependencies |
|---------|------|----------|--------------|
| T-4.1.1 | Configure Playwright MCP server | 2h | - |
| T-4.1.2 | Test Playwright MCP tools | 3h | T-4.1.1 |
| T-4.1.3 | Create wrapper for Playwright MCP tools | 3h | T-4.1.2 |

#### Sprint 4.2: Execution Engine
| Task ID | Task | Estimate | Dependencies |
|---------|------|----------|--------------|
| T-4.2.1 | Create ExecutionAgent | 3h | T-1.1.5 |
| T-4.2.2 | Implement `execute_scenario` | 5h | T-4.2.1, T-4.1.3 |
| T-4.2.3 | Implement `cpa run` command | 4h | T-4.2.2 |
| T-4.2.4 | Add filtering (tags, features) | 3h | T-4.2.3 |

### Phase 5: Reporting (Week 9)

#### Sprint 5.1: Result Analysis
| Task ID | Task | Estimate | Dependencies |
|---------|------|----------|--------------|
| T-5.1.1 | Create AnalysisAgent | 3h | T-1.1.5 |
| T-5.1.2 | Implement `parse_results` tool | 3h | T-5.1.1 |
| T-5.1.3 | Implement `cluster_failures` tool | 4h | T-5.1.2 |
| T-5.1.4 | Implement `analyze_root_cause` tool | 5h | T-5.1.3 |

#### Sprint 5.2: Report Generation
| Task ID | Task | Estimate | Dependencies |
|---------|------|----------|--------------|
| T-5.2.1 | Implement `generate_html_report` tool | 4h | T-5.1.4 |
| T-5.2.2 | Create HTML report template | 4h | T-5.2.1 |
| T-5.2.3 | Implement `cpa report` command | 2h | T-5.2.1 |
| T-5.2.4 | Test report generation | 2h | T-5.2.3 |

### Phase 6: Claude Skills (Week 10)

#### Sprint 6.1: Skill System
| Task ID | Task | Estimate | Dependencies |
|---------|------|----------|--------------|
| T-6.1.1 | Design skill YAML format | 2h | - |
| T-6.1.2 | Create SkillManager class | 4h | T-6.1.1 |
| T-6.1.3 | Implement `cpa skills list` | 1h | T-6.1.2 |
| T-6.1.4 | Implement `cpa skills create` | 3h | T-6.1.2 |
| T-6.1.5 | Implement `cpa skills run` | 3h | T-6.1.2 |

#### Sprint 6.2: Built-in Skills
| Task ID | Task | Estimate | Dependencies |
|---------|------|----------|--------------|
| T-6.2.1 | Create Self-Healing skill | 5h | T-6.1.2 |
| T-6.2.2 | Create Visual Testing skill | 4h | T-6.1.2 |
| T-6.2.3 | Create API Testing skill | 3h | T-6.1.2 |

### Phase 7: Testing & Polish (Week 11-12)

#### Sprint 7.1: Testing
| Task ID | Task | Estimate | Dependencies |
|---------|------|----------|--------------|
| T-7.1.1 | Unit tests for all agents | 8h | All phases |
| T-7.1.2 | Integration tests for CLI | 6h | All phases |
| T-7.1.3 | E2E test with real website | 4h | All phases |
| T-7.1.4 | Fix bugs from testing | 6h | T-7.1.1, T-7.1.2 |

#### Sprint 7.2: Documentation
| Task ID | Task | Estimate | Dependencies |
|---------|------|----------|--------------|
| T-7.2.1 | Write user guide | 6h | All phases |
| T-7.2.2 | Write API documentation | 4h | All phases |
| T-7.2.3 | Create example tutorials | 4h | All phases |
| T-7.2.4 | Record demo video | 2h | T-7.2.3 |

---

## 10. Security Considerations

### 10.1 API Key Management

```python
# Environment-based configuration
ANTHROPIC_API_KEY: Loaded from .env or environment
CPA_LICENSE_KEY: License validation

# Never log sensitive data
# Mask API keys in logs
# Secure storage for credentials
```

### 10.2 Code Execution Safety

```python
# Validate all inputs before execution
# Sandbox Playwright execution
# Restrict file system access
# Limit network access
```

### 10.3 License Protection

```python
# Hardware-locked licenses
# Online validation
# Offline grace period
# Tamper detection
```

---

## 11. Deployment

### 11.1 Installation Methods

| Method | Command | Use Case |
|--------|---------|----------|
| **PyPI** | `pip install claude-playwright-agent` | Standard |
| **Docker** | `docker pull cpa/agent` | Containerized |
| **Standalone** | Download binary | No Python |

### 11.2 Dependencies Installation

```bash
# After package install
pip install claude-playwright-agent

# Install Playwright browsers
playwright install --with-deps

# Install Playwright MCP (automatic via npx)
npx -y @microsoft/playwright-mcp

# Set up configuration
cpa config init
```

---

## Appendix

### A. Microsoft Playwright MCP Tools Reference

| Tool | Parameters | Returns |
|------|------------|---------|
| `browser_navigate` | url: string | page snapshot |
| `browser_click` | element: string, ref: string | action result |
| `browser_fill` | fields: array | action result |
| `browser_snapshot` | - | accessibility tree |
| `browser_screenshot` | path: string | screenshot data |
| `browser_run_code` | code: string | execution result |

### B. File Structure Reference

```
.cpa/                           # Configuration directory
├── config.yaml                 # Framework configuration
├── skills/                     # Custom skills
│   ├── core/                   # Built-in skills
│   └── custom/                 # User skills
└── state/                      # Runtime state

features/                       # BDD feature files
├── *.feature                   # Gherkin scenarios
└── *.md                        # Feature documentation

steps/                          # Step definitions
├── __init__.py
├── common.py                   # Common steps
└── *.py                        # Feature-specific steps

pages/                          # Page objects
├── __init__.py
└── *.py                        # Page object classes

reports/                        # Test reports
├── html/                       # HTML reports
├── json/                       # JSON results
└── screenshots/                # Failure screenshots

test_data/                      # Test fixtures
├── *.json                      # JSON fixtures
└── *.yaml                      # YAML fixtures

recordings/                     # Playwright recordings
└── *.js                        # Codegen output
```

### C. Configuration Reference

```yaml
# .cpa/config.yaml
framework:
  bdd: behave                    # behave | pytest-bdd
  browser: chromium              # chromium | firefox | webkit
  headless: true
  base_url: https://example.com
  timeout: 30000

execution:
  parallel: 4
  retry: 2
  self_healing: true

recording:
  auto_screenshots: true
  video: false

reporting:
  formats: [html, json]
  include_ai: true

skills:
  enabled: []
  auto_invoke: []
```

---

## 12. Documentation Index

This document provides the system-level design. For detailed specifications, see:

| Document | Purpose |
|----------|---------|
| **[AGENT_ARCHITECTURE.md](AGENT_ARCHITECTURE.md)** | Complete Orchestrator + Specialist Agent architecture with implementation |
| **[SKILLS_CATALOG.md](SKILLS_CATALOG.md)** | Complete reference for all 18 skills across agents |
| **[SKILLS_ARCHITECTURE.md](SKILLS_ARCHITECTURE.md)** | Skills system design and patterns |
| **[COMPONENT_SPECS.md](COMPONENT_SPECS.md)** | Detailed component specifications |
| **[STATE_SCHEMA.md](STATE_SCHEMA.md)** | State management schema (state.json) |
| **[SKILL_DEV_GUIDE.md](SKILL_DEV_GUIDE.md)** | Guide for developing custom skills |
| **[SDK_MAPPING.md](SDK_MAPPING.md)** | Claude Agent SDK Python implementation mapping |
| **[EXAMPLES.md](EXAMPLES.md)** | Development examples and workflows |
| **[API_DESIGN.md](API_DESIGN.md)** | CLI and Agent API design |
| **[DEV_SETUP.md](DEV_SETUP.md)** | Development environment setup |

---

**Document Version:** 1.1
**Last Updated:** 2025-01-11

**Sources:**
- [Microsoft Playwright MCP GitHub](https://github.com/microsoft/playwright-mcp)
- [Claude Agent SDK Python](https://github.com/anthropics/claude-agent-sdk-python)
- [Playwright for Python Documentation](https://playwright.dev/python/)
- [AI Playwright Framework](https://github.com/ksmuvva/ai-playwright-framework)
