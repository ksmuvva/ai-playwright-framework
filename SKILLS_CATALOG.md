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

## 2. Orchestrator Agent Skills

### 2.1 orchestrator-core (e2_1)

**Type:** Core Orchestrator Skill
**Agent:** Orchestrator Agent
**Category:** orchestration
**Epic:** E2 - Multi-Agent Orchestration

**Purpose:** Central coordination system for multi-agent workflows with context propagation

**Capabilities:**
- Workflow orchestration with context propagation
- Agent spawning and task distribution
- Result aggregation with context preservation
- Error handling and recovery with context tracking

**Key Components:**

**ExecutionContext Dataclass:**
```python
@dataclass
class ExecutionContext:
    workflow_id: str                    # Unique workflow identifier
    task_id: str                        # Current task identifier
    parent_context: ExecutionContext    # Parent context for nested workflows
    recording_id: str                   # Associated recording ID
    project_path: str                   # Project root path
    agent_chain: list[str]              # Ordered list of agent IDs
    context_chain: list[str]            # Chain of context IDs
    metadata: dict[str, Any]            # Additional metadata
    created_at: str                     # Creation timestamp
    updated_at: str                     # Last update timestamp
```

**Workflow Orchestration:**
- Create and manage execution contexts
- Spawn child agents with inherited context
- Propagate context through agent chain
- Aggregate results with context preservation

**Usage Example:**
```python
from skills.builtins.e2_1_orchestrator_core import ExecutionContext, OrchestratorCore

# Create root context
context = ExecutionContext(
    task_id="ingest_recording",
    project_path="/path/to/project",
    recording_id="rec_123"
)

# Create child context for nested execution
child_context = context.create_child(
    task_id="parse_actions",
    agent_id="ingestion_agent"
)

# Update metadata
context.update_metadata("file_path", "/recordings/test.spec.js")
context.add_agent("ingestion_agent")
```

**Configuration:**
```yaml
orchestrator_core:
  enabled: true
  max_concurrent_agents: 10
  agent_timeout: 300
  context_propagation: true
```

**Dependencies:**
- e1_2_state_management
- e2_2_lifecycle_management
- e2_3_inter_agent_communication

**Location:**
```
src/claude_playwright_agent/skills/builtins/e2_1_orchestrator_core/
├── __init__.py
├── main.py
└── skill.yaml
```

---

### 2.2 lifecycle-management (e2_2)

**Type:** Orchestrator Skill
**Agent:** Orchestrator Agent
**Category:** orchestration
**Epic:** E2 - Multi-Agent Orchestration

**Purpose:** Manage agent lifecycle from initialization to termination

**Capabilities:**
- Agent initialization and configuration
- Health monitoring and heartbeat tracking
- Graceful shutdown and cleanup
- Agent state management

**Lifecycle States:**
```
INITIALIZING → READY → RUNNING → STOPPING → TERMINATED
                      ↓
                   FAILED
```

**Key Features:**
- Automatic agent discovery and registration
- Health check monitoring with configurable intervals
- Resource cleanup on termination
- State persistence and recovery

**Configuration:**
```yaml
lifecycle_management:
  enabled: true
  health_check_interval: 30
  max_startup_time: 60
  shutdown_timeout: 30
  auto_restart: false
```

**Dependencies:**
- e1_2_state_management
- e2_1_orchestrator_core

**Location:**
```
src/claude_playwright_agent/skills/builtins/e2_2_lifecycle_management/
```

---

### 2.3 inter-agent-communication (e2_3)

**Type:** Communication Skill
**Agent:** Orchestrator Agent
**Category:** orchestration
**Epic:** E2 - Multi-Agent Orchestration

**Purpose:** Enable message passing and communication between agents

**Capabilities:**
- Message queue management
- Publish-subscribe messaging
- Request-response patterns
- Message routing and filtering

**Message Types:**
- **Task Messages:** Assign tasks to agents
- **Result Messages:** Return results from agents
- **Control Messages:** Start/stop/pause agents
- **Event Messages:** Broadcast events

