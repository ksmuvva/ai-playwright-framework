# Agent Architecture - Complete Specification

## Document Information

| Field | Value |
|-------|-------|
| **Project** | AI Playwright Automation Agent |
| **Version** | 2.0 |
| **Date** | 2025-01-11 |
| **Status** | Updated Design |

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Orchestrator Agent (Always-Running)](#2-orchestrator-agent-always-running)
3. [Specialist Agents (On-Demand)](#3-specialist-agents-on-demand)
4. [Inter-Agent Communication](#4-inter-agent-communication)
5. [Skills Catalog](#5-skills-catalog)
6. [Deduplication Strategy](#6-deduplication-strategy)
7. [Implementation Roadmap](#7-implementation-roadmap)

---

## 1. Architecture Overview

### 1.1 Agent Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Orchestrator Agent                                │
│                        (Always Running - Daemon)                               │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                           Core Skills                                     │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       │  │
│  │  │ agent-orchestration│  │   cli-handler    │  │  state-manager   │       │  │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘       │  │
│  │  ┌──────────────────┐                                                   │  │
│  │  │   error-handler  │                                                   │  │
│  │  └──────────────────┘                                                   │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
        ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
        │   Ingestion   │ │ Deduplication │ │  BDD Conv.    │
        │    Agent      │ │    Agent      │ │    Agent      │
        │ (on-demand)   │ │ (on-demand)   │ │ (on-demand)   │
        └───────────────┘ └───────────────┘ └───────────────┘
                    │
                    ▼
        ┌───────────────┐ ┌───────────────┐
        │   Execution   │ │    Analysis   │
        │    Agent      │ │    Agent      │
        │ (on-demand)   │ │ (on-demand)   │
        └───────────────┘ └───────────────┘
```

### 1.2 Command Flow

```
User Command: cpa ingest recordings/login.js
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ Orchestrator Agent (cli-handler skill)                      │
│  1. Parse command: ingest <file>                            │
│  2. Validate input: file exists, format valid               │
│  3. Determine required agent: Ingestion Agent               │
│  4. Spawn Ingestion Agent with context                      │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ Ingestion Agent                                             │
│  1. Load recording file                                     │
│  2. Parse JavaScript (playwright-parser skill)              │
│  3. Extract actions (action-extractor skill)                │
│  4. Analyze selectors (selector-analyzer skill)             │
│  5. Send TASK_COMPLETE message to Orchestrator              │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ Orchestrator Agent (agent-orchestration skill)              │
│  1. Receive TASK_COMPLETE from Ingestion Agent              │
│  2. Check workflow: Next is Deduplication Agent             │
│  3. Spawn Deduplication Agent with actions data             │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ Deduplication Agent                                         │
│  1. Load actions from previous step                         │
│  2. Find common elements (element-deduplicator skill)       │
│  3. Extract components (component-extractor skill)          │
│  4. Generate page objects (page-object-generator skill)     │
│  5. Send TASK_COMPLETE to Orchestrator                      │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
... (continues through BDD Conversion Agent)
```

---

## 2. Orchestrator Agent (Always Running)

### 2.1 Agent Specification

```yaml
agent:
  name: orchestrator
  type: daemon
  lifecycle: always_running
  description: Central coordinator for all agents and skills

core_skills:
  - agent-orchestration
  - cli-handler
  - state-manager
  - error-handler
```

### 2.2 Skill: agent-orchestration

**File:** `.cpa/skills/core/agent-orchestration.skill`

```yaml
name: agent-orchestration
version: 1.0.0
description: Manage agent lifecycle and communication
category: orchestration

capabilities:
  - Spawn child agents based on CLI command
  - Maintain agent registry (active/completed/failed)
  - Message queue for inter-agent communication
  - Agent health monitoring
  - Workflow coordination

agent_registry:
  active: {}          # Currently running agents
  completed: []       # Completed agent executions
  failed: []          # Failed agent executions

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

triggers:
  - event: AgentTaskComplete
    action: check_workflow_next_step

  - event: AgentTaskFailed
    action: handle_agent_failure

  - event: MessageReceived
    action: route_message
```

**Implementation:**

```python
# src/claude_playwright_agent/agents/orchestrator.py

from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import asyncio


class AgentStatus(Enum):
    """Agent execution status."""
    SPAWNING = "spawning"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class AgentTask:
    """Agent task representation."""
    task_id: str
    agent_type: str
    status: AgentStatus = AgentStatus.SPAWNING
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    parent_task_id: Optional[str] = None


@dataclass
class Message:
    """Inter-agent message."""
    message_id: str
    from_agent: str
    to_agent: str
    message_type: str  # TASK_COMPLETE, TASK_FAILED, REQUEST, RESPONSE
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class AgentOrchestrator:
    """
    Orchestrator Agent - Manages all agent lifecycle and communication.

    This is a daemon process that:
    1. Spawns specialist agents on demand
    2. Maintains agent registry
    3. Routes messages between agents
    4. Coordinates workflows
    """

    # Agent type mapping
    AGENT_TYPES = {
        'ingestion': 'IngestionAgent',
        'deduplication': 'DeduplicationAgent',
        'bdd_conversion': 'BDDConversionAgent',
        'execution': 'ExecutionAgent',
        'analysis': 'AnalysisAgent',
    }

    # Workflow definitions
    WORKFLOWS = {
        'ingest': ['ingestion', 'deduplication', 'bdd_conversion'],
        'run': ['execution', 'analysis'],
        'init': [],  # Direct execution, no agent
        'report': ['analysis'],
    }

    def __init__(self):
        self.agent_registry: Dict[str, AgentTask] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self.active_tasks: Dict[str, AgentTask] = {}
        self.completed_tasks: List[AgentTask] = []
        self.failed_tasks: List[AgentTask] = []

    async def spawn_agent(
        self,
        agent_type: str,
        context: Dict[str, Any],
        parent_task_id: Optional[str] = None
    ) -> AgentTask:
        """
        Spawn a new specialist agent.

        Args:
            agent_type: Type of agent to spawn
            context: Execution context for the agent
            parent_task_id: Optional parent task for workflow tracking

        Returns:
            AgentTask representing the spawned agent
        """
        task_id = f"{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        task = AgentTask(
            task_id=task_id,
            agent_type=agent_type,
            parent_task_id=parent_task_id
        )

        self.active_tasks[task_id] = task
        self.agent_registry[task_id] = task

        # Import and instantiate the agent
        agent_class = self._get_agent_class(agent_type)
        agent = agent_class()

        # Execute agent asynchronously
        asyncio.create_task(self._run_agent(task, agent, context))

        return task

    async def _run_agent(
        self,
        task: AgentTask,
        agent: Any,
        context: Dict[str, Any]
    ) -> None:
        """Run agent and handle completion/failure."""
        task.status = AgentStatus.RUNNING

        try:
            result = await agent.execute(context)

            task.status = AgentStatus.COMPLETED
            task.result = result
            task.end_time = datetime.now()

            # Move to completed
            self.completed_tasks.append(task)
            del self.active_tasks[task.task_id]

            # Send completion message
            await self._send_message(
                from_agent=task.agent_type,
                to_agent="orchestrator",
                message_type="TASK_COMPLETE",
                payload={
                    "task_id": task.task_id,
                    "result": result,
                }
            )

        except Exception as e:
            task.status = AgentStatus.FAILED
            task.error = str(e)
            task.end_time = datetime.now()

            # Move to failed
            self.failed_tasks.append(task)
            del self.active_tasks[task.task_id]

            # Send failure message
            await self._send_message(
                from_agent=task.agent_type,
                to_agent="orchestrator",
                message_type="TASK_FAILED",
                payload={
                    "task_id": task.task_id,
                    "error": str(e),
                }
            )

    def _get_agent_class(self, agent_type: str) -> type:
        """Get agent class by type."""
        from claude_playwright_agent.agents.ingestion_agent import IngestionAgent
        from claude_playwright_agent.agents.deduplication_agent import DeduplicationAgent
        from claude_playwright_agent.agents.bdd_conversion_agent import BDDConversionAgent
        from claude_playwright_agent.agents.execution_agent import ExecutionAgent
        from claude_playwright_agent.agents.analysis_agent import AnalysisAgent

        agents = {
            'ingestion': IngestionAgent,
            'deduplication': DeduplicationAgent,
            'bdd_conversion': BDDConversionAgent,
            'execution': ExecutionAgent,
            'analysis': AnalysisAgent,
        }

        return agents.get(agent_type)

    async def _send_message(
        self,
        from_agent: str,
        to_agent: str,
        message_type: str,
        payload: Dict[str, Any]
    ) -> None:
        """Send message to agent."""
        message = Message(
            message_id=f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            payload=payload
        )

        await self.message_queue.put(message)

    async def get_message(self, agent_type: str) -> Optional[Message]:
        """Get next message for agent."""
        while True:
            try:
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )

                if message.to_agent == agent_type or message.to_agent == "all":
                    return message

            except asyncio.TimeoutError:
                return None

    async def coordinate_workflow(
        self,
        workflow_name: str,
        initial_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Coordinate a multi-agent workflow.

        Args:
            workflow_name: Name of workflow to execute
            initial_context: Initial context for first agent

        Returns:
            Final workflow result
        """
        workflow = self.WORKFLOWS.get(workflow_name, [])

        current_context = initial_context
        parent_task_id = None

        for agent_type in workflow:
            # Spawn agent
            task = await self.spawn_agent(
                agent_type=agent_type,
                context=current_context,
                parent_task_id=parent_task_id
            )

            # Wait for completion
            while task.status not in [AgentStatus.COMPLETED, AgentStatus.FAILED]:
                await asyncio.sleep(0.1)

            if task.status == AgentStatus.FAILED:
                return {
                    "success": False,
                    "error": task.error,
                    "failed_at": agent_type,
                }

            # Update context for next agent
            current_context = task.result
            parent_task_id = task.task_id

        return {
            "success": True,
            "result": current_context,
        }

    def get_agent_status(self, task_id: str) -> Optional[AgentStatus]:
        """Get status of an agent task."""
        task = self.agent_registry.get(task_id)
        return task.status if task else None

    def get_active_agents(self) -> List[AgentTask]:
        """Get all currently active agents."""
        return list(self.active_tasks.values())

    def get_completed_agents(self) -> List[AgentTask]:
        """Get all completed agents."""
        return self.completed_tasks

    def get_failed_agents(self) -> List[AgentTask]:
        """Get all failed agents."""
        return self.failed_tasks
```

### 2.3 Skill: cli-handler

**File:** `.cpa/skills/core/cli-handler.skill`

```yaml
name: cli-handler
version: 1.0.0
description: Parse CLI commands and validate inputs
category: orchestration

commands:
  init:
    syntax: cpa init <project-name>
    args:
      - name: project-name
        type: string
        required: true
        validation: |
          - Must not be empty
          - Must be valid Python identifier
          - Must not conflict with existing directory

  ingest:
    syntax: cpa ingest <recording-file>
    args:
      - name: recording-file
        type: file
        required: true
        validation: |
          - File must exist
          - Must be .js file (Playwright codegen)
          - File must be readable

  run:
    syntax: cpa run [options]
    args:
      - name: feature-name
        type: string
        required: false
      - name: tags
        type: string
        required: false
        pattern: "@[\\w]+"
      - name: parallel
        type: integer
        required: false
        default: 1

  report:
    syntax: cpa report [test-run-id]
    args:
      - name: test-run-id
        type: string
        required: false

  list-skills:
    syntax: cpa list-skills
    args: []

  add-skill:
    syntax: cpa add-skill <skill-path>
    args:
      - name: skill-path
        type: file
        required: true

command_to_agent:
  init: null  # Direct execution, no agent
  ingest: ingestion_agent
  run: execution_agent
  report: analysis_agent
  list-skills: null
  add-skill: null

command_to_workflow:
  ingest: ingest_flow
  run: run_flow
```

**Implementation:**

```python
# src/claude_playwright_agent/skills/cli_handler.py

import click
from pathlib import Path
from typing import Dict, Any, Optional, List
import re


class CLIHandler:
    """Handle CLI command parsing and validation."""

    COMMANDS = {
        'init': {
            'agent': None,
            'workflow': None,
            'args': {
                'project_name': {
                    'required': True,
                    'type': 'string',
                    'pattern': r'^[a-zA-Z_][a-zA-Z0-9_]*$',
                }
            }
        },
        'ingest': {
            'agent': 'ingestion_agent',
            'workflow': 'ingest_flow',
            'args': {
                'recording_file': {
                    'required': True,
                    'type': 'file',
                    'extensions': ['.js'],
                }
            }
        },
        'run': {
            'agent': 'execution_agent',
            'workflow': 'run_flow',
            'args': {
                'feature_name': {
                    'required': False,
                    'type': 'string',
                },
                'tags': {
                    'required': False,
                    'type': 'string',
                    'pattern': r'@[\w]+(,\s*@[\w]+)*',
                },
                'parallel': {
                    'required': False,
                    'type': 'int',
                    'default': 1,
                    'min': 1,
                    'max': 10,
                }
            }
        },
        'report': {
            'agent': 'analysis_agent',
            'workflow': None,
            'args': {
                'test_run_id': {
                    'required': False,
                    'type': 'string',
                }
            }
        },
        'list-skills': {
            'agent': None,
            'workflow': None,
            'args': {}
        },
        'add-skill': {
            'agent': None,
            'workflow': None,
            'args': {
                'skill_path': {
                    'required': True,
                    'type': 'file',
                    'extensions': ['.skill', '.yaml'],
                }
            }
        },
    }

    def parse_command(self, command: str, args: List[str]) -> Dict[str, Any]:
        """
        Parse CLI command into structured format.

        Args:
            command: Command name (e.g., 'init', 'ingest')
            args: Command arguments

        Returns:
            Parsed command with validation results
        """
        if command not in self.COMMANDS:
            return {
                'success': False,
                'error': f'Unknown command: {command}',
                'available_commands': list(self.COMMANDS.keys()),
            }

        command_spec = self.COMMANDS[command]

        # Parse arguments
        parsed_args = {}
        errors = []

        for arg_name, arg_spec in command_spec['args'].items():
            # Get argument value
            if args and arg_spec['required']:
                if arg_name == 'project_name':
                    value = args[0] if args else None
                else:
                    value = self._extract_arg_value(arg_name, args)
            else:
                value = arg_spec.get('default')

            # Validate argument
            if value is not None or arg_spec['required']:
                validation = self._validate_argument(arg_name, value, arg_spec)
                if not validation['valid']:
                    errors.append(validation['error'])
                else:
                    parsed_args[arg_name] = value

        if errors:
            return {
                'success': False,
                'error': 'Validation failed',
                'validation_errors': errors,
            }

        return {
            'success': True,
            'command': command,
            'agent': command_spec['agent'],
            'workflow': command_spec['workflow'],
            'args': parsed_args,
        }

    def _extract_arg_value(self, arg_name: str, args: List[str]) -> Any:
        """Extract argument value from args list."""
        # This would handle named arguments (--flag, --key=value)
        # For now, simplified
        if args:
            return args[0]
        return None

    def _validate_argument(self, name: str, value: Any, spec: Dict) -> Dict[str, Any]:
        """Validate a single argument."""
        if value is None:
            if spec.get('required', False):
                return {'valid': False, 'error': f'{name} is required'}
            return {'valid': True}

        # Type validation
        if spec['type'] == 'file':
            path = Path(value)
            if not path.exists():
                return {'valid': False, 'error': f'File not found: {value}'}

            # Check extension
            if 'extensions' in spec:
                if path.suffix not in spec['extensions']:
                    return {
                        'valid': False,
                        'error': f'File must be {", ".join(spec["extensions"])}'
                    }

        # Pattern validation
        if 'pattern' in spec:
            if not re.match(spec['pattern'], str(value)):
                return {
                    'valid': False,
                    'error': f'{name} does not match required pattern'
                }

        # Range validation
        if 'min' in spec and value < spec['min']:
            return {
                'valid': False,
                'error': f'{name} must be at least {spec["min"]}'
            }

        if 'max' in spec and value > spec['max']:
            return {
                'valid': False,
                'error': f'{name} must be at most {spec["max"]}'
            }

        return {'valid': True}

    def get_help(self, command: Optional[str] = None) -> str:
        """Generate help text."""
        if command:
            if command not in self.COMMANDS:
                return f'Unknown command: {command}'

            spec = self.COMMANDS[command]
            help_text = f'Command: cpa {command}\n\n'

            help_text += 'Arguments:\n'
            for arg_name, arg_spec in spec['args'].items():
                required = 'required' if arg_spec.get('required') else 'optional'
                help_text += f'  {arg_name}: {required}\n'

            return help_text

        # General help
        help_text = 'Claude Playwright Agent - AI-powered test automation\n\n'
        help_text += 'Commands:\n'
        for cmd_name, spec in self.COMMANDS.items():
            help_text += f'  cpa {cmd_name}\n'

        help_text += '\nUse "cpa <command> --help" for more information.'

        return help_text
```

### 2.4 Skill: state-manager

**File:** `.cpa/skills/core/state-manager.skill`

```yaml
name: state-manager
version: 1.0.0
description: Track framework state and agent progress
category: orchestration

state_structure:
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

**Implementation:**

```python
# src/claude_playwright_agent/skills/state_manager.py

from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import threading


class StateManager:
    """Manage framework state and agent progress."""

    def __init__(self, project_path: Optional[str] = None):
        if project_path:
            self.project_path = Path(project_path)
        else:
            self.project_path = Path.cwd()

        self.state_dir = self.project_path / '.cpa'
        self.state_file = self.state_dir / 'state.json'

        # Ensure state directory exists
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Load or initialize state
        self.state = self._load_state()

        # Thread lock for state updates
        self._lock = threading.Lock()

    def _load_state(self) -> Dict[str, Any]:
        """Load state from file."""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        else:
            return self._initialize_state()

    def _initialize_state(self) -> Dict[str, Any]:
        """Initialize new state."""
        return {
            'project_metadata': {
                'name': self.project_path.name,
                'created_at': datetime.now().isoformat(),
                'framework_type': 'behave',
                'version': '1.0.0',
            },
            'recordings': [],
            'scenarios': [],
            'test_runs': [],
            'agent_status': [],
            'components': {},  # Deduplication results
            'page_objects': {},
        }

    def save(self) -> None:
        """Save state to file."""
        with self._lock:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)

    def get_project_metadata(self) -> Dict[str, Any]:
        """Get project metadata."""
        return self.state['project_metadata']

    def add_recording(
        self,
        recording_id: str,
        file_path: str,
        status: str = 'pending'
    ) -> None:
        """Add recording to state."""
        self.state['recordings'].append({
            'recording_id': recording_id,
            'file_path': file_path,
            'ingested_at': datetime.now().isoformat(),
            'status': status,
        })
        self.save()

    def update_recording_status(self, recording_id: str, status: str) -> None:
        """Update recording status."""
        for recording in self.state['recordings']:
            if recording['recording_id'] == recording_id:
                recording['status'] = status
                break
        self.save()

    def add_scenario(
        self,
        scenario_id: str,
        feature_file: str,
        recording_source: str
    ) -> None:
        """Add scenario to state."""
        self.state['scenarios'].append({
            'scenario_id': scenario_id,
            'feature_file': feature_file,
            'recording_source': recording_source,
            'created_at': datetime.now().isoformat(),
        })
        self.save()

    def add_test_run(self, results: Dict[str, Any]) -> str:
        """Add test run to state."""
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.state['test_runs'].append({
            'run_id': run_id,
            'timestamp': datetime.now().isoformat(),
            'total': results.get('total', 0),
            'passed': results.get('passed', 0),
            'failed': results.get('failed', 0),
            'skipped': results.get('skipped', 0),
            'duration': results.get('duration', 0),
        })
        self.save()

        return run_id

    def update_agent_status(
        self,
        agent_id: str,
        agent_type: str,
        status: str
    ) -> None:
        """Update agent status."""
        # Remove old status for this agent
        self.state['agent_status'] = [
            s for s in self.state['agent_status']
            if s['agent_id'] != agent_id
        ]

        # Add new status
        self.state['agent_status'].append({
            'agent_id': agent_id,
            'agent_type': agent_type,
            'status': status,
            'timestamp': datetime.now().isoformat(),
        })
        self.save()

    def store_components(self, components: Dict[str, Any]) -> None:
        """Store deduplicated components."""
        self.state['components'] = components
        self.save()

    def get_components(self) -> Dict[str, Any]:
        """Get deduplicated components."""
        return self.state.get('components', {})

    def store_page_objects(self, page_objects: Dict[str, Any]) -> None:
        """Store generated page objects."""
        self.state['page_objects'] = page_objects
        self.save()

    def get_page_objects(self) -> Dict[str, Any]:
        """Get page objects."""
        return self.state.get('page_objects', {})

    def get_recordings(self) -> List[Dict[str, Any]]:
        """Get all recordings."""
        return self.state.get('recordings', [])

    def get_scenarios(self) -> List[Dict[str, Any]]:
        """Get all scenarios."""
        return self.state.get('scenarios', [])

    def get_test_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent test runs."""
        runs = self.state.get('test_runs', [])
        return runs[-limit:]

    def get_active_agents(self) -> List[Dict[str, Any]]:
        """Get currently active agents."""
        return [
            s for s in self.state.get('agent_status', [])
            if s['status'] in ['spawning', 'running']
        ]
```

### 2.5 Skill: error-handler

**File:** `.cpa/skills/core/error-handler.skill`

```yaml
name: error-handler
version: 1.0.0
description: Graceful error handling and user feedback
category: orchestration

error_types:
  invalid_recording_format:
    category: validation
    recovery: suggest_fix
    message: "Recording file is not valid Playwright codegen output"

  missing_dependencies:
    category: environment
    recovery: install_command
    message: "Playwright is not installed"

  agent_timeout:
    category: execution
    recovery: retry_or_skip
    message: "Agent execution timed out"

  agent_crash:
    category: execution
    recovery: restart_agent
    message: "Agent crashed unexpectedly"

  bdd_conversion_failure:
    category: conversion
    recovery: partial_result
    message: "Failed to convert some actions to BDD"
```

**Implementation:**

```python
# src/claude_playwright_agent/skills/error_handler.py

from typing import Dict, Any, Optional
from enum import Enum
import traceback


class ErrorCategory(Enum):
    """Error categories."""
    VALIDATION = "validation"
    ENVIRONMENT = "environment"
    EXECUTION = "execution"
    CONVERSION = "conversion"
    NETWORK = "network"
    UNKNOWN = "unknown"


class RecoveryAction(Enum):
    """Recovery action types."""
    SUGGEST_FIX = "suggest_fix"
    INSTALL_COMMAND = "install_command"
    RETRY_OR_SKIP = "retry_or_skip"
    RESTART_AGENT = "restart_agent"
    PARTIAL_RESULT = "partial_result"
    NONE = "none"


@dataclass
class ErrorInfo:
    """Structured error information."""
    error_type: str
    category: ErrorCategory
    message: str
    recovery_action: RecoveryAction
    context: Dict[str, Any]
    suggestion: Optional[str] = None
    traceback_str: Optional[str] = None


class ErrorHandler:
    """Handle errors gracefully with actionable feedback."""

    ERROR_DEFINITIONS = {
        'invalid_recording_format': {
            'category': ErrorCategory.VALIDATION,
            'recovery': RecoveryAction.SUGGEST_FIX,
            'message': 'Recording file is not valid Playwright codegen output',
            'suggestion': 'Ensure file was generated by: npx playwright codegen',
        },
        'file_not_found': {
            'category': ErrorCategory.VALIDATION,
            'recovery': RecoveryAction.SUGGEST_FIX,
            'message': 'File not found',
            'suggestion': 'Check the file path and try again',
        },
        'playwright_not_installed': {
            'category': ErrorCategory.ENVIRONMENT,
            'recovery': RecoveryAction.INSTALL_COMMAND,
            'message': 'Playwright is not installed',
            'suggestion': 'Run: pip install playwright && playwright install',
        },
        'agent_timeout': {
            'category': ErrorCategory.EXECUTION,
            'recovery': RecoveryAction.RETRY_OR_SKIP,
            'message': 'Agent execution timed out',
            'suggestion': 'Try increasing timeout or check for stuck processes',
        },
        'bdd_conversion_failure': {
            'category': ErrorCategory.CONVERSION,
            'recovery': RecoveryAction.PARTIAL_RESULT,
            'message': 'Failed to convert some actions to BDD',
            'suggestion': 'Review feature file and manually fix failed conversions',
        },
    }

    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorInfo:
        """
        Handle an error and return structured information.

        Args:
            error: The exception that occurred
            context: Additional context about the error

        Returns:
            ErrorInfo with recovery suggestions
        """
        error_type = type(error).__name__
        error_str = str(error)

        # Look up error definition
        if error_type in self.ERROR_DEFINITIONS:
            definition = self.ERROR_DEFINITIONS[error_type]
            return ErrorInfo(
                error_type=error_type,
                category=definition['category'],
                message=definition['message'],
                recovery_action=definition['recovery'],
                context=context or {},
                suggestion=definition['suggestion'],
                traceback_str=traceback.format_exc() if context.get('include_traceback') else None,
            )

        # Unknown error - try to categorize
        category = self._categorize_error(error)
        return ErrorInfo(
            error_type=error_type,
            category=category,
            message=error_str,
            recovery_action=RecoveryAction.NONE,
            context=context or {},
            traceback_str=traceback.format_exc() if context.get('include_traceback') else None,
        )

    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize an unknown error."""
        error_str = str(error).lower()

        if 'file' in error_str and 'not found' in error_str:
            return ErrorCategory.VALIDATION
        if 'timeout' in error_str:
            return ErrorCategory.EXECUTION
        if 'connection' in error_str or 'network' in error_str:
            return ErrorCategory.NETWORK
        if 'import' in error_str or 'module' in error_str:
            return ErrorCategory.ENVIRONMENT

        return ErrorCategory.UNKNOWN

    def format_user_message(self, error_info: ErrorInfo) -> str:
        """Format error message for user."""
        message = f"❌ {error_info.message}\n"

        if error_info.suggestion:
            message += f"\n💡 Suggestion: {error_info.suggestion}\n"

        # Add context-specific information
        if error_info.context:
            if 'file_path' in error_info.context:
                message += f"\n📄 File: {error_info.context['file_path']}\n"
            if 'agent_type' in error_info.context:
                message += f"\n🤖 Agent: {error_info.context['agent_type']}\n"

        return message

    def can_recover(self, error_info: ErrorInfo) -> bool:
        """Check if error is recoverable."""
        return error_info.recovery_action != RecoveryAction.NONE

    def get_recovery_command(self, error_info: ErrorInfo) -> Optional[str]:
        """Get recovery command if applicable."""
        if error_info.recovery_action == RecoveryAction.INSTALL_COMMAND:
            return "pip install playwright && playwright install"

        if error_info.error_type == 'playwright_not_installed':
            return "npm install -D @playwright/test"

        return None
```

---

## 3. Specialist Agents (On-Demand)

### 3.1 Ingestion Agent

**File:** `src/claude_playwright_agent/agents/ingestion_agent.py`

```python
"""
Ingestion Agent - Parse Playwright recordings and extract actions.
"""

from typing import Dict, Any, List
from pathlib import Path
import json
import asyncio

from claude_playwright_agent.agents.base import BaseAgent
from claude_playwright_agent.skills.playwright_parser import PlaywrightParserSkill
from claude_playwright_agent.skills.action_extractor import ActionExtractorSkill
from claude_playwright_agent.skills.selector_analyzer import SelectorAnalyzerSkill


class IngestionAgent(BaseAgent):
    """
    Ingestion Agent - Parse Playwright codegen recordings.

    Triggered by: cpa ingest <recording-file>

    Skills:
    - playwright-parser: Parse JavaScript AST
    - action-extractor: Classify and enrich actions
    - selector-analyzer: Analyze and normalize selectors
    """

    def __init__(self):
        super().__init__(
            system_prompt="You are an expert at parsing Playwright codegen recordings."
        )

        self.parser = PlaywrightParserSkill()
        self.extractor = ActionExtractorSkill()
        self.analyzer = SelectorAnalyzerSkill()

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute ingestion workflow.

        Context:
            recording_file: Path to Playwright codegen JS file
            project_path: Project root directory

        Returns:
            Dictionary with:
                recording_id: Unique ID for this recording
                actions: List of extracted actions
                selectors: Analyzed selector data
                next_agent: "deduplication_agent"
        """
        recording_file = Path(context['recording_file'])
        project_path = Path(context.get('project_path', Path.cwd()))

        # Step 1: Parse Playwright script
        raw_actions = await self.parser.parse(recording_file)

        # Step 2: Extract and classify actions
        enriched_actions = await self.extractor.extract(raw_actions)

        # Step 3: Analyze selectors
        selector_data = await self.analyzer.analyze(enriched_actions)

        # Generate recording ID
        recording_id = f"recording_{recording_file.stem}_{asyncio.get_event_loop().time()}"

        # Save to project
        state_dir = project_path / '.cpa' / 'recordings'
        state_dir.mkdir(parents=True, exist_ok=True)

        output_file = state_dir / f'{recording_id}.json'
        with open(output_file, 'w') as f:
            json.dump({
                'recording_id': recording_id,
                'source_file': str(recording_file),
                'actions': enriched_actions,
                'selectors': selector_data,
            }, f, indent=2)

        return {
            'recording_id': recording_id,
            'actions_file': str(output_file),
            'actions': enriched_actions,
            'selectors': selector_data,
            'next_agent': 'deduplication_agent',
        }
```

**Skills:**

#### 3.1.1 Playwright Parser Skill

```python
# src/claude_playwright_agent/skills/playwright_parser.py

import ast
import re
from typing import Dict, Any, List
from pathlib import Path


class PlaywrightParserSkill:
    """Parse Playwright codegen JavaScript output."""

    async def parse(self, recording_file: Path) -> List[Dict[str, Any]]:
        """
        Parse Playwright codegen JavaScript file.

        Args:
            recording_file: Path to .js file

        Returns:
            List of raw action dictionaries
        """
        with open(recording_file, 'r') as f:
            js_content = f.read()

        actions = []

        # Parse Playwright actions using regex patterns
        patterns = {
            'goto': r'await page\.goto\([\'"]([^\'"]+)[\'"]\)',
            'click': r'await page\.(?:click|locator\([^\)]+\)\.click)\([\'"]?([^\'")\]]+)[\'"]?\)',
            'fill': r'await page\.(?:fill|locator\([^\)]+\)\.fill)\([\'"]?([^\'")\]]+)[\'"]?,\s*[\'"]([^\'"]*)[\'"]\)',
            'select': r'await page\.(?:selectOption|locator\([^\)]+\)\.selectOption)\([\'"]?([^\'")\]]+)[\'"]?,\s*[\'"]([^\'"]*)[\'"]\)',
            'check': r'await page\.(?:check|locator\([^\)]+\)\.check)\([\'"]?([^\'")\]]+)[\'"]?\)',
            'press': r'await page\.(?:press|locator\([^\)]+\)\.press)\([\'"]?([^\'")\]]+)[\'"]?,\s*[\'"]([^\'"]*)[\'"]\)',
            'type': r'await page\.(?:type|locator\([^\)]+\)\.type)\([\'"]?([^\'")\]]+)[\'"]?,\s*[\'"]([^\'"]*)[\'"]\)',
        }

        lines = js_content.split('\n')
        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('//'):
                continue

            # Match patterns
            for action_type, pattern in patterns.items():
                match = re.search(pattern, line)
                if match:
                    action = {
                        'type': action_type,
                        'line': line_num,
                        'raw': line,
                    }

                    groups = match.groups()
                    if action_type == 'goto':
                        action['url'] = groups[0]
                    elif action_type in ['fill', 'type', 'press']:
                        action['selector'] = groups[0]
                        action['value'] = groups[1] if len(groups) > 1 else ''
                    elif action_type == 'select':
                        action['selector'] = groups[0]
                        action['value'] = groups[1] if len(groups) > 1 else ''
                    else:
                        action['selector'] = groups[0] if groups else ''

                    actions.append(action)
                    break

        return actions
```

#### 3.1.2 Action Extractor Skill

```python
# src/claude_playwright_agent/skills/action_extractor.py

from typing import Dict, Any, List


class ActionExtractorSkill:
    """Classify and enrich extracted actions."""

    ACTION_CATEGORIES = {
        'NAVIGATION': ['goto', 'goBack', 'reload', 'waitForURL'],
        'INTERACTION': ['click', 'fill', 'type', 'select', 'check', 'uncheck', 'hover', 'drag'],
        'ASSERTION': ['expect', 'waitFor', 'waitForSelector', 'waitForText'],
        'WAIT': ['waitForTimeout', 'waitForLoadState'],
        'NAVIGATION': ['screenshot', 'pdf'],
    }

    PATTERNS = {
        'login': ['username', 'password', 'email', 'login', 'signin'],
        'search': ['search', 'query', 'find'],
        'form': ['submit', 'save', 'create', 'update'],
        'checkout': ['cart', 'checkout', 'payment', 'shipping'],
    }

    async def extract(self, raw_actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract and classify actions.

        Args:
            raw_actions: Raw parsed actions from PlaywrightParser

        Returns:
            Enriched action list with metadata
        """
        enriched = []

        for action in raw_actions:
            action_type = action['type']

            enriched_action = {
                'type': action_type,
                'category': self._categorize_action(action_type),
                'selector': action.get('selector', ''),
                'value': action.get('value', ''),
                'url': action.get('url', ''),
                'raw': action.get('raw', ''),
                'line': action.get('line', 0),
                'metadata': self._extract_metadata(action),
            }

            enriched.append(enriched_action)

        # Detect patterns across actions
        pattern = self._detect_pattern(enriched)
        if pattern:
            for action in enriched:
                action['pattern'] = pattern

        return enriched

    def _categorize_action(self, action_type: str) -> str:
        """Categorize an action type."""
        for category, types in self.ACTION_CATEGORIES.items():
            if action_type in types:
                return category
        return 'UNKNOWN'

    def _extract_metadata(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from action."""
        metadata = {}

        selector = action.get('selector', '')

        # Extract element type from selector
        if 'button' in selector.lower() or 'role=button' in selector:
            metadata['element_type'] = 'button'
        elif 'input' in selector.lower():
            if 'type="email"' in selector or 'email' in selector:
                metadata['element_type'] = 'email_input'
            elif 'type="password"' in selector or 'password' in selector:
                metadata['element_type'] = 'password_input'
            else:
                metadata['element_type'] = 'text_input'
        elif 'select' in selector.lower():
            metadata['element_type'] = 'dropdown'
        elif 'a' in selector or 'link' in selector.lower():
            metadata['element_type'] = 'link'

        return metadata

    def _detect_pattern(self, actions: List[Dict[str, Any]]) -> str:
        """Detect common action patterns."""
        action_str = ' '.join([a.get('value', '') + ' ' + a.get('selector', '') for a in actions]).lower()

        for pattern, keywords in self.PATTERNS.items():
            if any(keyword in action_str for keyword in keywords):
                return pattern

        return None
```

#### 3.1.3 Selector Analyzer Skill

```python
# src/claude_playwright_agent/skills/selector_analyzer.py

from typing import Dict, Any, List
import re


class SelectorAnalyzerSkill:
    """Analyze and normalize selectors for reliability."""

    async def analyze(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze selectors and generate metadata.

        Args:
            actions: Enriched action list

        Returns:
            Selector analysis data
        """
        selector_data = {
            'selectors': [],
            'fragility_scores': {},
            'recommendations': {},
        }

        for action in actions:
            selector = action.get('selector', '')
            if not selector:
                continue

            analysis = self._analyze_selector(selector)
            selector_data['selectors'].append({
                'selector': selector,
                'action_type': action['type'],
                'analysis': analysis,
            })

            selector_data['fragility_scores'][selector] = analysis['fragility_score']

            if analysis['recommendations']:
                selector_data['recommendations'][selector] = analysis['recommendations']

        return selector_data

    def _analyze_selector(self, selector: str) -> Dict[str, Any]:
        """Analyze a single selector."""
        analysis = {
            'selector_type': self._get_selector_type(selector),
            'fragility_score': 0.0,
            'recommendations': [],
            'alternatives': [],
        }

        # Calculate fragility score
        # Higher = more fragile (bad)
        score = 0.0

        # High fragility indicators
        if ':nth-child' in selector:
            score += 0.4
            analysis['recommendations'].append('Avoid nth-child selectors')

        if '>' in selector and selector.count('>') > 2:
            score += 0.3
            analysis['recommendations'].append('Deep nesting is fragile')

        # Low fragility indicators
        if 'data-testid=' in selector or 'data-test=' in selector:
            score = 0.0  # Best case
            analysis['recommendations'].append('Excellent: uses data-testid')

        elif 'aria-label=' in selector or 'role=' in selector:
            score = min(score, 0.2)  # Good
            analysis['recommendations'].append('Good: uses ARIA attributes')

        elif '#' in selector:  # ID selector
            score = min(score, 0.3)  # Okay
            analysis['recommendations'].append('Okay: uses ID selector')

        # Generate alternatives
        analysis['alternatives'] = self._generate_alternatives(selector)

        analysis['fragility_score'] = score

        return analysis

    def _get_selector_type(self, selector: str) -> str:
        """Get selector type."""
        if 'data-' in selector:
            return 'data_attribute'
        if 'role=' in selector:
            return 'aria_role'
        if '#' in selector and not '>' in selector:
            return 'id'
        if '.' in selector:
            return 'class'
        if '[' in selector:
            return 'attribute'
        return 'css'

    def _generate_alternatives(self, selector: str) -> List[str]:
        """Generate alternative selectors."""
        alternatives = []

        # Try data-testid first
        if 'data-testid=' not in selector:
            # Can't really generate without knowing the element
            pass

        # Try aria-label
        if 'aria-label=' not in selector and 'role=' not in selector:
            pass

        # Try text content (if possible)
        # This would need more context

        return alternatives
```

---

### 3.2 Deduplication Agent

**File:** `src/claude_playwright_agent/agents/deduplication_agent.py`

```python
"""
Deduplication Agent - Identify common elements and generate page objects.
"""

from typing import Dict, Any, List
from pathlib import Path
import json
from collections import defaultdict

from claude_playwright_agent.agents.base import BaseAgent
from claude_playwright_agent.skills.element_deduplicator import ElementDeduplicatorSkill
from claude_playwright_agent.skills.component_extractor import ComponentExtractorSkill
from claude_playwright_agent.skills.page_object_generator import PageObjectGeneratorSkill


class DeduplicationAgent(BaseAgent):
    """
    Deduplication Agent - Find common elements and create reusable components.

    Triggered by: After Ingestion Agent completes

    Skills:
    - element-deduplicator: Find duplicate/common UI elements
    - component-extractor: Extract reusable UI components
    - page-object-generator: Auto-generate Page Object classes
    """

    def __init__(self):
        super().__init__(
            system_prompt="You are an expert at identifying common UI elements and creating reusable components."
        )

        self.deduplicator = ElementDeduplicatorSkill()
        self.extractor = ComponentExtractorSkill()
        self.generator = PageObjectGeneratorSkill()

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute deduplication workflow.

        Context:
            actions_file: Path to actions JSON from Ingestion Agent
            project_path: Project root directory

        Returns:
            Dictionary with:
                common_elements: List of deduplicated elements
                components: Extracted reusable components
                page_objects: Generated page object classes
                next_agent: "bdd_conversion_agent"
        """
        actions_file = Path(context['actions_file'])
        project_path = Path(context.get('project_path', Path.cwd()))

        # Load actions
        with open(actions_file, 'r') as f:
            data = json.load(f)

        actions = data['actions']

        # Step 1: Find common elements (exact + structural matching)
        common_elements = await self.deduplicator.deduplicate(actions)

        # Step 2: Extract reusable components
        components = await self.extractor.extract(actions, common_elements)

        # Step 3: Generate page objects
        page_objects = await self.generator.generate(components)

        # Save to state
        state_file = project_path / '.cpa' / 'state.json'
        state = json.loads(state_file.read_text()) if state_file.exists() else {}
        state['components'] = components
        state['page_objects'] = page_objects

        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)

        return {
            'common_elements': common_elements,
            'components': components,
            'page_objects': page_objects,
            'next_agent': 'bdd_conversion_agent',
        }
```

---

### 3.3 BDD Conversion Agent

**File:** `src/claude_playwright_agent/agents/bdd_conversion_agent.py`

```python
"""
BDD Conversion Agent - Convert actions to Gherkin scenarios.
"""

from typing import Dict, Any, List
from pathlib import Path

from claude_playwright_agent.agents.base import BaseAgent
from claude_playwright_agent.skills.gherkin_generator import GherkinGeneratorSkill
from claude_playwright_agent.skills.step_definition_creator import StepDefinitionCreatorSkill
from claude_playwright_agent.skills.scenario_optimizer import ScenarioOptimizerSkill


class BDDConversionAgent(BaseAgent):
    """
    BDD Conversion Agent - Convert actions to Gherkin scenarios.

    Triggered by: After Deduplication Agent completes

    Skills:
    - gherkin-generator: Generate Given/When/Then from actions
    - step-definition-creator: Create Python step definitions
    - scenario-optimizer: Optimize scenarios for maintainability
    """

    def __init__(self):
        super().__init__(
            system_prompt="You are an expert at converting test actions into BDD scenarios."
        )

        self.gherkin = GherkinGeneratorSkill()
        self.steps = StepDefinitionCreatorSkill()
        self.optimizer = ScenarioOptimizerSkill()

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute BDD conversion workflow."""
        project_path = Path(context.get('project_path', Path.cwd()))

        # Generate Gherkin scenarios
        feature_files = await self.gherkin.generate(context)

        # Generate step definitions
        step_files = await self.steps.create(context)

        # Optimize scenarios
        optimized = await self.optimizer.optimize(feature_files)

        return {
            'feature_files': feature_files,
            'step_files': step_files,
            'optimized': optimized,
            'success': True,
        }
```

---

### 3.4 Execution Agent

**File:** `src/claude_playwright_agent/agents/execution_agent.py`

```python
"""
Execution Agent - Run BDD tests with Playwright.
"""

from typing import Dict, Any, List
from pathlib import Path
import subprocess

from claude_playwright_agent.agents.base import BaseAgent
from claude_playwright_agent.skills.test_runner import TestRunnerSkill
from claude_playwright_agent.skills.report_generator import ReportGeneratorSkill
from claude_playwright_agent.skills.failure_analyzer import FailureAnalyzerSkill
from claude_playwright_agent.skills.self_healing import SelfHealingSkill


class ExecutionAgent(BaseAgent):
    """
    Execution Agent - Execute BDD scenarios.

    Triggered by: cpa run [options]

    Skills:
    - test-runner: Execute tests with Behave
    - report-generator: Generate HTML reports
    - failure-analyzer: AI-powered root cause analysis
    - self-healing: Auto-fix broken selectors
    """

    def __init__(self):
        super().__init__(
            system_prompt="You are a test execution coordinator."
        )

        self.runner = TestRunnerSkill()
        self.reporter = ReportGeneratorSkill()
        self.analyzer = FailureAnalyzerSkill()
        self.healer = SelfHealingSkill()

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute test workflow."""
        # Run tests
        results = await self.runner.run(context)

        # If failures and self-healing enabled
        if results['failed'] > 0 and context.get('self_heal'):
            results = await self.healer.heal(results, context)

        # Generate report
        report = await self.reporter.generate(results)

        # Analyze failures
        if results['failed'] > 0:
            analysis = await self.analyzer.analyze(results)
        else:
            analysis = {}

        return {
            'results': results,
            'report': report,
            'analysis': analysis,
        }
```

---

## 4. Inter-Agent Communication

### 4.1 Message Format

```python
# src/claude_playwright_agent/messaging/message.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum


class MessageType(Enum):
    """Message types."""
    TASK_COMPLETE = "TASK_COMPLETE"
    TASK_FAILED = "TASK_FAILED"
    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"
    STATUS_UPDATE = "STATUS_UPDATE"
    SELF_HEAL_REQUEST = "SELF_HEAL_REQUEST"


@dataclass
class Message:
    """Inter-agent communication message."""

    message_id: str
    from_agent: str
    to_agent: str
    message_type: MessageType
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None  # For request/response
    priority: int = 5  # 1-10, 1 = highest

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'message_id': self.message_id,
            'from_agent': self.from_agent,
            'to_agent': self.to_agent,
            'message_type': self.message_type.value,
            'payload': self.payload,
            'timestamp': self.timestamp.isoformat(),
            'correlation_id': self.correlation_id,
            'priority': self.priority,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create from dictionary."""
        return cls(
            message_id=data['message_id'],
            from_agent=data['from_agent'],
            to_agent=data['to_agent'],
            message_type=MessageType(data['message_type']),
            payload=data['payload'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            correlation_id=data.get('correlation_id'),
            priority=data.get('priority', 5),
        )
```

### 4.2 Communication Patterns

```python
# src/claude_playwright_agent/messaging/patterns.py

from typing import Dict, Any, List, Optional
import asyncio


class SequentialHandoff:
    """
    Pattern: Sequential handoff between agents.

    Flow: Agent A → Orchestrator → Agent B → Orchestrator → Agent C
    """

    async def execute(
        self,
        orchestrator: 'AgentOrchestrator',
        workflow: List[str],
        initial_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute sequential workflow."""
        context = initial_context

        for agent_type in workflow:
            # Spawn agent
            task = await orchestrator.spawn_agent(
                agent_type=agent_type,
                context=context
            )

            # Wait for completion
            while task.status not in ['completed', 'failed']:
                await asyncio.sleep(0.1)

            if task.status == 'failed':
                raise Exception(f"Agent {agent_type} failed: {task.error}")

            # Update context
            context = task.result

        return context


class ParallelExecution:
    """
    Pattern: Execute multiple agents in parallel.

    Flow: Spawn Agent A, B, C simultaneously → Wait for all
    """

    async def execute(
        self,
        orchestrator: 'AgentOrchestrator',
        agents: List[Dict[str, Any]]  # [{'type': 'ingestion', 'context': {...}}, ...]
    ) -> List[Dict[str, Any]]:
        """Execute agents in parallel."""
        tasks = []

        for agent_spec in agents:
            task = await orchestrator.spawn_agent(
                agent_type=agent_spec['type'],
                context=agent_spec['context']
            )
            tasks.append(task)

        # Wait for all
        results = []
        for task in tasks:
            while task.status not in ['completed', 'failed']:
                await asyncio.sleep(0.1)
            results.append({
                'agent_type': task.agent_type,
                'status': task.status,
                'result': task.result,
            })

        return results


class OnDemandRequest:
    """
    Pattern: Agent requests help from another agent.

    Flow: Agent A → Orchestrator → Agent B → Response → Agent A
    """

    async def execute(
        self,
        orchestrator: 'AgentOrchestrator',
        from_agent: str,
        to_agent: str,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute on-demand request."""
        # Send request
        message = Message(
            message_id=f"req_{asyncio.get_event_loop().time()}",
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=MessageType.REQUEST,
            payload=request,
        )

        await orchestrator._send_message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type="REQUEST",
            payload=request,
        )

        # Wait for response
        while True:
            response = await orchestrator.get_message(from_agent)
            if response and response.message_type == MessageType.RESPONSE:
                return response.payload
```

---

## 5. Skills Catalog

### 5.1 Complete Skills List

| Agent | Skill | Purpose |
|-------|-------|---------|
| **Orchestrator** | agent-orchestration | Spawn/manage agents, maintain registry |
| | cli-handler | Parse commands, validate inputs |
| | state-manager | Track framework state |
| | error-handler | Graceful error handling |
| **Ingestion** | playwright-parser | Parse Playwright codegen JS |
| | action-extractor | Classify and enrich actions |
| | selector-analyzer | Analyze selector reliability |
| **Deduplication** | element-deduplicator | Find common elements |
| | component-extractor | Extract reusable components |
| | page-object-generator | Generate Page Object classes |
| **BDD Conversion** | gherkin-generator | Generate Given/When/Then |
| | step-definition-creator | Create Python step definitions |
| | scenario-optimizer | Optimize scenarios |
| **Execution** | test-runner | Execute Behave tests |
| | report-generator | Generate HTML reports |
| | failure-analyzer | AI root cause analysis |
| | self-healing | Auto-fix broken selectors |

### 5.2 Skill Dependencies

```
Orchestrator Skills (Independent):
  - agent-orchestration
  - cli-handler
  - state-manager
  - error-handler

Ingestion Agent Skills (Sequential):
  playwright-parser → action-extractor → selector-analyzer

Deduplication Agent Skills (Sequential):
  element-deduplicator → component-extractor → page-object-generator

BDD Conversion Agent Skills (Sequential):
  gherkin-generator → step-definition-creator → scenario-optimizer

Execution Agent Skills (Parallel + Sequential):
  test-runner → [failure-analyzer || self-healing] → report-generator
```

---

## 6. Deduplication Strategy

### 6.1 Rule-Based Deduplication (No ML)

```python
# src/claude_playwright_agent/skills/element_deduplicator.py

from typing import Dict, Any, List
from collections import defaultdict


class ElementDeduplicatorSkill:
    """
    Find duplicate/common UI elements using rule-based matching.

    NO ML, NO fuzzy matching, NO embeddings.
    Pure rule-based: exact match + structural patterns.
    """

    def __init__(self):
        self.selector_registry: Dict[str, Dict[str, Any]] = {}
        self.pattern_rules = self._build_pattern_rules()

    async def deduplicate(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Deduplicate elements across all actions.

        Args:
            actions: List of enriched actions

        Returns:
            Dictionary with common_elements and reusable_components
        """
        # Strategy 1: Exact Selector Matching
        common_elements = self._exact_match_deduplication(actions)

        # Strategy 2: Structural Pattern Matching
        pattern_groups = self._structural_pattern_deduplication(actions)

        # Strategy 3: Context-Based Grouping (form flows)
        form_groups = self._context_based_deduplication(actions)

        # Strategy 4: URL-Based Page Grouping
        page_groups = self._url_based_deduplication(actions)

        return {
            'common_elements': common_elements,
            'pattern_groups': pattern_groups,
            'form_groups': form_groups,
            'page_groups': page_groups,
        }

    def _exact_match_deduplication(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Strategy 1: Exact Selector Matching.

        Rule: Same selector + same action type = duplicate
        """
        selector_registry = defaultdict(lambda: {
            'count': 0,
            'recordings': [],
            'selector': '',
            'action_type': '',
        })

        for action in actions:
            selector = action.get('selector', '')
            action_type = action.get('type', '')

            if not selector:
                continue

            key = f"{selector}:{action_type}"

            selector_registry[key]['count'] += 1
            selector_registry[key]['selector'] = selector
            selector_registry[key]['action_type'] = action_type
            selector_registry[key]['recordings'].append(action.get('recording_id', 'unknown'))

        # Return common elements (count > 1)
        common = [
            {**v, 'id': k}
            for k, v in selector_registry.items()
            if v['count'] > 1
        ]

        return common

    def _structural_pattern_deduplication(self, actions: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """
        Strategy 2: Structural Pattern Matching.

        Rule: Same component type (email_input, password_input, etc.)
        """
        # Normalization patterns
        patterns = {
            'email_input': ['#email', '#user-email', '#username', '#user', 'input[type="email"]', 'input[name*="email"]'],
            'password_input': ['#password', '#pass', '#user-password', 'input[type="password"]', 'input[name*="password"]'],
            'submit_button': ['button[type="submit"]', '#submit', '#login-btn', 'role=button[name*="submit"]', 'role=button[name*="login"]', 'role=button[name*="sign"]'],
            'search_input': ['#search', '#query', 'input[name*="search"]', 'input[placeholder*="search"]'],
            'date_input': ['input[type="date"]', '#date', 'input[name*="date"]'],
        }

        component_groups = defaultdict(list)

        for action in actions:
            selector = action.get('selector', '').lower()

            for component_type, selector_patterns in patterns.items():
                if any(pattern.lower() in selector for pattern in selector_patterns):
                    component_groups[component_type].append(action)
                    break

        return dict(component_groups)

    def _context_based_deduplication(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Strategy 3: Context-Based Grouping.

        Rule: Multiple fill() actions followed by click(submit) = form
        """
        form_groups = []
        current_form = []

        for action in actions:
            if action['type'] == 'fill':
                current_form.append(action)
            elif action['type'] == 'click' and 'submit' in action.get('selector', '').lower():
                current_form.append(action)
                if len(current_form) > 1:  # At least 2 fields + submit
                    form_groups.append({
                        'type': 'form',
                        'fields': current_form[:-1],
                        'submit': current_form[-1],
                    })
                current_form = []
            elif action['type'] == 'navigation':
                current_form = []

        return form_groups

    def _url_based_deduplication(self, actions: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """
        Strategy 4: URL-Based Page Grouping.

        Rule: Same URL = same page context
        """
        page_groups = defaultdict(list)
        current_page = None

        for action in actions:
            if action['type'] == 'goto':
                current_page = action['url']

            if current_page:
                page_groups[current_page].append(action)

        return dict(page_groups)

    def _build_pattern_rules(self) -> Dict[str, List[str]]:
        """Build normalization pattern rules."""
        return {
            'email_input': ['#email', '#user-email', '#username', 'input[type="email"]'],
            'password_input': ['#password', '#pass', 'input[type="password"]'],
            'submit_button': ['button[type="submit"]', '#submit', '#login'],
        }
```

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

**Deliverable:** `cpa init my-project` works

| Task | Description |
|------|-------------|
| 1.1 | Create Orchestrator Agent skeleton |
| 1.2 | Implement cli-handler skill |
| 1.3 | Implement state-manager skill |
| 1.4 | Implement error-handler skill |
| 1.5 | Implement framework-creator skill |
| 1.6 | Create project directory structure |
| 1.7 | Generate configuration files |

### Phase 2: Ingestion (Week 3-4)

**Deliverable:** `cpa ingest recording.js` produces actions JSON

| Task | Description |
|------|-------------|
| 2.1 | Create Ingestion Agent |
| 2.2 | Implement playwright-parser skill |
| 2.3 | Implement action-extractor skill |
| 2.4 | Implement selector-analyzer skill |
| 2.5 | Test with sample recordings |

### Phase 3: Deduplication (Week 5-6)

**Deliverable:** Common elements identified, Page Objects generated

| Task | Description |
|------|-------------|
| 3.1 | Create Deduplication Agent |
| 3.2 | Implement element-deduplicator (exact match) |
| 3.3 | Implement structural pattern matching |
| 3.4 | Implement context-based grouping |
| 3.5 | Implement component-extractor skill |
| 3.6 | Implement page-object-generator skill |

### Phase 4: BDD Conversion (Week 7-8)

**Deliverable:** `cpa ingest` produces runnable .feature files

| Task | Description |
|------|-------------|
| 4.1 | Create BDD Conversion Agent |
| 4.2 | Implement gherkin-generator skill |
| 4.3 | Implement step-definition-creator skill |
| 4.4 | Implement scenario-optimizer skill |
| 4.5 | Generate Behave-compatible output |

### Phase 5: Execution (Week 9-10)

**Deliverable:** `cpa run` executes tests, generates AI reports

| Task | Description |
|------|-------------|
| 5.1 | Create Execution Agent |
| 5.2 | Implement test-runner skill |
| 5.3 | Implement report-generator skill |
| 5.4 | Implement failure-analyzer skill |
| 5.5 | Implement self-healing skill (rule-based) |

### Phase 6: Polish (Week 11-12)

**Deliverable:** Production-ready v1.0

| Task | Description |
|------|-------------|
| 6.1 | Advanced error recovery |
| 6.2 | Parallel test execution |
| 6.3 | CI/CD integration templates |
| 6.4 | Custom skill extensibility |
| 6.5 | Documentation and examples |

---

**Document Version:** 2.0
**Last Updated:** 2025-01-11
