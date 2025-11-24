# Structured Logging Guide

This framework now includes comprehensive structured logging using `structlog` for detailed visibility into all framework operations.

## Features

### 🎨 Color-Coded Output
- 🟢 **INFO** (Green) - Normal operations, successful completions
- 🟡 **WARNING** (Yellow) - Warnings, non-critical issues
- 🔴 **ERROR** (Red) - Errors, failures, exceptions
- 🔵 **DEBUG** (Cyan) - Detailed debugging information
- **CRITICAL** (Bold Red) - Critical failures

### 📊 Rich Context
Every log entry includes:
- **Timestamp** - ISO format with local timezone
- **Log Level** - Color-coded for quick identification
- **Event Name** - Structured event identifier (e.g., `scenario_started`, `ai_response`)
- **Context Data** - Relevant details (tokens, duration, status, etc.)
- **Human-Readable Message** - Clear description of what happened

### 🔍 What Gets Logged

#### Framework Initialization
```
2025-11-24T10:30:15.234Z [info] framework_initialization_started 🚀 Initializing AI Playwright Test Framework...
2025-11-24T10:30:15.345Z [info] phoenix_initialization_started Starting Phoenix tracing initialization...
2025-11-24T10:30:16.123Z [info] phoenix_ui_launched ui_url=http://localhost:6006 🎯 Phoenix UI is now running
2025-11-24T10:30:16.234Z [info] phoenix_initialized service_name=ai-playwright-framework ✅ Phoenix tracing initialized successfully
```

#### AI Operations
```
2025-11-24T10:30:20.123Z [info] cot_reasoning_started max_steps=5 🧠 Starting Chain of Thought reasoning...
2025-11-24T10:30:20.234Z [debug] cot_ai_request provider=anthropic model=claude-sonnet-4-5-20250929 Calling anthropic API...
2025-11-24T10:30:22.456Z [info] cot_ai_response input_tokens=1234 output_tokens=567 total_tokens=1801 duration_ms=2222 ✅ AI response received
2025-11-24T10:30:22.567Z [info] cot_reasoning_complete steps_generated=5 duration_ms=2444 ✅ Chain of Thought reasoning completed
```

#### Test Execution
```
2025-11-24T10:30:25.123Z [info] scenario_started scenario="User Login" tags=['@login', '@smoke']
2025-11-24T10:30:25.234Z [info] auth_start user=test@example.com 🔐 Authenticating user...
2025-11-24T10:30:26.789Z [info] auth_success ✅ Authentication successful
2025-11-24T10:30:27.123Z [debug] step_passed step="Given I navigate to login page" ✓
2025-11-24T10:30:28.456Z [info] scenario_passed scenario="User Login" duration_ms=3333 ✅ Scenario passed
```

#### Error Tracking
```
2025-11-24T10:35:12.345Z [error] scenario_failed scenario="Invalid Login" ❌ Scenario failed
2025-11-24T10:35:12.456Z [error] failure_context url=https://app.example.com/login title="Login Page" Page state at failure
2025-11-24T10:35:12.567Z [error] step_failed step="Then I should see error message" status=failed ✗
```

## Configuration

### Log Levels

Set the `LOG_LEVEL` environment variable in your `.env` file:

```bash
LOG_LEVEL=INFO  # Default - recommended for normal use
```

Available levels (from most to least verbose):

#### 1. DEBUG
Shows **everything** - all framework operations, API calls, browser actions, etc.
```bash
LOG_LEVEL=DEBUG
```

**Use when:**
- Troubleshooting test failures
- Understanding framework behavior
- Debugging AI reasoning steps
- Investigating performance issues

**Output includes:**
- All INFO, WARNING, ERROR messages
- Browser page creation details
- Timeout configuration
- Screenshot captures
- Phoenix/OpenTelemetry initialization steps
- Internal state changes

#### 2. INFO (Default)
Shows major events and successful operations.
```bash
LOG_LEVEL=INFO
```

**Use when:**
- Running tests normally
- Monitoring test execution
- Tracking AI token usage
- Viewing scenario results

**Output includes:**
- Framework initialization
- Phoenix status
- Scenario start/end
- Authentication status
- AI reasoning results
- Test statistics
- Warnings and errors

#### 3. WARNING
Shows only warnings and errors.
```bash
LOG_LEVEL=WARNING
```

**Use when:**
- You want minimal output
- Running in CI/CD pipelines
- Only interested in problems