**Usage Example:**
```python
from skills.builtins.e2_3_inter_agent_communication import MessageBus, Message

# Create message bus
bus = MessageBus()

# Send task message
task_message = Message(
    sender="orchestrator",
    receiver="ingestion_agent",
    type="task",
    data={"file_path": "/recordings/test.spec.js"}
)
await bus.send(task_message)

# Subscribe to events
async def on_test_complete(message):
    print(f"Test completed: {message.data}")

bus.subscribe("test_complete", on_test_complete)
```

**Configuration:**
```yaml
inter_agent_communication:
  enabled: true
  message_queue_size: 1000
  message_timeout: 60
  persist_messages: true
```

**Dependencies:**
- e1_2_state_management
- e2_1_orchestrator_core

**Location:**
```
src/claude_playwright_agent/skills/builtins/e2_3_inter_agent_communication/
```

---

### 2.4 task-queue-scheduling (e2_4)

**Type:** Scheduling Skill
**Agent:** Orchestrator Agent
**Category:** orchestration
**Epic:** E2 - Multi-Agent Orchestration

**Purpose:** Schedule and distribute tasks across available agents

**Capabilities:**
- Task queue management
- Priority-based scheduling
- Load balancing across agents
- Task dependency resolution

**Scheduling Strategies:**
- **FIFO:** First-in-first-out
- **Priority:** Higher priority tasks first
- **Round Robin:** Distribute evenly
- **Shortest Job First:** Optimize for speed

**Configuration:**
```yaml
task_queue_scheduling:
  enabled: true
  scheduling_strategy: "priority"
  max_queue_size: 1000
  task_timeout: 300
  retry_failed_tasks: true
  max_retries: 3
```

**Dependencies:**
- e1_2_state_management
- e2_1_orchestrator_core
- e2_3_inter_agent_communication

**Location:**
```
src/claude_playwright_agent/skills/builtins/e2_4_task_queue_scheduling/
```

---

### 2.5 health-monitoring (e2_5)

**Type:** Monitoring Skill
**Agent:** Orchestrator Agent
**Category:** orchestration
**Epic:** E2 - Multi-Agent Orchestration

**Purpose:** Monitor health and performance of all agents

**Capabilities:**
- Agent heartbeat tracking
- Performance metrics collection
- Anomaly detection
- Alert generation

**Monitored Metrics:**
- CPU usage
- Memory usage
- Response time
- Task success rate
- Error rate

**Health States:**
- **HEALTHY:** All metrics normal
- **DEGRADED:** Some metrics elevated
- **UNHEALTHY:** Critical issues detected
- **UNKNOWN:** Agent not responding

**Configuration:**
```yaml
health_monitoring:
  enabled: true
  check_interval: 30
  alert_threshold:
    cpu_percent: 80
    memory_percent: 85
    response_time_ms: 5000
  alert_channel: "console"
```

**Dependencies:**
- e1_2_state_management
- e2_1_orchestrator_core
- e2_2_lifecycle_management

**Location:**
```
src/claude_playwright_agent/skills/builtins/e2_5_health_monitoring/
```

---

## 3. Ingestion Agent Skills

### 3.1 ingestion-agent (e3_1)

**Type:** Core Ingestion Skill
**Agent:** Ingestion Agent
**Category:** ingestion
**Epic:** E3 - Recording Ingestion

**Purpose:** Main entry point for ingesting Playwright recordings

**Capabilities:**
- File validation and parsing
- Recording format detection
- Batch processing
- Error recovery

**Supported Formats:**
- Playwright Python (.py)
- Playwright JavaScript (.js)
- Playwright TypeScript (.ts)
- JSON recordings (.json)

**Usage Example:**
```python
from skills.builtins.e3_1_ingestion_agent import IngestionAgent

agent = IngestionAgent()

# Ingest single file
result = await agent.ingest("/recordings/test.spec.js")

# Ingest batch
results = await agent.ingest_batch([
    "/recordings/test1.spec.js",
    "/recordings/test2.spec.js"
])
```

