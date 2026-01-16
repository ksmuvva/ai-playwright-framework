# AI Playwright Framework - Architecture Documentation

## Overview

The AI Playwright Framework is an intelligent test automation framework that combines:
- Self-healing selectors with memory
- Multi-agent orchestration
- BDD test generation
- Real-time reporting
- CI/CD integration

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Layer                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Commands │  │  Memory  │  │Generate  │  │   Test   │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
└───────┼────────────┼────────────┼────────────┼────────────┘
        │            │            │            │
┌───────▼────────────▼────────────▼────────────▼────────────┐
│                  Agent Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ Orchestrator│→ │Ingestion    │  │Execution    │      │
│  │   Agent     │  │   Agent     │  │   Agent     │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
│         ↓                ↓                ↓                │
│  ┌─────────────────────────────────────────────────┐     │
│  │          AgentLifecycleManager                 │     │
│  └─────────────────────────────────────────────────┘     │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│                Services Layer                             │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐           │
│  │  Memory   │  │Self-Healing│  │   BDD     │           │
│  │  Manager  │  │   Engine   │  │ Converter │           │
│  └───────────┘  └───────────┘  └───────────┘           │
└───────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│                Infrastructure Layer                       │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐           │
│  │   State   │  │  Report   │  │   Test    │           │
│  │  Manager  │  │Generator  │  │Discovery  │           │
│  └───────────┘  └───────────┘  └───────────┘           │
└───────────────────────────────────────────────────────────┘
```

## Data Flow

### Test Execution Flow

1. **Test Recording**
   - Playwright codegen creates `.spec.js` files
   - Stored in `recordings/` directory

2. **Ingestion**
   - IngestionAgent parses recordings
   - Extracts actions, metadata, screenshots
   - Stores in StateManager

3. **Deduplication**
   - DeduplicationAgent identifies duplicates
   - Merges similar test cases
   - Removes redundancy

4. **BDD Conversion**
   - BDDConversionAgent generates Gherkin scenarios
   - Creates feature files
   - Generates step definitions

5. **Test Discovery**
   - TestDiscovery scans for tests
   - Catalogs scenarios, step definitions, page objects

6. **Test Execution**
   - TestExecutionEngine runs tests
   - Parallel execution support
   - Retry logic with exponential backoff

7. **Reporting**
   - Results stored in memory
   - HTML reports generated
   - Trends analyzed over time

## Agent Communication

### Message Bus Architecture

```python
# Agent publishes message
await agent_bus.publish(AgentMessage(
    channel="test_execution",
    message_type="test_complete",
    data={"test_name": "login", "status": "passed"},
    priority=MessagePriority.HIGH,
))

# Other agents subscribe
await agent_bus.subscribe(
    agent_id="analytics_agent",
    channel="test_execution",
    callback=handle_test_event,
)
```

## Memory System

### Memory Types

1. **Short-term Memory**
   - Ephemeral session data
   - Limited capacity (default: 1000 entries)
   - Fast access, auto-eviction

2. **Long-term Memory**
   - Persistent knowledge
   - Unlimited capacity
   - Stored in SQLite (`.cpa/memory.db`)

3. **Semantic Memory**
   - Concepts and patterns
   - Used for self-healing strategies
   - Tag-based retrieval

4. **Episodic Memory**
   - Test execution events
   - Timestamped records
   - Historical analysis

5. **Working Memory**
   - Current task context
   - Very limited (~50 items)
   - LRU eviction

### Memory Operations

```python
# Store information
await agent.remember(
    key="test_result",
    value={"status": "passed"},
    memory_type="episodic",
    tags=["test", "passed"],
    priority="high",
)

# Recall information
result = await agent.recall("test_result")

# Search memories
passed_tests = await agent.search_memories(tags=["passed"])
```

## Self-Healing System

### Healing Strategies

1. **Fallback Selector** - Use alternative selectors
2. **ARIA Attributes** - Use aria-label, aria-describedby
3. **Data-testid** - Use data-test-id attributes
4. **Text Content** - Match by text
5. **Role Based** - Match by ARIA role
6. **Parent Relative** - Navigate DOM from parent
7. **Sibling Relative** - Navigate from siblings
8. **Partial Match** - Fuzzy selector matching
9. **Regex Pattern** - Pattern-based matching

### Memory-Powered Healing

```python
# First failure: tries strategies, remembers successful one
page.click("#login-button")  # Fails, heals with #login-btn

# Future failures: uses remembered strategy immediately
page.click("#login-button")  # Auto-healed with #login-btn
```

## Multi-Agent Coordination

### Agent Lifecycle

1. **Spawning**
   ```python
   agent = await lifecycle.spawn_agent("ingestion", config)
   ```

2. **Monitoring**
   ```python
   status = lifecycle.get_agent_status(agent_id)
   ```

3. **Cleanup**
   ```python
   await lifecycle.stop_agent(agent_id)
   ```

### Workflow Execution

```python
result = await orchestrator.run_workflow(
    workflow_type="bdd_conversion",
    input_data={"recording_file": "test.spec.js"},
)
```

## Configuration

### Environment Variables

```bash
# Framework
CPA_PROJECT_PATH=/path/to/project
CPA_MEMORY_DB_PATH=.cpa/memory.db
CPA_LOG_LEVEL=INFO

