# Skills Catalog - Complete Reference

## Document Information

| Field | Value |
|-------|-------|
| **Project** | AI Playwright Automation Agent |
| **Version** | 2.0 |
| **Date** | 2025-01-11 |
| **Status** | Updated Design |

---

## Table of Contents

1. [Orchestrator Skills](#1-orchestrator-skills)
2. [Ingestion Agent Skills](#2-ingestion-agent-skills)
3. [Deduplication Agent Skills](#3-deduplication-agent-skills)
4. [BDD Conversion Agent Skills](#4-bdd-conversion-agent-skills)
5. [Execution Agent Skills](#5-execution-agent-skills)
6. [Analysis Agent Skills](#6-analysis-agent-skills)
7. [Custom Skills](#7-custom-skills)

---

## 1. Orchestrator Skills

### 1.1 agent-orchestration

**Type:** Core Orchestrator Skill
**Agent:** Orchestrator Agent
**Category:** orchestration

**Purpose:** Manage agent lifecycle and communication

**Capabilities:**
- Spawn child agents based on CLI command
- Maintain agent registry (active/completed/failed)
- Message queue for inter-agent communication
- Agent health monitoring
- Workflow coordination

**Configuration:**
```yaml
agent_registry:
  active: {}
  completed: []
  failed: []

message_queue:
  type: in_memory
  max_size: 1000
  persistence: true

workflows:
  ingest_flow:
    - ingestion_agent
    - deduplication_agent
    - bdd_conversion_agent
  run_flow:
    - execution_agent
    - analysis_agent
```

---

### 1.2 cli-handler

**Type:** Core Orchestrator Skill
**Agent:** Orchestrator Agent
**Category:** orchestration

**Purpose:** Parse CLI commands and validate inputs

**Commands:**

| Command | Syntax | Agent | Workflow |
|---------|--------|-------|----------|
| init | `cpa init <project-name>` | None | None |
| ingest | `cpa ingest <recording-file>` | ingestion_agent | ingest_flow |
| run | `cpa run [options]` | execution_agent | run_flow |
| report | `cpa report [test-run-id]` | analysis_agent | None |
| list-skills | `cpa list-skills` | None | None |
| add-skill | `cpa add-skill <skill-path>` | None | None |

**Validation Rules:**
- project-name: Valid Python identifier, no conflicts
- recording-file: Must exist, .js extension
- tags: Must match pattern `@[\w]+`
- parallel: 1-10

---

### 1.3 state-manager

**Type:** Core Orchestrator Skill
**Agent:** Orchestrator Agent
**Category:** orchestration

**Purpose:** Track framework state and agent progress

**State Structure:**
```yaml
project_metadata:
  name: string
  created_at: datetime
  framework_type: string  # behave, pytest-bdd
  version: string

recordings:
  - recording_id: string
    file_path: string
    ingested_at: datetime
    status: string  # pending, processing, completed, failed

scenarios:
  - scenario_id: string
    feature_file: string
    recording_source: string
    created_at: datetime

test_runs:
  - run_id: string
    timestamp: datetime
    total: int
    passed: int
    failed: int
    duration: float

agent_status:
  - agent_id: string
    agent_type: string
    status: string
    start_time: datetime
    end_time: datetime
```

---

### 1.4 error-handler

**Type:** Core Orchestrator Skill
**Agent:** Orchestrator Agent
**Category:** orchestration

**Purpose:** Graceful error handling and user feedback

**Error Types:**

| Error Type | Category | Recovery |
|------------|----------|----------|
| invalid_recording_format | validation | suggest_fix |
| file_not_found | validation | suggest_fix |
| missing_dependencies | environment | install_command |
| agent_timeout | execution | retry_or_skip |
| agent_crash | execution | restart_agent |
| bdd_conversion_failure | conversion | partial_result |

---

## 2. Ingestion Agent Skills

### 2.1 playwright-parser

**Type:** Parser Skill
**Agent:** Ingestion Agent
**Category:** ingestion

**Purpose:** Parse Playwright Codegen JavaScript recordings

**Input:** Playwright codegen .js file

**Output:** Structured action list (JSON)

**Example:**
```javascript
// Input (JS)
await page.goto('https://example.com');
await page.locator('#username').fill('admin');
await page.locator('#password').fill('pass123');
await page.getByRole('button', { name: 'Login' }).click();
```

```json
// Output (JSON)
{
  "actions": [
    {"type": "goto", "url": "https://example.com"},
    {"type": "fill", "selector": "#username", "value": "admin"},
    {"type": "fill", "selector": "#password", "value": "pass123"},
    {"type": "click", "selector": "role=button[name='Login']"}
  ]
}
```

**Pattern Support:**
- `goto(url)` - Navigation
- `click(selector)` - Click element
- `fill(selector, value)` - Fill input
- `select(selector, value)` - Select dropdown
- `check(selector)` - Check checkbox
- `uncheck(selector)` - Uncheck checkbox
- `press(selector, key)` - Press key
- `type(selector, text)` - Type text

---

### 2.2 action-extractor

**Type:** Enrichment Skill
**Agent:** Ingestion Agent
**Category:** ingestion

**Purpose:** Classify and enrich extracted actions

**Action Categories:**

| Category | Actions |
|----------|---------|
| NAVIGATION | goto, goBack, reload |
| INTERACTION | click, fill, select, check, hover, drag |
| ASSERTION | expect, waitFor |
| WAIT | waitForTimeout, waitForSelector |

**Pattern Detection:**
- `login`: fill(username) → fill(password) → click(submit)
- `search`: fill(searchBox) → click(searchButton) → waitFor(results)
- `form`: Multiple fills → click(submit)

**Output Enhancement:**
```json
{
  "type": "fill",
  "category": "INTERACTION",
  "selector": "#username",
  "value": "admin",
  "metadata": {
    "element_type": "text_input",
    "pattern": "login"
  }
}
```

---

### 2.3 selector-analyzer

**Type:** Analysis Skill
**Agent:** Ingestion Agent
**Category:** ingestion

**Purpose:** Analyze and normalize selectors for reliability

**Fragility Score Calculation:**
- 0.0 = Excellent (data-testid)
- 0.1-0.3 = Good (ARIA, ID)
- 0.4-0.6 = Fair (class, structural)
- 0.7+ = Poor (nth-child, deep nesting)

**Example:**
```yaml
Original: "#login-form > div:nth-child(2) > input"

Analysis:
  fragility_score: 0.7
  selector_type: css
  issues:
    - Uses nth-child
    - Deep nesting
  recommendations:
    - "Add data-testid attribute"
    - "Use ID selector if possible"
  alternatives:
    - primary: "role=textbox[name='Username']"
    - fallback: "#username"
    - backup: "input[placeholder='Enter username']"
```

---

## 3. Deduplication Agent Skills

### 3.1 element-deduplicator

**Type:** Deduplication Skill
**Agent:** Deduplication Agent
**Category:** deduplication

**Purpose:** Identify duplicate/common UI elements across recordings

**Strategy:** Rule-based (NO ML/fuzzy matching)

**Deduplication Rules:**

1. **EXACT MATCH:** Same selector + same action type
```yaml
All recordings use: click(role=button[name="Login"])
→ Create reusable step: "When I click the login button"
```

2. **STRUCTURAL SIMILARITY:** Same selector pattern
```yaml
Recording 1: fill("#email", "user1@test.com")
Recording 2: fill("#email", "user2@test.com")
→ Create parameterized step: "When I enter {email} in email field"
```

3. **COMPONENT PATTERN:** Common UI component types
```yaml
All date pickers use: input[type="date"]
→ Extract as: DatePicker class
```

4. **NAVIGATION DEDUP:** Same URLs
```yaml
All recordings start with: goto('https://app.example.com/login')
→ Create: Background step
```

**Output:**
```json
{
  "common_elements": [
    {
      "id": "login_button",
      "selector": "role=button[name='Login']",
      "action": "click",
      "occurrences": 5,
      "recordings": ["login_001", "checkout_002"]
    }
  ],
  "reusable_components": [
    {
      "id": "email_input",
      "selector": "#email",
      "component_type": "text_input",
      "occurrences": 3
    }
  ]
}
```

---

### 3.2 component-extractor

**Type:** Extraction Skill
**Agent:** Deduplication Agent
**Category:** deduplication

**Purpose:** Extract reusable UI components for Page Object Model

**Component Types:**

| Type | Description | Elements |
|------|-------------|----------|
| FORM | Group of inputs + submit button | Multiple fills + submit |
| NAVIGATION | Menu/navbar elements | Links, menu items |
| TABLE | Data grid | Rows, columns, headers |
| MODAL | Popup/dialog | Modal container, content, close |

**Example:**
```yaml
Detected: LoginForm Component

Elements:
  - username_input: "#username"
  - password_input: "#password"
  - submit_button: "role=button[name='Login']"
  - forgot_link: "text='Forgot password?'"

Generated Page Object:
  class LoginForm(BasePage):
      def __init__(self, page):
          self.page = page
          self.username = "#username"
          self.password = "#password"
          self.submit_btn = "role=button[name='Login']"

      async def login(self, username, password):
          await self.page.locator(self.username).fill(username)
          await self.page.locator(self.password).fill(password)
          await self.page.locator(self.submit_btn).click()
```

---

### 3.3 page-object-generator

**Type:** Generation Skill
**Agent:** Deduplication Agent
**Category:** deduplication

**Purpose:** Auto-generate Page Object Model classes

**Generated Structure:**
```
pages/
├── base_page.py           # Base Page Object class
├── login_page.py          # Generated from LoginForm
├── dashboard_page.py      # Generated from Dashboard components
└── common_components.py   # Shared components
```

**Base Page Template:**
```python
class BasePage:
    """Base Page Object class."""

    def __init__(self, page):
        self.page = page
        self.timeout = 30000

    async def wait_for_selector(self, selector, state='visible'):
        """Wait for element."""
        await self.page.wait_for_selector(selector, state=state, timeout=self.timeout)

    async def click(self, selector):
        """Click element."""
        await self.page.click(selector)

    async def fill(self, selector, value):
        """Fill element."""
        await self.page.fill(selector, value)
```

---

## 4. BDD Conversion Agent Skills

### 4.1 gherkin-generator

**Type:** Generation Skill
**Agent:** BDD Conversion Agent
**Category:** bdd_conversion

**Purpose:** Convert action sequences into Gherkin scenarios

**Conversion Logic:**

| Action | Gherkin |
|--------|---------|
| goto('https://app/login') | Given I am on the login page |
| fill('#username', 'admin') | When I enter "admin" as username |
| click('#login-btn') | And I click the login button |
| waitFor('.dashboard') | Then I should see the dashboard |

**Generated Feature:**
```gherkin
Feature: User Authentication

  Scenario: Successful login with valid credentials
    Given I am on the login page
    When I enter "admin" as username
    And I enter "pass123" as password
    And I click the login button
    Then I should see the dashboard
```

**With Deduplication (Parameterized):**
```gherkin
  Scenario Outline: User login
    Given I am on the login page
    When I enter "<username>" as username
    And I enter "<password>" as password
    And I click the login button
    Then I should see the "<expected_page>"

    Examples:
      | username | password | expected_page |
      | admin    | pass123  | dashboard     |
      | user1    | test456  | dashboard     |
```

---

### 4.2 step-definition-creator

**Type:** Generation Skill
**Agent:** BDD Conversion Agent
**Category:** bdd_conversion

**Purpose:** Generate Python step definitions for Gherkin steps

**Generated Steps (Behave):**
```python
from behave import given, when, then
from pages.login_page import LoginPage

@given('I am on the login page')
def step_navigate_to_login(context):
    context.login_page = LoginPage(context.page)
    await context.login_page.navigate()

@when('I enter "{text}" as username')
def step_enter_username(context, text):
    await context.login_page.fill_username(text)

@when('I click the login button')
def step_click_login(context):
    await context.login_page.click_login()

@then('I should see the dashboard')
def step_verify_dashboard(context):
    await context.page.wait_for_selector('.dashboard')
```

**Generated Steps (pytest-bdd):**
```python
from pytest_bdd import given, when, then, scenario
from pages.login_page import LoginPage

@scenario('../features/login.feature', 'Successful login')
def test_successful_login():
    pass

@given('I am on the login page')
def step_navigate_to_login(page):
    page = LoginPage(page)
    page.navigate()

@when('I enter "{text}" as username')
def step_enter_username(page, text):
    page.fill_username(text)
```

---

### 4.3 scenario-optimizer

**Type:** Optimization Skill
**Agent:** BDD Conversion Agent
**Category:** bdd_conversion

**Purpose:** Optimize generated scenarios for maintainability

**Optimizations:**

1. **Extract Background:**
```gherkin
# Before
Scenario A: Login test 1
  Given I navigate to "https://app/login"
  When I fill "#username" with "admin"
  ...

Scenario B: Login test 2
  Given I navigate to "https://app/login"
  When I fill "#username" with "user1"
  ...

# After
Background:
  Given I am on the login page

@smoke @login
Scenario Outline: User login
  When I login with "<username>" and "<password>"
  Then I should see the "<page>"
```

2. **Suggest Tags:**
```gherkin
@smoke @login @authentication
Scenario: User login
```

3. **Merge Duplicates:**
```gherkin
# Detects similar scenarios and merges into Scenario Outline
```

4. **Optimize Verbosity:**
```gherkin
# Verbose: "When I enter the text 'admin' into the username input field"
# Optimized: "When I enter "admin" as username"
```

---

## 5. Execution Agent Skills

### 5.1 test-runner

**Type:** Execution Skill
**Agent:** Execution Agent
**Category:** execution

**Purpose:** Execute BDD scenarios using Behave + Playwright

**Execution Flow:**
1. Load feature files from `features/`
2. Initialize Playwright browser context
3. Run scenarios (sequential or parallel)
4. Collect results (passed/failed/skipped)
5. Generate execution report

**CLI Options:**
```bash
cpa run                    # Run all features
cpa run login              # Run login.feature
cpa run --tags @smoke      # Run smoke tests
cpa run --parallel 4       # Run with 4 workers
```

---

### 5.2 report-generator

**Type:** Reporting Skill
**Agent:** Execution Agent
**Category:** execution

**Purpose:** Generate intelligent test reports with AI analysis

**Report Structure:**
```
reports/
└── run_20250111_143022/
    ├── index.html            # Main report
    ├── screenshots/          # Failure screenshots
    ├── videos/              # Test execution videos
    └── analysis.json        # AI-generated insights
```

**AI-Generated Insights:**
```json
{
  "summary": {
    "total": 10,
    "passed": 7,
    "failed": 3,
    "pass_rate": "70%"
  },
  "failure_analysis": [
    {
      "scenario": "User login with invalid password",
      "reason": "Selector not found: role=button[name='Login']",
      "category": "UI_CHANGE",
      "recommendation": "Update selector to use data-testid",
      "confidence": 0.85
    }
  ],
  "trends": {
    "flaky_tests": ["Search functionality"],
    "stable_tests": ["User login", "Dashboard load"]
  }
}
```

---

### 5.3 failure-analyzer

**Type:** Analysis Skill
**Agent:** Execution Agent
**Category:** execution

**Purpose:** AI-powered root cause analysis of test failures

**Failure Categories:**

| Category | Description | Fix |
|----------|-------------|-----|
| UI_CHANGE | Element selector no longer valid | Use self-healing |
| TIMING_ISSUE | Element not ready when expected | Add explicit wait |
| DATA_ISSUE | Expected data doesn't match | Update test data |
| ENVIRONMENT | Network error, server down | Retry test |

**Example:**
```
Failed Step: "When I click the login button"
Error: "Timeout 30000ms exceeded waiting for locator"

AI Analysis:
  - Button selector changed from 'role=button[name="Login"]'
  - New button found: 'role=button[name="Sign In"]'
  - Confidence: 92%
  - Suggested Fix: Update step definition selector
  - Auto-fix available: Yes
```

---

### 5.4 self-healing

**Type:** Healing Skill
**Agent:** Execution Agent
**Category:** execution

**Purpose:** Automatically fix broken selectors during test execution

**Strategy:** Try fallback selectors when primary fails (NO ML)

**Self-Healing Logic:**
1. Primary selector fails
2. Try fallback selectors in order:
   - data-testid attribute
   - aria-label / role
   - Visible text match
   - Structural position (last resort)
3. If found, update selector in code
4. Log healing action for review

**Example:**
```
Original Selector: "#login-btn"
Failure: Element not found

Healing Attempts:
  1. Try: "data-testid=login-button" → FOUND ✓
  2. Update login_steps.py with new selector
  3. Log: "Healed selector in scenario 'User login'"

Healing Report:
{
  "scenario": "User login",
  "original_selector": "#login-btn",
  "new_selector": "data-testid=login-button",
  "healing_method": "data-testid_fallback",
  "auto_applied": true,
  "requires_review": false
}
```

---

### 5.5 intelligent-waits

**Type:** Wait Management Skill
**Agent:** Execution Agent
**Category:** execution
**Epic:** E6 - Advanced Automation Techniques

**Purpose:** Intelligent wait strategies for robust test automation

**Problem Solved:**
Eliminates flaky tests caused by timing issues by using AI-powered wait strategies that adapt to page conditions.

**Capabilities:**

| Strategy | Description | Best For |
|----------|-------------|----------|
| **explicit_wait** | Wait for specific condition (visible, hidden, enabled, etc.) | Known element states |
| **implicit_wait** | Global wait for all element interactions | General stability |
| **smart_wait** | AI-powered context analysis with multiple fallback strategies | Dynamic content |
| **hybrid_wait** | Combines explicit + smart strategies | Maximum reliability |

**Wait Conditions:**

- `visible` - Element is visible in viewport
- `hidden` - Element is not visible
- `attached` - Element is in DOM
- `detached` - Element removed from DOM
- `enabled` - Element is enabled
- `disabled` - Element is disabled
- `stable` - Element position is stable (no animations)

**Smart Wait Strategies (AI-powered):**

The `smart_wait` analyzes page context and tries multiple strategies in order:

1. **direct_locator** - Direct Playwright wait (fastest)
2. **wait_for_loading_complete** - Wait for loading spinners to disappear
3. **wait_for_network_idle** - Wait for network to be idle
4. **wait_for_animations** - Wait for CSS animations to complete
5. **poll_visibility** - Poll for element visibility
6. **wait_for_dom_content** - Wait for DOM to stabilize
7. **wait_for_attribute** - Wait for data-loaded or data-ready attribute

**Configuration:**
```yaml
intelligent_waits:
  default_timeout: 30000
  implicit_wait_enabled: true
  implicit_wait_duration: 5000
  smart_wait_enabled: true
  context_aware: true
  retry_count: 3
  track_analytics: true
```

**Usage Examples:**

**Example 1: Smart wait for element**
```python
from skills.builtins.e6_6_intelligent_waits import wait_for_element_visible

# Wait for button to be visible (auto-selects best strategy)
await wait_for_element_visible(page, "#submit-button")
```

**Example 2: Explicit wait with condition**
```python
from skills.builtins.e6_6_intelligent_waits import IntelligentWaitsManager, WaitCondition

manager = IntelligentWaitsManager(page)
result = await manager.explicit_wait(
    selector="#modal",
    condition=WaitCondition.VISIBLE,
    timeout=30000
)
if result.success:
    print(f"Wait completed in {result.duration_ms}ms")
```

**Example 3: Smart wait with context analysis**
```python
# AI analyzes page and tries optimal strategies
result = await manager.smart_wait(
    selector="#dynamic-content",
    condition=WaitCondition.VISIBLE,
    timeout=30000,
    retry_count=3
)
# Result includes which strategy succeeded
print(f"Strategy used: {result.optimizations}")
```

**Example 4: Hybrid wait for maximum reliability**
```python
# Try explicit first, fall back to smart
result = await manager.hybrid_wait(
    selector="#slow-element",
    condition=WaitCondition.ENABLED,
    timeout=30000
)
```

**Example 5: Wait for page load**
```python
from skills.builtins.e6_6_intelligent_waits import wait_for_page_load

# Wait for network idle
await wait_for_page_load(page, timeout=30000)
```

**Example 6: Wait for text content**
```python
from skills.builtins.e6_6_intelligent_waits import wait_for_text

# Wait for element to contain specific text
success = await wait_for_text(
    page,
    selector="#message",
    text="Success",
    timeout=10000
)
```

**Analytics & Optimization:**

The skill tracks wait patterns and provides optimization suggestions:

```python
# Get analytics summary
analytics = manager.get_analytics_summary()
print(f"Total waits: {analytics['total_waits']}")
print(f"Success rate: {analytics['success_rate']:.1%}")
print(f"Average wait time: {analytics['average_wait_ms']:.0f}ms")
print(f"Recommended timeout: {analytics['recommended_timeout_ms']}ms")

# Get optimization suggestions
suggestions = manager.get_optimization_suggestions()
for suggestion in suggestions:
    print(f"Suggestion: {suggestion}")
```

**Example Analytics Output:**
```json
{
  "total_waits": 150,
  "successful_waits": 142,
  "failed_waits": 8,
  "success_rate": 0.947,
  "total_wait_time_ms": 1250000,
  "average_wait_ms": 8333,
  "recommended_timeout_ms": 15000,
  "optimization_suggestions": [
    "Average wait time (8333ms) is optimal",
    "Success rate is excellent (94.7%)",
    "Consider reducing timeout to 15000ms for faster test failures"
  ]
}
```

**Benefits:**

- ✅ **Eliminates flaky tests** - Adapts to network and page conditions
- ✅ **Faster execution** - Uses optimal strategy, not fixed delays
- ✅ **Better debugging** - Detailed analytics and suggestions
- ✅ **Self-optimizing** - Learns from historical wait times
- ✅ **Context-aware** - Detects loading indicators, animations, network state

**Integration with BasePage:**

The intelligent waits are automatically available in BasePage:

```python
# In page objects
from pages.base_page import BasePage

class MyPage(BasePage):
    def wait_for_submit_button(self):
        # Uses intelligent wait automatically
        self.assert_visible("#submit-button")

    def wait_for_modal_to_close(self):
        # Smart wait for element to disappear
        self.wait_for_selector("#modal", state="hidden")
```

**Technical Details:**

- **Context Analysis**: Evaluates page load state, network idle, element visibility, loading indicators, animations
- **Strategy Selection**: Chooses optimal strategy based on context
- **Fallback Mechanism**: Tries multiple strategies in sequence
- **Performance Tracking**: Records wait times for optimization
- **Dynamic Timeouts**: Adjusts based on network conditions

**Dependencies:**
- Playwright async API
- Python 3.8+ asyncio support
- No external ML dependencies

**Location:**
```
src/claude_playwright_agent/skills/builtins/e6_6_intelligent_waits/
├── __init__.py
├── main.py
└── skill.yaml
```

---

## 6. Analysis Agent Skills

### 6.1 failure-clustering

**Type:** Analysis Skill
**Agent:** Analysis Agent
**Category:** analysis

**Purpose:** Group similar failures for analysis

**Clustering Rules:**
- By error message
- By selector
- By page/feature
- By timing pattern

---

### 6.2 trend-analysis

**Type:** Analysis Skill
**Agent:** Analysis Agent
**Category:** analysis

**Purpose:** Analyze test trends over time

**Metrics:**
- Pass rate trends
- Flaky test detection
- Performance degradation
- Coverage changes

---

### 6.3 executive-summary

**Type:** Reporting Skill
**Agent:** Analysis Agent
**Category:** analysis

**Purpose:** Generate business-friendly summaries

**Output:** Markdown summary with:
- Overall health
- Risk assessment
- Recommendations
- Action items

---

## 7. Custom Skills

### 7.1 jira-integration

**Type:** Integration Skill
**Category:** integration

**Purpose:** Create JIRA tickets for test failures

**Triggers:** TestRunComplete with failed tests

---

### 7.2 slack-notifications

**Type:** Integration Skill
**Category:** integration

**Purpose:** Send test results to Slack

**Triggers:** TestRunComplete

---

### 7.3 custom-assertions

**Type:** Custom Skill
**Category:** custom

**Purpose:** Domain-specific assertion helpers

**Examples:**
- validate_email_format
- validate_phone_number
- validate_currency

---

## Skills Summary Matrix

| Skill | Agent | Category | Trigger |
|-------|-------|----------|---------|
| agent-orchestration | Orchestrator | orchestration | Always |
| cli-handler | Orchestrator | orchestration | CLI command |
| state-manager | Orchestrator | orchestration | State access |
| error-handler | Orchestrator | orchestration | Error |
| playwright-parser | Ingestion | ingestion | cpa ingest |
| action-extractor | Ingestion | ingestion | After parser |
| selector-analyzer | Ingestion | ingestion | After extractor |
| element-deduplicator | Deduplication | deduplication | After ingestion |
| component-extractor | Deduplication | deduplication | After dedup |
| page-object-generator | Deduplication | deduplication | After extractor |
| gherkin-generator | BDD Conversion | bdd_conversion | After deduplication |
| step-definition-creator | BDD Conversion | bdd_conversion | After gherkin |
| scenario-optimizer | BDD Conversion | bdd_conversion | After steps |
| test-runner | Execution | execution | cpa run |
| failure-analyzer | Execution | execution | On failure |
| self-healing | Execution | execution | On selector fail |
| report-generator | Execution | execution | After run |
| failure-clustering | Analysis | analysis | After run |
| trend-analysis | Analysis | analysis | After run |
| executive-summary | Analysis | analysis | After run |

---

**Document Version:** 2.0
**Last Updated:** 2025-01-11