**Configuration:**
```yaml
ingestion_agent:
  enabled: true
  validate_recording: true
  max_file_size_mb: 10
  batch_size: 50
```

**Dependencies:**
- e1_2_state_management
- e3_2_playwright_parser
- e3_5_ingestion_logging

**Location:**
```
src/claude_playwright_agent/skills/builtins/e3_1_ingestion_agent/
```

### 3.5 ingestion-logging (e3_5)

**Type:** Logging Skill
**Agent:** Ingestion Agent
**Category:** ingestion
**Epic:** E3 - Recording Ingestion

**Purpose:** Detailed logging for ingestion process

**Capabilities:**
- Structured logging
- Log aggregation
- Ingestion metrics tracking
- Debug logging

**Log Levels:**
- DEBUG: Detailed diagnostic information
- INFO: General informational messages
- WARNING: Warning messages for potential issues
- ERROR: Error messages for failures

**Metrics Tracked:**
- Files processed
- Actions extracted
- Errors encountered
- Processing time

**Location:**
```
src/claude_playwright_agent/skills/builtins/e3_5_ingestion_logging/
```

---

## 4. Deduplication Agent Skills

### 4.1 deduplication-agent (e4_1)

**Type:** Core Deduplication Skill
**Agent:** Deduplication Agent
**Category:** deduplication
**Epic:** E4 - Pattern Deduplication

**Purpose:** Coordinate deduplication workflow

**Capabilities:**
- Workflow orchestration
- Pattern detection coordination
- Result aggregation
- Metric collection

**Deduplication Strategies:**
- Exact match detection
- Fuzzy matching
- Pattern similarity
- Behavioral analysis

**Location:**
```
src/claude_playwright_agent/skills/builtins/e4_1_deduplication_agent/
```

### 4.5 selector-catalog (e4_5)

**Type:** Catalog Skill
**Agent:** Deduplication Agent
**Category:** deduplication
**Epic:** E4 - Pattern Deduplication

**Purpose:** Maintain catalog of all selectors for analysis

**Capabilities:**
- Selector indexing
- Usage frequency tracking
- Selector health monitoring
- Selector optimization suggestions

**Catalog Features:**
- Cross-referenced selector database
- Selector variant tracking
- Stability metrics
- Performance analytics

**Location:**
```
src/claude_playwright_agent/skills/builtins/e4_5_selector_catalog/
```

---

## 5. BDD Conversion Agent Skills

### 5.1 bdd-conversion (e5_1)

**Type:** Core BDD Skill
**Agent:** BDD Conversion Agent
**Category:** bdd_conversion
**Epic:** E5 - BDD Test Generation

**Purpose:** Main BDD conversion workflow coordinator

**Capabilities:**
- Gherkin generation orchestration
- Step definition creation
- Scenario optimization
- Feature file management

**Workflow:**
```
Deduplicated Actions → Gherkin Scenarios → Step Definitions → Optimized Features
```

**Configuration:**
```yaml
bdd_conversion:
  enabled: true
  gherkin_language: "en"
  step_definition_style: "behave"
  optimize_scenarios: true
```

**Location:**
```
src/claude_playwright_agent/skills/builtins/e5_1_bdd_conversion/
```

### 5.5 feature-management (e5_5)

**Type:** Management Skill
**Agent:** BDD Conversion Agent
**Category:** bdd_conversion
**Epic:** E5 - BDD Test Generation

**Purpose:** Manage feature files and organization

**Capabilities:**
- Feature file organization
- Tag management
- Feature versioning
- Dependency tracking

**Organization Strategies:**
- By feature/functionality
- By page/section
- By user journey
- Custom organization

**Location:**
```
src/claude_playwright_agent/skills/builtins/e5_5_feature_management/
```

---

## 6. Advanced Recording Skills

### 6.1 advanced-recording (e6_1)

**Type:** Recording Skill
**Agent:** Recording Agent
**Category:** recording
**Epic:** E6 - Advanced Recording Techniques

