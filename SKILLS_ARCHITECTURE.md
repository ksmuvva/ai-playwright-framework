# Claude Skills Architecture

## Document Information

| Field | Value |
|-------|-------|
| **Project** | AI Playwright Automation Agent |
| **Version** | 1.0 |
| **Date** | 2025-01-11 |
| **Status** | Design |

---

## Table of Contents

1. [Skills Architecture Overview](#1-skills-architecture-overview)
2. [Skill Definition Format](#2-skill-definition-format)
3. [Core Skills (Built-in)](#3-core-skills-built-in)
4. [Advanced Skills](#4-advanced-skills)
5. [Custom Skills](#5-custom-skills)
6. [Skill Manager](#6-skill-manager)
7. [Skill Execution Flow](#7-skill-execution-flow)
8. [Skill Development Guide](#8-skill-development-guide)

---

## 1. Skills Architecture Overview

### 1.1 What are Claude Skills?

**Claude Skills** are reusable, configurable capabilities that extend the AI agent's functionality. Each skill defines:

- **Triggers**: When the skill should activate (events, conditions)
- **Actions**: What the skill does (agent calls, tool usage)
- **Context**: What data the skill needs
- **Output**: What the skill produces

### 1.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Skills Layer                                    │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                       Skill Manager                                 │  │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐      │  │
│  │  │   List    │  │  Create   │  │  Invoke   │  │  Delete   │      │  │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘      │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                    │                                     │
│                                    ▼                                     │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                       Skill Registry                                │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐   │  │
│  │  │   Core     │  │  Advanced  │  │  Custom    │  │  Shared    │   │  │
│  │  │  Skills    │  │  Skills    │  │  Skills    │  │  Libraries  │   │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                    │                                     │
│                                    ▼                                     │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                       Skill Executor                                │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │  1. Match Trigger     2. Load Context    3. Execute Actions │  │  │
│  │  │  4. Process Results   5. Update State    6. Emit Events     │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Agent Layer                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │  Framework   │  │  Conversion  │  │  Execution   │  │   Analysis   ││
│  │    Agent     │  │    Agent     │  │    Agent     │  │    Agent     ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Skill Categories

| Category | Description | Examples |
|----------|-------------|----------|
| **Reliability** | Improve test stability | Self-Healing, Retry, Wait Optimization |
| **Execution** | Enhance test execution | Parallel Run, Browser Pool, Smart Retry |
| **Analysis** | Analyze and improve tests | Failure Clustering, Flaky Detection, Coverage |
| **Reporting** | Generate reports | HTML Report, Executive Summary, Trends |
| **Integration** | External integrations | JIRA, Slack, GitHub, CI/CD |
| **Custom** | User-defined | Domain-specific, Company-specific |

---

## 2. Skill Definition Format

### 2.1 YAML Skill Definition

```yaml
# .cpa/skills/self-healing.skill

# Skill Metadata
name: self-healing
version: 1.0.0
description: Automatically heal broken locators during test execution
author: CPA Team
category: reliability
tags: [locators, self-healing, automation]
enabled: true

# Triggers - When this skill activates
triggers:
  - event: TestStepFailure
    condition: "error.message includes 'Element not found' or 'Locator not found'"
    priority: high

  - event: TestStepFailure
    condition: "error.message includes 'Timeout waiting for selector'"
    priority: medium

# Context - What data the skill needs
context:
  required:
    - failed_locator
    - page_snapshot
    - error_message
  optional:
    - test_scenario
    - step_definition
    - browser_type

# Actions - What the skill does
actions:
  - name: AnalyzeFailedLocator
    agent: ConversionAgent
    tools:
      - browser_snapshot
      - analyze_dom_structure
      - find_similar_elements
    prompt: |
      Analyze why this locator failed: {failed_locator}
      Page state: {page_snapshot}
      Error: {error_message}

      Find similar elements and suggest alternative locators.

  - name: GenerateHealedLocators
    agent: ConversionAgent
    depends_on: AnalyzeFailedLocator
    prompt: |
      Based on analysis, generate 3-5 alternative locators:
      1. Primary fallback (most robust)
      2. Secondary fallback (text-based)
      3. Tertiary fallback (position-based)

      For each, provide:
      - Locator string
      - Confidence score (0-1)
      - Reasoning

  - name: ApplyHealedLocator
    action: RetryTestStep
    with_healed_locator: true
    max_attempts: 3

# Output - What the skill produces
output:
  healed_locator: string
  confidence: float
  attempt_count: integer
  success: boolean

# Events - What events the skill emits
events:
  - name: LocatorHealed
    data:
      original_locator: string
      healed_locator: string
      confidence: float

  - name: HealingFailed
    data:
      original_locator: string
      reason: string

# Configuration
configuration:
  max_attempts: 3
  confidence_threshold: 0.7
  update_page_objects: true
  log_all_attempts: false
```

### 2.2 JSON Skill Definition

```json
{
  "name": "self-healing",
  "version": "1.0.0",
  "description": "Automatically heal broken locators",
  "triggers": [
    {
      "event": "TestStepFailure",
      "condition": "error.message includes 'Element not found'"
    }
  ],
  "actions": [
    {
      "name": "AnalyzeFailedLocator",
      "agent": "ConversionAgent",
      "tools": ["browser_snapshot"]
    }
  ],
  "output": {
    "healed_locator": "string",
    "confidence": "float"
  }
}
```

---

## 3. Core Skills (Built-in)

### 3.1 Self-Healing Locator

**File:** `.cpa/skills/core/self-healing.skill`

```yaml
name: self-healing-locator
version: 1.0.0
description: Automatically heal broken locators during test execution
category: reliability
priority: high

triggers:
  - event: TestStepFailure
    condition: "error includes 'Element not found' or 'Locator not found'"

actions:
  - name: CapturePageState
    agent: ExecutionAgent
    tools: [browser_snapshot, screenshot]

  - name: AnalyzeFailure
    agent: AnalysisAgent
    prompt: |
      Analyze this locator failure:
      Locator: {failed_locator}
      Page state: {page_snapshot}

      Identify:
      1. Why it failed (element moved, changed, removed)
      2. Similar elements on page
      3. Best alternative selector strategies

  - name: GenerateAlternatives
    agent: ConversionAgent
    prompt: |
      Generate 3 alternative locators for: {element_description}
      Priority order:
      1. Stable attributes (data-testid, aria-label)
      2. Text content
      3. CSS selectors with class names
      4. XPath with text

  - name: RetryWithAlternatives
    agent: ExecutionAgent
    action: retry_test_step
    with_alternative_locators: true

output:
  healed_locator: string
  alternatives: array
  success: boolean
```

### 3.2 Smart Wait

**File:** `.cpa/skills/core/smart-wait.skill`

```yaml
name: smart-wait
version: 1.0.0
description: Dynamically optimize wait times based on page load patterns
category: reliability

triggers:
  - event: BeforeTestStep
    condition: "step.type in ['click', 'fill', 'select']"

  - event: TestStepFailure
    condition: "error includes 'Timeout'"

actions:
  - name: AnalyzePageLoad
    agent: ExecutionAgent
    tools: [browser_evaluate]
    prompt: |
      Measure page readiness:
      1. DOM content loaded
      2. Network idle
      3. Element visible
      4. Element clickable

  - name: CalculateOptimalWait
    agent: AnalysisAgent
    prompt: |
      Based on page load analysis:
      - Current wait: {current_wait}
      - Page load time: {page_load_time}
      - Element ready time: {element_ready_time}

      Calculate optimal wait time with 20% buffer.

  - name: ApplyWaitStrategy
    agent: ExecutionAgent
    action: update_step_wait
    wait_strategy: adaptive

configuration:
  min_wait: 100
  max_wait: 30000
  buffer_percent: 20
  learn_from_history: true
```

### 3.3 Flaky Test Detector

**File:** `.cpa/skills/core/flaky-detector.skill`

```yaml
name: flaky-test-detector
version: 1.0.0
description: Identify and flag flaky tests based on historical data
category: analysis

triggers:
  - event: TestRunComplete
    condition: "always"

actions:
  - name: LoadHistory
    agent: AnalysisAgent
    tools: [load_test_history]
    prompt: |
      Load last 10 test runs for comparison

  - name: IdentifyInconsistentTests
    agent: AnalysisAgent
    prompt: |
      Compare results across runs:
      {test_runs}

      Identify tests with:
      - Different results across runs
      - Intermittent failures
      - Timing-dependent failures

  - name: CalculateFlakinessScore
    agent: AnalysisAgent
    prompt: |
      For each inconsistent test:
      Flakiness Score = (failed_runs / total_runs) * volatility_factor

      Classify:
      - High flakiness (> 0.3)
      - Medium flakiness (0.1 - 0.3)
      - Low flakiness (< 0.1)

  - name: GenerateReport
    agent: AnalysisAgent
    action: generate_flakiness_report

output:
  flaky_tests: array
  flakiness_scores: object
  recommendations: array
```

### 3.4 Auto Screenshot

**File:** `.cpa/skills/core/auto-screenshot.skill`

```yaml
name: auto-screenshot
version: 1.0.0
description: Automatically capture screenshots at strategic points
category: execution

triggers:
  - event: TestStepComplete
    condition: "step.is_assertion == true"

  - event: TestStepFailure
    condition: "always"

  - event: TestScenarioComplete
    condition: "scenario.status == 'passed'"

actions:
  - name: CaptureScreenshot
    agent: ExecutionAgent
    tools: [browser_screenshot]
    prompt: |
      Capture screenshot:
      - Name: {scenario_name}_{step_name}_{timestamp}
      - Full page: {is_final_step}
      - Highlight element: {assertion_element}

  - name: AttachToReport
    agent: ReportingAgent
    action: attach_screenshot_to_report

configuration:
  screenshot_format: png
  full_page_on_failure: true
  thumbnail_size: [300, 200]
  retention_days: 30
```

### 3.5 Visual Regression

**File:** `.cpa/skills/core/visual-regression.skill`

```yaml
name: visual-regression
version: 1.0.0
description: Detect visual changes by comparing screenshots
category: analysis

triggers:
  - event: TestScenarioComplete
    condition: "scenario.tags includes '@visual'"

actions:
  - name: CaptureBaseline
    agent: ExecutionAgent
    tools: [browser_screenshot]
    condition: "baseline does not exist"

  - name: CompareWithBaseline
    agent: AnalysisAgent
    tools: [visual_compare]
    prompt: |
      Compare current screenshot with baseline:
      - Current: {current_screenshot}
      - Baseline: {baseline_screenshot}
      - Tolerance: {tolerance}

      Detect:
      - Pixel differences
      - Layout shifts
      - Color changes
      - Missing elements

  - name: GenerateDiffReport
    agent: ReportingAgent
    action: generate_visual_diff

  - name: UpdateBaseline
    agent: ExecutionAgent
    action: update_baseline
    condition: "approved == true"

output:
  diff_detected: boolean
  diff_percentage: float
  diff_regions: array
  baseline_updated: boolean
```

### 3.6 Performance Monitor

**File:** `.cpa/skills/core/performance-monitor.skill`

```yaml
name: performance-monitor
version: 1.0.0
description: Monitor and report test execution performance
category: analysis

triggers:
  - event: TestStepComplete
    condition: "always"

  - event: TestScenarioComplete
    condition: "always"

  - event: TestRunComplete
    condition: "always"

actions:
  - name: RecordMetrics
    agent: AnalysisAgent
    prompt: |
      Record metrics for:
      - Step duration: {step_duration}
      - Scenario duration: {scenario_duration}
      - Page load time: {page_load_time}
      - Resource timing: {resource_timing}

  - name: DetectAnomalies
    agent: AnalysisAgent
    prompt: |
      Compare with historical averages:
      - Current: {current_metrics}
      - Average: {historical_average}
      - Threshold: 2x average

      Flag anomalies:
      - Slow steps
      - Degraded performance
      - Resource issues

  - name: GeneratePerformanceReport
    agent: ReportingAgent
    action: generate_performance_report

output:
  metrics: object
  anomalies: array
  trends: object
```

---

## 4. Advanced Skills

### 4.1 API Testing

**File:** `.cpa/skills/advanced/api-testing.skill`

```yaml
name: api-testing
version: 1.0.0
description: Test REST APIs with automatic request/response validation
category: integration

triggers:
  - event: ManualInvocation
    command: "cpa skills run api-testing --spec openapi.yaml"

actions:
  - name: ParseAPISpec
    agent: ConversionAgent
    tools: [parse_openapi, parse_graphql]
    prompt: |
      Parse API specification:
      - File: {spec_file}
      - Format: {format}

      Extract:
      - Endpoints
      - Methods
      - Parameters
      - Response schemas

  - name: GenerateTestScenarios
    agent: ConversionAgent
    prompt: |
      Generate test scenarios for each endpoint:
      - Happy path
      - Missing required fields
      - Invalid data types
      - Authentication failures
      - Rate limiting

  - name: ExecuteAPIRequests
    agent: ExecutionAgent
    tools: [http_request, websocket_client]
    prompt: |
      Execute requests:
      - Method: {method}
      - URL: {url}
      - Headers: {headers}
      - Body: {body}

      Validate:
      - Status code
      - Response schema
      - Response time
      - Headers

  - name: GenerateAPIReport
    agent: ReportingAgent
    action: generate_api_test_report

output:
  endpoints_tested: integer
  passed: integer
  failed: integer
  coverage: float
```

### 4.2 Mobile Testing

**File:** `.cpa/skills/advanced/mobile-testing.skill`

```yaml
name: mobile-testing
version: 1.0.0
description: Test mobile web and native apps with device emulation
category: execution

triggers:
  - event: TestRunStart
    condition: "config.target == 'mobile'"

actions:
  - name: ConfigureDevice
    agent: ExecutionAgent
    prompt: |
      Configure mobile device:
      - Device: {device_type} (iPhone, Pixel, iPad)
      - Orientation: {orientation}
      - Viewport: {viewport}
      - User agent: {user_agent}

  - name: EmulateTouchActions
    agent: ExecutionAgent
    tools: [browser_touch]
    prompt: |
      Convert mouse actions to touch:
      - click → tap
      - hover → long press
      - drag → swipe

  - name: CaptureDeviceMetrics
    agent: AnalysisAgent
    prompt: |
      Capture mobile-specific metrics:
      - Touch target sizes
      - Text readability
      - Viewport usage
      - Performance on 3G

output:
  device_type: string
  touch_targets_valid: boolean
  mobile_usability_score: float
```

### 4.3 Accessibility Testing

**File:** `.cpa/skills/advanced/accessibility.skill`

```yaml
name: accessibility-testing
version: 1.0.0
description: Automated accessibility testing (WCAG 2.1 AA compliance)
category: analysis

triggers:
  - event: TestScenarioComplete
    condition: "scenario.tags includes '@a11y'"

actions:
  - name: AnalyzeAccessibilityTree
    agent: AnalysisAgent
    tools: [browser_snapshot, axe_core]
    prompt: |
      Analyze page for accessibility:
      - ARIA labels
      - Alt text
      - Heading structure
      - Focus management
      - Color contrast
      - Keyboard navigation

  - name: RunAxeScan
    agent: AnalysisAgent
    tools: [axe_core]
    prompt: |
      Run axe-core scan:
      - WCAG level: AA
      - Tags: ['wcag2a', 'wcag2aa', 'best-practice']

      Detect violations:
      - Critical
      - Serious
      - Moderate
      - Minor

  - name: GenerateA11yReport
    agent: ReportingAgent
    action: generate_accessibility_report

output:
  violations: array
  wcag_compliant: boolean
  score: float
  recommendations: array
```

### 4.4 Security Testing

**File:** `.cpa/skills/advanced/security-testing.skill`

```yaml
name: security-testing
version: 1.0.0
description: Basic security scanning for common vulnerabilities
category: analysis

triggers:
  - event: TestScenarioComplete
    condition: "scenario.tags includes '@security'"

actions:
  - name: ScanForVulnerabilities
    agent: AnalysisAgent
    tools: [security_scan]
    prompt: |
      Scan for common vulnerabilities:
      - XSS injection points
      - SQL injection possibilities
      - CSRF token presence
      - Security headers
      - Input validation
      - Authentication/authorization

  - name: CheckHeaders
    agent: AnalysisAgent
    tools: [http_headers]
    prompt: |
      Verify security headers:
      - Strict-Transport-Security
      - Content-Security-Policy
      - X-Frame-Options
      - X-Content-Type-Options
      - Referrer-Policy

  - name: GenerateSecurityReport
    agent: ReportingAgent
    action: generate_security_report

output:
  vulnerabilities: array
  security_score: float
  headers_status: object
```

### 4.5 Cross-Browser Testing

**File:** `.cpa/skills/advanced/cross-browser.skill`

```yaml
name: cross-browser-testing
version: 1.0.0
description: Execute tests across multiple browsers in parallel
category: execution

triggers:
  - event: TestRunStart
    condition: "config.browsers.length > 1"

actions:
  - name: CreateBrowserMatrix
    agent: ExecutionAgent
    prompt: |
      Create test matrix:
      - Browsers: {browsers}
      - Versions: {versions}
      - Platforms: {platforms}
      - Scenarios: {scenarios}

  - name: ExecuteInParallel
    agent: ExecutionAgent
    action: parallel_execution
    workers: len(browsers)

  - name: CompareResults
    agent: AnalysisAgent
    prompt: |
      Compare results across browsers:
      - Browser-specific failures
      - Timing differences
      - Compatibility issues

  - name: GenerateCrossBrowserReport
    agent: ReportingAgent
    action: generate_cross_browser_report

output:
  browser_results: object
  compatibility_issues: array
  unified_result: boolean
```

### 4.6 Data-Driven Testing

**File:** `.cpa/skills/advanced/data-driven.skill`

```yaml
name: data-driven-testing
version: 1.0.0
description: Execute scenarios with multiple data sets
category: execution

triggers:
  - event: TestScenarioLoad
    condition: "scenario.data_file exists"

actions:
  - name: LoadTestData
    agent: ExecutionAgent
    tools: [load_json, load_csv, load_excel]
    prompt: |
      Load test data from:
      - File: {data_file}
      - Format: {format}

      Validate:
      - Required columns
      - Data types
      - Value ranges

  - name: GenerateScenarios
    agent: ConversionAgent
    prompt: |
      Create scenario outline:
      - Examples: {data_rows}
      - Parameters: {column_names}

      Generate:
      - Scenario Outline
      - Examples table
      - Parameterized steps

  - name: ExecuteForEachRow
    agent: ExecutionAgent
    action: execute_data_driven

output:
  rows_executed: integer
  rows_passed: integer
  rows_failed: integer
  failed_rows: array
```

---

## 5. Custom Skills

### 5.1 JIRA Integration

**File:** `.cpa/skills/custom/jira-integration.skill`

```yaml
name: jira-integration
version: 1.0.0
description: Create JIRA tickets for test failures
category: integration

triggers:
  - event: TestRunComplete
    condition: "failed_tests > 0 and config.jira.enabled"

actions:
  - name: GroupFailures
    agent: AnalysisAgent
    prompt: |
      Group failures by similarity to avoid duplicate tickets

  - name: CreateJIRATickets
    agent: IntegrationAgent
    tools: [jira_api]
    prompt: |
      Create JIRA tickets:
      - Project: {jira_project}
      - Type: Bug
      - Summary: {failure_summary}
      - Description: |
        {failure_details}

        Test: {test_name}
        Steps: {failed_steps}
        Screenshot: {screenshot_url}
        Logs: {logs_url}

      Labels: [automated-test, {environment}]

  - name: LinkTicketsToReport
    agent: ReportingAgent
    action: add_jira_links

output:
  tickets_created: array
  ticket_urls: array
```

### 5.2 Slack Notifications

**File:** `.cpa/skills/custom/slack-notify.skill`

```yaml
name: slack-notifications
version: 1.0.0
description: Send test results to Slack
category: integration

triggers:
  - event: TestRunComplete
    condition: "config.slack.enabled"

actions:
  - name: FormatMessage
    agent: ReportingAgent
    prompt: |
      Create Slack message:
      - Status: {pass_fail_emoji}
      - Summary: {test_summary}
      - Failed tests: {failure_list}

  - name: SendToSlack
    agent: IntegrationAgent
    tools: [slack_webhook]
    prompt: |
      Send message:
      - Webhook: {slack_webhook_url}
      - Channel: {slack_channel}
      - Message: {formatted_message}
      - Attachments: [{report_url}]

output:
  message_sent: boolean
  timestamp: string
```

### 5.3 GitHub Integration

**File:** `.cpa/skills/custom/github-integration.skill`

```yaml
name: github-integration
version: 1.0.0
description: Post test results as GitHub comments
category: integration

triggers:
  - event: TestRunComplete
    condition: "env.GITHUB_ACTIONS == true"

actions:
  - name: DetectPR
    agent: IntegrationAgent
    tools: [github_api]
    prompt: |
      Get PR information from GitHub Actions context

  - name: GenerateComment
    agent: ReportingAgent
    prompt: |
      Create GitHub comment with:
      - Test summary
      - Failed tests
      - Coverage report
      - Links to full reports

  - name: PostComment
    agent: IntegrationAgent
    tools: [github_api]
    prompt: |
      Post comment to PR:
      - Repository: {github_repository}
      - PR number: {pr_number}
      - Comment: {comment_body}

output:
  comment_url: string
  pr_number: integer
```

### 5.4 Custom Assertions

**File:** `.cpa/skills/custom/custom-assertions.skill`

```yaml
name: custom-assertions
version: 1.0.0
description: Domain-specific assertion helpers
category: custom

triggers:
  - event: TestStepLoad
    condition: "step.name matches custom assertion pattern"

actions:
  - name: ValidateBusinessRule
    agent: AnalysisAgent
    prompt: |
      Custom validation for:
      - Rule: {rule_name}
      - Data: {actual_data}
      - Expected: {expected_pattern}

    examples:
      - validate_email_format
      - validate_phone_number
      - validate_postal_code
      - validate_currency

  - name: GenerateAssertion
    agent: ConversionAgent
    prompt: |
      Generate assertion code:
      - Type: {assertion_type}
      - Expected: {expected_value}
      - Actual: {actual_value}
      - Message: {error_message}

output:
  valid: boolean
  error_message: string
```

---

## 6. Skill Manager

### 6.1 Manager Architecture

```python
"""
Skill Manager - Manages Claude Skills lifecycle.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
import json


class SkillManager:
    """Manages Claude Skills."""

    def __init__(self, project_path: Optional[str] = None):
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.skills_dir = self.project_path / '.cpa' / 'skills'
        self._skills_cache: Dict[str, Skill] = {}

    def list_skills(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all available skills."""
        skills = []

        # Load core skills
        core_dir = self.skills_dir / 'core'
        if core_dir.exists():
            for skill_file in core_dir.glob('*.skill'):
                skill = self._load_skill(skill_file)
                if skill and (category is None or skill.category == category):
                    skills.append(self._skill_to_dict(skill))

        # Load custom skills
        custom_dir = self.skills_dir / 'custom'
        if custom_dir.exists():
            for skill_file in custom_dir.glob('*.skill'):
                skill = self._load_skill(skill_file)
                if skill and (category is None or skill.category == category):
                    skills.append(self._skill_to_dict(skill))

        return skills

    def create_skill(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new custom skill."""
        name = options['name']
        template = options.get('template', 'basic')

        # Generate skill file
        skill_content = self._generate_skill_template(name, template, options)

        # Save skill
        custom_dir = self.skills_dir / 'custom'
        custom_dir.mkdir(parents=True, exist_ok=True)

        skill_file = custom_dir / f'{name}.skill'
        skill_file.write_text(skill_content)

        return {
            'success': True,
            'skill_path': str(skill_file),
        }

    def invoke_skill(
        self,
        name: str,
        context: Dict[str, Any],
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Invoke a skill by name."""
        skill = self._load_skill_by_name(name)

        if not skill:
            return {'success': False, 'error': f'Skill not found: {name}'}

        # Check triggers
        if not self._should_trigger(skill, context):
            return {'success': False, 'error': 'Skill triggers not met'}

        # Execute actions
        actions = []
        for action in skill.actions:
            action_result = {
                'name': action.name,
                'agent': action.agent,
                'dry_run': dry_run,
            }
            actions.append(action_result)

            if not dry_run:
                # Execute action
                result = self._execute_action(action, context)
                action_result['result'] = result

        return {
            'success': True,
            'actions': actions,
        }

    def update_skill(self, name: str, **kwargs) -> Dict[str, Any]:
        """Update a skill's configuration."""
        skill_file = self._find_skill_file(name)

        if not skill_file:
            return {'success': False, 'error': f'Skill not found: {name}'}

        with open(skill_file, 'r') as f:
            skill_data = yaml.safe_load(f)

        # Update fields
        for key, value in kwargs.items():
            if value is not None:
                skill_data[key] = value

        # Write back
        with open(skill_file, 'w') as f:
            yaml.dump(skill_data, f)

        return {'success': True}

    def delete_skill(self, name: str) -> Dict[str, Any]:
        """Delete a custom skill."""
        skill_file = self._find_skill_file(name)

        if not skill_file:
            return {'success': False, 'error': f'Skill not found: {name}'}

        # Don't allow deleting core skills
        if 'core' in skill_file.parts:
            return {'success': False, 'error': 'Cannot delete core skills'}

        skill_file.unlink()
        return {'success': True}

    def validate_skill(self, skill_path: str) -> Dict[str, Any]:
        """Validate a skill configuration file."""
        skill_file = Path(skill_path)

        with open(skill_file, 'r') as f:
            skill_data = yaml.safe_load(f)

        errors = []

        # Validate required fields
        required_fields = ['name', 'version', 'description', 'triggers', 'actions']
        for field in required_fields:
            if field not in skill_data:
                errors.append(f'Missing required field: {field}')

        # Validate triggers
        for trigger in skill_data.get('triggers', []):
            if 'event' not in trigger:
                errors.append('Trigger missing event')

        # Validate actions
        for action in skill_data.get('actions', []):
            if 'name' not in action:
                errors.append('Action missing name')

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'name': skill_data.get('name'),
            'version': skill_data.get('version'),
            'triggers': [t.get('event') for t in skill_data.get('triggers', [])],
        }

    def _load_skill(self, skill_file: Path) -> Optional['Skill']:
        """Load a skill from file."""
        with open(skill_file, 'r') as f:
            data = yaml.safe_load(f)
        return Skill(**data)

    def _load_skill_by_name(self, name: str) -> Optional['Skill']:
        """Load a skill by name."""
        skill_file = self._find_skill_file(name)
        return self._load_skill(skill_file) if skill_file else None

    def _find_skill_file(self, name: str) -> Optional[Path]:
        """Find a skill file by name."""
        # Check core skills
        core_file = self.skills_dir / 'core' / f'{name}.skill'
        if core_file.exists():
            return core_file

        # Check custom skills
        custom_file = self.skills_dir / 'custom' / f'{name}.skill'
        if custom_file.exists():
            return custom_file

        return None

    def _should_trigger(self, skill: 'Skill', context: Dict[str, Any]) -> bool:
        """Check if skill should trigger based on context."""
        for trigger in skill.triggers:
            event = trigger.get('event')
            condition = trigger.get('condition', 'true')

            # Check event match
            if context.get('event') != event:
                continue

            # Check condition (simplified)
            if condition == 'true':
                return True

            # TODO: Implement condition evaluation

        return False

    def _execute_action(self, action: 'Action', context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a skill action."""
        # This would delegate to the appropriate agent
        # For now, return placeholder
        return {'executed': True}

    def _generate_skill_template(
        self,
        name: str,
        template: str,
        options: Dict[str, Any]
    ) -> str:
        """Generate skill template content."""
        if template == 'basic':
            return f'''# {name}

name: {name}
version: 1.0.0
description: {options.get('description', f'{name} skill')}
author: Generated
category: {options.get('category', 'custom')}
enabled: true

triggers:
  - event: ManualInvocation
    condition: "always"

actions:
  - name: ExecuteAction
    agent: ExecutionAgent
    prompt: |
      Your action here

output:
  result: string
'''
        else:
            return f'''# {name} (Advanced)

name: {name}
version: 1.0.0
description: {options.get('description', f'{name} skill')}
author: Generated
category: {options.get('category', 'custom')}
enabled: true

triggers:
  - event: ManualInvocation
    condition: "always"

actions:
  - name: Step1
    agent: ConversionAgent
    prompt: |
      First step

  - name: Step2
    agent: ExecutionAgent
    depends_on: Step1
    prompt: |
      Second step

  - name: Step3
    agent: AnalysisAgent
    depends_on: Step2
    prompt: |
      Third step

output:
  step1_result: string
  step2_result: string
  step3_result: string
'''

    def _skill_to_dict(self, skill: 'Skill') -> Dict[str, Any]:
        """Convert skill to dictionary."""
        return {
            'name': skill.name,
            'description': skill.description,
            'version': skill.version,
            'category': skill.category,
            'author': skill.author,
            'built_in': skill.built_in,
            'triggers': [t.event for t in skill.triggers],
        }


class Skill:
    """Skill data model."""

    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        triggers: List[Dict[str, Any]],
        actions: List[Dict[str, Any]],
        author: str = 'Unknown',
        category: str = 'custom',
        enabled: bool = True,
        built_in: bool = False,
    ):
        self.name = name
        self.version = version
        self.description = description
        self.triggers = [Trigger(**t) for t in triggers]
        self.actions = [Action(**a) for a in actions]
        self.author = author
        self.category = category
        self.enabled = enabled
        self.built_in = built_in


class Trigger:
    """Skill trigger."""

    def __init__(self, event: str, condition: str = 'true', priority: str = 'medium'):
        self.event = event
        self.condition = condition
        self.priority = priority


class Action:
    """Skill action."""

    def __init__(
        self,
        name: str,
        agent: str,
        prompt: str,
        tools: List[str] = None,
        depends_on: str = None,
    ):
        self.name = name
        self.agent = agent
        self.prompt = prompt
        self.tools = tools or []
        self.depends_on = depends_on
```

---

## 7. Skill Execution Flow

### 7.1 Execution Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Event Occurs                                    │
│  (TestStepFailure, TestRunComplete, ManualInvocation, etc.)             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       Skill Manager                                      │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  1. Find matching skills by event                                 │  │
│  │  2. Evaluate trigger conditions                                   │  │
│  │  3. Sort by priority                                               │  │
│  │  4. Filter enabled skills                                         │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       Skill Executor                                     │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  For each skill:                                                   │  │
│  │                                                                    │  │
│  │  1. Load context data                                              │  │
│  │  2. Execute actions in dependency order                           │  │
│  │  3. Collect outputs                                                │  │
│  │  4. Handle errors                                                  │  │
│  │  5. Emit skill events                                              │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       Agent Layer                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │  Agent Call  │─>│  Tool Use    │─>│  Result      │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       Output Handling                                    │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  1. Process skill outputs                                          │  │
│  │  2. Update test state                                              │  │
│  │  3. Generate reports                                               │  │
│  │  4. Trigger dependent skills                                       │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Event Types

| Event | Description | Context Data |
|-------|-------------|--------------|
| `TestRunStart` | Test execution begins | config, tags, features |
| `TestScenarioStart` | Scenario execution begins | scenario_name, tags |
| `TestStepStart` | Step execution begins | step_name, step_type |
| `TestStepComplete` | Step completes | step_name, status, duration |
| `TestStepFailure` | Step fails | step_name, error, screenshot |
| `TestScenarioComplete` | Scenario completes | scenario_name, status, duration |
| `TestRunComplete` | Test run completes | results, duration |
| `ManualInvocation` | User invokes skill | skill_name, args |
| `BeforeAssertion` | Before assertion check | assertion, expected, actual |
| `AfterAssertion` | After assertion check | assertion, result |

---

## 8. Skill Development Guide

### 8.1 Creating a Simple Skill

**Step 1: Use CLI to create template**

```bash
cpa skills create my-custom-skill --category custom --description "My first skill"
```

**Step 2: Edit the generated skill file**

```yaml
# .cpa/skills/custom/my-custom-skill.skill

name: my-custom-skill
version: 1.0.0
description: My first custom skill
author: Your Name
category: custom
enabled: true

triggers:
  - event: TestScenarioComplete
    condition: "scenario.name includes 'checkout'"

actions:
  - name: ValidateCheckout
    agent: AnalysisAgent
    prompt: |
      Validate the checkout scenario:
      - Scenario: {scenario_name}
      - Steps: {steps}

      Check for:
      - Cart validation
      - Payment information
      - Shipping address
      - Order confirmation

output:
  validation_passed: boolean
  issues_found: array
```

**Step 3: Test the skill**

```bash
# Validate skill syntax
cpa skills validate .cpa/skills/custom/my-custom-skill.skill

# Run skill manually
cpa skills run my-custom-skill
```

### 8.2 Creating an Advanced Skill

```yaml
# .cpa/skills/custom/advanced-checkout.skill

name: advanced-checkout-validation
version: 1.0.0
description: Comprehensive checkout flow validation
author: Your Name
category: custom
enabled: true

triggers:
  - event: TestScenarioComplete
    condition: "scenario.tags includes '@checkout'"

context:
  required:
    - scenario_name
    - test_results
    - page_screenshots
  optional:
    - api_responses
    - network_logs

actions:
  - name: CaptureCheckoutState
    agent: ExecutionAgent
    tools: [browser_snapshot, get_network_logs]
    prompt: |
      Capture complete checkout state:
      - Cart contents
      - Form data
      - API responses
      - Page screenshots

  - name: ValidateCart
    agent: AnalysisAgent
    depends_on: CaptureCheckoutState
    prompt: |
      Validate cart state:
      - Items present: {cart_items}
      - Quantities correct: {quantities}
      - Prices match: {prices}
      - Discounts applied: {discounts}

  - name: ValidatePayment
    agent: AnalysisAgent
    depends_on: CaptureCheckoutState
    prompt: |
      Validate payment processing:
      - Payment method: {payment_method}
      - Amount charged: {amount}
      - Currency: {currency}
      - Transaction ID: {transaction_id}

  - name: ValidateShipping
    agent: AnalysisAgent
    depends_on: CaptureCheckoutState
    prompt: |
      Validate shipping information:
      - Address: {address}
      - Method: {shipping_method}
      - Cost: {shipping_cost}
      - Delivery date: {delivery_date}

  - name: GenerateCheckoutReport
    agent: ReportingAgent
    depends_on: [ValidateCart, ValidatePayment, ValidateShipping]
    action: generate_checkout_report

configuration:
  require_all_validations: true
  screenshot_on_failure: true
  notify_on_failure: true

output:
  cart_valid: boolean
  payment_valid: boolean
  shipping_valid: boolean
  overall_valid: boolean
  report_path: string
```

### 8.3 Best Practices

1. **Clear Naming**: Use descriptive names for skills, actions, and outputs
2. **Granular Triggers**: Make triggers specific to avoid unnecessary execution
3. **Context Requirements**: Clearly document required context data
4. **Error Handling**: Always handle potential failures gracefully
5. **Idempotency**: Skills should produce the same result given the same input
6. **Logging**: Include comprehensive logging for debugging
7. **Testing**: Test skills with various scenarios before deploying
8. **Documentation**: Document skill purpose, usage, and examples

---

**Document Version:** 1.0
**Last Updated:** 2025-01-11
