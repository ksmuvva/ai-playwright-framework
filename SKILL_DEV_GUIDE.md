# Skill Development Guide

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
2. [Skill Architecture](#skill-architecture)
3. [Skill Types](#skill-types)
4. [Development Workflow](#development-workflow)
5. [Skill Design Principles](#skill-design-principles)
6. [Custom Skill Template](#custom-skill-template)
7. [Integration Patterns](#integration-patterns)
8. [Testing Strategy](#testing-strategy)
9. [Best Practices](#best-practices)
10. [Examples](#examples)

---

## Overview

### What is a Skill?

A **Skill** is a self-contained unit of functionality that an agent can perform. Skills are the building blocks of agent capabilities, enabling agents to:

- Parse and process data
- Generate content (code, text, reports)
- Analyze and categorize information
- Execute external operations
- Communicate with other agents

### Skill vs. Agent

| Aspect | Skill | Agent |
|--------|-------|-------|
| **Purpose** | Single capability | Collection of related skills |
| **Lifecycle** | Called as needed | Spawned/managed by Orchestrator |
| **State** | Stateless (usually) | Maintains conversation context |
| **Communication** | Returns result | Can message other agents |
| **Example** | `playwright-parser` | Ingestion Agent |

### Skill vs. MCP Tool

| Aspect | Skill | MCP Tool |
|--------|-------|----------|
| **Scope** | Business logic capability | Low-level system operation |
| **Host** | Runs within agent process | Runs in separate process |
| **Protocol** | Direct function call | MCP protocol (JSON-RPC) |
| **Use Case** | "Parse Playwright recording" | "Take browser screenshot" |
| **Example** | `action-extractor` | `browser_click` (Playwright MCP) |

---

## Skill Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                      Skill Container                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Trigger   │→│   Execute   │→│   Return    │         │
│  │   Handler   │  │   Method    │  │   Result    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                 │                  │              │
│         ▼                 ▼                  ▼              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Condition  │  │   Context   │  │   Output    │         │
│  │   Checker   │  │   Builder   │  │   Formatter │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Skill Metadata Structure

```yaml
skill:
  id: string                    # Unique identifier
  name: string                  # Display name
  version: string               # Semantic version
  agent: string                 # Owning agent
  category: string              # Functional category

  # Trigger specification
  trigger:
    type: automatic | manual | event
    condition: string           # When this skill activates

  # Execution specification
  execution:
    timeout: int                # Max execution time (ms)
    retry_count: int            # Retry attempts on failure
    dependencies: []            # Required skills/tools

  # I/O Specification
  input:
    schema: object              # Input data schema
    validation: string          # Validation rules

  output:
    schema: object              # Output data schema
    format: json | markdown | text

  # Error handling
  errors:
    recovery: string            # Recovery strategy
    fallback: string            # Fallback skill ID
```

---

## Skill Types

### 1. Parser Skills

**Purpose:** Convert raw data into structured format

**Characteristics:**
- Input: Raw file/string (JS, JSON, XML)
- Output: Structured data (JSON, dict)
- Stateless: No side effects
- Fast: < 5 seconds typically

**Examples:**
- `playwright-parser`: Parse Playwright codegen JS
- `gherkin-parser`: Parse .feature files
- `report-parser`: Parse test reports

**Design Pattern:**
```
Input (Raw) → Tokenize → Parse → Validate → Output (Structured)
```

### 2. Generator Skills

**Purpose:** Create new content from structured data

**Characteristics:**
- Input: Structured data + templates
- Output: Generated content (code, text)
- May use LLM: For natural language generation
- Template-driven: Uses defined patterns

**Examples:**
- `gherkin-generator`: Generate BDD scenarios
- `step-definition-creator`: Generate Python step code
- `page-object-generator`: Generate Page Object classes

**Design Pattern:**
```
Input (Data) → Template → Render → Validate → Output (Content)
```

### 3. Analysis Skills

**Purpose:** Extract insights from data

**Characteristics:**
- Input: Structured data
- Output: Analysis results, classifications
- May be complex: Longer execution time
- Context-aware: Uses domain knowledge

**Examples:**
- `action-extractor`: Classify actions
- `selector-analyzer`: Score selector fragility
- `failure-clustering`: Group similar failures

**Design Pattern:**
```
Input (Data) → Analyze → Classify → Score → Output (Insights)
```

### 4. Execution Skills

**Purpose:** Perform external operations

**Characteristics:**
- Input: Action parameters
- Output: Execution results
- Side effects: Changes external state
- May timeout: External system dependency

**Examples:**
- `test-runner`: Execute BDD tests
- `browser-automation`: Control browser (via MCP)
- `file-operations`: Manage files

**Design Pattern:**
```
Input (Params) → Prepare → Execute → Capture → Output (Result)
```

### 5. Orchestrator Skills

**Purpose:** Coordinate multiple agents/skills

**Characteristics:**
- Input: High-level command
- Output: Coordination result
- Manages state: Updates agent registry
- Spawns agents: Creates child processes

**Examples:**
- `agent-orchestration`: Manage agent lifecycle
- `cli-handler`: Parse and route CLI commands
- `state-manager`: Track framework state

**Design Pattern:**
```
Input (Command) → Parse → Route → Coordinate → Aggregate → Output
```

---

## Development Workflow

### Phase 1: Discovery

**Goal:** Define what the skill should do

**Questions to Answer:**
1. What problem does this skill solve?
2. What agent will own this skill?
3. What type of skill is it (parser, generator, etc.)?
4. What are the input and output formats?
5. What dependencies does it have (other skills, tools)?

**Deliverable:** Skill Concept Document

```yaml
Skill Concept:
  name: element-deduplicator
  purpose: Identify duplicate UI elements across recordings
  agent: Deduplication Agent
  type: Analysis
  input: List of parsed actions from multiple recordings
  output: Common elements + reusable components
  dependencies: [playwright-parser]
```

### Phase 2: Specification

**Goal:** Define the skill contract

**Specification Document:**

```yaml
Skill Specification:
  id: element-deduplicator
  version: 1.0.0
  agent: deduplication_agent

  trigger:
    type: automatic
    condition: After ingestion completes

  input:
    schema:
      recordings:
        type: array
        items:
          recording_id: string
          actions: array
    validation: All recordings must be parsed

  output:
    schema:
      common_elements: array
      reusable_components: array
      deduplication_report: object
    format: json

  execution:
    timeout: 30000
    retry_count: 2
    dependencies: []

  algorithm:
    type: rule_based
    rules:
      - EXACT_MATCH
      - STRUCTURAL_SIMILARITY
      - COMPONENT_PATTERN
      - NAVIGATION_DEDUP
```

### Phase 3: Design

**Goal:** Plan the implementation approach

**Design Decisions:**

1. **Algorithm Selection:** Rule-based vs LLM vs hybrid
2. **Data Structures:** How to represent intermediate data
3. **Error Handling:** What can go wrong and how to handle
4. **Validation:** Input and output validation rules
5. **Performance:** Optimization considerations

**Design Document Outline:**

```markdown
# Element Deduplicator Skill Design

## Algorithm
- Rule-based deduplication (NO ML)
- Four matching strategies

## Data Structures
- RecordingIndex: Map recording_id → actions
- ElementSignature: selector + action_type hash
- ComponentPattern: Identified reusable UI elements

## Matching Rules
1. EXACT_MATCH: Same selector + action
2. STRUCTURAL: Same selector pattern
3. COMPONENT: Common UI element types
4. NAVIGATION: Same base URLs

## Error Handling
- Missing recording_id: Skip with warning
- Invalid action format: Log and continue
- Empty actions list: Return empty results

## Validation
- Input: At least 2 recordings required
- Output: All element signatures must be unique
```

### Phase 4: Implementation Planning

**Goal:** Prepare for coding (without writing code)

**Implementation Checklist:**

- [ ] File location: `src/claude_playwright_agent/agents/deduplication/skills/`
- [ ] Dependencies: List required packages
- [ ] Configuration: Any config file parameters
- [ ] Testing strategy: Unit, integration, end-to-end
- [ ] Documentation: Docstrings, examples
- [ ] Error scenarios: All edge cases covered

**File Structure:**

```
deduplication_agent/
├── skills/
│   ├── __init__.py
│   ├── element_deduplicator.py
│   ├── component_extractor.py
│   └── page_object_generator.py
├── agent.py
└── config.yaml
```

### Phase 5: Testing Design

**Goal:** Define test coverage

**Test Categories:**

1. **Unit Tests:** Test skill in isolation
2. **Integration Tests:** Test with dependencies
3. **E2E Tests:** Test in full workflow
4. **Edge Cases:** Boundary conditions

**Test Specification:**

```yaml
Test Cases:
  - name: Exact match detection
    input: Two recordings with identical selectors
    expected: One common element identified

  - name: Structural similarity
    input: Same selector pattern, different values
    expected: Parameterized step suggested

  - name: No common elements
    input: Completely different recordings
    expected: Empty common_elements array

  - name: Single recording
    input: Only one recording
    expected: Error (min 2 required)
```

---

## Skill Design Principles

### 1. Single Responsibility

A skill should do ONE thing well.

**Bad:** `process-ingestion` skill that parses, deduplicates, AND converts to BDD

**Good:** Separate skills:
- `playwright-parser`: Parse JS to actions
- `element-deduplicator`: Find common elements
- `gherkin-generator`: Convert to BDD

### 2. Stateless Operation

Skills should not maintain internal state between calls.

**Bad:** Skill with instance variables that accumulate data

**Good:** Pure function: Input → Process → Output

**Rationale:** Enables parallel execution, easier testing, predictable behavior

### 3. Explicit Dependencies

Skills must declare all dependencies upfront.

```yaml
execution:
  dependencies:
    skills: [playwright-parser]
    tools: [file-read, json-parse]
    mcp_servers: []
    environment: [PROJECT_ROOT]
```

### 4. Graceful Degradation

Skills should handle failures gracefully.

**Failure Modes:**
- **Soft Failure:** Return partial results with warning
- **Hard Failure:** Return error with recovery suggestion
- **Fallback:** Delegate to alternative skill

**Example:**
```yaml
errors:
  recovery: partial_result
  fallback: action-extractor-basic
```

### 5. Observable Execution

Skills should provide visibility into execution.

**Logging Levels:**
- DEBUG: Detailed execution trace
- INFO: High-level progress
- WARNING: Non-fatal issues
- ERROR: Failures with context

**Metrics to Track:**
- Execution time
- Input/output sizes
- Success/failure rate
- Resource usage

### 6. Schema-Based I/O

All skill inputs and outputs must have defined schemas.

**Benefits:**
- Automatic validation
- Clear contracts
- IDE support
- Documentation generation

**Schema Format:** JSON Schema Draft 2020-12

```json
{
  "type": "object",
  "properties": {
    "actions": {
      "type": "array",
      "items": {"$ref": "#/definitions/action"}
    }
  },
  "required": ["actions"]
}
```

---

## Custom Skill Template

### Metadata File: `skill.yaml`

Every skill requires a metadata file:

```yaml
skill:
  id: my-custom-skill
  name: My Custom Skill
  version: 1.0.0
  description: Description of what this skill does
  author: Your Name

  agent: custom_agent
  category: custom

  trigger:
    type: manual
    condition: User invokes via CLI or API

  execution:
    timeout: 30000
    retry_count: 1
    dependencies:
      skills: []
      tools: [file-read]
      mcp_servers: []

  input:
    schema:
      type: object
      properties:
        source_file:
          type: string
      required: [source_file]
    validation: File must exist and be readable

  output:
    schema:
      type: object
      properties:
        result:
          type: string
        status:
          type: string
    format: json

  errors:
    recovery: log_and_continue
    fallback: null
```

### Directory Structure

```
skills/
└── my-custom-skill/
    ├── skill.yaml           # Metadata
    ├── README.md            # Documentation
    ├── __init__.py          # Package init
    ├── skill.py             # Main implementation
    ├── schemas/
    │   ├── input.json       # Input schema
    │   └── output.json      # Output schema
    └── tests/
        ├── test_unit.py
        └── test_integration.py
```

### Documentation Template: `README.md`

```markdown
# My Custom Skill

## Purpose
Brief description of what this skill does and why it exists.

## Usage

### Via CLI
\```bash
cpa run --skill my-custom-skill --input source_file=path/to/file
\```

### Via Agent API
\```python
result = await agent.execute_skill(
    skill_id="my-custom-skill",
    input_data={"source_file": "path/to/file"}
)
\```

## Input Schema
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| source_file | string | Yes | Path to input file |

## Output Schema
| Field | Type | Description |
|-------|------|-------------|
| result | string | Processed result |
| status | string | Execution status |

## Dependencies
- Tools: file-read
- Skills: None
- MCP Servers: None

## Examples

### Example 1: Basic Usage
Input: `{"source_file": "test.js"}`
Output: `{"result": "...", "status": "success"}`

## Error Handling
| Error | Recovery |
|-------|----------|
| File not found | Return error with suggestion |

## Version History
- 1.0.0: Initial release
```

---

## Integration Patterns

### Pattern 1: Sequential Skills

Skills execute in a defined order, passing output to next.

**Use Case:** Standard processing pipeline

```
[Parser] → [Extractor] → [Deduplicator] → [Generator]
```

**Implementation:**
- Orchestrator coordinates sequence
- Each skill receives previous skill's output
- State manager tracks pipeline progress

### Pattern 2: Fan-Out / Fan-In

Multiple skills execute in parallel, results aggregated.

**Use Case:** Independent analysis tasks

```
           ┌→ [Analyzer A] ─┐
[Input] ───→┼→ [Analyzer B] ─┼→ [Aggregator]
           └→ [Analyzer C] ─┘
```

**Implementation:**
- Orchestrator spawns multiple agent instances
- Each agent runs different skill
- Results collected and merged

### Pattern 3: Event-Driven

Skills trigger based on events.

**Use Case:** Reactive processing

```
[Test Failure] → [Failure Analyzer] → [Self-Healing]
```

**Implementation:**
- Event bus for agent communication
- Skills subscribe to specific events
- Async event handling

### Pattern 4: Conditional Branching

Different skills execute based on conditions.

**Use Case:** Adaptive workflows

```
[Input] → [Classifier] ─┬→ [Path A: Skill A]
                         └→ [Path B: Skill B]
```

**Implementation:**
- Classifier skill determines path
- Orchestrator routes to appropriate skill
- State tracks which path was taken

---

## Testing Strategy

### Unit Tests

**Scope:** Test skill in isolation

**Framework:** pytest

**What to Test:**
- Input validation
- Output schema compliance
- Core algorithm correctness
- Error handling

**Example Test Specification:**
```yaml
Test Suite: element_deduplicator_unit

Tests:
  - name: Exact match creates common element
    input:
      recordings:
        - actions: [{type: "click", selector: "#btn"}]
        - actions: [{type: "click", selector: "#btn"}]
    expected:
      common_elements:
        - selector: "#btn"
          occurrences: 2

  - name: Different selectors no match
    input:
      recordings:
        - actions: [{type: "click", selector: "#btn1"}]
        - actions: [{type: "click", selector: "#btn2"}]
    expected:
      common_elements: []
```

### Integration Tests

**Scope:** Test skill with dependencies

**Framework:** pytest with fixtures

**What to Test:**
- Dependency resolution
- Data flow between skills
- State transitions
- MCP tool interactions

**Example Test Specification:**
```yaml
Test Suite: deduplication_flow_integration

Tests:
  - name: Full ingestion to deduplication flow
    setup:
      - Create test recording files
      - Initialize state.json
    steps:
      - Execute playwright-parser
      - Execute element-deduplicator
    expected:
      - state.json.bdd_registry populated
      - common_elements identified
```

### End-to-End Tests

**Scope:** Test complete workflow

**Framework:** Behave (BDD tests for CLI)

**What to Test:**
- CLI commands
- Full agent orchestration
- State persistence
- Report generation

**Example Test Specification:**
```gherkin
Feature: Skill Integration

Scenario: Custom skill integrates with orchestrator
  Given I have a custom skill "my-skill"
  And I have a valid input file
  When I run "cpa run --skill my-skill"
  Then the skill should execute successfully
  And the output should match the schema
```

### Performance Tests

**Scope:** Test skill under load

**Metrics:**
- Execution time
- Memory usage
- CPU utilization
- Scalability

**Test Scenarios:**
```yaml
Performance Tests:
  - name: Large recording handling
    input: 1000 recordings with 100 actions each
    max_time: 30000  # 30 seconds
    max_memory: 512MB

  - name: Concurrent execution
    input: 10 parallel skill invocations
    expected: All complete without deadlock
```

---

## Best Practices

### DO ✓

1. **Keep skills focused:** One responsibility per skill
2. **Use schemas:** Define I/O contracts explicitly
3. **Handle errors:** Graceful degradation over crashes
4. **Log effectively:** INFO for progress, DEBUG for details
5. **Test thoroughly:** Unit, integration, E2E coverage
6. **Document clearly:** README, examples, docstrings
7. **Version carefully:** Semantic versioning
8. **Design for reuse:** Make skills composable

### DON'T ✗

1. **Don't mix concerns:** Parsing + generation in one skill
2. **Don't maintain state:** No instance variables for state
3. **Don't hardcode paths:** Use configuration
4. **Don't ignore errors:** Handle all failure modes
5. **Don't skip tests:** Every skill needs tests
6. **Don't assume inputs:** Validate everything
7. **Don't over-optimize:** Clarity over cleverness
8. **Don't break compatibility:** Respect version contracts

---

## Examples

### Example 1: Parser Skill

**Skill:** `playwright-parser`

**Type:** Parser

**Input:** Playwright codegen JavaScript file

**Output:** Structured action list (JSON)

**Workflow:**
```
1. Read .js file
2. Parse JavaScript AST
3. Extract Playwright API calls
4. Normalize selector format
5. Classify action types
6. Output JSON actions array
```

### Example 2: Generator Skill

**Skill:** `gherkin-generator`

**Type:** Generator

**Input:** Deduplicated action sequences

**Output:** Gherkin .feature file

**Workflow:**
```
1. Receive action sequences
2. Group actions by scenario
3. Map actions to Gherkin keywords
4. Generate Feature/Scenario structure
5. Add parameterization for duplicates
6. Write .feature file
```

### Example 3: Analysis Skill

**Skill:** `selector-analyzer`

**Type:** Analysis

**Input:** Selector string

**Output:** Fragility score + recommendations

**Workflow:**
```
1. Parse selector type (CSS, XPath, role)
2. Check for fragility patterns (nth-child, deep nesting)
3. Score selector reliability (0.0-1.0)
4. Generate alternative selectors
5. Return analysis with recommendations
```

### Example 4: Orchestrator Skill

**Skill:** `cli-handler`

**Type:** Orchestrator

**Input:** CLI command string

**Output:** Execution plan or result

**Workflow:**
```
1. Parse CLI command
2. Validate arguments
3. Route to appropriate agent
4. Spawn agent if needed
5. Monitor execution
6. Return result to user
```

---

## Adding a Custom Skill: Step-by-Step

### Step 1: Define the Skill

Create `skill.yaml` with complete metadata

### Step 2: Design the Interface

Define input and output schemas in JSON Schema format

### Step 3: Plan the Implementation

Create algorithm design and error handling strategy

### Step 4: Implement the Skill

Write the skill implementation following the template

### Step 5: Write Tests

Create unit and integration tests

### Step 6: Document

Create README.md with usage examples

### Step 7: Register with Agent

Add skill to agent's skill registry

### Step 8: Test Integration

Run E2E tests to verify integration

### Step 9: Version and Release

Tag release and update changelog

---

## Quick Reference

### Skill Lifecycle

```
Design → Specify → Implement → Test → Integrate → Deploy
```

### Key Files

| File | Purpose |
|------|---------|
| `skill.yaml` | Skill metadata |
| `skill.py` | Implementation |
| `schemas/*.json` | I/O schemas |
| `README.md` | Documentation |
| `tests/*.py` | Test suite |

### Common Patterns

| Pattern | Use Case |
|---------|----------|
| Parser | Raw → Structured |
| Generator | Data → Content |
| Analysis | Data → Insights |
| Execution | Params → Action |
| Orchestrator | Command → Coordination |

---

**Document Version:** 1.0
**Last Updated:** 2025-01-11