**Purpose:** Video recording, screenshots, and trace capture with full context

**Capabilities:**
- Video recording (WebM/MP4)
- Screenshot capture (PNG/JPEG)
- Trace files with full context
- Artifact management and cleanup

**Recording Features:**
```python
# Video recording
await page.video.save_as("/ recordings/test.webm")

# Screenshots
await page.screenshot(path="screenshot.png", full_page=True)

# Trace files
context = await browser.new_context(record_trace_dir="/traces")
await context.tracing.start_chunk(title="test chunk")
await context.tracing.stop_chunk(path="/traces/test.zip")
```

**Configuration:**
```yaml
advanced_recording:
  enabled: true
  record_video: true
  capture_screenshots: true
  save_traces: true
  video_size: {width: 1280, height: 720}
  screenshot_type: "png"
```

**Artifacts Generated:**
- videos/ - Test execution videos
- screenshots/ - Failure screenshots
- traces/ - Playwright trace files
- har/ - Network archives

**Dependencies:**
- e1_2_state_management
- e3_1_ingestion_agent
- e3_2_playwright_parser

**Location:**
```
src/claude_playwright_agent/skills/builtins/e6_1_advanced_recording/
├── __init__.py
├── main.py
└── skill.yaml
```

---

### 6.2 network-recording (e6_2)

**Type:** Network Skill
**Agent:** Recording Agent
**Category:** recording
**Epic:** E6 - Advanced Recording Techniques

**Purpose:** Capture and analyze network traffic during test execution

**Capabilities:**
- HAR file generation
- Network request/response logging
- API call tracking
- Performance metrics

**Network Data Captured:**
- Request URLs and methods
- Request/response headers
- Request/response bodies
- Status codes
- Timing information
- Network errors

**Usage Example:**
```python
from skills.builtins.e6_2_network_recording import NetworkRecorder

# Start network recording
recorder = NetworkRecorder(page)
await recorder.start()

# Execute test
await page.click("#load-data")

# Get network logs
logs = await recorder.get_logs()
api_calls = [log for log in logs if log['url'].startswith('/api/')]

# Save HAR file
await recorder.save_har("/network/test.har")
```

**Configuration:**
```yaml
network_recording:
  enabled: true
  save_har_files: true
  capture_bodies: true
  capture_headers: true
  max_body_size_mb: 5
```

**Use Cases:**
- Debug API issues
- Verify API calls
- Performance analysis
- Security testing

**Dependencies:**
- e1_2_state_management
- e3_1_ingestion_agent

**Location:**
```
src/claude_playwright_agent/skills/builtins/e6_2_network_recording/
```

---

### 6.3 visual-regression (e6_3)

**Type:** Visual Testing Skill
**Agent:** Recording Agent
**Category:** recording
**Epic:** E6 - Advanced Recording Techniques

**Purpose:** Visual regression testing with screenshot comparison

**Capabilities:**
- Baseline screenshot capture
- Screenshot comparison
- Difference highlighting
- Visual diff reports

**Comparison Modes:**
- **Exact:** Pixel-perfect comparison
- **Layout:** Ignore content, compare structure
- **Content:** Ignore layout, compare content
- **Fuzzy:** Allow minor differences

**Usage Example:**
```python
from skills.builtins.e6_3_visual_regression import VisualRegression

regression = VisualRegression(page)

# Capture baseline
await regression.capture_baseline("dashboard")

# Compare with baseline
result = await regression.compare("dashboard")

if result.has_differences:
    # View diff report
    await regression.save_diff_report("dashboard_diff.png")
```

**Configuration:**
```yaml
visual_regression:
  enabled: true
  comparison_mode: "fuzzy"
  threshold: 0.1
  ignore_regions:
    - "#dynamic-content"
    - ".timestamp"
```

**Report Features:**
- Side-by-side comparison
- Difference highlighting
- Similarity score
- Accept/reject workflow

**Dependencies:**
- e1_2_state_management
- e6_1_advanced_recording