**Output includes:**
- Authentication failures (non-fatal)
- Phoenix initialization warnings
- Deprecated feature warnings
- All errors

#### 4. ERROR
Shows only errors.
```bash
LOG_LEVEL=ERROR
```

**Use when:**
- Only want to see failures
- Running in production monitoring

**Output includes:**
- Scenario failures
- AI request errors
- Browser errors
- Exception stack traces

#### 5. CRITICAL
Shows only critical failures.
```bash
LOG_LEVEL=CRITICAL
```

**Use when:**
- Absolute minimal logging
- Only catastrophic failures matter

## Example Output

### Full Test Execution (LOG_LEVEL=INFO)

```
======================================================================
2025-11-24T10:30:15.123Z [info] framework_initialization_started 🚀 Initializing AI Playwright Test Framework...
======================================================================
2025-11-24T10:30:15.234Z [info] framework_initialized version=2.0.0 python_version=3.11.5 log_level=INFO

2025-11-24T10:30:15.345Z [info] phoenix_init Initializing Phoenix tracing for LLM observability...
2025-11-24T10:30:15.456Z [info] phoenix_initialization_started Starting Phoenix tracing initialization...
2025-11-24T10:30:15.567Z [info] phoenix_ui_launching Launching Phoenix UI server...
2025-11-24T10:30:16.123Z [info] phoenix_ui_launched ui_url=http://localhost:6006 🎯 Phoenix UI is now running - open http://localhost:6006 in your browser
2025-11-24T10:30:16.234Z [info] phoenix_initialized service_name=ai-playwright-framework-python service_version=2.0.0 endpoint=http://localhost:6006/v1/traces ui_launched=true ✅ Phoenix tracing initialized successfully - All LLM calls will now be traced

2025-11-24T10:30:16.345Z [info] phoenix_capabilities capabilities=['LLM request prompts and responses', 'Token usage (input/output/total)', 'Latency metrics', 'Model and provider information', 'Error tracking', 'Chain of thought reasoning traces'] Phoenix will capture the following metrics

2025-11-24T10:30:16.456Z [info] phoenix_enabled endpoint=http://localhost:6006/v1/traces ui_launched=true Phoenix tracing is active - all LLM calls will be traced

2025-11-24T10:30:16.567Z [info] ai_configured provider=anthropic model=claude-sonnet-4-5-20250929 reasoning_enabled=true prompt_caching=true streaming=false ai_cache=true healing=true

2025-11-24T10:30:16.678Z [info] playwright_init Starting Playwright...
2025-11-24T10:30:17.123Z [info] browser_launch browser=chromium headless=false Launching browser...
2025-11-24T10:30:18.456Z [info] browser_configured browser=chromium headless=false viewport={'width': 1920, 'height': 1080}

2025-11-24T10:30:18.567Z [info] framework_ready app_url=https://your-app.com timeout_ms=10000 ✅ Framework initialization complete - Ready to run tests!
======================================================================

======================================================================
2025-11-24T10:30:20.123Z [info] scenario_started scenario="User can login successfully" tags=['@login']

2025-11-24T10:30:20.234Z [info] auth_start user=test@example.com 🔐 Authenticating user...
2025-11-24T10:30:22.456Z [info] auth_success ✅ Authentication successful

✓ Given I navigate to the login page
✓ When I enter valid credentials
✓ And I click the login button
✓ Then I should see the dashboard

2025-11-24T10:30:25.123Z [info] scenario_passed scenario="User can login successfully" ✅ Scenario passed
2025-11-24T10:30:25.234Z [info] screenshots_captured count=4 📸 Screenshots: 4
2025-11-24T10:30:25.345Z [info] scenario_passed scenario="User can login successfully" status=passed duration_ms=5222
======================================================================

======================================================================
2025-11-24T10:30:30.123Z [info] framework_shutdown 🏁 Test execution completed - Starting cleanup...
======================================================================

2025-11-24T10:30:30.234Z [info] healing_statistics failed_locators=2 healing_attempts=2 🔧 Self-healing statistics
2025-11-24T10:30:30.345Z [info] wait_statistics total_waits=15 success_rate=93.3% ⏱️ Wait optimization statistics

2025-11-24T10:30:30.456Z [info] phoenix_shutdown Shutting down Phoenix tracing...
2025-11-24T10:30:30.567Z [info] phoenix_shutdown_complete ✅ Phoenix tracing shutdown successfully

2025-11-24T10:30:30.678Z [info] browser_close Closing browser...
2025-11-24T10:30:30.789Z [info] playwright_stop Stopping Playwright...

======================================================================
2025-11-24T10:30:30.890Z [info] framework_complete ✅ Framework shutdown complete!
======================================================================
```

