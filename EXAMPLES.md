# Development Examples and Workflows

## Document Information

| Field | Value |
|-------|-------|
| **Project** | AI Playwright Automation Agent |
| **Version** | 2.0 |
| **Date** | 2025-01-11 |
| **Status** | Planning Document |

---

## Table of Contents

1. [Overview](#overview)
2. [User Workflows](#user-workflows)
3. [Agent Interactions](#agent-interactions)
4. [Skill Execution Examples](#skill-execution-examples)
5. [State Transitions](#state-transitions)
6. [Error Handling Scenarios](#error-handling-scenarios)
7. [Custom Skill Integration](#custom-skill-integration)
8. [Testing Workflows](#testing-workflows)
9. [MCP Tool Usage](#mcp-tool-usage)

---

## Overview

This document provides comprehensive examples of how the AI Playwright Automation Agent (CPA) operates in various scenarios. These examples illustrate:

- User workflows from CLI to results
- Inter-agent communication patterns
- Skill execution flows
- State management operations
- Error handling and recovery
- Custom skill integration
- Testing strategies

### Example Format

Each example follows this structure:

```yaml
Example:
  title: Descriptive title
  scenario: What is being demonstrated
  prerequisites: Required setup
  steps: Sequential actions
  expected_outcomes: What should happen
  state_changes: How state.json changes
```

---

## User Workflows

### Example 1: First-Time Project Setup

**Title:** Initialize a new CPA project

**Scenario:** User wants to create a new test automation project

**Prerequisites:**
- CPA installed: `pip install claude-playwright-agent`
- Playwright installed: `npm install -g playwright`

**Steps:**

```bash
# Step 1: Create new project
cpa init my-ecommerce-tests

# Output:
# ✓ Created project: my-ecommerce-tests
# ✓ Created .cpa/ directory
# ✓ Initialized state.json
# ✓ Created features/ directory
# ✓ Created pages/ directory
# ✓ Created recordings/ directory
# ✓ Created reports/ directory
# Next: Run 'cd my-ecommerce-tests'
# Next: Record test with 'npx playwright codegen'

# Step 2: Navigate to project
cd my-ecommerce-tests

# Step 3: Verify setup
cpa status

# Output:
# Project: my-ecommerce-tests
# Framework: Behave
# Recordings: 0
# Scenarios: 0
# Test Runs: 0
```

**Expected Outcomes:**
- Project directory created
- `.cpa/state.json` initialized
- Directory structure ready
- CLI confirms successful setup

**State Changes:**

```json
// state.json - Initial state
{
  "project_metadata": {
    "name": "my-ecommerce-tests",
    "created_at": "2025-01-11T10:00:00Z",
    "framework_type": "behave",
    "version": "2.0.0"
  },
  "agent_registry": {
    "active": {},
    "completed": [],
    "failed": []
  },
  "recording_index": [],
  "bdd_registry": {
    "features": [],
    "scenarios": []
  },
  "component_library": {
    "pages": [],
    "components": []
  },
  "execution_log": [],
  "skills_index": {
    "core": ["agent-orchestration", "cli-handler", "state-manager", "error-handler"],
    "custom": []
  },
  "configuration": {
    "bdd_framework": "behave",
    "default_browser": "chromium",
    "headless": true
  }
}
```

---

### Example 2: Recording and Ingesting a Test

**Title:** Record user action and convert to BDD

**Scenario:** User records login flow and converts to BDD scenario

**Prerequisites:**
- CPA project initialized
- Application under test available

**Steps:**

```bash
# Step 1: Start Playwright codegen
npx playwright codegen https://example.com/login --target=javascript

# User performs actions:
# 1. Page loads at https://example.com/login
# 2. Fills username: "test@example.com"
# 3. Fills password: "password123"
# 4. Clicks "Login" button
# 5. Sees dashboard

# Step 2: Save recording (Playwright generates)
# File: recordings/login_flow.js

# Step 3: Ingest recording
cpa ingest recordings/login_flow.js

# Output:
# → Parsing Playwright recording: login_flow.js
# ✓ Extracted 5 actions
# ✓ Analyzed selectors (2 excellent, 3 good)
# → Checking for duplicate elements...
# → Generating BDD scenario...
# ✓ Created feature: features/login.feature
# ✓ Created steps: features/steps/login_steps.py
# ✓ Created page object: pages/login_page.py
# Ingestion complete!
```

**Expected Outcomes:**
- Recording parsed successfully
- BDD feature file generated
- Step definitions created
- Page object model created

**Generated Files:**

```gherkin
# features/login.feature
Feature: User Authentication

  Scenario: Successful login with valid credentials
    Given I am on the login page
    When I enter "test@example.com" as username
    And I enter "password123" as password
    And I click the login button
    Then I should see the dashboard
```

```python
# features/steps/login_steps.py
from behave import given, when, then
from pages.login_page import LoginPage

@given('I am on the login page')
def step_navigate_to_login(context):
    context.login_page = LoginPage(context.page)
    await context.login_page.navigate()

@when('I enter "{email}" as username')
def step_enter_username(context, email):
    await context.login_page.fill_email(email)

@when('I enter "{password}" as password')
def step_enter_password(context, password):
    await context.login_page.fill_password(password)

@when('I click the login button')
def step_click_login(context):
    await context.login_page.click_login()

@then('I should see the dashboard')
def step_verify_dashboard(context):
    assert await context.login_page.is_dashboard_visible()
```

```python
# pages/login_page.py
from pages.base_page import BasePage

class LoginPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.url = "https://example.com/login"
        self.email_input = "#email"
        self.password_input = "#password"
        self.login_button = "role=button[name='Login']"
        self.dashboard = ".dashboard"

    async def navigate(self):
        await self.page.goto(self.url)

    async def fill_email(self, email):
        await self.page.fill(self.email_input, email)

    async def fill_password(self, password):
        await self.page.fill(self.password_input, password)

    async def click_login(self):
        await self.page.click(self.login_button)

    async def is_dashboard_visible(self):
        return await self.page.is_visible(self.dashboard)
```

**State Changes:**

```json
// state.json - After ingestion
{
  "recording_index": [
    {
      "recording_id": "rec_001",
      "file_path": "recordings/login_flow.js",
      "ingested_at": "2025-01-11T10:15:00Z",
      "status": "completed",
      "actions_count": 5
    }
  ],
  "bdd_registry": {
    "features": [
      {
        "feature_id": "feat_001",
        "file_path": "features/login.feature",
        "name": "User Authentication",
        "scenarios": 1
      }
    ],
    "scenarios": [
      {
        "scenario_id": "scen_001",
        "feature_id": "feat_001",
        "name": "Successful login with valid credentials",
        "recording_source": "rec_001"
      }
    ]
  },
  "component_library": {
    "pages": [
      {
        "page_id": "page_001",
        "class_name": "LoginPage",
        "file_path": "pages/login_page.py",
        "selectors": {
          "email_input": "#email",
          "password_input": "#password",
          "login_button": "role=button[name='Login']"
        }
      }
    ]
  }
}
```

---

### Example 3: Running Tests

**Title:** Execute BDD tests and generate report

**Scenario:** User runs tests and views intelligent report

**Prerequisites:**
- BDD scenarios generated
- Application under test accessible

**Steps:**

```bash
# Step 1: Run all tests
cpa run

# Output:
# → Starting test execution...
# → Initializing browser: chromium (headless)
# ✓ Running 1 scenario(s)
#
# Feature: User Authentication
#   Scenario: Successful login with valid credentials
#     ✓ Given I am on the login page
#     ✓ When I enter "test@example.com" as username
#     ✓ When I enter "password123" as password
#     ✓ When I click the login button
#     ✓ Then I should see the dashboard
#
# Results: 1 passed, 0 failed (100% pass rate)
# Duration: 5.2s
# → Generating report...
# ✓ Report: reports/run_20250111_101500/index.html

# Step 2: View report
open reports/run_20250111_101500/index.html

# Output shows:
# - Test execution summary
# - Screenshots of each step
# - Execution video
# - Performance metrics
# - AI-generated insights
```

**Expected Outcomes:**
- Tests execute successfully
- HTML report generated
- Screenshots captured
- Video recording created
- AI analysis included

**Report Structure:**

```
reports/run_20250111_101500/
├── index.html              # Main report
├── screenshots/
│   ├── step_1_given.png    # Screenshot for each step
│   ├── step_2_when.png
│   ├── step_3_when.png
│   ├── step_4_when.png
│   └── step_5_then.png
├── videos/
│   └── scenario_1.webm     # Full execution video
└── analysis.json           # AI-generated insights
```

**AI Analysis (analysis.json):**

```json
{
  "summary": {
    "total": 1,
    "passed": 1,
    "failed": 0,
    "pass_rate": "100%",
    "duration": 5.2
  },
  "performance": {
    "slowest_step": "When I click the login button",
    "slowest_time": 1.8,
    "recommendation": "Consider optimizing page load wait"
  },
  "stability": {
    "status": "stable",
    "flaky_indicators": []
  },
  "coverage": {
    "features_covered": ["User Authentication"],
    "pages_covered": ["LoginPage"],
    "selectors_used": 4
  }
}
```

**State Changes:**

```json
// state.json - After test run
{
  "execution_log": [
    {
      "run_id": "run_001",
      "timestamp": "2025-01-11T10:15:00Z",
      "total": 1,
      "passed": 1,
      "failed": 0,
      "duration": 5.2,
      "report_path": "reports/run_20250111_101500"
    }
  ]
}
```

---

### Example 4: Handling Test Failure with Self-Healing

**Title:** Test fails, self-healing activates

**Scenario:** Button selector changed, test fails, self-healing recovers

**Prerequisites:**
- Test exists with broken selector
- Page has alternative selectors available

**Steps:**

```bash
# Step 1: Run test (will fail due to selector change)
cpa run

# Output:
# → Starting test execution...
#
# Feature: User Authentication
#   Scenario: Successful login with valid credentials
#     ✓ Given I am on the login page
#     ✗ When I click the login button
#       Error: Selector not found: role=button[name='Login']
#
# → Self-healing activated...
# → Attempting fallback selectors...
#   1. Trying: data-testid=login-button → FOUND ✓
#   2. Updated selector in login_steps.py
#   3. Retrying step...
#     ✓ When I click the login button (healed)
#     ✓ Then I should see the dashboard
#
# Results: 1 passed, 0 failed (self-healed)
# → Healing report:
#   Original: role=button[name='Login']
#   Healed: data-testid=login-button
#   Method: data-testid_fallback
#   Auto-applied: true
```

**Expected Outcomes:**
- Test initially fails
- Self-healing finds alternative selector
- Step definition updated automatically
- Test completes successfully
- Healing logged for review

**Healing Report:**

```json
{
  "healing_events": [
    {
      "scenario": "Successful login with valid credentials",
      "step": "When I click the login button",
      "original_selector": "role=button[name='Login']",
      "new_selector": "data-testid=login-button",
      "healing_method": "data-testid_fallback",
      "attempts": 1,
      "auto_applied": true,
      "requires_review": false,
      "confidence": 1.0
    }
  ]
}
```

**State Changes:**

```json
// state.json - Healing recorded
{
  "execution_log": [
    {
      "run_id": "run_002",
      "healed_scenarios": 1,
      "healing_events": [
        {
          "selector": "role=button[name='Login']",
          "healed_to": "data-testid=login-button"
        }
      ]
    }
  ]
}
```

---

## Agent Interactions

### Example 5: Orchestrator Spawning Specialist Agent

**Title:** Ingestion command triggers specialist agent spawn

**Scenario:** User runs `cpa ingest`, Orchestrator spawns IngestionAgent

**Prerequisites:**
- Orchestrator running (daemon mode)
- Recording file exists

**Agent Flow:**

```yaml
Step 1: User Command
  user: cpa ingest test.js
  cli: Parses command → Sends to Orchestrator

Step 2: Orchestrator Processing
  orchestrator_agent:
    receives: {command: "ingest", file: "test.js"}
    cli_handler skill:
      - Validates command
      - Checks file exists
      - Determines required agent: IngestionAgent
    agent_orchestration skill:
      - Checks if IngestionAgent running
      - If not: Spawns new IngestionAgent
      - Creates agent registry entry

Step 3: Agent Spawn
  orchestrator → IngestionAgent:
    message_type: SPAWN
    payload:
      task: ingest_recording
      recording_file: test.js
      agent_id: ingest_agent_001

Step 4: Specialist Agent Execution
  ingestion_agent:
    receives: task from Orchestrator
    skills_executed:
      1. playwright_parser:
         - Input: test.js
         - Output: Parsed actions

      2. action_extractor:
         - Input: Parsed actions
         - Output: Enriched actions with categories

      3. selector_analyzer:
         - Input: Actions with selectors
         - Output: Selector fragility scores

    sends_result: To Orchestrator

Step 5: Result Return
  ingestion_agent → orchestrator:
    message_type: RESPONSE
    payload:
      status: success
      parsed_actions: [...]
      selector_analysis: [...]

Step 6: Orchestrator Updates State
  orchestrator:
    state_manager skill:
      - Updates recording_index
      - Persists to state.json
    sends_response: To CLI
    terminates: IngestionAgent (task complete)

Step 7: CLI Output
  cli: Displays success message to user
```

**Message Flow:**

```yaml
Messages exchanged:

  1. CLI → Orchestrator:
     {
       "type": "REQUEST",
       "from": "cli",
       "to": "orchestrator_agent",
       "payload": {
         "command": "ingest",
         "file": "test.js"
       }
     }

  2. Orchestrator → IngestionAgent (spawn):
     {
       "type": "SPAWN",
       "from": "orchestrator_agent",
       "to": "ingestion_agent",
       "payload": {
         "agent_id": "ingest_agent_001",
         "task": "ingest_recording",
         "recording_file": "test.js"
       }
     }

  3. IngestionAgent → Orchestrator (result):
     {
       "type": "RESPONSE",
       "from": "ingestion_agent",
       "to": "orchestrator_agent",
       "payload": {
         "status": "success",
         "parsed_actions": [...],
         "selector_analysis": [...]
       }
     }

  4. Orchestrator → CLI:
     {
       "type": "RESPONSE",
       "from": "orchestrator_agent",
       "to": "cli",
       "payload": {
         "status": "success",
         "message": "Ingestion complete"
       }
     }
```

---

### Example 6: Multi-Agent Workflow

**Title:** Full pipeline: Ingest → Deduplicate → Convert BDD

**Scenario:** User ingests multiple recordings, agents work in sequence

**Prerequisites:**
- 3 recording files
- Orchestrator running

**Agent Flow:**

```yaml
User Command:
  cpa ingest recordings/*.js

Orchestrator Processing:
  1. cli_handler: Parses glob pattern
  2. Finds 3 files: login.js, search.js, checkout.js
  3. Creates batch processing plan

Sequential Agent Execution:

  Phase 1: Ingestion
    agent: IngestionAgent
    input: 3 recording files
    skills:
      - playwright_parser (x3)
      - action_extractor (x3)
      - selector_analyzer (x3)
    output: Parsed actions for all 3 recordings
    sends_to: Orchestrator

  Phase 2: Deduplication
    agent: DeduplicationAgent
    input: All parsed actions
    skills:
      - element_deduplicator:
         Finds common elements:
         - All use: goto(https://example.com)
         - login.js + checkout.js: Same email input
      - component_extractor:
         Identifies LoginForm component
      - page_object_generator:
         Generates LoginPage class
    output:
      - Common elements list
      - Reusable components
      - Page objects
    sends_to: Orchestrator

  Phase 3: BDD Conversion
    agent: BDDConversionAgent
    input:
      - Deduplicated action sequences
      - Common elements
      - Page objects
    skills:
      - gherkin_generator:
         Creates 3 scenarios
         Extracts background (common navigation)
      - step_definition_creator:
         Generates step definitions
      - scenario_optimizer:
         Merges duplicate patterns
    output:
      - features/auth.feature (with 3 scenarios)
      - features/steps/auth_steps.py
      - pages/login_page.py
    sends_to: Orchestrator

Final State Update:
  state_manager:
    - Updates recording_index (3 entries)
    - Updates bdd_registry (1 feature, 3 scenarios)
    - Updates component_library (1 page, 3 components)

CLI Output:
  ✓ Processed 3 recordings
  ✓ Identified 5 common elements
  ✓ Generated 1 feature file
  ✓ Generated 3 BDD scenarios
  ✓ Created 1 page object class
```

---

## Skill Execution Examples

### Example 7: Parser Skill Execution

**Title:** `playwright-parser` skill processing

**Scenario:** IngestionAgent executes parser skill on recording

**Input Data:**

```javascript
// recordings/login_flow.js
(async () => {
  const { chromium } = require('playwright');

  const browser = await chromium.launch();
  const page = await browser.newPage();

  await page.goto('https://example.com/login');
  await page.locator('#email').fill('test@example.com');
  await page.locator('#password').fill('password123');
  await page.getByRole('button', { name: 'Login' }).click();

  await browser.close();
})();
```

**Skill Execution:**

```yaml
Skill: playwright-parser
Agent: IngestionAgent
Context: Processing login_flow.js

Input:
  {
    "file_path": "recordings/login_flow.js"
  }

Processing Steps:
  1. Read file contents
  2. Parse JavaScript AST
  3. Extract Playwright API calls:
     - page.goto()
     - page.locator().fill()
     - page.getByRole().click()
  4. Normalize selectors to standard format
  5. Classify action types
  6. Output structured actions

Output:
  {
    "success": true,
    "actions": [
      {
        "type": "goto",
        "url": "https://example.com/login",
        "category": "NAVIGATION",
        "line": 8
      },
      {
        "type": "fill",
        "selector": "#email",
        "value": "test@example.com",
        "category": "INTERACTION",
        "line": 9
      },
      {
        "type": "fill",
        "selector": "#password",
        "value": "password123",
        "category": "INTERACTION",
        "line": 10
      },
      {
        "type": "click",
        "selector": "role=button[name='Login']",
        "category": "INTERACTION",
        "line": 11
      }
    ],
    "metadata": {
      "source_file": "login_flow.js",
      "total_actions": 4,
      "parse_errors": []
    }
  }

Execution Time: 0.15s
```

---

### Example 8: Deduplication Skill Execution

**Title:** `element-deduplicator` skill finds common elements

**Scenario:** DeduplicationAgent analyzes multiple recordings for duplicates

**Input Data:**

```json
{
  "recordings": [
    {
      "recording_id": "login_001",
      "actions": [
        {"type": "goto", "url": "https://example.com/login"},
        {"type": "fill", "selector": "#email", "value": "user1@test.com"},
        {"type": "fill", "selector": "#password", "value": "pass1"},
        {"type": "click", "selector": "role=button[name='Login']"}
      ]
    },
    {
      "recording_id": "login_002",
      "actions": [
        {"type": "goto", "url": "https://example.com/login"},
        {"type": "fill", "selector": "#email", "value": "user2@test.com"},
        {"type": "fill", "selector": "#password", "value": "pass2"},
        {"type": "click", "selector": "role=button[name='Login']"}
      ]
    },
    {
      "recording_id": "checkout_001",
      "actions": [
        {"type": "goto", "url": "https://example.com/login"},
        {"type": "fill", "selector": "#email", "value": "buyer@test.com"},
        {"type": "fill", "selector": "#password", "value": "pass3"},
        {"type": "click", "selector": "role=button[name='Login']"}
      ]
    }
  ]
}
```

**Skill Execution:**

```yaml
Skill: element-deduplicator
Agent: DeduplicationAgent

Processing Steps:
  1. Extract all unique selectors across recordings
  2. Apply deduplication rules:
     - EXACT_MATCH: Same selector + action
     - STRUCTURAL: Same pattern, different values
     - NAVIGATION: Same URLs

Deduplication Results:

  Rule: EXACT_MATCH
  Found:
    - goto("https://example.com/login")
      Occurrences: 3 (login_001, login_002, checkout_001)
      Suggestion: Background step

    - click(role=button[name='Login'])
      Occurrences: 3
      Suggestion: Reusable step "When I click the login button"

  Rule: STRUCTURAL_SIMILARITY
  Found:
    - fill("#email", <value>)
      Occurrences: 3
      Pattern: Same selector, different values
      Suggestion: Parameterized step
                "When I enter {email} in email field"

    - fill("#password", <value>)
      Occurrences: 3
      Pattern: Same selector, different values
      Suggestion: Parameterized step
                "When I enter {password} in password field"

Output:
  {
    "common_elements": [
      {
        "id": "common_nav_001",
        "type": "navigation",
        "url": "https://example.com/login",
        "occurrences": 3,
        "recordings": ["login_001", "login_002", "checkout_001"],
        "suggestion": "Background: Given I am on the login page"
      },
      {
        "id": "common_action_001",
        "type": "click",
        "selector": "role=button[name='Login']",
        "occurrences": 3,
        "suggestion": "When I click the login button"
      },
      {
        "id": "param_action_001",
        "type": "fill",
        "selector": "#email",
        "occurrences": 3,
        "pattern": "structural",
        "suggestion": "When I enter {email} in email field"
      },
      {
        "id": "param_action_002",
        "type": "fill",
        "selector": "#password",
        "occurrences": 3,
        "pattern": "structural",
        "suggestion": "When I enter {password} in password field"
      }
    ],
    "reusable_components": [
      {
        "id": "login_form",
        "component_type": "FORM",
        "selectors": {
          "email": "#email",
          "password": "#password",
          "submit": "role=button[name='Login']"
        },
        "occurrences": 3
      }
    ]
  }
```

---

### Example 9: Generator Skill Execution

**Title:** `gherkin-generator` skill creates BDD scenarios

**Scenario:** BDDConversionAgent generates feature file from deduplicated actions

**Input Data:**

```json
{
  "recording": {
    "recording_id": "login_001",
    "actions": [
      {"type": "goto", "url": "https://example.com/login"},
      {"type": "fill", "selector": "#email", "value": "admin@example.com"},
      {"type": "fill", "selector": "#password", "value": "admin123"},
      {"type": "click", "selector": "role=button[name='Login']"}
    ]
  },
  "deduplication_info": {
    "common_navigation": "https://example.com/login",
    "parameterized_fields": {
      "email": "#email",
      "password": "#password"
    }
  }
}
```

**Skill Execution:**

```yaml
Skill: gherkin-generator
Agent: BDDConversionAgent

Processing Steps:
  1. Analyze action sequence
  2. Map actions to Gherkin keywords:
     - goto → Given
     - fill → When
     - click → And
  3. Apply deduplication knowledge:
     - Common nav → Background
     - Parameterized → Scenario Outline
  4. Generate feature file

Output:
  {
    "success": true,
    "feature_file": "features/login.feature",
    "content": "Feature: User Authentication\n\n  Background:\n    Given I am on the login page\n\n  Scenario: Login with admin credentials\n    When I enter \"admin@example.com\" as email\n    And I enter \"admin123\" as password\n    And I click the login button\n    Then I should be logged in",
    "scenarios": [
      {
        "name": "Login with admin credentials",
        "steps": 4
      }
    ]
  }

Generated File (features/login.feature):

  Feature: User Authentication

    Background:
      Given I am on the login page

    Scenario: Login with admin credentials
      When I enter "admin@example.com" as email
      And I enter "admin123" as password
      And I click the login button
      Then I should be logged in
```

---

## State Transitions

### Example 10: Complete State Lifecycle

**Title:** State evolution through full workflow

**Scenario:** Track state.json changes from init to test execution

**State 0: Initial (Empty)**
```json
{
  "project_metadata": null,
  "agent_registry": {"active": {}, "completed": [], "failed": []},
  "recording_index": [],
  "bdd_registry": {"features": [], "scenarios": []},
  "component_library": {"pages": [], "components": []},
  "execution_log": [],
  "skills_index": {"core": [...], "custom": []},
  "configuration": {}
}
```

**State 1: After `cpa init`**
```json
{
  "project_metadata": {
    "name": "my-project",
    "created_at": "2025-01-11T10:00:00Z",
    "framework_type": "behave",
    "version": "2.0.0"
  },
  "configuration": {
    "bdd_framework": "behave",
    "default_browser": "chromium"
  }
  // ... rest unchanged
}
```

**State 2: After `cpa ingest test.js`**
```json
{
  "recording_index": [
    {
      "recording_id": "rec_001",
      "file_path": "recordings/test.js",
      "status": "completed"
    }
  ],
  "bdd_registry": {
    "features": [{"feature_id": "feat_001", "scenarios": 1}],
    "scenarios": [{"scenario_id": "scen_001"}]
  },
  "component_library": {
    "pages": [{"page_id": "page_001", "class_name": "LoginPage"}]
  }
  // ... rest unchanged
}
```

**State 3: After `cpa run`**
```json
{
  "execution_log": [
    {
      "run_id": "run_001",
      "timestamp": "2025-01-11T10:15:00Z",
      "total": 1,
      "passed": 1,
      "failed": 0,
      "duration": 5.2
    }
  ]
  // ... previous state preserved
}
```

---

## Error Handling Scenarios

### Example 11: Recording Parse Error

**Title:** Invalid Playwright recording handled gracefully

**Scenario:** User provides malformed JavaScript file

**Steps:**

```bash
cpa ingest recordings/broken.js

# Output:
# → Parsing Playwright recording: broken.js
# ✗ Parse error: Invalid JavaScript syntax
#
# Details:
#   File: recordings/broken.js
#   Line: 5
#   Error: Unexpected token '{'
#
# Recovery Options:
#   1. Fix the JavaScript syntax
#   2. Re-record with Playwright codegen
#   3. Use example recording as template
#
# → Recording marked as failed in state.json
```

**State Update:**

```json
{
  "recording_index": [
    {
      "recording_id": "rec_002",
      "file_path": "recordings/broken.js",
      "status": "failed",
      "error": "Invalid JavaScript syntax at line 5"
    }
  ]
}
```

---

### Example 12: Agent Timeout Recovery

**Title:** Specialist agent times out, Orchestrator handles recovery

**Scenario:** BDDConversionAgent hangs on large recording

**Handling:**

```yaml
Event: Agent timeout
Agent: BDDConversionAgent
Timeout: 30 seconds

Orchestrator Response:
  1. Detects agent timeout
  2. error_handler skill activates:
     - Logs timeout event
     - Creates agent crash dump
     - Updates agent_registry
  3. Determines recovery action:
     - Large recording → Split into chunks
     - Retry with increased timeout
  4. User notification:
     "Agent timeout. Retrying with 60s timeout..."

Recovery Execution:
  1. Spawn new BDDConversionAgent
  2. Increase timeout to 60s
  3. Retry conversion
  4. Success: Complete conversion

State Update:
  agent_registry:
    active: {}
    completed: ["bdd_conversion_agent_002"]
    failed: ["bdd_conversion_agent_001"]
```

---

## Custom Skill Integration

### Example 13: Adding Custom Skill

**Title:** User adds custom `jira-integration` skill

**Scenario:** Automatically create JIRA tickets for failed tests

**Steps:**

```bash
# Step 1: Create skill directory
mkdir -p skills/jira-integration

# Step 2: Create skill metadata
cat > skills/jira-integration/skill.yaml <<EOF
skill:
  id: jira-integration
  name: JIRA Integration
  version: 1.0.0
  agent: AnalysisAgent
  category: integration

  trigger:
    type: event
    event: TestRunComplete
    condition: failed_tests > 0

  input:
    schema:
      type: object
      properties:
        test_run: object
      required: [test_run]

  output:
    schema:
      type: object
      properties:
        tickets_created: array
EOF

# Step 3: Register skill
cpa add-skill skills/jira-integration

# Output:
# ✓ Registered skill: jira-integration
# ✓ Added to AnalysisAgent
# ✓ Trigger: TestRunComplete with failed_tests > 0

# Step 4: Test with failed run
cpa run --tags @flaky

# Output:
# ...
# Results: 2 passed, 1 failed
# → jira-integration skill triggered
# → Creating JIRA ticket for failed scenario...
# ✓ Created ticket: TEST-101
#   Title: [Automated] Failed: Login with invalid credentials
#   Description: Test failure detected in run_003
```

---

## Testing Workflows

### Example 14: E2E Testing of CPA

**Title:** Test complete CPA workflow

**Scenario:** Behave test validates `init → ingest → run` flow

**Test Feature:**

```gherkin
Feature: CPA End-to-End Workflow

  Scenario: Complete workflow from init to test execution
    Given I have a fresh CPA project
    When I run "cpa init test-project"
    Then the project should be initialized
    And state.json should exist

    When I copy "recordings/login.js" to project
    And I run "cpa ingest recordings/login.js"
    Then BDD files should be generated
    And state.json should contain recording entry

    When I run "cpa run"
    Then tests should execute
    And report should be generated
```

---

## MCP Tool Usage

### Example 15: Playwright MCP Integration

**Title:** ExecutionAgent uses Playwright MCP tools

**Scenario:** Test execution requires browser automation

**Tool Usage:**

```yaml
Agent: ExecutionAgent
MCP Server: microsoft/playwright-mcp

Test Step: "When I click the login button"

Tool Calls:
  1. browser_snapshot:
     - Purpose: Get page state before action
     - Input: {}
     - Output: Page accessibility tree

  2. browser_click:
     - Purpose: Click login button
     - Input:
       - element: "Login button"
       - ref: "role=button[name='Login']"
     - Output: Click result

  3. browser_wait_for:
     - Purpose: Wait for navigation
     - Input:
       - text: "Dashboard"
     - Output: Wait result

  4. browser_snapshot:
     - Purpose: Verify new page state
     - Input: {}
     - Output: Updated page tree

Result: Step execution complete
Duration: 2.3s
```

---

**Document Version:** 1.0
**Last Updated:** 2025-01-11