**Location:**
```
src/claude_playwright_agent/skills/builtins/e6_3_visual_regression/
```

---

### 6.4 performance-recording (e6_4)

**Type:** Performance Skill
**Agent:** Recording Agent
**Category:** recording
**Epic:** E6 - Advanced Recording Techniques

**Purpose:** Performance metrics collection during test execution

**Capabilities:**
- Page load time tracking
- Resource timing analysis
- Core Web Vitals measurement
- Performance bottleneck detection

**Metrics Collected:**
- **Page Load Time:** Time to fully load page
- **Time to First Byte (TTFB):** Server response time
- **First Contentful Paint (FCP):** First visual content
- **Largest Contentful Paint (LCP):** Main content loaded
- **Cumulative Layout Shift (CLS):** Layout stability
- **First Input Delay (FID):** Interactivity

**Usage Example:**
```python
from skills.builtins.e6_4_performance_recording import PerformanceRecorder

recorder = PerformanceRecorder(page)
await recorder.start()

# Navigate to page
await page.goto("https://example.com")

# Get performance metrics
metrics = await recorder.get_metrics()

print(f"LCP: {metrics.lcp}ms")
print(f"CLS: {metrics.cls}")
print(f"FID: {metrics.fid}ms")
```

**Configuration:**
```yaml
performance_recording:
  enabled: true
  collect_core_web_vitals: true
  collect_resource_timing: true
  collect_navigation_timing: true
```

**Performance Reports:**
- Summary metrics
- Resource breakdown
- Timeline visualization
- Bottleneck identification

**Dependencies:**
- e1_2_state_management
- e6_2_network_recording

**Location:**
```
src/claude_playwright_agent/skills/builtins/e6_4_performance_recording/
```

---

### 6.5 recording-enhancement (e6_5)

**Type:** Enhancement Skill
**Agent:** Recording Agent
**Category:** recording
**Epic:** E6 - Advanced Recording Techniques

**Purpose:** Enhance recordings with additional context and metadata

**Capabilities:**
- Automatic wait insertion
- Selector optimization
- Action annotation
- Metadata enrichment

**Enhancements:**
- Add intelligent waits before actions
- Replace fragile selectors with robust ones
- Add comments and descriptions
- Tag actions with business context

**Usage Example:**
```python
from skills.builtins.e6_5_recording_enhancement import RecordingEnhancer

enhancer = RecordingEnhancer()

original_actions = [
    {"action": "click", "selector": "#submit-btn"}
]

# Enhance with intelligent waits and better selectors
enhanced = await enhancer.enhance_actions(original_actions)

# Result:
# {
#   "action": "click",
#   "selector": "data-testid=submit-button",
#   "wait": {"strategy": "smart", "condition": "visible"},
#   "description": "Submit form"
# }
```

**Configuration:**
```yaml
recording_enhancement:
  enabled: true
  add_intelligent_waits: true
  optimize_selectors: true
  add_metadata: true
  add_descriptions: true
```

**Benefits:**
- More reliable tests
- Better documentation
- Self-healing selectors
- Easier maintenance

**Dependencies:**
- e1_2_state_management
- e3_1_ingestion_agent
- e6_6_intelligent_waits

**Location:**
```
src/claude_playwright_agent/skills/builtins/e6_5_recording_enhancement/
```

---

## 7. Custom Skills Support

### 7.1 skill-registry (e7_1)

**Type:** Registry Skill
**Agent:** System
**Category:** custom_skills
**Epic:** E7 - Custom Skills

**Purpose:** Registry for all skills (built-in and custom)

**Capabilities:**
- Skill discovery and registration
- Metadata management
- Dependency resolution
- Version tracking

**Registry Features:**
- Automatic skill discovery
- Skill metadata indexing
- Dependency graph management
- Version compatibility checking

**Location:**
```
src/claude_playwright_agent/skills/builtins/e7_1_skill_registry/
```

---

### 7.2 manifest-parser (e7_2)

