# State Management Schema Design

## Document Information

| Field | Value |
|-------|-------|
| **Project** | AI Playwright Automation Agent |
| **Version** | 2.0 |
| **Date** | 2025-01-11 |
| **Status** | Design (Planning Phase) |

---

## Table of Contents

1. [Schema Overview](#1-schema-overview)
2. [Root Level Structure](#2-root-level-structure)
3. [Section Definitions](#3-section-definitions)
4. [State Update Patterns](#4-state-update-patterns)
5. [Validation Rules](#5-validation-rules)
6. [State Lifecycle](#6-state-lifecycle)
7. [Migration Strategy](#7-migration-strategy)

---

## 1. Schema Overview

### 1.1 Design Principles

| Principle | Description |
|-----------|-------------|
| **Single Source of Truth** | All framework state in one file |
| **Atomic Updates** | Lock-based writes prevent corruption |
| **Version Controlled** | Schema version enables migration |
| **Traceable** | Every change auditable |
| **Incremental** | Support parallel agent operations |
| **Minimal Size** | Keep state.json < 100KB for performance |

### 1.2 State Location

```
Project Root
└── .cpa/
    ├── state.json              # Primary state file
    ├── state.lock              # Write lock
    ├── state.backup.json       # Automatic backup
    ├── events/                 # Event log (optional)
    │   └── events.log
    └── agent-logs/             # Agent execution logs
        ├── ingestion_agent_001.log
        └── deduplication_agent_002.log
```

### 1.3 Schema Versioning

```
Format: "MAJOR.MINOR.PATCH"

MAJOR: Breaking changes (requires migration script)
MINOR: Additive changes (backward compatible)
PATCH: Bug fixes

Current: "2.0.0"

Example Migration:
  1.0.0 → 2.0.0: Add agent_registry section
  2.0.0 → 2.1.0: Add skills_index section
```

---

## 2. Root Level Structure

### 2.1 Complete Schema

```yaml
# Root level keys
schema_version: "2.0.0"

# Core sections
project_metadata: {}      # Project information (immutable)
agent_registry: {}       # Active/queued/completed agents
recording_index: {}      # All recordings and their status
bdd_registry: {}         # Features, scenarios, steps
component_library: {}    # Page objects and components
execution_log: {}        # Test runs and results
skills_index: {}         # Installed skills
configuration: {}         # Runtime settings

# Optional sections (future)
ci_integration: {}        # GitHub Actions, Jenkins, etc
telemetry: {}            # Anonymous usage metrics
cache: {}                # Computed data, can be rebuilt
```

### 2.2 Section Relationships

```
                    ┌─────────────────────────────────────┐
                    │          project_metadata          │
                    │   (immutable, created once)        │
                    └─────────────────────────────────────┘
                                      │
        ┌─────────────────────────────────────────────┴──────────────┐
        │                                                             │
        ▼                                                             ▼
┌───────────────────┐                                       ┌───────────────────┐
│   agent_registry   │───────────────────────────────────────────│  recording_index   │
│ (ephemeral, runtime)│                                       │ (persistent data)  │
└───────────────────┘                                       └───────────────────┘
        │                                                             │
        └─────────────────────────────────────────────────────────────┘
                                      │
        ┌─────────────────────────────────────┴──────────────────────────┐
        │                                                               │
        ▼                                                               ▼
┌───────────────────┐                                       ┌───────────────────┐
│   skills_index     │───────────────────────────────────────────────│  bdd_registry       │
│ (skill inventory)  │                                       │ (generated content)│
└───────────────────┘                                       └───────────────────┘
        │                                                             │
        └─────────────────────────────────────────────────────────────┘
                                      │
        ┌─────────────────────────────────────┴──────────────────────────┐
        │                                                               │
        ▼                                                               ▼
┌───────────────────┐                                       ┌───────────────────┐
│ component_library  │───────────────────────────────────────────────│  execution_log       │
│ (reusable assets)  │                                       │ (test history)       │
└───────────────────┘                                       └───────────────────┘
        │                                                             │
        └─────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                            ┌───────────────────────────┐
                            │      configuration        │
                            │   (runtime settings)      │
                            └───────────────────────────┘
```

---

## 3. Section Definitions

### 3.1 project_metadata

**Purpose:** Core project information (immutable after creation)

```yaml
project_metadata:
  # Immutable fields
  project_name: "my-ecommerce-tests"
  project_id: "proj_abc123"           # UUID
  created_at: "2025-01-11T14:30:22Z"
  created_by: "orchestrator_agent"
  framework_version: "2.0.0"
  framework_type: "behave"             # behave | pytest-bdd

  # Auto-updated fields
  last_modified: "2025-01-11T16:45:30Z"

  # File paths
  project_root: "/home/user/my-ecommerce-tests"

  # Version control
  git_integration:
    enabled: true
    repository: "https://github.com/user/tests.git"
    current_branch: "main"
    last_commit: "abc123def456"

  # Dependencies
  dependencies:
    playwright: "1.48.0"
    pytest: "8.0.0"
    behave: "1.2.6"
    claude-agent-sdk: "0.1.0"
```

**Key Decisions:**
- `project_id` is UUID for unique identification
- `created_at` never changes
- `last_modified` updated on any state change
- Dependencies tracked for reproducibility

---

### 3.2 agent_registry

**Purpose:** Track active, queued, and completed agent executions

```yaml
agent_registry:
  # Currently running agents (cleared on completion)
  active_agents:
  - agent_id: "ingestion_agent_001"
    agent_type: "ingestion"
    pid: 12345
    status: "running"
    task: "parse_recording"
    current_file: "recordings/checkout.js"
    started_at: "2025-01-11T16:40:00Z"
    health_check_interval: 30
    last_heartbeat: "2025-01-11T16:42:00Z"

  # Queued tasks waiting for execution
  task_queue:
  - task_id: "task_002"
    task_type: "deduplication"
    priority: "normal"            # low | normal | high
    dependencies: ["ingestion_agent_001"]
    context:
      input_file: ".cpa/recordings/checkout_001_actions.json"
    status: "queued"
    queued_at: "2025-01-11T16:41:00Z"

  # Historical record of all agent executions
  agent_history:
  - agent_id: "ingestion_agent_000"
    agent_type: "ingestion"
    status: "completed"
    task: "parse_recording"
    file_processed: "recordings/login.js"
    started_at: "2025-01-11T14:30:00Z"
    completed_at: "2025-01-11T14:32:15Z"
    duration_seconds: 135
    output:
      actions_extracted: 8
      output_file: ".cpa/recordings/login_001_actions.json"
    errors: []
    resource_usage:
      memory_mb: 128
      cpu_percent: 15

  # Lightweight message log (full messages in agent-logs/)
  communication_log:
  - message_id: "msg_001"
    from: "ingestion_agent_000"
    to: "orchestrator"
    message_type: "TASK_COMPLETE"
    timestamp: "2025-01-11T14:32:15Z"
    payload_hash: "sha256:abcd1234..."
```

**Key Decisions:**
- `active_agents` limited to `max_concurrent_agents` from config
- `task_queue` enables dependency tracking
- `agent_history` provides audit trail (never deleted)
- `communication_log` is lightweight (hash only, not full payload)

---

### 3.3 recording_index

**Purpose:** Track all recordings from ingestion through BDD conversion

```yaml
recording_index:
  # All ingested recordings
  recordings:
  - recording_id: "login_001"
    original_file: "recordings/login.js"
    file_hash: "sha256:xyz789..."
    ingested_at: "2025-01-11T14:32:15Z"
    ingested_by: "ingestion_agent_000"
    status: "converted"           # uploaded → processing → processed → converted → failed
    processing_stage: "bdd"       # ingestion → deduplication → bdd

    # Metadata extracted by ingestion skills
    metadata:
      total_actions: 8
      action_types:
        navigation: 1
        fill: 2
        click: 1
        wait: 1
        assertion: 3
      pages_involved:
        - "https://app.example.com/login"
      duration_estimate_seconds: 15
      detected_pattern: "login"

    # Output files
    artifacts:
      actions_file: ".cpa/recordings/login_001_actions.json"
      feature_file: "features/login.feature"
      step_file: "features/steps/login_steps.py"

    # Linked BDD content
    converted_scenarios: ["scenario_001", "scenario_002"]

  # Deduplication results (shared across recordings)
  deduplication_map:
    common_elements:
    - element_id: "elem_001"
      selector: "role=button[name='Login']"
      action_type: "click"
      component_type: "button"
      occurrences: 5
      found_in_recordings: ["login_001", "checkout_002", "profile_003"]
      reusable_component: "common_components.LoginButton"
      step_definition: "When I click the login button"
      confidence: 0.95

    common_flows:
    - flow_id: "flow_001"
      flow_name: "user_authentication"
      action_sequence: ["goto_login", "fill_username", "fill_password", "click_login"]
      found_in_recordings: ["login_001", "checkout_002"]
      gherkin_background: "Given I am logged in as a user"
      extracted_as: "Background"

    # URL-based page groupings
    page_contexts:
    - url: "https://app.example.com/login"
      page_id: "page_001"
      page_name: "Login Page"
      recordings: ["login_001", "login_002", "checkout_002"]
      elements: ["elem_001", "elem_002", "elem_003"]

  # Audit log for each recording
  ingestion_log:
  - recording_id: "login_001"
    event: "ingestion_started"
    timestamp: "2025-01-11T14:30:00Z"
    agent: "ingestion_agent_000"
    details: {}

  - recording_id: "login_001"
    event: "actions_extracted"
    timestamp: "2025-01-11T14:31:30Z"
    agent: "ingestion_agent_000"
    details:
      action_count: 8

  - recording_id: "login_001"
    event: "deduplication_applied"
    timestamp: "2025-01-11T14:32:00Z"
    agent: "deduplication_agent_000"
    details:
      common_elements_found: 2
      flows_extracted: 1
```

**Key Decisions:**
- Recording status enum: `uploaded | processing | processed | converted | failed`
- Processing stage enum: `ingestion | deduplication | bdd | completed`
- Deduplication map is shared across all recordings
- Each recording linked to generated BDD artifacts

---

### 3.4 bdd_registry

**Purpose:** Track generated features, scenarios, and step definitions

```yaml
bdd_registry:
  # Feature files
  features:
  - feature_id: "feat_001"
    feature_name: "User Authentication"
    file_path: "features/login.feature"
    created_at: "2025-01-11T14:35:00Z"
    created_by: "bdd_conversion_agent_001"
    source_recordings: ["login_001"]
    tags: ["@smoke", "@authentication"]
    scenarios: ["scenario_001", "scenario_002"]
    description: "User login and authentication flows"

  # Individual scenarios
  scenarios:
  - scenario_id: "scenario_001"
    scenario_name: "Successful login with valid credentials"
    scenario_type: "scenario"       # scenario | scenario_outline
    feature_id: "feat_001"
    line_number: 5
    tags: ["@smoke"]

    # Step references
    steps:
    - step_id: "step_001"
      step_type: "given"
      step_text: "I am on the login page"
      step_definition_id: "stepdef_001"
      line_number: 6

    - step_id: "step_002"
      step_type: "when"
      step_text: "I enter \"{username}\" as username"
      step_definition_id: "stepdef_002"
      line_number: 7
      parameters: ["username"]

    # Page objects used
    mapped_page_objects: ["LoginPage"]

    # Source traceability
    source_recording: "login_001"
    source_actions: ["action_001", "action_002", "action_003"]

    # Execution history
    execution_history:
    - run_id: "run_001"
      status: "passed"
      duration_seconds: 12.5
      executed_at: "2025-01-11T15:00:00Z"
      browser: "chromium"
      failure_reason: null

  # Step definitions
  step_definitions:
  - step_def_id: "stepdef_001"
    step_pattern: "I am on the login page"
    step_type: "given"
    file_path: "features/steps/login_steps.py"
    function_name: "step_navigate_to_login"
    uses_page_object: "LoginPage"
    parameters: []

    # Reusability tracking
    reusable: true
    used_in_scenarios: ["scenario_001", "scenario_004", "scenario_007"]
    total_uses: 3

    # Page object method binding
    page_object_method: "LoginPage.navigate"

  # Scenario outlines (parameterized)
  scenario_outlines:
  - outline_id: "outline_001"
    feature_id: "feat_001"
    scenario_name: "User login"
    examples_table:
      headers: ["username", "password", "expected_page"]
      rows:
      - ["admin", "pass123", "dashboard"]
      - ["user1", "test456", "dashboard"]
      - ["user2", "test789", "profile"]

    generated_scenarios: 3
    parameter_binding: "steps/parameterized_steps.py"
```

**Key Decisions:**
- Bidirectional linking: Features ↔ Scenarios ↔ Steps ↔ Page Objects
- Execution history enables flakiness detection
- Reusability tracking identifies common steps
- Full traceability back to source recordings

---

### 3.5 component_library

**Purpose:** Page objects, reusable components, and selector catalog

```yaml
component_library:
  # Page object classes
  page_objects:
  - page_object_id: "po_001"
    class_name: "LoginPage"
    file_path: "pages/login_page.py"
    page_url_pattern: "https://app.example.com/login"
    base_class: "BasePage"

    # Elements defined in this page object
    elements:
    - element_name: "username_input"
      selector: "#username"
      selector_type: "css"
      primary: true
      fallback_selectors:
        - "data-testid=username-field"
        - "input[placeholder='Username']"
        - "role=textbox[name='username']"
      element_type: "text_input"
      fragility_score: 0.3
      self_healing_enabled: true

    - element_name: "password_input"
      selector: "#password"
      selector_type: "css"
      primary: true
      fallback_selectors:
        - "data-testid=password-field"
        - "input[type='password']"
      element_type: "password_input"
      fragility_score: 0.2

    - element_name: "login_button"
      selector: "role=button[name='Login']"
      selector_type: "role"
      primary: true
      fallback_selectors: []
      element_type: "button"
      fragility_score: 0.1

    # Methods defined in this page object
    methods:
    - method_name: "login"
      parameters: ["username", "password"]
      return_type: "void"
      description: "Performs login with given credentials"
      used_in_steps: ["stepdef_003", "stepdef_004"]

    - method_name: "navigate"
      parameters: []
      return_type: "void"
      description: "Navigate to login page"
      used_in_steps: ["stepdef_001"]

    # Metadata
    created_by: "page_object_generator_skill"
    created_at: "2025-01-11T14:33:00Z"
    last_updated: "2025-01-11T14:33:00Z"

  # Shared components across pages
  common_components:
  - component_id: "comp_001"
    component_name: "NavigationHeader"
    component_type: "navigation"
    file_path: "pages/common_components.py"
    class_name: "NavigationHeader"

    # Where this component appears
    appears_on_pages:
    - page_id: "po_001"
      page_name: "LoginPage"
    - page_id: "po_002"
      page_name: "DashboardPage"
    - page_id: "po_003"
      page_name: "ProfilePage"

    # Elements in this component
    elements:
    - element_name: "logo"
      selector: ".header-logo"
      element_type: "image"

    - element_name: "user_menu"
      selector: "#user-dropdown"
      element_type: "dropdown"

    - element_name: "logout_link"
      selector: "a[href='/logout']"
      element_type: "link"

  # Selector catalog (for healing and analysis)
  selector_catalog:
    total_selectors: 47

    # By type
    by_type:
      css: 25
      role: 15
      text: 5
      xpath: 2

    # By fragility
    fragility_index:
      low: 30        # 0.0 - 0.3
      medium: 12     # 0.4 - 0.6
      high: 5        # 0.7 - 1.0

    # All selectors with metadata
    selectors:
    - selector_id: "sel_001"
      selector: "role=button[name='Login']"
      selector_type: "role"
      fragility_score: 0.2
      category: "primary"

      # Where it's used
      used_in_components: ["LoginPage"]
      used_in_recordings: ["login_001", "checkout_002"]
      used_in_steps: ["stepdef_003"]

      # Self-healing data
      self_healing_enabled: true
      healing_history:
      - healing_id: "heal_001"
        original_selector: "#login-btn"
        new_selector: "data-testid=login-button"
        method: "data_testid_fallback"
        timestamp: "2025-01-11T15:02:30Z"
        verified: true
```

**Key Decisions:**
- Each element has ordered fallback selectors
- Fragility score: 0.0 (best) to 1.0 (worst)
- Self-healing history tracks all selector changes
- Components can span multiple pages

---

### 3.6 execution_log

**Purpose:** Test run history, failure analysis, trends

```yaml
execution_log:
  # All test runs
  test_runs:
  - run_id: "run_001"
    triggered_by: "cpa run"
    trigger_type: "cli"            # cli | ci | scheduled
    executed_by: "execution_agent_001"
    started_at: "2025-01-11T15:00:00Z"
    completed_at: "2025-01-11T15:05:30Z"
    duration_seconds: 330
    status: "completed"             # running | completed | failed | cancelled

    # What was executed
    filter:
      features: ["login.feature", "dashboard.feature"]
      tags: ["@smoke"]
      scenarios: null              # If specific scenarios

    # Results summary
    results:
      total_scenarios: 10
      total_steps: 45
      passed: 7
      failed: 3
      skipped: 0
      pass_rate: 0.70

    # Environment
    environment:
      browser: "chromium"
      browser_version: "120.0.6099"
      viewport: "1280x720"
      headless: true
      base_url: "https://staging.example.com"

    # Detailed failures
    failures:
    - scenario_id: "scenario_003"
      scenario_name: "Login with invalid password"
      feature_id: "feat_001"

      # Failure details
      failed_step: "When I click the login button"
      error_type: "TimeoutError"
      error_category: "UI_CHANGE"    # UI_CHANGE | TIMING_ISSUE | DATA_ISSUE | ENVIRONMENT
      error_message: "Timeout 30000ms exceeded waiting for selector"

      # Context
      screenshot: "reports/run_001/screenshots/scenario_003_failure.png"
      video: "reports/run_001/videos/scenario_003.webm"
      page_url: "https://app.example.com/login"

      # AI analysis
      ai_analysis:
        category: "UI_CHANGE"
        root_cause: "Selector 'role=button[name=\"Login\"]' not found"
        suggested_selector: "role=button[name=\"Sign In\"]"
        confidence: 0.92
        auto_fix_available: true
        auto_fix_applied: false
        requires_review: true
        recommendation: "Update step definition selector"

      # Healing attempt (if applicable)
      healing_attempted: true
      healing_result: "failed"          # success | failed | not_attempted

    # Report location
    report_path: "reports/run_001/index.html"

    # Resource usage
    resource_usage:
      max_memory_mb: 256
      max_cpu_percent: 25
      duration_seconds: 330

  # Trend analysis (computed from history)
  trends:
    # Flaky test detection
    flaky_scenarios:
    - scenario_id: "scenario_005"
      scenario_name: "Search functionality"
      total_runs: 10
      failures: 3
      failure_rate: 0.30
      failure_pattern: "intermittent"  # consistent | intermittent | random
      last_5_runs: [true, false, true, false, true]
      recommended_action: "Add explicit wait before search button click"
      detected_at: "2025-01-11T16:00:00Z"

    # Stable scenarios
    stable_scenarios:
    - scenario_id: "scenario_001"
      scenario_name: "Successful login with valid credentials"
      total_runs: 15
      pass_rate: 1.0
      last_failure: null

    # Performance metrics
    performance_metrics:
      avg_scenario_duration_seconds: 15.2
      slowest_scenario:
        scenario_id: "scenario_008"
        scenario_name: "Load user profile"
        avg_duration: 45.3
      fastest_scenario:
        scenario_id: "scenario_002"
        scenario_name: "Logout"
        avg_duration: 3.5

  # Self-healing audit log
  self_healing_log:
  - healing_id: "heal_001"
    run_id: "run_001"
    scenario_id: "scenario_003"
    step_id: "step_005"

    # Healing details
    original_selector: "#login-btn"
    new_selector: "data-testid=login-button"
    healing_method: "data_testid_fallback"

    # Confidence
    confidence: 0.95
    verified: true              # Human verified the fix

    # Metadata
    auto_applied: true
    requires_review: false
    timestamp: "2025-01-11T15:02:30Z"
```

**Key Decisions:**
- Failure categories enable intelligent grouping
- AI analysis provides actionable insights
- Flaky detection uses historical pass/fail patterns
- Self-healing audit enables review and rollback

---

### 3.7 skills_index

**Purpose:** Track installed skills and their status

```yaml
skills_index:
  # Core framework skills (bundled)
  core_skills:
  - skill_id: "skill_001"
    skill_name: "playwright-parser"
    skill_type: "core"
    version: "1.0.0"
    agent: "ingestion_agent"
    file_path: "/opt/cpa/skills/core/playwright_parser.py"
    class_name: "PlaywrightParserSkill"

    # Status
    enabled: true
    last_used: "2025-01-11T14:32:15Z"
    usage_count: 47

    # Dependencies
    dependencies: []              # No external deps
    system_requirements: []       # No system deps

    # Manifest
    manifest: "skills/core/playwright-parser/skill_manifest.yaml"

    # Configuration
    configuration: {}

  # Custom user-added skills
  custom_skills:
  - skill_id: "custom_001"
    skill_name: "visual-regression-checker"
    skill_type: "custom"
    version: "1.0.0"
    agent: "execution_agent"
    file_path: "/home/user/my-project/.cpa/skills/visual_regression.py"
    class_name: "VisualRegressionSkill"

    # Status
    enabled: true
    last_used: "2025-01-11T16:30:00Z"
    usage_count: 3

    # Dependencies
    dependencies:
      python_packages:
        - "pixelmatch>=5.3.0"
        - "Pillow>=10.0.0"
      system_requirements: []
      claude_skills:
        - "screenshot-capture"

    # Manifest
    manifest: "/home/user/.cpa/skills/visual-regression/skill_manifest.yaml"

    # Configuration
    configuration:
      threshold: 0.1
      auto_update_baseline: false
      diff_color: "red"

  # Skill dependency graph
  skill_dependencies:
    bdd_conversion_agent:
      - gherkin-generator
      - step-definition-creator
      - scenario-optimizer

    execution_agent:
      - test-runner
      - report-generator
      - failure-analyzer
      - self-healing

    visual_regression:
      - screenshot-capture
      - pixel_compare

  # Summary statistics
  skill_registry:
    total_skills: 18
    core_skills: 15
    custom_skills: 3
    enabled_skills: 18
    disabled_skills: 0

    # By agent
    by_agent:
      orchestrator: 5
      ingestion: 3
      deduplication: 3
      bdd_conversion: 3
      execution: 4
```

**Key Decisions:**
- Skills have explicit agent binding
- Dependencies validated before skill execution
- Usage tracking identifies unused skills
- Manifest files enable skill discovery

---

### 3.8 configuration

**Purpose:** Runtime settings for browser, testing, and reporting

```yaml
configuration:
  # Browser settings
  browser_config:
    default_browser: "chromium"     # chromium | firefox | webkit
    browsers_enabled:
      - "chromium"
      - "firefox"
      - "webkit"
    headless: true
    viewport:
      width: 1280
      height: 720
    slow_mo: 0                      # Slow down actions (ms)
    timeout: 30000                   # Default timeout (ms)

    # Media capture
    video:
      enabled: true
      save_on: "failure"             # always | failure | never
      directory: "reports/{run_id}/videos"
      size: "720x720"

    screenshots:
      enabled: true
      save_on: "failure"
      directory: "reports/{run_id}/screenshots"
      format: "png"
      full_page: false

  # Test execution settings
  test_config:
    parallel_workers: 1
    max_workers: 4
    retry_failed: 1
    retry_flaky: true
    stop_on_first_failure: false
    fail_fast: false

    # Tag-based test selection
    tags:
      default_run:
        - "@smoke"
      nightly_run:
        - "@regression"
        - "@integration"
      quick:
        - "@smoke and not @slow"

    # Scenario selection
    scenarios: null                 # If set, only run these

    # Feature selection
    features: null                  # If set, only run these

  # Reporting settings
  reporting_config:
    report_format: "html"           # html | json | markdown | junit
    ai_analysis_enabled: true
    include_screenshots: true
    include_videos: true
    generate_executive_summary: true

    # Trend analysis
    trend_analysis_enabled: true
    minimum_runs_for_trends: 5

    # Report location
    output_directory: "reports"
    report_name_pattern: "run_{timestamp}"

  # Self-healing settings
  self_healing_config:
    enabled: true
    auto_apply_threshold: 0.90     # Auto-apply if confidence >= 0.90
    require_manual_review: true

    # Fallback strategy (in order)
    fallback_strategy:
      - "data_testid"
      - "role"
      - "aria_label"
      - "text"
      - "css"
      - "xpath"
      - "structural"

    # Healing limits
    max_attempts_per_selector: 3
    max_healings_per_run: 10

    # Review workflow
    healing_review_required: false

  # Agent orchestration settings
  agent_config:
    max_concurrent_agents: 3
    max_queue_depth: 100
    agent_timeout_seconds: 600     # 10 minutes
    health_check_interval_seconds: 30

    # Retry failed agents
    retry_failed_agents: true
    max_agent_retries: 2

    # Resource limits per agent
    agent_resource_limits:
      max_memory_mb: 512
      max_cpu_percent: 50
      max_execution_time: 600

  # CI/CD integration settings
  ci_config:
    enabled: false
    platform: "github_actions"     # github_actions | jenkins | gitlab_ci
    artifacts_retention_days: 30
    auto_commit_healed_selectors: false
    pr_comment_on_failure: true
```

**Key Decisions:**
- Configuration can be overridden per environment
- Self-healing has confidence threshold for auto-apply
- Resource limits prevent runaway agents
- Tag-based test selection for different contexts

---

## 4. State Update Patterns

### 4.1 Atomic Update Pattern

**Purpose:** Prevent concurrent modification conflicts

```
Operation: Add new recording

1. Acquire lock
   - File lock on .cpa/state.lock
   - Timeout: 30 seconds
   - Fails if lock not available

2. Read current state
   - Load state.json
   - Validate schema version matches

3. Apply update
   - Append to recording_index.recordings
   - Update last_modified timestamp
   - Increment version counter

4. Validate
   - Validate updated state against schema
   - Check for constraint violations

5. Write atomically
   - Write to temporary file: state.json.tmp
   - Rename atomically: state.json.tmp → state.json
   - Release lock

6. Create backup
   - Copy to state.backup.json
   - Keep last 5 backups: state.backup.{1-5}.json
```

---

### 4.2 Event Sourcing Pattern (Optional)

**Purpose:** Complete audit trail and time-travel debugging

```
Instead of direct state mutation:

1. All operations emit events
   Event: RecordingIngested
   Data: {recording_id, file_path, timestamp}

2. Events appended to .cpa/events.log
   Format: JSON Lines (JSONL)
   Rotation: Daily logs

3. State is computed view
   - Rebuild state.json from events on startup
   - Or rebuild on-demand (lazy loading)

4. Benefits
   - Complete audit trail
   - Time-travel debugging
   - Easy rollback to any point
   - Event replay for testing

5. Trade-offs
   - Added complexity for MVP
   - Longer startup time (rebuilding state)
   - Larger storage (events vs state snapshot)
```

---

### 4.3 Incremental Update Pattern

**Purpose:** Reduce I/O for frequent small updates

```
Use JSON Patch (RFC 6902) for delta updates:

Instead of:
  - Load full state (10KB)
  - Modify data
  - Write full state (10KB)

Do:
  - Load only modified section (1KB)
  - Apply patch operation
  - Write only changed data

Patch Operation Example:
{
  "op": "add",
  "path": "/recording_index/recordings/-",
  "value": {
    "recording_id": "new_001",
    "original_file": "recordings/new.js",
    ...
  }
}

Benefits:
- Faster updates (less I/O)
- Lower memory usage
- Better for concurrent access (smaller critical section)
```

---

## 5. Validation Rules

### 5.1 Schema Validation

| Field | Rule | Error Action |
|-------|------|-------------|
| `schema_version` | Must match framework version | Trigger migration script |
| `agent_registry.active_agents` | Count ≤ `max_concurrent_agents` | Queue excess agents |
| `recording_index.recordings.status` | Must be valid enum | Reject invalid status |
| `bdd_registry.scenarios.*.step_id` | Must reference existing step_def | Flag broken link |
| `selector_catalog.*.fragility_score` | Range [0.0, 1.0] | Clamp to valid range |
| `execution_log.test_runs.*.results.pass_rate` | Range [0.0, 1.0] | Clamping if needed |

---

### 5.2 Cross-Field Validation

```yaml
# Example validation rules

Rule 1: Recording-Scenario Link
  Constraint: converted_scenarios must reference existing scenario_id
  On: recording_index.recordings[*].converted_scenarios
  Validate: Each scenario_id exists in bdd_registry.scenarios
  Error: "Broken link: scenario {scenario_id} not found"

Rule 2: Step-Definition Binding
  Constraint: steps must reference existing step_definition
  On: bdd_registry.scenarios[*].steps[*].step_definition_id
  Validate: step_definition_id exists in bdd_registry.step_definitions
  Error: "Orphan step: step_definition_id {id} not found"

Rule 3: Selector Usage
  Constraint: All selectors must be cataloged
  On: component_library.page_objects[*].elements[*].selector
  Validate: Selector exists in selector_catalog.selectors
  Error: "Uncataloged selector: {selector}"

Rule 4: Agent Timeline
  Constraint: completed_at must be after started_at
  On: agent_registry.agent_history[*]
  Validate: completed_at > started_at
  Error: "Invalid timeline: completed_at before started_at"

Rule 5: Pass Rate Calculation
  Constraint: pass_rate must equal passed / total
  On: execution_log.test_runs[*].results.pass_rate
  Validate: abs(pass_rate - (passed/total)) < 0.01
  Error: "Pass rate mismatch"
```

---

### 5.3 Validation Timing

| Timing | Validations |
|--------|-------------|
| **On Load** | Schema version, field types, cross-field references |
| **Before Write** | All validation rules, constraint checks |
| **After Write** | Verify write succeeded, file integrity |
| **On Agent Spawn** | Resource limits, dependency availability |
| **Periodic** | State consistency, file size limits |

---

## 6. State Lifecycle

### 6.1 State Transitions

```
┌──────────────┐
│   CREATED    │  Initial state when project created
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   ACTIVE     │  Normal operation state
└──────┬───────┘
       │
       ├─────────────────┬─────────────────┐
       ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  UPDATING    │  │  ARCHIVED     │  │  CORRUPTED    │
└──────────────┘  └──────────────┘  └──────────────┘
       │
       ▼
┌──────────────┐
│  DELETED     │  Project removed
└──────────────┘
```

---

### 6.2 Backup Strategy

```
Backup Triggers:
1. Before major state changes
2. On state schema version change
3. Periodic (daily)

Backup Files:
- .cpa/state.backup.json        # Latest backup
- .cpa/state.backup.{1-5}.json   # Rolling backups

Backup Rotation:
- Keep last 5 backups
- Automatic cleanup of older backups
- Compress backups older than 7 days

Restore Process:
1. Validate current state is corrupted
2. Find latest valid backup
3. Restore from backup
4. Log restore event
5. Notify user
```

---

## 7. Migration Strategy

### 7.1 Schema Version Migration

```
From Version 1.0.0 → 2.0.0

Breaking Changes:
1. Added agent_registry section
2. Added skills_index section
3. Restructured recording_index

Migration Process:
1. Detect version mismatch
   - Read schema_version from state.json
   - Compare with framework version

2. Backup current state
   - Create state.pre-migration.json

3. Run migration script
   - scripts/migrate_1_to_2.py
   - Adds new sections
   - Restructures existing data
   - Validates output

4. Validate migrated state
   - Load and validate against new schema
   - Check for data loss

5. Update version
   - Set schema_version: "2.0.0"

6. Commit migration
   - Remove .pre-migration backup
   - Log migration event
```

---

### 7.2 Data Integrity Checks

```
Periodic Checks (run daily):

1. Consistency Check
   - All scenario_id references valid
   - All step_definition_id references valid
   - All selectors cataloged

2. Size Check
   - state.json size < 100KB
   - If > 100KB, trigger cleanup:
     - Archive old agent_history entries
     - Archive old execution_log entries
     - Compress large fields

3. Backup Check
   - At least one valid backup exists
   - Backup is recent (< 24 hours)

4. Health Check
   - State file readable
   - Lock file not stale (> 1 hour old without pid)
   - No corruption detected
```

---

## 8. State API Operations

### 8.1 Read Operations

| Operation | Path | Returns |
|-----------|------|---------|
| Get project metadata | `project_metadata` | Project info |
| Get active agents | `agent_registry.active_agents` | List of agents |
| Get recordings | `recording_index.recordings` | All recordings |
| Get recording | `recording_index.recordings[{recording_id}]` | Single recording |
| Get features | `bdd_registry.features` | All features |
| Get scenarios | `bdd_registry.scenarios` | All scenarios |
| Get page objects | `component_library.page_objects` | All page objects |
| Get test runs | `execution_log.test_runs` | All test runs |
| Get test run | `execution_log.test_runs[{run_id}]` | Single run |
| Get skills | `skills_index.{core_skills,custom_skills}` | All skills |
| Get config | `configuration` | Runtime config |

---

### 8.2 Write Operations

| Operation | Path | Validation |
|-----------|------|------------|
| Add recording | `recording_index.recordings` | File exists |
| Update recording | `recording_index.recordings[{id}]` | ID exists |
| Add feature | `bdd_registry.features` | Valid BDD |
| Add scenario | `bdd_registry.scenarios` | Linked to feature |
| Add step definition | `bdd_registry.step_definitions` | Unique pattern |
| Add page object | `component_library.page_objects` | Unique ID |
| Add test run | `execution_log.test_runs` | Valid results |
| Add skill | `skills_index.{core,custom}_skills` | Valid manifest |
| Update config | `configuration` | Valid values |
| Add agent to active | `agent_registry.active_agents` | Resource limit |

---

### 8.3 Write Operation Flow

```
State Write Operation Flow:

┌─────────────────────┐
│  Agent/Skill Request │
│  Write Operation    │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │ Acquire Lock │
    │ (30s timeout)│
    └──────┬───────┘
           │
    ┌──────▼───────┐
    │ Load Current │
    │   State     │
    └──────┬───────┘
           │
    ┌──────▼───────┐
    │ Validate    │
    │ Operation   │
    └──────┬───────┘
           │
    ┌──────▼───────┐
    │ Apply Update │
    │ (In-Memory)  │
    └──────┬───────┘
           │
    ┌──────▼───────┐
    │ Validate     │
    │ Updated      │
    └──────┬───────┘
           │
    ┌──────▼───────┐
    │ Write        │
    │ (Atomic)     │
    └──────┬───────┘
           │
    ┌──────▼───────┐
    │ Create       │
    │ Backup       │
    └──────┬───────┘
           │
    ┌──────▼───────┐
    │ Release Lock │
    └──────────────┘
           │
           ▼
    ┌──────────────┐
    │ Return       │
    │ Success      │
    └──────────────┘
```

---

## 9. State Size Management

### 9.1 Size Limits

| Section | Target Size | Max Size | Action When Exceeded |
|---------|-------------|-----------|----------------------|
| `project_metadata` | < 1KB | 5KB | N/A |
| `agent_registry.active_agents` | < 1KB | 5KB | Queue agents |
| `agent_registry.task_queue` | < 10KB | 50KB | Reject new tasks |
| `agent_registry.agent_history` | < 50KB | 500KB | Archive old entries |
| `recording_index.recordings` | < 20KB | 200KB | Archive old recordings |
| `bdd_registry.features` | < 10KB | 100KB | Archive old features |
| `bdd_registry.scenarios` | < 20KB | 200KB | Archive old scenarios |
| `component_library.page_objects` | < 15KB | 150KB | Archive old components |
| `execution_log.test_runs` | < 30KB | 300KB | Archive old runs |
| `skills_index` | < 5KB | 50KB | N/A |
| `configuration` | < 5KB | 20KB | N/A |
| **Total** | **< 100KB** | **1MB** | **Comprehensive cleanup** |

---

### 9.2 Cleanup Strategies

```
Automatic Cleanup Triggers:

1. State size > 150KB
   Action: Trigger comprehensive cleanup

2. Agent history > 1000 entries
   Action: Archive entries older than 30 days

3. Test runs > 100
   Action: Archive runs older than 90 days

Cleanup Operations:

1. Archive old agent_history
   - Move to .cpa/archive/agent_history_{date}.json
   - Keep last 100 entries in active state

2. Archive old test_runs
   - Move to .cpa/archive/test_runs_{date}.json
   - Keep last 50 runs in active state

3. Compress large fields
   - AI analysis text → gzip
   - Screenshots → move to separate storage

4. Remove unused data
   - Failed recordings that were never converted
   - Scenarios for deleted features
```

---

## 10. Example State File

### 10.1 Minimal State (New Project)

```json
{
  "schema_version": "2.0.0",
  "project_metadata": {
    "project_name": "my-test-project",
    "project_id": "proj_abc123",
    "created_at": "2025-01-11T14:30:22Z",
    "created_by": "orchestrator_agent",
    "framework_version": "2.0.0",
    "framework_type": "behave",
    "last_modified": "2025-01-11T14:30:22Z",
    "project_root": "/home/user/my-test-project"
  },
  "agent_registry": {
    "active_agents": [],
    "task_queue": [],
    "agent_history": [],
    "communication_log": []
  },
  "recording_index": {
    "recordings": [],
    "deduplication_map": {
      "common_elements": [],
      "common_flows": [],
      "page_contexts": {}
    },
    "ingestion_log": []
  },
  "bdd_registry": {
    "features": [],
    "scenarios": [],
    "step_definitions": [],
    "scenario_outlines": []
  },
  "component_library": {
    "page_objects": [],
    "common_components": [],
    "selector_catalog": {
      "total_selectors": 0,
      "by_type": {},
      "fragility_index": {
        "low": 0,
        "medium": 0,
        "high": 0
      },
      "selectors": []
    }
  },
  "execution_log": {
    "test_runs": [],
    "trends": {
      "flaky_scenarios": [],
      "stable_scenarios": [],
      "performance_metrics": {}
    },
    "self_healing_log": []
  },
  "skills_index": {
    "core_skills": [],
    "custom_skills": [],
    "skill_dependencies": {},
    "skill_registry": {
      "total_skills": 0,
      "by_agent": {},
      "custom_skills_enabled": 0
    }
  },
  "configuration": {
    "browser_config": {
      "default_browser": "chromium",
      "browsers_enabled": ["chromium", "firefox", "webkit"],
      "headless": true
    },
    "test_config": {},
    "reporting_config": {},
    "self_healing_config": {},
    "agent_config": {}
  }
}
```

---

**Document Version:** 2.0
**Last Updated:** 2025-01-11
**Status:** Design (Planning Phase)
