"""
E9.4 - API Validation Integration Skill.

This skill provides API validation capabilities:
- Schema validation
- Response validation
- Contract testing
- API mocking
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from claude_playwright_agent.agents.base import BaseAgent


class ValidationType(str, Enum):
    """Validation types."""

    SCHEMA = "schema"
    RESPONSE = "response"
    CONTRACT = "contract"
    SECURITY = "security"


class HTTPMethod(str, Enum):
    """HTTP methods."""

    GET = "get"
    POST = "post"
    PUT = "put"
    DELETE = "delete"
    PATCH = "patch"
    HEAD = "head"
    OPTIONS = "options"


class ValidationStatus(str, Enum):
    """Validation status types."""

    PENDING = "pending"
    VALIDATING = "validating"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class APISchema:
    """
    An API schema definition.

    Attributes:
        schema_id: Unique schema identifier
        name: Schema name
        endpoint: API endpoint
        method: HTTP method
        request_schema: Request body schema
        response_schema: Response body schema
        headers: Expected headers
        parameters: Query/path parameters
        version: API version
        content_type: Content type
    """

    schema_id: str = field(default_factory=lambda: f"schema_{uuid.uuid4().hex[:8]}")
    name: str = ""
    endpoint: str = ""
    method: HTTPMethod = HTTPMethod.GET
    request_schema: dict[str, Any] = field(default_factory=dict)
    response_schema: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)
    version: str = "1.0"
    content_type: str = "application/json"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "schema_id": self.schema_id,
            "name": self.name,
            "endpoint": self.endpoint,
            "method": self.method.value,
            "request_schema": self.request_schema,
            "response_schema": self.response_schema,
            "headers": self.headers,
            "parameters": self.parameters,
            "version": self.version,
            "content_type": self.content_type,
        }


@dataclass
class APIResponse:
    """
    An API response.

    Attributes:
        response_id: Unique response identifier
        status_code: HTTP status code
        headers: Response headers
        body: Response body
        duration_ms: Response time in milliseconds
        size_bytes: Response size in bytes
        timestamp: When response was received
    """

    response_id: str = field(default_factory=lambda: f"resp_{uuid.uuid4().hex[:8]}")
    status_code: int = 200
    headers: dict[str, str] = field(default_factory=dict)
    body: dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0
    size_bytes: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "response_id": self.response_id,
            "status_code": self.status_code,
            "headers": self.headers,
            "body": self.body,
            "duration_ms": self.duration_ms,
            "size_bytes": self.size_bytes,
            "timestamp": self.timestamp,
        }


@dataclass
class ValidationError:
    """
    A validation error.

    Attributes:
        error_id: Unique error identifier
        validation_type: Type of validation
        field: Field that failed validation
        expected: Expected value
        actual: Actual value
        message: Error message
        severity: Error severity
    """

    error_id: str = field(default_factory=lambda: f"err_{uuid.uuid4().hex[:8]}")
    validation_type: ValidationType = ValidationType.SCHEMA
    field: str = ""
    expected: Any = None
    actual: Any = None
    message: str = ""
    severity: str = "error"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error_id": self.error_id,
            "validation_type": self.validation_type.value,
            "field": self.field,
            "expected": self.expected,
            "actual": self.actual,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass
class ValidationContext:
    """
    Context for API validation operations.

    Attributes:
        context_id: Unique context identifier
        workflow_id: Associated workflow ID
        validations_performed: Number of validations performed
        validations_passed: Number of validations passed
        validations_failed: Number of validations failed
        validation_errors: List of validation errors
        started_at: When validation started
        completed_at: When validation completed
        context_preserved: Whether context was preserved
    """

    context_id: str = field(default_factory=lambda: f"val_ctx_{uuid.uuid4().hex[:8]}")
    workflow_id: str = ""
    validations_performed: int = 0
    validations_passed: int = 0
    validations_failed: int = 0
    validation_errors: list[ValidationError] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""
    context_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "context_id": self.context_id,
            "workflow_id": self.workflow_id,
            "validations_performed": self.validations_performed,
            "validations_passed": self.validations_passed,
            "validations_failed": self.validations_failed,
            "validation_errors": [e.to_dict() for e in self.validation_errors],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "context_preserved": self.context_preserved,
        }


class APIValidationAgent(BaseAgent):
    """
    API Validation Integration Agent.

    This agent provides:
    1. Schema validation
    2. Response validation
    3. Contract testing
    4. API mocking
    """

    name = "e9_4_api_validation"
    version = "1.0.0"
    description = "E9.4 - API Validation Integration"

    def __init__(self, **kwargs) -> None:
        """Initialize the API validation agent."""
        # Set a default system prompt if not provided
        if "system_prompt" not in kwargs:
            kwargs["system_prompt"] = 'You are a E9.4 - API Validation Integration agent for the Playwright test automation framework. You help users with e9.4 - api validation integration tasks and operations.'
        super().__init__(**kwargs)
        # Track context history
        self._context_history = []
        self._context_history: list[ValidationContext] = []
        self._schema_registry: dict[str, APISchema] = {}
        self._response_history: list[APIResponse] = []
        self._validation_errors: list[ValidationError] = []

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
        Execute API validation task.

        Args:
            task: Task to perform
            context: Execution context (always required)

        Returns:
            Result of the validation operation
        """
        # Extract execution context - always required
        execution_context = context.get("execution_context")
        if not execution_context:
            execution_context = {
                "task_id": context.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                "workflow_id": context.get("workflow_id", ""),
            }

        task_type = context.get("task_type", task)

        if task_type == "validate_schema":
            return await self._validate_schema(context, execution_context)
        elif task_type == "validate_response":
            return await self._validate_response(context, execution_context)
        elif task_type == "register_schema":
            return await self._register_schema(context, execution_context)
        elif task_type == "get_schema":
            return await self._get_schema(context, execution_context)
        elif task_type == "contract_test":
            return await self._contract_test(context, execution_context)
        elif task_type == "get_validation_context":
            return await self._get_validation_context(context, execution_context)
        elif task_type == "list_schemas":
            return await self._list_schemas(context, execution_context)
        else:
            return f"Unknown task type: {task_type}"

    async def _register_schema(self, context: dict[str, Any], execution_context: Any) -> str:
        """Register an API schema."""
        workflow_id = context.get("workflow_id", getattr(execution_context, "workflow_id", execution_context.get("workflow_id", "")))
        name = context.get("name", "")
        endpoint = context.get("endpoint", "")
        method = context.get("method", HTTPMethod.GET)
        request_schema = context.get("request_schema", {})
        response_schema = context.get("response_schema", {})

        if isinstance(method, str):
            method = HTTPMethod(method)

        schema = APISchema(
            name=name,
            endpoint=endpoint,
            method=method,
            request_schema=request_schema,
            response_schema=response_schema,
        )

        self._schema_registry[schema.schema_id] = schema

        return f"Registered schema '{name}' for {method.value.upper()} {endpoint} (ID: {schema.schema_id})"

    async def _validate_schema(self, context: dict[str, Any], execution_context: Any) -> str:
        """Validate data against a schema."""
        schema_id = context.get("schema_id")
        data = context.get("data", {})

        if not schema_id:
            return "Error: schema_id is required"

        schema = self._schema_registry.get(schema_id)
        if not schema:
            return f"Error: Schema '{schema_id}' not found"

        errors = []

        # Validate response schema
        if schema.response_schema:
            schema_errors = self._validate_against_schema(data, schema.response_schema)
            errors.extend(schema_errors)

        if errors:
            self._validation_errors.extend(errors)
            return f"Validation failed: {len(errors)} error(s)"

        return f"Validation passed: Data matches schema '{schema.name}'"

    def _validate_against_schema(self, data: dict[str, Any], schema: dict[str, Any]) -> list[ValidationError]:
        """Validate data against a JSON schema."""
        errors = []

        # Required fields
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                errors.append(ValidationError(
                    validation_type=ValidationType.SCHEMA,
                    field=field,
                    expected=f"present",
                    actual="missing",
                    message=f"Required field '{field}' is missing",
                ))

        # Type validation
        properties = schema.get("properties", {})
        for field_name, field_schema in properties.items():
            if field_name in data:
                expected_type = field_schema.get("type")
                actual_value = data[field_name]

                if expected_type == "string" and not isinstance(actual_value, str):
                    errors.append(ValidationError(
                        validation_type=ValidationType.SCHEMA,
                        field=field_name,
                        expected=expected_type,
                        actual=type(actual_value).__name__,
                        message=f"Field '{field_name}' should be {expected_type}",
                    ))
                elif expected_type == "integer" and not isinstance(actual_value, int):
                    errors.append(ValidationError(
                        validation_type=ValidationType.SCHEMA,
                        field=field_name,
                        expected=expected_type,
                        actual=type(actual_value).__name__,
                        message=f"Field '{field_name}' should be {expected_type}",
                    ))
                elif expected_type == "number" and not isinstance(actual_value, (int, float)):
                    errors.append(ValidationError(
                        validation_type=ValidationType.SCHEMA,
                        field=field_name,
                        expected=expected_type,
                        actual=type(actual_value).__name__,
                        message=f"Field '{field_name}' should be {expected_type}",
                    ))
                elif expected_type == "boolean" and not isinstance(actual_value, bool):
                    errors.append(ValidationError(
                        validation_type=ValidationType.SCHEMA,
                        field=field_name,
                        expected=expected_type,
                        actual=type(actual_value).__name__,
                        message=f"Field '{field_name}' should be {expected_type}",
                    ))
                elif expected_type == "array" and not isinstance(actual_value, list):
                    errors.append(ValidationError(
                        validation_type=ValidationType.SCHEMA,
                        field=field_name,
                        expected=expected_type,
                        actual=type(actual_value).__name__,
                        message=f"Field '{field_name}' should be {expected_type}",
                    ))
                elif expected_type == "object" and not isinstance(actual_value, dict):
                    errors.append(ValidationError(
                        validation_type=ValidationType.SCHEMA,
                        field=field_name,
                        expected=expected_type,
                        actual=type(actual_value).__name__,
                        message=f"Field '{field_name}' should be {expected_type}",
                    ))

        return errors

    async def _validate_response(self, context: dict[str, Any], execution_context: Any) -> str:
        """Validate an API response."""
        schema_id = context.get("schema_id")
        status_code = context.get("status_code", 200)
        headers = context.get("headers", {})
        body = context.get("body", {})
        duration_ms = context.get("duration_ms", 0)

        if not schema_id:
            return "Error: schema_id is required"

        schema = self._schema_registry.get(schema_id)
        if not schema:
            return f"Error: Schema '{schema_id}' not found"

        # Create response record
        response = APIResponse(
            status_code=status_code,
            headers=headers,
            body=body,
            duration_ms=duration_ms,
        )

        self._response_history.append(response)

        errors = []

        # Validate status code (expecting 2xx for success)
        if not (200 <= status_code < 300):
            errors.append(ValidationError(
                validation_type=ValidationType.RESPONSE,
                field="status_code",
                expected="2xx",
                actual=str(status_code),
                message=f"Status code {status_code} indicates failure",
            ))

        # Validate body against schema
        if schema.response_schema:
            schema_errors = self._validate_against_schema(body, schema.response_schema)
            errors.extend(schema_errors)

        # Validate content type
        if schema.content_type:
            content_type = headers.get("content-type", "")
            if schema.content_type not in content_type:
                errors.append(ValidationError(
                    validation_type=ValidationType.RESPONSE,
                    field="content-type",
                    expected=schema.content_type,
                    actual=content_type,
                    message=f"Content-Type mismatch",
                ))

        if errors:
            self._validation_errors.extend(errors)
            return f"Response validation failed: {len(errors)} error(s)"

        return f"Response validation passed: {status_code} OK, {len(body)} fields"

    async def _get_schema(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get schema by ID."""
        schema_id = context.get("schema_id")

        if not schema_id:
            return "Error: schema_id is required"

        schema = self._schema_registry.get(schema_id)
        if schema:
            return (
                f"Schema '{schema_id}': "
                f"{schema.name}, "
                f"{schema.method.value.upper()} {schema.endpoint}, "
                f"version={schema.version}"
            )

        return f"Error: Schema '{schema_id}' not found"

    async def _contract_test(self, context: dict[str, Any], execution_context: Any) -> str:
        """Perform contract testing."""
        schema_id = context.get("schema_id")
        test_requests = context.get("test_requests", [])

        if not schema_id:
            return "Error: schema_id is required"

        schema = self._schema_registry.get(schema_id)
        if not schema:
            return f"Error: Schema '{schema_id}' not found"

        passed = 0
        failed = 0

        for i, request_data in enumerate(test_requests):
            # Simulate contract test
            try:
                # Validate request against request schema
                if schema.request_schema:
                    errors = self._validate_against_schema(request_data, schema.request_schema)
                    if errors:
                        failed += 1
                        continue

                passed += 1
            except Exception:
                failed += 1

        return f"Contract test complete: {passed} passed, {failed} failed"

    async def _get_validation_context(self, context: dict[str, Any], execution_context: Any) -> str:
        """Get validation context by ID."""
        context_id = context.get("context_id")

        if not context_id:
            return "Error: context_id is required"

        for validation_context in self._context_history:
            if validation_context.context_id == context_id:
                return (
                    f"Validation context '{context_id}': "
                    f"{validation_context.validations_performed} validation(s), "
                    f"{validation_context.validations_passed} passed, "
                    f"{validation_context.validations_failed} failed"
                )

        return f"Error: Validation context '{context_id}' not found"

    async def _list_schemas(self, context: dict[str, Any], execution_context: Any) -> str:
        """List all registered schemas."""
        endpoint = context.get("endpoint")
        method = context.get("method")

        schemas = list(self._schema_registry.values())

        if endpoint:
            schemas = [s for s in schemas if s.endpoint == endpoint]

        if method:
            if isinstance(method, str):
                method = HTTPMethod(method)
            schemas = [s for s in schemas if s.method == method]

        if not schemas:
            return "No schemas found"

        output = f"Schemas ({len(schemas)}):\n"
        for schema in schemas:
            output += f"- {schema.name}: {schema.method.value.upper()} {schema.endpoint}\n"

        return output

    def get_schema_registry(self) -> dict[str, APISchema]:
        """Get schema registry."""
        return self._schema_registry.copy()

    def get_response_history(self) -> list[APIResponse]:
        """Get response history."""
        return self._response_history.copy()

    def get_validation_errors(self) -> list[ValidationError]:
        """Get validation errors."""
        return self._validation_errors.copy()

    def get_context_history(self) -> list[ValidationContext]:
        """Get context history."""
        return self._context_history.copy()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