**Type:** Parser Skill
**Agent:** System
**Category:** custom_skills
**Epic:** E7 - Custom Skills

**Purpose:** Parse skill.yaml manifest files

**Capabilities:**
- YAML validation
- Schema enforcement
- Metadata extraction
- Dependency parsing

**Manifest Schema:**
```yaml
name: skill_name
version: 1.0.0
description: Skill description
author: Author name
license: MIT
python_dependencies: []
dependencies: []
tags: []
capabilities: []
settings: {}
```

**Location:**
```
src/claude_playwright_agent/skills/builtins/e7_2_manifest_parser/
```

---

### 7.3 custom-skill-support (e7_3)

**Type:** Support Skill
**Agent:** System
**Category:** custom_skills
**Epic:** E7 - Custom Skills

**Purpose:** Framework for creating custom skills

**Capabilities:**
- Skill template generation
- Best practices enforcement
- Testing utilities
- Documentation generation

**Skill Template:**
```python
"""
Custom skill template
"""

from typing import Any, Dict

async def custom_skill(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for custom skill

    Args:
        input_data: Input parameters

    Returns:
        Result dictionary
    """
    # Implementation here
    return {"success": True, "result": {}}
```

**Location:**
```
src/claude_playwright_agent/skills/builtins/e7_3_custom_skill_support/
```

---

### 7.4 lifecycle-management (e7_4)

**Type:** Lifecycle Skill
**Agent:** System
**Category:** custom_skills
**Epic:** E7 - Custom Skills

**Purpose:** Manage custom skill lifecycle

**Capabilities:**
- Skill installation
- Skill updates
- Skill removal
- Skill state management

**Lifecycle States:**
- INSTALLED
- ACTIVE
- INACTIVE
- DEPRECATED

**Location:**
```
src/claude_playwright_agent/skills/builtins/e7_4_lifecycle_management/
```

---

### 7.5 discovery-documentation (e7_5)

**Type:** Documentation Skill
**Agent:** System
**Category:** custom_skills
**Epic:** E7 - Custom Skills

**Purpose:** Automatic documentation generation for skills

**Capabilities:**
- README generation
- API documentation
- Usage examples
- Best practices guide

**Location:**
```
src/claude_playwright_agent/skills/builtins/e7_5_discovery_documentation/
```

---

## 8. CLI & UX Skills

### 8.1 error-handling (e8_1)

**Type:** Error Handling Skill
**Agent:** CLI
**Category:** cli
**Epic:** E8 - CLI & User Experience

**Purpose:** Comprehensive error handling and recovery

**Capabilities:**
- Error categorization
- User-friendly error messages
- Recovery suggestions
- Error code reference

**Error Categories:**
- **VALIDATION_ERROR:** Invalid input
- **FILE_NOT_FOUND:** Missing file
- **PERMISSION_ERROR:** Access denied
- **NETWORK_ERROR:** Connection issues
- **AGENT_ERROR:** Agent failure

**Usage Example:**
```python
from skills.builtins.e8_1_error_handling import ErrorHandler

handler = ErrorHandler()

try:
    await execute_task()
except Exception as e:
    error = handler.handle_error(e)
    print(error.message)
    print(error.suggestion)
    print(error.documentation_link)
```

**Location:**
```
src/claude_playwright_agent/skills/builtins/e8_1_error_handling/
```

---

### 8.2 interactive-prompts (e8_2)

**Type:** Interaction Skill
**Agent:** CLI
**Category:** cli
**Epic:** E8 - CLI & User Experience

**Purpose:** Interactive user prompts for CLI

**Capabilities:**
- Text input prompts
- Confirmation prompts
- Selection prompts
- Multi-select prompts

**Prompt Types:**
```python
from skills.builtins.e8_2_interactive_prompts import Prompts

prompts = Prompts()

# Text input
name = await prompts.text("Enter project name:", default="my-tests")

# Confirmation
confirm = await prompts.confirm("Continue?", default=True)

# Selection
choice = await prompts.select(
    "Choose framework:",
    options=["behave", "pytest-bdd"],
    default="behave"
)

# Multi-select
tags = await prompts.multiselect(
    "Select tags:",
    options=["@smoke", "@regression", "@api"],
    default=["@smoke"]
)
```