## Programmatic Usage

### Using the Logger in Your Code

```python
from helpers.logger import get_logger, log_ai_request, log_ai_response, log_error

# Get a logger for your module
logger = get_logger("my_module")

# Log simple messages
logger.info("operation_started", message="Starting operation...")
logger.debug("debug_info", value=123, message="Debug information")
logger.warning("potential_issue", message="This might be a problem")
logger.error("operation_failed", error="Something went wrong")

# Log with rich context
logger.info(
    "user_action",
    user="john@example.com",
    action="click",
    element="submit_button",
    duration_ms=234,
    message="User clicked submit button"
)

# Use helper functions for common operations
log_ai_request("generate_test", "anthropic", "claude-sonnet-4-5-20250929", 1234)
log_ai_response("generate_test", success=True, tokens={'input': 1234, 'output': 567}, duration=2345)
log_error("database_query", DatabaseError("Connection failed"), {'query': 'SELECT * FROM users'})
```

### Custom Logging Functions

The framework provides specialized logging functions:

```python
from helpers.logger import (
    log_framework_info,
    log_phoenix_status,
    log_ai_config,
    log_browser_config,
    log_scenario_start,
    log_scenario_end,
    log_step_execution,
    log_healing_attempt,
)

# Log framework info
log_framework_info()

# Log Phoenix status
log_phoenix_status(enabled=True, endpoint="http://localhost:6006/v1/traces", ui_launched=True)

# Log AI configuration
log_ai_config("anthropic", "claude-sonnet-4-5-20250929", {
    'reasoning_enabled': True,
    'prompt_caching': True,
})

# Log browser config
log_browser_config("chromium", False, {'width': 1920, 'height': 1080})

# Log scenario events
log_scenario_start("User Login", ['@login', '@smoke'])
log_scenario_end("User Login", "passed", duration=3456)

# Log healing attempts
log_healing_attempt("#submit-button", True, "button[type='submit']")
```

## Integration with Phoenix

Structured logs complement Phoenix tracing:

- **Phoenix** - Captures LLM call details, token usage, latency, traces
- **Structured Logs** - Shows framework operations, test execution, business logic

Together they provide complete observability:
1. View traces in Phoenix UI (http://localhost:6006)
2. Review detailed logs in terminal
3. Correlate logs with traces using timestamps
4. Debug issues with full context

## Benefits

### For Development
- **Quick Debugging** - Color-coded logs make issues obvious
- **Rich Context** - See all relevant data at a glance
- **Performance Tracking** - Duration logged for every operation
- **AI Cost Monitoring** - Track token usage in real-time

### For CI/CD
- **Structured Format** - Easy to parse and analyze
- **Configurable Verbosity** - Set appropriate log level
- **Error Tracking** - Clear error messages with context
- **Metrics Collection** - Extract performance metrics from logs

### For Production
- **Observability** - Full visibility into framework behavior
- **Troubleshooting** - Detailed context for debugging issues
- **Audit Trail** - Complete record of all operations
- **Compliance** - Track AI usage and costs

## Best Practices

1. **Use INFO for normal runs** - Provides good visibility without overwhelming output
2. **Use DEBUG for troubleshooting** - When you need to understand what's happening
3. **Review logs after failures** - Detailed context helps identify root cause
4. **Monitor token usage** - Watch for unexpected AI cost increases
5. **Check Phoenix UI** - Complement logs with visual trace analysis

## Troubleshooting

### Too Much Output?
```bash
# Reduce verbosity
LOG_LEVEL=WARNING
```

### Not Enough Detail?
```bash
# Increase verbosity
LOG_LEVEL=DEBUG
```

### Want JSON Logs for Parsing?
Currently logs use human-readable format. For JSON logging, you can modify `helpers/logger.py` to use `structlog.processors.JSONRenderer()` instead of `ConsoleRenderer()`.

### Logs Not Showing Colors?
Ensure your terminal supports ANSI colors. The framework uses `colorama` for cross-platform color support.

## Related Documentation

- [PHOENIX_INTEGRATION.md](./PHOENIX_INTEGRATION.md) - Phoenix tracing setup and usage
- [README.md](./README.md) - Framework overview and getting started
- [CHANGELOG.md](./CHANGELOG.md) - Version history and changes
