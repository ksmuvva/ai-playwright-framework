# Tool Specifications for Claude Playwright Agent

This document defines all custom tools that will be implemented as MCP servers for the Claude Playwright Agent.

---

## Tool Architecture

All tools follow this pattern:
```python
from claude_agent_sdk import tool

@tool(
    name="tool_name",
    description="Human-readable description",
    input_schema={"param": type}
)
async def tool_function(args):
    """Detailed docstring"""
    # Implementation
    return {
        "content": [
            {"type": "text", "text": "Result message"},
            {"type": "image", "data": "base64_image"},  # Optional
            {"type": "resource", "uri": "file:///path"}  # Optional
        ]
    }
```

---

## 1. Playwright Tools (`playwright_tools.py`)

### 1.1 `start_recording`

**Description:** Starts a new browser recording session.

**Input Schema:**
```json
{
  "browser": "chromium | firefox | webkit",
  "headless": false,
  "viewport": {"width": 1920, "height": 1080},
  "base_url": "string (optional)",
  "save_path": "string (path to save recording)"
}
```

**Output:**
```json
{
  "recording_id": "uuid",
  "browser_port": 9222,
  "status": "recording"
}
```

---

### 1.2 `stop_recording`

**Description:** Stops the recording and returns captured actions.

**Input Schema:**
```json
{
  "recording_id": "uuid"
}
```

**Output:**
```json
{
  "actions": [
    {
      "type": "click | input | navigate | wait | assert",
      "selector": "string",
      "value": "string (optional)",
      "timestamp": "ISO8601"
    }
  ],
  "screenshots": ["paths to screenshots"],
  "duration_ms": 1234
}
```

---

### 1.3 `playback_recording`

**Description:** Plays back a recording to verify it works.

**Input Schema:**
```json
{
  "recording_id": "uuid",
  "headless": true,
  "slow_motion": 0
}
```

**Output:**
```json
{
  "success": true,
  "steps_passed": 10,
  "steps_failed": 0,
  "failure_reasons": [],
  "duration_ms": 2345
}
```

---

### 1.4 `capture_page_state`

**Description:** Captures comprehensive page state for AI analysis.

**Input Schema:**
```json
{
  "url": "string",
  "include_screenshot": true,
  "include_dom": true,
  "include_network": false
}
```

**Output:**
```json
{
  "screenshot": "base64",
  "dom_snapshot": "html",
  "accessible_tree": "a11y tree",
  "url": "current_url",
  "title": "page_title",
  "cookies": [],
  "local_storage": {},
  "session_storage": {}
}
```

---

## 2. BDD Tools (`bdd_tools.py`)

### 2.1 `generate_feature_file`

**Description:** Converts recording or requirements to Gherkin feature file.

**Input Schema:**
```json
{
  "source": "recording | requirements",
  "source_data": "actions array or text description",
  "framework": "behave | pytest-bdd",
  "naming_convention": "snake_case | camelCase"
}
```

**Output:**
```gherkin
Feature: User Login
  As a registered user
  I want to log in to my account
  So that I can access my dashboard

  Scenario: Successful login with valid credentials
    Given I am on the login page
    When I enter "user@example.com" in the email field
    And I enter "Password123" in the password field
    And I click the login button
    Then I should be redirected to the dashboard
    And I should see "Welcome back" message
```

---

### 2.2 `generate_step_definitions`

**Description:** Generates Python step definitions from feature file.

**Input Schema:**
```json
{
  "feature_file": "path to .feature",
  "output_path": "path for steps file",
  "use_playwright": true,
  "include_page_objects": true
}
```

**Output:** Python file with step definitions

---

### 2.3 `refactor_scenario`

**Description:** AI-powered scenario refactoring for better maintainability.

**Input Schema:**
```json
{
  "feature_file": "path",
  "refactoring_type": "extract_background | extract_scenario_outline | simplify_steps"
}
```

**Output:** Refactored feature file with diff

---

## 3. Locator Tools (`locator_tools.py`)

### 3.1 `generate_resilient_locator`

**Description:** Generates multiple fallback locator strategies.

**Input Schema:**
```json
{
  "element_description": "Submit button on form",
  "page_context": "HTML snippet or page state",
  "priority": ["data-testid", "aria-label", "text", "css"]
}
```

**Output:**
```json
{
  "primary": "data-testid=submit-btn",
  "fallbacks": [
    "button[type='submit']",
    "text='Submit'",
    "aria-label='submit form'"
  ],
  "confidence": 0.95,
  "reasoning": "Primary uses data-testid for stability..."
}
```

---

### 3.2 `heal_locator`

**Description:** Attempts to find a replacement for a broken locator.

**Input Schema:**
```json
{
  "failed_locator": "css=.submit-btn",
  "page_state": "current DOM snapshot",
  "original_intent": "click submit button"
}
```

**Output:**
```json
{
  "healed_locator": "button[type='submit']",
  "confidence": 0.87,
  "screenshot_highlight": "base64"
}
```

---

### 3.3 `validate_locator`

**Description:** Validates that a locator will work.

**Input Schema:**
```json
{
  "locator": "string",
  "page_url": "url to test against",
  "expected_count": 1
}
```

**Output:**
```json
{
  "valid": true,
  "match_count": 1,
  "visible": true,
  "interactive": true,
  "warnings": []
}
```