**Location:**
```
src/claude_playwright_agent/skills/builtins/e8_2_interactive_prompts/
```

---

### 8.3 cli-help (e8_3)

**Type:** Help Skill
**Agent:** CLI
**Category:** cli
**Epic:** E8 - CLI & User Experience

**Purpose:** Comprehensive help system for CLI

**Capabilities:**
- Command documentation
- Usage examples
- Parameter reference
- Troubleshooting guide

**Help Topics:**
- Command reference
- Configuration options
- Environment variables
- Common issues
- Best practices

**Location:**
```
src/claude_playwright_agent/skills/builtins/e8_3_cli_help/
```

---

### 8.4 progress-feedback (e8_4)

**Type:** Feedback Skill
**Agent:** CLI
**Category:** cli
**Epic:** E8 - CLI & User Experience

**Purpose:** Progress indicators and user feedback

**Capabilities:**
- Progress bars
- Spinners
- Status updates
- Completion summaries

**Feedback Types:**
```python
from skills.builtins.e8_4_progress_feedback import Progress

progress = Progress()

# Progress bar
with progress.bar("Processing files", total=100) as bar:
    for i in range(100):
        # Process file
        bar.advance()

# Spinner
with progress.spinner("Loading..."):
    await load_data()

# Status update
progress.status("Running tests...")
```

**Location:**
```
src/claude_playwright_agent/skills/builtins/e8_4_progress_feedback/
```

---

### 8.5 migration-tools (e8_5)

**Type:** Migration Skill
**Agent:** CLI
**Category:** cli
**Epic:** E8 - CLI & User Experience

**Purpose:** Tools for migrating between framework versions

**Capabilities:**
- Version detection
- Configuration migration
- Code transformation
- Rollback support

**Migration Features:**
- Backup creation
- Incremental migration
- Validation checks
- Migration reports

**Location:**
```
src/claude_playwright_agent/skills/builtins/e8_5_migration_tools/
```

---

## 9. Execution & Reporting Skills

### 9.1 parallel-execution (e9_1)

**Type:** Execution Skill
**Agent:** Execution Agent
**Category:** execution
**Epic:** E9 - Advanced Execution

**Purpose:** Parallel test execution with resource management

**Capabilities:**
- Multi-worker execution
- Load balancing
- Resource isolation
- Synchronization

**Execution Modes:**
- **Parallel:** Run tests simultaneously
- **Sharded:** Split tests across workers
- **Distributed:** Run across multiple machines

**Configuration:**
```yaml
parallel_execution:
  enabled: true
  max_workers: 4
  worker_timeout: 300
  isolation: "context"
  load_balancing: "round_robin"
```

**Usage Example:**
```bash
# Run with 4 parallel workers
cpa run --parallel 4

# Shard tests across 2 workers
cpa run --shard 2/4

# Run on distributed machines
cpa run --distributed --workers 8
```

**Benefits:**
- Faster test execution
- Better resource utilization
- Scalability
- Fault tolerance

**Dependencies:**
- e1_2_state_management
- e2_1_agent_lifecycle
- e5_4_scenario_optimization

**Location:**
```
src/claude_playwright_agent/skills/builtins/e9_1_parallel_execution/
├── __init__.py
├── main.py
└── skill.yaml
```

---

### 9.2 cicd-integration (e9_2)

**Type:** Integration Skill
**Agent:** Execution Agent
**Category:** execution
**Epic:** E9 - Advanced Execution

**Purpose:** CI/CD pipeline integration

**Capabilities:**
- GitHub Actions support
- GitLab CI support
- Jenkins support
- Azure DevOps support

**CI/CD Features:**
- Automatic test execution
- Result reporting
- Artifact collection
- Status notifications

**Configuration Examples:**

**GitHub Actions:**
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          cpa install
          cpa run --parallel 4
