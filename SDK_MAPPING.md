# Claude Agent SDK Python Mapping

## Document Information

| Field | Value |
|-------|-------|
| **Project** | AI Playwright Automation Agent |
| **Version** | 2.0 |
| **Date** | 2025-01-11 |
| **Status** | Planning Document |
| **SDK Target** | claude-agent-sdk-python |

---

## Table of Contents

1. [Overview](#overview)
2. [SDK Architecture Mapping](#sdk-architecture-mapping)
3. [Agent Implementation Mapping](#agent-implementation-mapping)
4. [Skill System Mapping](#skill-system-mapping)
5. [Tool Integration Mapping](#tool-integration-mapping)
6. [MCP Integration Mapping](#mcp-integration-mapping)
7. [State Management Mapping](#state-management-mapping)
8. [Communication Mapping](#communication-mapping)
9. [Configuration Mapping](#configuration-mapping)
10. [File Structure Mapping](#file-structure-mapping)

---

## Overview

### Claude Agent SDK Python: Core Concepts

The Claude Agent SDK Python provides a framework for building AI-powered agents with:

1. **Agent Class:** Base class for all agents
2. **Tools:** Functions agents can call (Built-in, Custom, MCP)
3. **Hooks:** Event-driven callbacks for customization
4. **Conversation Management:** Multi-turn dialog handling
5. **Message Queue:** Inter-agent communication
6. **Context Management:** Shared state across operations

### Mapping Strategy

| CPA Concept | SDK Concept | Notes |
|-------------|-------------|-------|
| Orchestrator Agent | `Agent` subclass | Main coordinator |
| Specialist Agents | `Agent` subclasses | Spawned as needed |
| Skills | Tool functions | Callable capabilities |
| MCP Tools | MCP-integrated tools | External process tools |
| Message Queue | Internal message routing | SDK conversation |
| State Manager | Context + File persistence | Hybrid approach |
| CLI Handler | Custom entry point | Uses SDK for core |

---

## SDK Architecture Mapping

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CPA Application                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              CLI Entry Point (cpa CLI)                   │    │
│  └───────────────────┬─────────────────────────────────────┘    │
│                      │                                          │
│                      ▼                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │         OrchestratorAgent (Agent subclass)               │    │
│  │  ┌─────────────────────────────────────────────────┐   │    │
│  │  │         Agent Runtime (SDK provided)             │   │    │
│  │  │  - Conversation management                      │   │    │
│  │  │  - Message routing                              │   │    │
│  │  │  - Tool execution                               │   │    │
│  │  │  - Hook system                                  │   │    │
│  │  └─────────────────────────────────────────────────┘   │    │
│  │                                                          │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │    │
│  │  │  Skill  │ │  Skill  │ │  Skill  │ │  Skill  │       │    │
│  │  │ Handler │ │ Handler │ │ Handler │ │ Handler │       │    │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                      │                                          │
│                      ▼                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Specialist Agents (spawned)                 │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │    │
│  │  │ Ingestion   │ │Deduplicatn ││BDD Conver.  │        │    │
│  │  │   Agent     │ │   Agent     │ │   Agent     │        │    │
│  │  └─────────────┘ └─────────────┘ └─────────────┘        │    │
│  │  ┌─────────────┐ ┌─────────────┐                        │    │
│  │  │ Execution   │ │  Analysis   │                        │    │
│  │  │   Agent     │ │   Agent     │                        │    │
│  │  └─────────────┘ └─────────────┘                        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                      │                                          │
│                      ▼                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Tool Layer                             │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐     │    │
│  │  │ Built-in     │ │ Custom       │ │ MCP Servers  │     │    │
│  │  │ Tools        │ │ Tools        │ │ (Playwright) │     │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### SDK Component Usage

| SDK Component | CPA Usage | Implementation |
|---------------|-----------|----------------|
| `Agent` class | Base for all agents | OrchestratorAgent, IngestionAgent, etc. |
| `Tool` decorator | Skill functions | @skill_tool decorator |
| `Hook` system | Event handling | @hook decorator for lifecycle events |
| `Conversation` | Agent dialog | Multi-turn conversations |
| `MessageQueue` | Inter-agent comms | Internal message routing |
| `Context` | Shared state | Operation context |
| `MCPClient` | Playwright MCP | External MCP server connection |

---

## Agent Implementation Mapping

### Base Agent Structure

All CPA agents inherit from SDK `Agent` class:

```yaml
CPA Agent Structure:
  base_class: claude_agent_sdk.Agent
  inheritance:
    - OrchestratorAgent extends Agent
    - IngestionAgent extends Agent
    - DeduplicationAgent extends Agent
    - BDDConversionAgent extends Agent
    - ExecutionAgent extends Agent
    - AnalysisAgent extends Agent

  required_methods:
    - __init__: Initialize agent with skills
    - get_name: Return agent identifier
    - get_skills: Return list of skill IDs

  optional_overrides:
    - before_tool_use: Pre-processing hook
    - after_tool_use: Post-processing hook
    - on_error: Error handling hook
```

### Orchestrator Agent Mapping

```yaml
OrchestratorAgent:
  sdk_base: Agent
  lifecycle: Singleton (always-running)

  initialization:
    - Load state from state.json
    - Register core skills
    - Initialize message queue
    - Setup hooks

  core_skills:
    - agent_orchestration: Spawn/manage agents
    - cli_handler: Parse and route commands
    - state_manager: Track state changes
    - error_handler: Handle errors gracefully

  hooks_used:
    - SessionStart: Initialize orchestrator
    - UserPromptSubmit: Handle CLI input
    - PreToolUse: Validate tool calls
    - PostToolUse: Update state
    - Stop: Cleanup and persist state

  conversation_pattern:
    type: continuous
    persistence: true
    state_file: .cpa/orchestrator_conversation.json
```

### Specialist Agent Mapping

```yaml
Specialist Agent Template:
  sdk_base: Agent
  lifecycle: Ephemeral (spawned on demand)

  initialization:
    - Receive task from Orchestrator
    - Load agent-specific configuration
    - Register agent skills
    - Setup execution context

  execution_pattern:
    1. Spawned by Orchestrator
    2. Receives task message
    3. Executes assigned skills
    4. Returns result to Orchestrator
    5. Terminates or persists (based on config)

  termination:
    condition: Task complete or timeout
    cleanup: Release resources, update state

  specialists:
    IngestionAgent:
      skills: [playwright-parser, action-extractor, selector-analyzer]

    DeduplicationAgent:
      skills: [element-deduplicator, component-extractor, page-object-generator]

    BDDConversionAgent:
      skills: [gherkin-generator, step-definition-creator, scenario-optimizer]

    ExecutionAgent:
      skills: [test-runner, failure-analyzer, self-healing, report-generator]

    AnalysisAgent:
      skills: [failure-clustering, trend-analysis, executive-summary]
```

---

## Skill System Mapping

### Skill as SDK Tool

```yaml
Skill Mapping:
  conceptual: Skill capability
  sdk_implementation: Tool function
  decorator: @skill_tool

  skill_tool_decorator:
    parameters:
      - name: Skill identifier
      - description: What the skill does
      - category: Functional grouping
      - input_schema: JSON Schema for input
      - output_schema: JSON Schema for output
      - timeout: Max execution time
      - retry_count: Retry attempts

  registration:
    mechanism: Agent.__init__ registers tools
    storage: Agent._tools dictionary
    lookup: By skill name
```

### Skill Function Signature

```yaml
Skill Function Pattern:
  signature: async def skill_name(self, context: Context, **kwargs) -> ToolResult

  parameters:
    self: Agent instance
    context: SDK Context object
      - conversation: Current conversation
      - user_id: User identifier
      - metadata: Additional context
    **kwargs: Skill-specific input parameters

  return: ToolResult
    - success: bool
    - data: Output data (matches output_schema)
    - error: Error message (if failed)
    - metadata: Execution metadata
```

### Skill Categories

```yaml
Skill Categories (mapped to agent ownership):

  orchestration:
    agent: OrchestratorAgent
    skills:
      - agent_orchestration
      - cli_handler
      - state_manager
      - error_handler

  ingestion:
    agent: IngestionAgent
    skills:
      - playwright_parser
      - action_extractor
      - selector_analyzer

  deduplication:
    agent: DeduplicationAgent
    skills:
      - element_deduplicator
      - component_extractor
      - page_object_generator

  bdd_conversion:
    agent: BDDConversionAgent
    skills:
      - gherkin_generator
      - step_definition_creator
      - scenario_optimizer

  execution:
    agent: ExecutionAgent
    skills:
      - test_runner
      - failure_analyzer
      - self_healing
      - report_generator

  analysis:
    agent: AnalysisAgent
    skills:
      - failure_clustering
      - trend_analysis
      - executive_summary
```

---

## Tool Integration Mapping

### Built-in SDK Tools

```yaml
SDK Built-in Tools (used by CPA):

  File Operations:
    - read_file: Read file contents
      usage: Read recordings, configs
    - write_file: Write file contents
      usage: Generate features, steps, reports
    - list_directory: List directory contents
      usage: Discover recordings, features

  Search:
    - search_files: Search file contents
      usage: Find specific patterns in code
    - glob_files: Pattern-based file search
      usage: Find all .js recordings

  System:
    - run_command: Execute shell command
      usage: Run Behave, Playwright, git operations
    - environment: Get/set environment variables
      usage: Configuration management
```

### Custom Tools

```yaml
CPA Custom Tools:

  State Management:
    - read_state: Read state.json
      category: state
      implementation: Custom tool

    - update_state: Update state atomically
      category: state
      implementation: Custom tool with file locking

    - backup_state: Create state backup
      category: state
      implementation: Custom tool

  Recording Processing:
    - parse_playwright_js: Parse Playwright codegen output
      category: parser
      implementation: Custom skill (wrapped as tool)

    - validate_recording: Validate recording format
      category: validation
      implementation: Custom skill (wrapped as tool)

  BDD Operations:
    - generate_gherkin: Generate .feature file
      category: generator
      implementation: Custom skill (wrapped as tool)

    - generate_steps: Generate step definitions
      category: generator
      implementation: Custom skill (wrapped as tool)

  Test Execution:
    - run_behave: Execute Behave tests
      category: execution
      implementation: Wrapper around run_command

    - capture_screenshot: Capture failure screenshot
      category: execution
      implementation: Custom tool
```

### Tool Registration Pattern

```yaml
Tool Registration Flow:

  1. Define tool function with @skill_tool decorator
  2. Agent.__init__ calls self.register_tool()
  3. SDK stores tool in agent's tool registry
  4. Tool available for agent execution
  5. Orchestrator can invoke via message routing

  example:
    agent: IngestionAgent
    tools:
      - playwright_parser (skill)
      - action_extractor (skill)
      - selector_analyzer (skill)
```

---

## MCP Integration Mapping

### MCP Architecture in CPA

```yaml
MCP Integration:

  pattern: Hybrid (in-process + external)

  in_process_mcp:
    description: Custom tools as local MCP server
    implementation: Optional, for tool standardization
    benefits: No subprocess overhead
    tools: Custom state, parsing, generation tools

  external_mcp:
    description: Separate MCP server process
    implementation: Required for Playwright
    server: microsoft/playwright-mcp
    transport: stdio
    tools: All browser automation tools
```

### Playwright MCP Integration

```yaml
Playwright MCP Server:

  source: https://github.com/microsoft/playwright-mcp
  installation: npm install -g @microsoft/playwright-mcp
  transport: stdio (standard input/output)
  protocol: MCP JSON-RPC

  configuration:
    server_config:
      command: npx
      args: ["@microsoft/playwright-mcp"]
      env:
        HEADLESS: "true"
        BROWSER: "chromium"

  client_setup:
    sdk_class: MCPClient
    initialization:
      - Create MCPClient instance
      - Connect to server via stdio
      - List available tools
      - Register tools with agent

  available_tools:
    category: browser_automation
    tools:
      - browser_navigate: Navigate to URL
      - browser_click: Click element
      - browser_fill: Fill input field
      - browser_type: Type text
      - browser_select_option: Select dropdown
      - browser_snapshot: Get page snapshot
      - browser_take_screenshot: Capture screenshot
      - browser_wait_for: Wait for condition
      - browser_console_messages: Get console logs
      - browser_evaluate: Execute JavaScript

  usage_pattern:
    agent: ExecutionAgent (for test execution)
    invocation: Via MCP client
    error_handling: MCP protocol error responses
```

### MCP Client Setup

```yaml
MCP Client Configuration:

  initialization_phase:
    1. Load MCP server config from .cpa/mcp_config.json
    2. Create MCPClient instances for each server
    3. Connect to servers
    4. Discover available tools
    5. Register tools with ExecutionAgent

  runtime_operation:
    - Agent receives message to use MCP tool
    - Agent routes to appropriate MCP client
    - MCP client sends JSON-RPC request
    - MCP server processes and responds
    - Client returns result to agent
    - Agent processes result

  error_handling:
    - Connection failure: Retry with backoff
    - Timeout: Log error, return partial result
    - Server crash: Restart server, retry operation
```

### Custom MCP Server (Optional)

```yaml
Custom MCP Server (for internal tools):

  purpose: Standardize custom tools as MCP protocol
  benefits: Consistent tool interface, future extensibility
  implementation: Optional, can use direct tool registration

  design:
    server_type: Local MCP server (stdio)
    tools_to_expose:
      - state_read: Read state.json
      - state_update: Update state.json
      - parse_recording: Parse Playwright JS
      - generate_gherkin: Generate BDD features

    transport: stdio
    protocol: MCP JSON-RPC

  decision_point:
    implement_now: No (use direct SDK tools)
    consider_later: Yes (if tool ecosystem grows)
```

---

## State Management Mapping

### Hybrid State Strategy

```yaml
State Management Architecture:

  approach: Hybrid (SDK Context + File persistence)

  components:

    1. SDK Context (In-Memory):
      purpose: Runtime state during operation
      scope: Single agent execution
      lifecycle: Per-conversation
      contents:
        - Current operation context
        - Temporary working data
        - Conversation history

    2. State File (Persistent):
      purpose: Persistent framework state
      scope: Cross-session, cross-agent
      lifecycle: Until explicitly deleted
      location: .cpa/state.json
      contents:
        - project_metadata
        - agent_registry
        - recording_index
        - bdd_registry
        - component_library
        - execution_log
        - skills_index
        - configuration

    3. Backups (Rollback):
      purpose: State recovery
      location: .cpa/state/backups/
      rotation: Keep 10 most recent
      trigger: Before major state changes
```

### State Update Pattern

```yaml
State Update Flow:

  1. Agent needs to update state
  2. Agent calls state_update skill/tool
  3. State manager:
     a. Creates backup (if major change)
     b. Acquires file lock
     c. Reads current state
     d. Applies atomic update
     e. Validates new state
     f. Writes to file
     g. Releases lock
  4. Returns updated state to agent
  5. Agent updates in-memory context

  atomic_updates:
    - Use file locking for concurrent safety
    - Write to temp file, then atomic rename
    - Validate before commit
    - Rollback on error

  sdk_integration:
    - State updates are SDK tool calls
    - State manager skill handles logic
    - Context updated with new state
```

### State Access Patterns

```yaml
State Access by Layer:

  OrchestratorAgent:
    access: Read/Write (all sections)
    responsibility: State lifecycle management
    tools:
      - read_state (full access)
      - update_state (all sections)
      - backup_state
      - restore_state

  Specialist Agents:
    access: Read/Write (specific sections)
    pattern: Requested access via Orchestrator
    tools:
      - read_state (limited scope)
      - update_section (specific section only)

  Skills:
    access: Read-only (via context)
    pattern: Receive relevant state in context
    modification: Request through agent

  CLI:
    access: Read (display state)
    tools:
      - cpa status (read state)
      - cpa report (read execution_log)
```

---

## Communication Mapping

### Inter-Agent Communication

```yaml
Agent Communication Architecture:

  pattern: Orchestrated message passing
  transport: SDK internal messaging
  persistence: Message queue in state

  message_flow:
    1. User/CLI sends command to Orchestrator
    2. Orchestrator determines required agent(s)
    3. Orchestrator spawns agent (if not running)
    4. Orchestrator sends task message
    5. Agent processes, executes skills
    6. Agent sends result message
    7. Orchestrator aggregates results
    8. Orchestrator returns to user/CLI

  message_format:
    from: agent_id
    to: agent_id
    type: request | response | event
    payload: task-specific data
    timestamp: ISO 8601
    correlation_id: Track request/response pairs

  sdk_implementation:
    mechanism: SDK Conversation + custom message layer
    storage: state.agent_registry.message_queue
    async: True (all agents async)
```

### Message Types

```yaml
Message Types:

  REQUEST:
    purpose: Agent requests action from another agent
    flow: Orchestrator → Specialist Agent
    example:
      type: REQUEST
      from: orchestrator_agent
      to: ingestion_agent
      payload:
        task: ingest_recording
        recording_file: test.js
        options: {}

  RESPONSE:
    purpose: Agent returns result
    flow: Specialist Agent → Orchestrator
    example:
      type: RESPONSE
      from: ingestion_agent
      to: orchestrator_agent
      payload:
        status: success
        result: {...}
        execution_time: 2.5

  EVENT:
    purpose: Broadcast notification
    flow: Any Agent → All subscribed agents
    example:
      type: EVENT
      from: execution_agent
      to: all
      event_type: TestRunComplete
      payload:
        run_id: run_123
        total: 10
        passed: 7
        failed: 3

  ERROR:
    purpose: Report failure
    flow: Any Agent → Orchestrator
    example:
      type: ERROR
      from: bdd_conversion_agent
      to: orchestrator_agent
      payload:
        error_type: ConversionError
        message: "Invalid action format"
        recording: test.js
```

### Hook Integration

```yaml
SDK Hooks Used by CPA:

  Lifecycle Hooks:
    SessionStart:
      handler: OrchestratorAgent
      action: Load state, initialize
      trigger: CPA daemon starts

    Stop:
      handler: OrchestratorAgent
      action: Persist state, cleanup
      trigger: CPA daemon stops

  Tool Hooks:
    PreToolUse:
      handler: All agents
      action: Validate input, log execution
      trigger: Before any skill/tool call

    PostToolUse:
      handler: All agents
      action: Process output, update state
      trigger: After any skill/tool call

  User Hooks:
    UserPromptSubmit:
      handler: OrchestratorAgent
      action: Parse CLI command, route
      trigger: User runs cpa command

  Agent Hooks:
    SubagentStop:
      handler: OrchestratorAgent
      action: Update agent registry
      trigger: Specialist agent terminates

  Notification Hooks:
    Notification:
      handler: AnalysisAgent
      action: Generate alerts
      trigger: Test failures detected
```

---

## Configuration Mapping

### SDK Configuration Integration

```yaml
Configuration Layers:

  1. SDK Default Configuration:
    source: Claude Agent SDK defaults
    override: By CPA config
    settings:
      - Agent defaults
      - Tool timeouts
      - Message queue size
      - Logging levels

  2. CPA Global Configuration:
    location: .cpa/config.yaml
    scope: Project-wide settings
    contents:
      - Framework configuration
      - Agent settings
      - MCP server settings
      - Skill registrations

  3. Agent-Specific Configuration:
    location: .cpa/agents/<agent_name>/config.yaml
    scope: Single agent
    contents:
      - Agent behavior settings
      - Skill configurations
      - Tool preferences

  4. User Configuration:
    location: .cpa/local.yaml
    scope: User-specific overrides
    contents:
      - User preferences
      - Local paths
      - API keys
```

### Configuration File Structure

```yaml
.cpa/config.yaml:

  sdk_settings:
    agent_timeout: 300000  # 5 minutes
    tool_timeout: 30000    # 30 seconds
    message_queue_size: 1000
    log_level: INFO

  framework:
    project_name: string
    bdd_framework: behave | pytest_bdd
    default_browser: chromium
    headless: true

  agents:
    orchestrator:
      auto_start: true
      persist_state: true

    ingestion:
      batch_size: 10
      parallel: false

    execution:
      parallel_workers: 4
      retry_failed: true

  mcp_servers:
    playwright:
      command: npx
      args: ["@microsoft/playwright-mcp"]
      transport: stdio

  skills:
    custom_path: skills/
    auto_discover: true
```

---

## File Structure Mapping

### Project Directory Structure

```yaml
CPA Project Structure:

  root/                          # Project root
  ├── .cpa/                      # CPA internal directory
  │   ├── state.json             # Framework state (SDK managed)
  │   ├── config.yaml            # Global configuration
  │   ├── local.yaml             # User overrides (gitignored)
  │   ├── mcp_config.json        # MCP server configurations
  │   ├── orchestrator.log       # Orchestrator logs
  │   ├── agents/                # Agent-specific data
  │   │   ├── ingestion/
  │   │   ├── deduplication/
  │   │   ├── bdd_conversion/
  │   │   ├── execution/
  │   │   └── analysis/
  │   ├── state/
  │   │   └── backups/           # State backups
  │   └── conversations/         # SDK conversation storage
  │
  ├── src/                       # Source code
  │   └── claude_playwright_agent/
  │       ├── __init__.py
  │       ├── cli/               # CLI entry point
  │       │   ├── __init__.py
  │       │   └── main.py
  │       ├── agents/            # Agent implementations
  │       │   ├── __init__.py
  │       │   ├── base.py        # Base agent class
  │       │   ├── orchestrator.py
  │       │   ├── ingestion.py
  │       │   ├── deduplication.py
  │       │   ├── bdd_conversion.py
  │       │   ├── execution.py
  │       │   └── analysis.py
  │       ├── skills/            # Skill implementations
  │       │   ├── __init__.py
  │       │   ├── base.py        # Base skill class
  │       │   ├── orchestration/
  │       │   ├── ingestion/
  │       │   ├── deduplication/
  │       │   ├── bdd_conversion/
  │       │   ├── execution/
  │       │   └── analysis/
  │       ├── tools/             # Custom tools
  │       │   ├── __init__.py
  │       │   ├── state_tools.py
  │       │   ├── file_tools.py
  │       │   └── parser_tools.py
  │       ├── mcp/               # MCP client implementations
  │       │   ├── __init__.py
  │       │   ├── base_client.py
  │       │   └── playwright_client.py
  │       ├── state/             # State management
  │       │   ├── __init__.py
  │       │   ├── manager.py
  │       │   └── schema.py
  │       └── utils/             # Utilities
  │           ├── __init__.py
  │           ├── logging.py
  │           └── validation.py
  │
  ├── features/                  # BDD feature files (generated)
  │   └── *.feature
  │
  ├── features/steps/            # Step definitions (generated)
  │   └── *.py
  │
  ├── pages/                     # Page objects (generated)
  │   └── *.py
  │
  ├── recordings/                # Playwright recordings (input)
  │   └── *.js
  │
  ├── reports/                   # Test execution reports
  │   └── run_*/
  │
  ├── skills/                    # Custom skills (user-defined)
  │   └── */
  │
  ├── tests/                     # Test suite
  │   ├── unit/
  │   ├── integration/
  │   └── e2e/
  │
  ├── pyproject.toml             # Python package config
  ├── README.md
  └── .gitignore
```

---

## Implementation Roadmap

### Phase 1: SDK Foundation (Week 1-2)

```yaml
Foundation Tasks:
  - Set up claude-agent-sdk-python dependency
  - Create base agent class (extends SDK Agent)
  - Implement skill decorator and registration
  - Create CLI entry point
  - Set up basic configuration system
  - Initialize state.json structure

  deliverables:
    - Running CLI: cpa --help
    - Base OrchestratorAgent (minimal)
    - State file initialized
```

### Phase 2: Core Skills (Week 3-4)

```yaml
Core Skills Implementation:
  - Orchestrator skills:
    - cli_handler: Parse commands
    - state_manager: Read/write state
  - File I/O tools (SDK built-in)
  - Basic error handling

  deliverables:
    - cpa init: Create new project
    - cpa status: Show framework state
    - State persistence working
```

### Phase 3: MCP Integration (Week 5)

```yaml
MCP Integration:
  - Integrate microsoft/playwright-mcp
  - Create MCP client wrapper
  - Register browser tools
  - Test browser automation

  deliverables:
    - Playwright MCP connected
    - Browser tools available
    - Basic browser navigation working
```

### Phase 4: Ingestion Pipeline (Week 6-7)

```yaml
Ingestion Agent:
  - Implement IngestionAgent
  - Create ingestion skills:
    - playwright_parser
    - action_extractor
    - selector_analyzer
  - Implement cpa ingest command

  deliverables:
    - cpa ingest test.js
    - Parsed actions in state.json
    - Selector fragility analysis
```

### Phase 5: Deduplication & BDD (Week 8-9)

```yaml
Deduplication & BDD:
  - Implement DeduplicationAgent
  - Create deduplication skills:
    - element_deduplicator
    - component_extractor
  - Implement BDDConversionAgent
  - Create BDD conversion skills:
    - gherkin_generator
    - step_definition_creator

  deliverables:
    - Common elements identified
    - .feature files generated
    - Step definitions generated
```

### Phase 6: Execution & Analysis (Week 10-11)

```yaml
Execution & Analysis:
  - Implement ExecutionAgent
  - Create execution skills:
    - test_runner
    - failure_analyzer
    - self_healing
    - report_generator
  - Implement AnalysisAgent
  - Create analysis skills:
    - failure_clustering
    - trend_analysis

  deliverables:
    - cpa run working
    - Test reports generated
    - Failure analysis working
```

### Phase 7: Polish & Release (Week 12)

```yaml
Final Tasks:
  - Comprehensive testing
  - Documentation completion
  - Performance optimization
  - Error handling refinement
  - Packaging for distribution

  deliverables:
    - Production-ready CPA
    - Complete documentation
    - Example workflows
    - Release artifacts
```

---

## Summary

| Component | SDK Mapping | Implementation Notes |
|-----------|-------------|---------------------|
| Orchestrator | `Agent` subclass | Singleton, manages other agents |
| Specialist Agents | `Agent` subclasses | Ephemeral, spawned on demand |
| Skills | Tool functions | Decorated with `@skill_tool` |
| State | SDK Context + File | Hybrid persistence strategy |
| MCP | `MCPClient` | Playwright MCP integration |
| Hooks | SDK Hook system | Lifecycle and event handling |
| CLI | Custom entry point | Uses SDK for agent operations |

---

**Document Version:** 1.0
**Last Updated:** 2025-01-11