---

## 4. Test Data Tools (`test_data_tools.py`)

### 4.1 `generate_test_data`

**Description:** Generates realistic test data based on schema.

**Input Schema:**
```json
{
  "schema": {
    "type": "object",
    "properties": {
      "email": {"type": "string", "format": "email"},
      "name": {"type": "string"},
      "age": {"type": "integer", "minimum": 18}
    }
  },
  "count": 5,
  "locale": "en-US"
}
```

**Output:**
```json
{
  "data": [
    {"email": "john.doe@example.com", "name": "John Doe", "age": 32},
    {"email": "jane.smith@example.com", "name": "Jane Smith", "age": 28}
  ]
}
```

---

### 4.2 `generate_boundary_values`

**Description:** Generates boundary value test data.

**Input Schema:**
```json
{
  "field": "age",
  "constraints": {"min": 18, "max": 65},
  "include_edges": true
}
```

**Output:**
```json
{
  "values": [17, 18, 19, 32, 64, 65, 66],
  "scenarios": {
    "below_minimum": 17,
    "at_minimum": 18,
    "nominal": 32,
    "at_maximum": 65,
    "above_maximum": 66
  }
}
```

---

## 5. Reporting Tools (`reporting_tools.py`)

### 5.1 `generate_html_report`

**Description:** Generates comprehensive HTML test report.

**Input Schema:**
```json
{
  "test_results": "path to JSON results",
  "template": "default | detailed | minimal",
  "include_screenshots": true,
  "include_videos": false
}
```

**Output:** HTML file path

---

### 5.2 `analyze_failures`

**Description:** AI-powered failure analysis and clustering.

**Input Schema:**
```json
{
  "test_results": "path",
  "include_ai_insights": true
}
```

**Output:**
```json
{
  "total_failures": 15,
  "clusters": [
    {
      "name": "Authentication failures",
      "count": 8,
      "root_cause": "API token expired",
      "affected_tests": ["test1", "test2"],
      "suggested_fix": "Refresh token before test suite"
    }
  ],
  "flaky_tests": [
    {
      "test": "test_search",
      "failure_rate": 0.3,
      "suggested_action": "Increase wait timeout"
    }
  ]
}
```

---

### 5.3 `generate_executive_summary`

**Description:** Generates business-friendly summary.

**Input Schema:**
```json
{
  "test_results": "path",
  "include_trends": true,
  "comparison_baseline": "previous run"
}
```

**Output:** Markdown summary

---

## 6. Power Apps Tools (`power_apps_tools.py`)

### 6.1 `analyze_power_apps`

**Description:** Analyzes Power Apps structure for test planning.

**Input Schema:**
```json
{
  "app_url": "url",
  "credentials": "encrypted credentials reference"
}
```

**Output:**
```json
{
  "screens": [
    {"name": "Home", "controls": 15},
    {"name": "Details", "controls": 23}
  ],
  "data_sources": ["SharePoint", "SQL Server"],
  "special_selectors": "Power Apps specific selector strategy"
}
```

---

### 6.2 `generate_power_apps_tests`

**Description:** Generates tests optimized for Power Apps.

**Input Schema:**
```json
{
  "app_analysis": "from analyze_power_apps",
  "test_scenarios": ["user flows to test"]
}
```

**Output:** Feature files with Power Apps selectors

---

## 7. Debug Tools (`debug_tools.py`)

### 7.1 `analyze_failure`

**Description:** Deep analysis of a single test failure.

**Input Schema:**
```json
{
  "test_name": "string",
  "error_message": "string",
  "stack_trace": "string",
  "screenshots": ["paths"],
  "page_state": "DOM snapshot",
  "network_logs": "logs"
}
```

**Output:**
```json
{
  "root_cause": "Element not interactable - covered by modal",
  "confidence": 0.92,
  "evidence": ["modal present in DOM", "element has z-index: 0"],
  "suggested_fix": "Wait for modal to close before clicking",
  "code_fix": "await page.wait_for_selector('.modal', state='hidden')"
}
```

---

### 7.2 `suggest_improvements`

**Description:** Suggests test improvements based on patterns.

**Input Schema:**
```json
{
  "test_file": "path",
  "historical_data": "past test runs"
}
```

**Output:**
```json
{
  "suggestions": [
    {
      "type": "add_wait",
      "location": "line 15",
      "reason": "Frequent timeout here",
      "code": "await page.wait_for_load_state('networkidle')"
    }
  ]
}
```

---

## Tool Server Organization

```python
# tools/playwright_tools.py
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("start_recording", "Start browser recording", {...})
async def start_recording(args): ...

@tool("stop_recording", "Stop recording and get actions", {...})
async def stop_recording(args): ...

# Create the server
playwright_server = create_sdk_mcp_server(
    name="playwright-tools",
    version="1.0.0",
    tools=[start_recording, stop_recording, ...]
)
```

---

## Error Handling

All tools must follow this error response pattern:

```json
{
  "success": false,
  "error": {
    "code": "PLAYWRIGHT_NOT_INSTALLED",
    "message": "Playwright browser not found",
    "suggestion": "Run: playwright install chromium",
    "recoverable": true
  }
}
```

---

**Version:** 1.0
**Last Updated:** 2025-01-11