```

**GitLab CI:**
```yaml
test:
  script:
    - pip install claude-playwright-agent
    - cpa run
  artifacts:
    when: always
    paths:
      - reports/
```

**Location:**
```
src/claude_playwright_agent/skills/builtins/e9_2_cicd_integration/
```

---

### 9.3 test-reporting (e9_3)

**Type:** Reporting Skill
**Agent:** Execution Agent
**Category:** execution
**Epic:** E9 - Advanced Execution

**Purpose:** Comprehensive test reporting

**Capabilities:**
- HTML reports
- JSON reports
- JUnit XML reports
- Console summaries

**Report Formats:**

**HTML Report:**
- Interactive dashboard
- Screenshots and videos
- Timeline visualization
- Failure analysis

**JSON Report:**
```json
{
  "summary": {
    "total": 100,
    "passed": 95,
    "failed": 5,
    "skipped": 0
  },
  "tests": [...],
  "failures": [...]
}
```

**JUnit XML:**
```xml
<testsuites>
  <testsuite name="login" tests="5" failures="0">
    <testcase name="valid login" status="passed"/>
  </testsuite>
</testsuites>
```

**Configuration:**
```yaml
test_reporting:
  enabled: true
  formats: ["html", "json", "junit"]
  output_dir: "reports"
  include_screenshots: true
  include_videos: true
```

**Location:**
```
src/claude_playwright_agent/skills/builtins/e9_3_test_reporting/
```

---

### 9.4 api-validation (e9_4)

**Type:** Validation Skill
**Agent:** Execution Agent
**Category:** execution
**Epic:** E9 - Advanced Execution

**Purpose:** API validation and testing

**Capabilities:**
- Request/response validation
- Schema validation
- Contract testing
- Performance testing

**Validation Types:**
- **Status Code:** Verify HTTP status
- **Headers:** Validate response headers
- **Body:** Validate response body
- **Schema:** JSON schema validation
- **Contract:** API contract compliance

**Usage Example:**
```python
from skills.builtins.e9_4_api_validation import APIValidator

validator = APIValidator()

# Validate API response
response = await page.request.get("/api/users")
result = validator.validate_response(
    response,
    expected_status=200,
    expected_schema=user_list_schema
)

assert result.valid, result.errors
```

**Configuration:**
```yaml
api_validation:
  enabled: true
  validate_status_codes: true
  validate_schema: true
  validate_contract: true
  performance_threshold_ms: 1000
```

**Location:**
```
src/claude_playwright_agent/skills/builtins/e9_4_api_validation/
```

---

### 9.5 performance-monitoring (e9_5)

**Type:** Monitoring Skill
**Agent:** Execution Agent
**Category:** execution
**Epic:** E9 - Advanced Execution

**Purpose:** Real-time performance monitoring during test execution

**Capabilities:**
- Resource usage tracking
- Response time monitoring
- Bottleneck identification
- Performance trends

**Monitored Metrics:**
- CPU usage per test
- Memory usage per test
- Network I/O
- Test execution time
- API response times

**Performance Reports:**
```json
{
  "summary": {
    "avg_cpu_percent": 45,
    "avg_memory_mb": 512,
    "avg_execution_time_ms": 2500
  },
  "slow_tests": [
    {"name": "test_login", "time_ms": 5000}
  ],
  "resource_hogs": [
    {"name": "test_upload", "memory_mb": 1024}
  ]
}
```

**Configuration:**
```yaml
performance_monitoring:
  enabled: true
  sampling_interval_ms: 100
  alert_thresholds:
    cpu_percent: 80
    memory_mb: 1024
    execution_time_ms: 10000
```

**Benefits:**
- Identify slow tests
- Detect resource leaks
- Optimize test performance
- Capacity planning

**Dependencies:**
- e1_2_state_management
- e6_4_performance_recording
- e9_3_test_reporting

**Location:**
```
src/claude_playwright_agent/skills/builtins/e9_5_performance_monitoring/
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
