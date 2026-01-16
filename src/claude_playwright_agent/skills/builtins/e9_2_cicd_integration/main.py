"""
E9.2 - CI/CD Integration Skill.

This skill provides CI/CD integration capabilities:
- Pipeline configuration generation
- GitHub Actions integration
- GitLab CI integration
- Jenkins integration
- Artifact management
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class Platform(str, Enum):
    """CI/CD platforms."""

    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    JENKINS = "jenkins"
    AZURE_DEVOPS = "azure_devops"
    CIRCLE_CI = "circle_ci"
    BITBUCKET = "bitbucket"


class PipelineStatus(str, Enum):
    """Pipeline status types."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class ArtifactType(str, Enum):
    """Artifact types."""

    TEST_REPORT = "test_report"
    COVERAGE_REPORT = "coverage_report"
    SCREENSHOTS = "screenshots"
    VIDEOS = "videos"
    LOGS = "logs"
    ARTIFACTS = "artifacts"


@dataclass
class PipelineStep:
    """
    A step in a CI/CD pipeline.

    Attributes:
        step_id: Unique step identifier
        name: Step name
        command: Command to execute
        run_condition: Condition for running step
        depends_on: List of step IDs this step depends on
        timeout_seconds: Step timeout
        retry_count: Number of retries on failure
        continue_on_error: Whether to continue on error
        artifacts: Artifacts to collect
    """

    step_id: str = field(default_factory=lambda: f"step_{uuid.uuid4().hex[:8]}")
    name: str = ""
    command: str = ""
    run_condition: str = "always"
    depends_on: list[str] = field(default_factory=list)
    timeout_seconds: int = 300
    retry_count: int = 0
    continue_on_error: bool = False
    artifacts: list[ArtifactType] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_id": self.step_id,
            "name": self.name,
            "command": self.command,
            "run_condition": self.run_condition,
            "depends_on": self.depends_on,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "continue_on_error": self.continue_on_error,
            "artifacts": [a.value for a in self.artifacts],
        }


@dataclass
class PipelineConfig:
    """
    CI/CD pipeline configuration.

    Attributes:
        config_id: Unique config identifier
        workflow_id: Associated workflow ID
        platform: CI/CD platform
        name: Pipeline name
        description: Pipeline description
        trigger_events: Events that trigger pipeline
        environment_vars: Environment variables
        steps: Pipeline steps
        artifacts: Artifacts to collect
        generated_at: When config was generated
    """

    config_id: str = field(default_factory=lambda: f"cfg_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    platform: Platform = Platform.GITHUB_ACTIONS
    name: str = ""
    description: str = ""
    trigger_events: list[str] = field(default_factory=list)
    environment_vars: dict[str, str] = field(default_factory=dict)
    steps: list[PipelineStep] = field(default_factory=list)
    artifacts: list[ArtifactType] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "config_id": self.config_id,
            "workflow_id": self.workflow_id,
            "platform": self.platform.value,
            "name": self.name,
            "description": self.description,
            "trigger_events": self.trigger_events,
            "environment_vars": self.environment_vars,
            "steps": [s.to_dict() for s in self.steps],
            "artifacts": [a.value for a in self.artifacts],
            "generated_at": self.generated_at,
        }


@dataclass
class PipelineExecution:
    """
    A pipeline execution record.

    Attributes:
        execution_id: Unique execution identifier
        config_id: Associated config ID
        workflow_id: Associated workflow ID
        run_number: Run number
        status: Execution status
        started_at: When execution started
        completed_at: When execution completed
        duration_seconds: Execution duration
        steps_completed: Number of steps completed
        steps_failed: Number of steps failed
        artifacts_collected: Artifacts collected
        commit_sha: Commit SHA
        branch: Branch name
        trigger_actor: User or system that triggered
    """

    execution_id: str = field(default_factory=lambda: f"exec_{uuid.uuid4().hex[:8]}")
    config_id: str = ""
    workflow_id: str = ""
    run_number: int = 0
    status: PipelineStatus = PipelineStatus.PENDING
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    duration_seconds: float = 0.0
    steps_completed: int = 0
    steps_failed: int = 0
    artifacts_collected: dict[str, str] = field(default_factory=dict)
    commit_sha: str = ""
    branch: str = ""
    trigger_actor: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "execution_id": self.execution_id,
            "config_id": self.config_id,
            "workflow_id": self.workflow_id,
            "run_number": self.run_number,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.duration_seconds,
            "steps_completed": self.steps_completed,
            "steps_failed": self.steps_failed,
            "artifacts_collected": self.artifacts_collected,
            "commit_sha": self.commit_sha,
            "branch": self.branch,
            "trigger_actor": self.trigger_actor,
        }


