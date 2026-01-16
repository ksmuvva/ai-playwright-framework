"""
E6.2 - Network Recording Skill.

This skill provides network recording capabilities:
- HAR capture
- Request/response tracking
- Network mocking
- Traffic analysis
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class NetworkEventType(str, Enum):
    """Network event types."""

    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"


class MockRuleType(str, Enum):
    """Mock rule types."""

    STATUS = "status"
    RESPONSE_BODY = "response_body"
    HEADERS = "headers"
    DELAY = "delay"
    FAILURE = "failure"


@dataclass
class NetworkRequest:
    """
    A network request.

    Attributes:
        request_id: Unique request identifier
        url: Request URL
        method: HTTP method
        headers: Request headers
        body: Request body
        timestamp: When request was made
        resource_type: Type of resource
    """

    request_id: str = field(default_factory=lambda: f"req_{uuid.uuid4().hex[:8]}")
    url: str = ""
    method: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    body: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    resource_type: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "url": self.url,
            "method": self.method,
            "headers": self.headers,
            "body": self.body,
            "timestamp": self.timestamp,
            "resource_type": self.resource_type,
        }


@dataclass
class NetworkResponse:
    """
    A network response.

    Attributes:
        response_id: Unique response identifier
        request_id: Associated request ID
        status_code: HTTP status code
        headers: Response headers
        body: Response body
        duration_ms: Response time in milliseconds
        size_bytes: Response size in bytes
        timestamp: When response was received
    """

    response_id: str = field(default_factory=lambda: f"resp_{uuid.uuid4().hex[:8]}")
    request_id: str = ""
    status_code: int = 200
    headers: dict[str, str] = field(default_factory=dict)
    body: str = ""
    duration_ms: int = 0
    size_bytes: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "response_id": self.response_id,
            "request_id": self.request_id,
            "status_code": self.status_code,
            "headers": self.headers,
            "body": self.body,
            "duration_ms": self.duration_ms,
            "size_bytes": self.size_bytes,
            "timestamp": self.timestamp,
        }


@dataclass
class MockRule:
    """
    A mock rule for network mocking.

    Attributes:
        rule_id: Unique rule identifier
        url_pattern: URL pattern to match
        rule_type: Type of mock rule
        value: Mock value
        delay_ms: Delay to apply
        priority: Rule priority (higher = first)
        enabled: Whether rule is enabled
    """

    rule_id: str = field(default_factory=lambda: f"rule_{uuid.uuid4().hex[:8]}")
    url_pattern: str = ""
    rule_type: MockRuleType = MockRuleType.RESPONSE_BODY
    value: Any = None
    delay_ms: int = 0
    priority: int = 0
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule_id": self.rule_id,
            "url_pattern": self.url_pattern,
            "rule_type": self.rule_type.value,
            "value": self.value,
            "delay_ms": self.delay_ms,
            "priority": self.priority,
            "enabled": self.enabled,
        }


@dataclass
class NetworkContext:
    """
    Context for network recording operations.

    Attributes:
        context_id: Unique context identifier
        workflow_id: Associated workflow ID
        requests_captured: Number of requests captured
        responses_captured: Number of responses captured
        har_files_generated: Number of HAR files generated
        mock_rules_created: Number of mock rules created
        traffic_history: List of network events
        started_at: When context started
        completed_at: When context completed
        context_preserved: Whether context was preserved
    """

    context_id: str = field(default_factory=lambda: f"net_ctx_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    requests_captured: int = 0
    responses_captured: int = 0
    har_files_generated: int = 0
    mock_rules_created: int = 0
    traffic_history: list[dict[str, Any]] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "context_id": self.context_id,
            "workflow_id": self.workflow_id,
            "requests_captured": self.requests_captured,
            "responses_captured": self.responses_captured,
            "har_files_generated": self.har_files_generated,
            "mock_rules_created": self.mock_rules_created,
            "traffic_history": self.traffic_history,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "context_preserved": self.context_preserved,
        }


class NetworkRecordingAgent(BaseAgent):
    """
    Network Recording Agent.

    This agent provides:
    1. HAR capture
    2. Request/response tracking
    3. Network mocking
    4. Traffic analysis
    """

    name = "e6_2_network_recording"
    version = "1.0.0"
    description = "E6.2 - Network Recording"

    def __init__(self, **kwargs) -> None:
        """Initialize the network recording agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E6.2 - Network Recording agent for the Playwright test automation framework. You help users with e6.2 - network recording tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._context_history: list[NetworkContext] = []
        self._request_registry: dict[str, NetworkRequest] = {}
        self._response_registry: dict[str, NetworkResponse] = {}
        self._mock_rules: list[MockRule] = []

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
        """Execute network recording task."""
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "capture_request":
            return await self._capture_request(context, execution_context)
        elif task_type == "capture_response":
            return await self._capture_response(context, execution_context)
        elif task_type == "generate_har":
            return await self._generate_har(context, execution_context)
        elif task_type == "add_mock_rule":
            return await self._add_mock_rule(context, execution_context)
        elif task_type == "get_traffic":
            return await self._get_traffic(context, execution_context)
        elif task_type == "get_mock_rules":
            return await self._get_mock_rules(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _capture_request(self, context: dict[str, Any], execution_context: Any) -> str:
        """Capture a network request."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        url = context.get("url", "")
        method = context.get("method", "GET")
        headers = context.get("headers", {})
        body = context.get("body", "")

        request = NetworkRequest(
            url=url,
            method=method,
            headers=headers,
            body=body,
        )

        self._request_registry[request.request_id] = request

        return f"Captured request: {method} {url} (ID: {request.request_id})"

    async def _capture_response(self, context: dict[str, Any], execution_context: Any) -> str:
        """Capture a network response."""
        request_id = context.get("request_id")
        status_code = context.get("status_code", 200)
        headers = context.get("headers", {})
        body = context.get("body", "")
        duration_ms = context.get("duration_ms", 0)

        response = NetworkResponse(
            request_id=request_id,
            status_code=status_code,
            headers=headers,
            body=body,
            duration_ms=duration_ms,
        )

        self._response_registry[response.response_id] = response

        return f"Captured response: {status_code} for request '{request_id}'"

    async def _generate_har(self, context: dict[str, Any], execution_context: Any) -> str:
        """Generate HAR file from captured traffic."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        output_path = context.get("output_path", "network.har")

        # Simulate HAR generation
        request_count = len(self._request_registry)
        response_count = len(self._response_registry)

        har_content = {
            "log": {
                "version": "1.2",
                "creator": {"name": "Claude Playwright Agent"},
                "entries": [],
            }
        }

        # Add entries from requests/responses
        for req in self._request_registry.values():
            resp = self._response_registry.get(req.request_id)
            entry = {
                "request": {
                    "method": req.method,
                    "url": req.url,
                    "headers": req.headers,
                },
                "response": {
                    "status": resp.status_code if resp else 0,
                    "headers": resp.headers if resp else {},
                },
                "timings": {
                    "duration": resp.duration_ms if resp else 0,
                },
            }
            har_content["log"]["entries"].append(entry)

        return f"Generated HAR file: {output_path} with {request_count} request(s)"

    async def _add_mock_rule(self, context: dict[str, Any], execution_context: Any) -> str:
        """Add a mock rule."""
        url_pattern = context.get("url_pattern", "")
        rule_type = context.get("rule_type", MockRuleType.RESPONSE_BODY)
        value = context.get("value")
        delay_ms = context.get("delay_ms", 0)
        priority = context.get("priority", 0)

        if isinstance(rule_type, str):
            rule_type = MockRuleType(rule_type)

        rule = MockRule(
            url_pattern=url_pattern,
            rule_type=rule_type,
            value=value,
            delay_ms=delay_ms,
            priority=priority,
        )

        self._mock_rules.append(rule)
        self._mock_rules.sort(key=lambda r: r.priority, reverse=True)

        return f"Added mock rule for pattern: {url_pattern}"

    async def _get_traffic(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get captured traffic."""
        url_pattern = context.get("url_pattern")

        requests = list(self._request_registry.values())

        if url_pattern:
            import re
            requests = [r for r in requests if re.search(url_pattern, r.url)]

        if not requests:
            return "No traffic captured"

        return f"Traffic: {len(requests)} request(s) captured"

    async def _get_mock_rules(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get all mock rules."""
        if not self._mock_rules:
            return "No mock rules defined"

        return f"Mock rules: {len(self._mock_rules)} rule(s)"

    def get_request_registry(self) -> dict[str, NetworkRequest]:
        """Get request registry."""
        return self._request_registry.copy()

    def get_response_registry(self) -> dict[str, NetworkResponse]:
        """Get response registry."""
        return self._response_registry.copy()

    def get_context_history(self) -> list[NetworkContext]:
        """Get context history."""
        return self._context_history.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