# AI Provider
CPA_AI_PROVIDER=anthropic
CPA_AI_MODEL=claude-3-5-sonnet-20241022
CPA_AI_MAX_TOKENS=8192

# Self-Healing
CPA_SELF_HEALING_ENABLED=true
CPA_SELF_HEALING_THRESHOLD=0.8
CPA_SELF_HEALING_MAX_ATTEMPTS=3

# Test Execution
CPA_PARALLEL_WORKERS=4
CPA_TEST_TIMEOUT=30000
CPA_RETRY_MAX_RETRIES=3
```

### Config File

```yaml
# config/config.yaml
ai:
  provider: anthropic
  model: claude-3-5-sonnet-20241022
  max_tokens: 8192

self_healing:
  enabled: true
  auto_apply_threshold: 0.8
  max_attempts: 3

memory:
  persist_to_disk: true
  db_path: .cpa/memory.db
  max_short_term: 1000

testing:
  parallel_workers: 4
  timeout: 30000
  retries: 3
```

## Performance Optimization

### Async Operations
- All I/O operations are async
- Parallel test execution
- Concurrent agent communication

### Caching
- Test result caching (TTL: 1 hour)
- Memory consolidation caching
- Selector pattern caching

### Resource Management
- Agent lifecycle cleanup
- Memory database connection pooling
- Automatic resource deallocation

## Security

### Best Practices

1. **Secrets Management**
   - Use environment variables for API keys
   - Never commit `.env` files
   - Use secret managers in production

2. **Input Validation**
   - Validate all user inputs
   - Sanitize file paths
   - Check file permissions

3. **Access Control**
   - Restrict file system access
   - Validate agent permissions
   - Audit logging

## Troubleshooting

### Common Issues

1. **Tests timeout**
   - Increase `CPA_TEST_TIMEOUT`
   - Check network connectivity
   - Verify selectors are correct

2. **Self-healing not working**
   - Enable with `CPA_SELF_HEALING_ENABLED=true`
   - Check healing analytics
   - Verify state manager is initialized

3. **Memory database errors**
   - Ensure `.cpa/` directory exists
   - Check file permissions
   - Run `cpa memory stats` to verify

4. **Agent communication failures**
   - Check agent IDs are unique
   - Verify agent lifecycle
   - Review message bus logs

### Debug Mode

```bash
# Enable debug logging
CPA_LOG_LEVEL=DEBUG cpa test run

# Run with verbose output
cpa --verbose test run features/

# Check memory
cpa memory query "selector_healing" --limit 20
cpa memory stats
cpa memory list
```

## API Reference

### CLI Commands

#### Memory Management
```bash
cpa memory query <query> [--type TYPE] [--limit N]
cpa memory list [--type TYPE]
cpa memory get <key>
cpa memory delete <key>
cpa memory clear [--type TYPE]
cpa memory stats
cpa memory export <file>
cpa memory import <file>
cpa memory consolidate
cpa memory recent [--type TYPE] [--limit N]
```

#### Test Management
```bash
cpa test discover [--project PATH]
cpa test run [FILES...] [--tags TAGS] [--parallel] [--workers N]
cpa test find <pattern>
cpa test filter-by-tag <tags>
cpa test validate
```

#### Step Generation
```bash
cpa generate-steps <feature_file> [--output PATH] [--framework FRAMEWORK]
```

### Python API

#### Using Agents

```python
from src.claude_playwright_agent.agents.ingest_agent import IngestionAgent

agent = IngestionAgent()
await agent.initialize()

result = await agent.process({"recording_file": "test.spec.js"})

await agent.cleanup()
```

#### Using Memory

```python
from src.claude_playwright_agent.agents.base import BaseAgent

class MyAgent(BaseAgent):
    async def process(self, input_data):
        # Store
        await self.remember("key", {"data": "value"})

        # Recall
        result = await self.recall("key")

        # Search
        results = await self.search_memories(tags=["tag1", "tag2"])

        return result
```

#### Using Self-Healing

```python
from pages.base_page import BasePage
from src.claude_playwright_agent.state.manager import StateManager

state = StateManager()
page = BasePage(
    page=browser_page,
    base_url="https://example.com",
    state_manager=state,
    enable_self_healing=True,
)

# Self-healing is automatic
page.click("#selector")  # Will auto-heal if needed
```

## Contributing

See `CONTRIBUTING.md` for guidelines.

## License

MIT License - See LICENSE file for details.