@dataclass
class IntegrationContext:
    """
    Context for CI/CD integration operations.

    Attributes:
        context_id: Unique context identifier
        workflow_id: Associated workflow ID
        configs_generated: Number of configs generated
        pipelines_executed: Number of pipelines executed
        artifacts_uploaded: Number of artifacts uploaded
        execution_history: List of pipeline executions
        started_at: When context started
        completed_at: When context completed
        context_preserved: Whether context was preserved
    """

    context_id: str = field(default_factory=lambda: f"cicd_ctx_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    configs_generated: int = 0
    pipelines_executed: int = 0
    artifacts_uploaded: int = 0
    execution_history: list[PipelineExecution] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "context_id": self.context_id,
            "workflow_id": self.workflow_id,
            "configs_generated": self.configs_generated,
            "pipelines_executed": self.pipelines_executed,
            "artifacts_uploaded": self.artifacts_uploaded,
            "execution_history": [e.to_dict() for e in self.execution_history],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "context_preserved": self.context_preserved,
        }


class CICDIntegrationAgent(BaseAgent):
    """
    CI/CD Integration Agent.

    This agent provides:
    1. Pipeline configuration generation
    2. GitHub Actions integration
    3. GitLab CI integration
    4. Jenkins integration
    5. Artifact management
    """

    name = "e9_2_cicd_integration"
    version = "1.0.0"
    description = "E9.2 - CI/CD Integration"

    def __init__(self, **kwargs) -> None:
        """Initialize the CI/CD integration agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E9.2 - CI/CD Integration agent for the Playwright test automation framework. You help users with e9.2 - ci/cd integration tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._context_history: list[IntegrationContext] = []
        self._config_registry: dict[str, PipelineConfig] = {}
        self._execution_history: list[PipelineExecution] = []
        self._artifact_registry: dict[str, dict[str, str]] = {}

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process input data and return results.

        Args:
            input_data: Input data for processing

        Returns:
            Processing results
        """
        task = input_data.get("task", "unknown")
        context = input_data.get("context", {})

        # Track context history
        self._context_history.append({
            "operation": "process",
            "task": task,
            "timestamp": self._get_timestamp()
        })

        result = await self.run(task, context)

        return {
            "success": True,
            "result": result,
            "agent": self.name
        }

    async def run(self, task: str, context: dict[str, Any]) -> str:
        """
        Execute CI/CD integration task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the CI/CD operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "generate_pipeline":
            return await self._generate_pipeline(context, execution_context)
        elif task_type == "get_pipeline_config":
            return await self._get_pipeline_config(context, execution_context)
        elif task_type == "execute_pipeline":
            return await self._execute_pipeline(context, execution_context)
        elif task_type == "get_execution_status":
            return await self._get_execution_status(context, execution_context)
        elif task_type == "upload_artifact":
            return await self._upload_artifact(context, execution_context)
        elif task_type == "get_artifact":
            return await self._get_artifact(context, execution_context)
        elif task_type == "list_artifacts":
            return await self._list_artifacts(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _generate_pipeline(self, context: dict[str, Any], execution_context: Any) -> str:
        """Generate CI/CD pipeline configuration."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        platform = context.get("platform", Platform.GITHUB_ACTIONS)
        name = context.get("name", "Test Pipeline")
        description = context.get("description", "")
        trigger_events = context.get("trigger_events", ["push", "pull_request"])

        if isinstance(platform, str):
            platform = Platform(platform)

        # Create pipeline steps
        steps = [
            PipelineStep(
                name="Checkout",
                command="actions/checkout@v3" if platform == Platform.GITHUB_ACTIONS else "git clone $CI_REPOSITORY_URL",
            ),
            PipelineStep(
                name="Setup Python",
                command="actions/setup-python@v3 with python-version: '3.12'" if platform == Platform.GITHUB_ACTIONS else "pip install python",
            ),
            PipelineStep(
                name="Install Dependencies",
                command="pip install -r requirements.txt",
            ),
            PipelineStep(
                name="Run Tests",
                command="cpa run workflow test",
                artifacts=[ArtifactType.TEST_REPORT, ArtifactType.SCREENSHOTS],
            ),
        ]

        # Create pipeline config
        config = PipelineConfig(
            workflow_id=workflow_id,
            platform=platform,
            name=name,
            description=description,
            trigger_events=trigger_events,
            steps=steps,
            artifacts=[ArtifactType.TEST_REPORT, ArtifactType.COVERAGE_REPORT],
        )

        self._config_registry[config.config_id] = config

        # Generate platform-specific YAML
        yaml_content = self._generate_yaml(config)

        return f"Generated {platform.value} pipeline '{name}' (ID: {config.config_id})\n\n{yaml_content}"

    def _generate_yaml(self, config: PipelineConfig) -> str:
        """Generate platform-specific YAML configuration."""
        if config.platform == Platform.GITHUB_ACTIONS:
            return self._generate_github_actions(config)
        elif config.platform == Platform.GITLAB_CI:
            return self._generate_gitlab_ci(config)
        elif config.platform == Platform.JENKINS:
            return self._generate_jenkins(config)
        else:
            return f"# Platform {config.platform.value} not yet supported"

    def _generate_github_actions(self, config: PipelineConfig) -> str:
        """Generate GitHub Actions workflow YAML."""
        yaml = f"""name: {config.name}

on:
"""
        for event in config.trigger_events:
            if event == "push":
                yaml += "  push:\n    branches: [ main, develop ]\n"
            elif event == "pull_request":
                yaml += "  pull_request:\n    branches: [ main ]\n"

        yaml += f"""
jobs:
  test:
    runs-on: ubuntu-latest

    steps:
"""
        for step in config.steps:
            yaml += f"    - name: {step.name}\n"
            if "checkout" in step.command.lower():
                yaml += "      uses: actions/checkout@v3\n"
            elif "setup" in step.command.lower():
                yaml += "      uses: actions/setup-python@v3\n"
                yaml += "      with:\n"
                yaml += "        python-version: '3.12'\n"
            else:
                yaml += f"      run: {step.command}\n"

            if ArtifactType.TEST_REPORT in step.artifacts:
                yaml += """      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: test-report
        path: reports/test-report.html
"""

        return yaml

    def _generate_gitlab_ci(self, config: PipelineConfig) -> str:
        """Generate GitLab CI configuration."""
        yaml = f"""stages:
  - test
  - report

variables:
  PROJECT_PATH: "$CI_PROJECT_DIR"

before_script:
  - pip install -r requirements.txt

"""
        for i, step in enumerate(config.steps):
            yaml += f"{step.name.lower().replace(' ', '_')}:\n"
            yaml += f"  stage: test\n"
            yaml += f"  script:\n"
            yaml += f"    - {step.command}\n"
            if ArtifactType.TEST_REPORT in step.artifacts:
                yaml += "  artifacts:\n"
                yaml += "    paths:\n"
                yaml += "      - reports/\n"
                yaml += "    when: always\n"
            yaml += "\n"

        return yaml

    def _generate_jenkins(self, config: PipelineConfig) -> str:
        """Generate Jenkins pipeline configuration."""
        jenkinsfile = f"""pipeline {{
    agent any

    stages {{
"""
        for step in config.steps:
            jenkinsfile += f"        stage('{step.name}') {{\n"
            jenkinsfile += "            steps {\n"
            jenkinsfile += f"                sh '{step.command}'\n"
            if ArtifactType.TEST_REPORT in step.artifacts:
                jenkinsfile += "                publishHTML(target: [\n"
                jenkinsfile += "                    reportDir: 'reports',\n"
                jenkinsfile += "                    reportFiles: 'test-report.html',\n"
                jenkinsfile += "                    reportName: 'Test Report'\n"
                jenkinsfile += "                ])\n"
            jenkinsfile += "            }\n"
            jenkinsfile += "        }\n"

        jenkinsfile += "    }\n"
        jenkinsfile += "    post {\n"
        jenkinsfile += "        always {\n"
        jenkinsfile += "            archiveArtifacts artifacts: 'reports/**/*'\n"
        jenkinsfile += "        }\n"
        jenkinsfile += "    }\n"
        jenkinsfile += "}\n"

        return jenkinsfile

    async def _get_pipeline_config(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get pipeline configuration by ID."""
        config_id = context.get("config_id")

        if not config_id:
            return "Error: config_id is required"

        config = self._config_registry.get(config_id)
        if config:
            return (
                f"Pipeline '{config_id}': "
                f"{config.name} on {config.platform.value}, "
                f"{len(config.steps)} step(s)"
            )

        return f"Error: Pipeline config '{config_id}' not found"

    async def _execute_pipeline(self, context: dict[str, Any], execution_context: Any) -> str:
        """Execute a pipeline."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        config_id = context.get("config_id")
        commit_sha = context.get("commit_sha", "")
        branch = context.get("branch", "main")
        trigger_actor = context.get("trigger_actor", "system")

        if not config_id:
            return "Error: config_id is required"

        config = self._config_registry.get(config_id)
        if not config:
            return f"Error: Pipeline config '{config_id}' not found"

        # Create execution record
        execution = PipelineExecution(
            config_id=config_id,
            workflow_id=workflow_id,
            status=PipelineStatus.RUNNING,
            commit_sha=commit_sha,
            branch=branch,
            trigger_actor=trigger_actor,
        )

        self._execution_history.append(execution)

        # Simulate pipeline execution
        execution.steps_completed = len(config.steps)
        execution.status = PipelineStatus.SUCCESS
        execution.completed_at = datetime.now().isoformat()
        execution.duration_seconds = 30.0

        return f"Executed pipeline '{config_id}' with status: {execution.status.value}"

    async def _get_execution_status(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get pipeline execution status."""
        execution_id = context.get("execution_id")

        if not execution_id:
            return "Error: execution_id is required"

        for execution in self._execution_history:
            if execution.execution_id == execution_id:
                return (
                    f"Execution '{execution_id}': "
                    f"status={execution.status.value}, "
                    f"{execution.steps_completed} step(s) completed, "
                    f"{execution.duration_seconds:.2f}s"
                )

        return f"Error: Execution '{execution_id}' not found"

    async def _upload_artifact(self, context: dict[str, Any], execution_context: Any) -> str:
        """Upload an artifact."""
        execution_id = context.get("execution_id")
        artifact_type = context.get("artifact_type")
        artifact_path = context.get("artifact_path")

        if not execution_id or not artifact_type:
            return "Error: execution_id and artifact_type are required"

        if isinstance(artifact_type, str):
            artifact_type = ArtifactType(artifact_type)

        # Find execution
        for execution in self._execution_history:
            if execution.execution_id == execution_id:
                execution.artifacts_collected[artifact_type.value] = artifact_path or f"artifacts/{artifact_type.value}"
                return f"Uploaded artifact '{artifact_type.value}' for execution '{execution_id}'"

        return f"Error: Execution '{execution_id}' not found"

    async def _get_artifact(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get artifact info."""
        execution_id = context.get("execution_id")
        artifact_type = context.get("artifact_type")

        if not execution_id or not artifact_type:
            return "Error: execution_id and artifact_type are required"

        for execution in self._execution_history:
            if execution.execution_id == execution_id:
                artifact_path = execution.artifacts_collected.get(artifact_type)
                if artifact_path:
                    return f"Artifact '{artifact_type}': {artifact_path}"

        return f"Error: Artifact '{artifact_type}' not found for execution '{execution_id}'"

    async def _list_artifacts(self, context: dict[str, Any], execution_context: Any) -> str:
        """List all artifacts for an execution."""
        execution_id = context.get("execution_id")

        if not execution_id:
            return "Error: execution_id is required"

        for execution in self._execution_history:
            if execution.execution_id == execution_id:
                if not execution.artifacts_collected:
                    return "No artifacts found"

                output = f"Artifacts for execution '{execution_id}':\n"
                for artifact_type, path in execution.artifacts_collected.items():
                    output += f"- {artifact_type}: {path}\n"

                return output

        return f"Error: Execution '{execution_id}' not found"

    def get_config_registry(self) -> dict[str, PipelineConfig]:
        """Get config registry."""
        return self._config_registry.copy()

    def get_execution_history(self) -> list[PipelineExecution]:
        """Get execution history."""
        return self._execution_history.copy()

    def get_context_history(self) -> list[IntegrationContext]:
        """Get context history."""
        return self._context_history.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

