# Arize Phoenix Integration Guide

This guide explains how to use Arize Phoenix for LLM observability and tracing in the AI Playwright Framework.

## 🎯 What's New in v2.0.0

- ✅ **Auto-Launch Phoenix UI** - Phoenix now starts automatically when the framework initializes!
- ✅ **Structured Logging** - Detailed, color-coded logs with timestamps and context
- ✅ **Early Initialization** - Phoenix starts in `before_all()` hook, capturing all LLM calls
- ✅ **Comprehensive Logging** - Every framework operation is logged with rich context
- ✅ **Token Usage Tracking** - Real-time visibility into AI costs and performance

## Overview

Arize Phoenix is integrated into this framework to provide comprehensive observability for all LLM interactions. It captures:

- **All LLM API calls** (Anthropic Claude, OpenAI)
- **Token usage** (input tokens, output tokens, total tokens with cost estimation)
- **Response latency** (milliseconds per request)
- **Request/response payloads** (prompts and completions)
- **Error tracking** and exceptions with full stack traces
- **Chain of Thought** and **Tree of Thought** reasoning traces
- **Framework operations** (browser launch, authentication, scenario execution)

## Quick Start

### 1. Install Dependencies

**Python (Recommended):**
```bash
cd cli/templates/python
uv sync  # or: pip install -r requirements.txt
```

The framework now includes:
- `arize-phoenix>=12.16.0` - Phoenix observability platform
- `opentelemetry-*` - OpenTelemetry SDK and exporters
- `structlog>=24.1.0` - Structured logging library
- `colorama>=0.4.6` - Cross-platform colored terminal output

### 2. Configure Environment Variables

Add the following to your `.env` file (or use the provided `.env.example`):

```bash
# Phoenix Tracing & Observability
ENABLE_PHOENIX_TRACING=true        # Enable Phoenix tracing (default: true)
PHOENIX_LAUNCH_UI=true             # Auto-launch Phoenix UI (default: true)
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006/v1/traces
SERVICE_NAME=ai-playwright-framework
SERVICE_VERSION=2.0.0

# Logging Configuration
LOG_LEVEL=INFO                     # DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
```

### 3. Run Your Tests - Phoenix Launches Automatically! 🚀

Phoenix now starts automatically when you run tests. No manual setup required!

```bash
# Phoenix will auto-launch and you'll see detailed logs:
behave features/your_test.feature

# Initialize Phoenix (this happens automatically in reasoning.py)
PhoenixTracer.initialize()

# Access UI at: http://localhost:6006
```

### 4. Use the Framework (Tracing is Automatic)

Once configured, all LLM calls are automatically traced:

**TypeScript:**
```typescript
import { AnthropicClient } from './ai/anthropic-client';

const client = new AnthropicClient();
// All calls to generateBDDScenario, healLocator, etc. are automatically traced
const result = await client.generateBDDScenario(recording, 'Login Test');
```

**Python:**
```python
from helpers.reasoning import ChainOfThought

cot = ChainOfThought(None)  # Tracing initializes automatically
result = cot.reason(prompt, context)
```

## Features

### 1. Automatic Instrumentation

Phoenix tracing is automatically enabled for:

- **TypeScript:**
  - `generateBDDScenario()` (with and without reasoning)
  - `healLocator()`
  - `generateTestData()`
  - `optimizeWaits()`
  - `analyzePatterns()`

- **Python:**
  - `ChainOfThought.reason()`
  - `TreeOfThought.explore()`
  - All LLM helper functions

### 2. Trace Attributes

Each LLM call captures:

| Attribute | Description | Example |
|-----------|-------------|---------|
| `llm.provider` | LLM provider | `anthropic`, `openai` |
| `llm.model` | Model identifier | `claude-sonnet-4-5-20250929` |
| `llm.request.prompt` | Input prompt (truncated) | First 1000 chars |
| `llm.max_tokens` | Max tokens requested | `4000` |
| `llm.usage.prompt_tokens` | Input tokens consumed | `523` |
| `llm.usage.completion_tokens` | Output tokens generated | `1024` |
| `llm.usage.total_tokens` | Total tokens | `1547` |
| `llm.latency_ms` | Request duration | `2340.5` |
| `llm.response` | Output text (truncated) | First 1000 chars |

### 3. Error Tracking

Errors are automatically captured with:
- Exception type and message
- Stack traces
- Span status marked as `ERROR`
- Retry attempt tracking

## Phoenix UI

Access the Phoenix UI at **http://localhost:6006** to view:

### Traces View
- Timeline of all LLM requests
- Hierarchical trace structure
- Request/response details
- Token usage per call

### Analytics Dashboard
- Token consumption trends
- Latency percentiles (p50, p95, p99)
- Error rates
- Cost estimation (based on token usage)

### Search & Filter
- Filter by model, provider, or operation
- Search by prompt content
- Time-based filtering
- Status filtering (success/error)

## Configuration Options

### TypeScript Configuration

**Location:** `cli/src/tracing/phoenix-tracer.ts`

```typescript
PhoenixTracer.initialize(
  'http://localhost:6006/v1/traces',  // Phoenix endpoint
  'ai-playwright-framework',           // Service name
  '1.0.0'                              // Service version
);
```

### Python Configuration

**Location:** `cli/templates/python/helpers/phoenix_tracer.py`

```python
PhoenixTracer.initialize(
    phoenix_endpoint='http://localhost:6006/v1/traces',
    service_name='ai-playwright-framework-python',
    service_version='1.0.0',
    launch_ui=True  # Auto-launch Phoenix UI
)
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_PHOENIX_TRACING` | `true` | Enable/disable tracing |
| `PHOENIX_COLLECTOR_ENDPOINT` | `http://localhost:6006/v1/traces` | OTLP endpoint |
| `PHOENIX_LAUNCH_UI` | `true` | Launch Phoenix UI (Python only) |
| `SERVICE_NAME` | `ai-playwright-framework` | Service identifier |
| `SERVICE_VERSION` | `1.0.0` | Version for traces |

## Disabling Phoenix Tracing

To disable Phoenix tracing:

```bash
# In .env file
ENABLE_PHOENIX_TRACING=false
```

Or programmatically:

**TypeScript:**
```typescript
// Don't call PhoenixTracer.initialize()
// Tracing will be skipped automatically
```

**Python:**
```python
import os
os.environ['ENABLE_PHOENIX_TRACING'] = 'false'
```

## Advanced Usage

### Custom Span Attributes

**TypeScript:**
```typescript
import { trace } from '@opentelemetry/api';

const tracer = trace.getTracer('my-custom-tracer');
tracer.startActiveSpan('custom-operation', (span) => {
  span.setAttribute('custom.attribute', 'value');
  // Your code here
  span.end();
});
```

**Python:**
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span('custom-operation') as span:
    span.set_attribute('custom.attribute', 'value')
    # Your code here
```

### Export Traces

Phoenix supports exporting traces to:
- **Arize Platform** (for production observability)
- **CSV** (for offline analysis)
- **Parquet** (for data engineering workflows)

See [Phoenix documentation](https://docs.arize.com/phoenix) for export details.

## Troubleshooting

### Phoenix UI Not Launching

**Python:**
```python
# Manually launch Phoenix
import phoenix as px
session = px.launch_app()
print(session.url)  # Should print: http://localhost:6006
```

### No Traces Appearing

1. Check that tracing is enabled: `ENABLE_PHOENIX_TRACING=true`
2. Verify endpoint configuration: `PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006/v1/traces`
3. Ensure Phoenix is running: Visit http://localhost:6006
4. Check console logs for initialization errors

### TypeScript Traces Missing

```bash
# Check OpenTelemetry packages are installed
cd cli
npm list | grep opentelemetry
```

### Python Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt

# Verify Phoenix installation
python -c "import phoenix; print(phoenix.__version__)"
```

## Performance Impact

Phoenix tracing has minimal performance overhead:
- **Latency:** < 5ms per span
- **Memory:** ~10MB for SDK
- **Network:** Batched exports (default: every 5 seconds)

For production, consider:
- Setting `PHOENIX_LAUNCH_UI=false` (Python)
- Using sampling (trace 10% of requests)
- Exporting to Arize Platform instead of local UI

## Best Practices

1. **Always enable in development** - Catch issues early
2. **Monitor token usage** - Optimize prompts to reduce costs
3. **Track latency trends** - Identify slow LLM calls
4. **Review error traces** - Debug failures quickly
5. **Export production traces** - Use Arize Platform for persistent storage

## Resources

- [Arize Phoenix Documentation](https://docs.arize.com/phoenix)
- [OpenTelemetry Specification](https://opentelemetry.io/docs/)
- [Phoenix GitHub Repository](https://github.com/Arize-ai/phoenix)

## Support

For issues or questions:
1. Check the [Phoenix documentation](https://docs.arize.com/phoenix)
2. Review this framework's GitHub issues
3. Join the [Arize Slack community](https://arize.com/slack)
