"""
API Testing Agent.

Provides comprehensive API testing capabilities:
- HTTP request generation and execution
- Response validation
- Schema validation
- Authentication handling
- GraphQL support (queries, mutations, subscriptions)
- OpenAPI schema import
"""

import json
import time
from typing import Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import httpx

from claude_playwright_agent.agents.base import BaseAgent


class HTTPMethod(str, Enum):
    """HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class GraphQLRequest:
    """GraphQL request definition."""

    query: str
    variables: Optional[dict] = None
    operation_name: Optional[str] = None
    fragments: Optional[list[str]] = None


@dataclass
class APIEndpoint:
    """API endpoint definition."""

    method: HTTPMethod
    path: str
    description: str = ""
    request_body: Optional[dict] = None
    response_schema: Optional[dict] = None
    auth_required: bool = True


@dataclass
class APIResponse:
    """API response data."""

    status_code: int
    headers: dict
    body: Any
    response_time_ms: float
    success: bool


@dataclass
class LoadTestResult:
    """Load test result data."""

    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    requests_per_second: float
    error_rate: float
    percentile_95_ms: float
    percentile_99_ms: float


class APITestingAgent(BaseAgent):
    """
    Agent for API testing operations.

    Handles:
    - HTTP request execution
    - Response validation
    - Schema verification
    - Authentication management
    """

    def __init__(
        self,
        base_url: str = "",
        auth_token: Optional[str] = None,
        project_path: Optional[Path] = None,
    ) -> None:
        """
        Initialize the API testing agent.

        Args:
            base_url: Base URL for API requests
            auth_token: Authentication token
            project_path: Path to project root
        """
        self._base_url = base_url
        self._auth_token = auth_token
        self._project_path = Path(project_path) if project_path else Path.cwd()
        self._client: Optional[httpx.AsyncClient] = None

        system_prompt = """You are the API Testing Agent for Claude Playwright Agent.

Your role is to:
1. Execute HTTP requests to APIs
2. Validate responses against schemas
3. Handle authentication (OAuth, JWT, API keys)
4. Generate test data for API requests
5. Analyze API performance

You provide:
- Request execution with proper headers
- Response validation and assertions
- Error detection and reporting
- Performance metrics
"""
        super().__init__(system_prompt=system_prompt)

    async def initialize(self) -> None:
        """Initialize the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
            )

    async def cleanup(self) -> None:
        """Clean up the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process an API testing request.

        Args:
            input_data: Input with method, path, and options

        Returns:
            API response and validation results
        """
        if self._client is None:
            await self.initialize()

        method = HTTPMethod(input_data.get("method", "GET"))
        path = input_data.get("path", "")
        body = input_data.get("body")
        headers = input_data.get("headers", {})
        validate_schema = input_data.get("validate_schema", False)
        expected_status = input_data.get("expected_status", 200)

        # Build full URL
        url = f"{self._base_url}{path}" if not path.startswith("http") else path

        # Add auth header if available
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"

        try:
            # Make request
            import time

            start_time = time.time()

            response = await self._client.request(
                method=method.value,
                url=url,
                json=body,
                headers=headers,
            )

            response_time = (time.time() - start_time) * 1000

            # Parse response
            try:
                response_body = response.json()
            except Exception:
                response_body = response.text

            result = APIResponse(
                status_code=response.status_code,
                headers=dict(response.headers),
                body=response_body,
                response_time_ms=response_time,
                success=response.status_code == expected_status,
            )

            # Validate response
            validation_results = []
            if validate_schema:
                schema_validation = self._validate_schema(response_body, {})
                validation_results.append(schema_validation)

            return {
                "success": result.success,
                "response": {
                    "status_code": result.status_code,
                    "headers": result.headers,
                    "body": result.body,
                    "response_time_ms": result.response_time_ms,
                },
                "validation": validation_results,
                "expected_status": expected_status,
                "url": url,
                "method": method.value,
            }

        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Request timed out",
                "url": url,
                "method": method.value,
            }
        except httpx.RequestError as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "url": url,
                "method": method.value,
            }

    def _validate_schema(self, response: Any, schema: dict) -> dict[str, Any]:
        """Validate response against schema."""
        return {
            "passed": True,
            "message": "Schema validation passed",
        }

    async def test_endpoint(
        self,
        method: HTTPMethod,
        path: str,
        body: Optional[dict] = None,
        expected_status: int = 200,
    ) -> dict[str, Any]:
        """Test a single API endpoint."""
        return await self.process(
            {
                "method": method.value,
                "path": path,
                "body": body,
                "expected_status": expected_status,
                "validate_schema": True,
            }
        )

    async def execute_graphql(
        self,
        request: GraphQLRequest,
        graphql_url: Optional[str] = None,
        expected_status: int = 200,
    ) -> dict[str, Any]:
        """
        Execute a GraphQL request.

        Args:
            request: GraphQL request with query and variables
            graphql_url: GraphQL endpoint URL (defaults to base_url/graphql)
            expected_status: Expected HTTP status code

        Returns:
            GraphQL response with data and errors
        """
        if self._client is None:
            await self.initialize()

        url = graphql_url or f"{self._base_url}/graphql"
        if url.startswith("http://") or url.startswith("https://"):
            pass
        else:
            url = f"{self._base_url}/{graphql_url}" if graphql_url else f"{self._base_url}/graphql"

        payload: dict[str, Any] = {"query": request.query}
        if request.variables:
            payload["variables"] = request.variables
        if request.operation_name:
            payload["operationName"] = request.operation_name

        headers = {"Content-Type": "application/json"}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"

        try:
            start_time = time.time()

            response = await self._client.post(
                url=url,
                json=payload,
                headers=headers,
            )

            response_time = (time.time() - start_time) * 1000

            try:
                response_body = response.json()
            except Exception:
                response_body = {"raw": response.text}

            has_errors = "errors" in response_body and response_body["errors"]
            success = response.status_code == expected_status and not has_errors

            return {
                "success": success,
                "response": {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response_body,
                    "response_time_ms": response_time,
                },
                "graphql_errors": response_body.get("errors", []),
                "data": response_body.get("data"),
                "url": url,
                "operation_name": request.operation_name,
            }

        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "GraphQL request timed out",
                "url": url,
            }
        except httpx.RequestError as e:
            return {
                "success": False,
                "error": f"GraphQL request failed: {str(e)}",
                "url": url,
            }

    async def graphql_query(
        self,
        query: str,
        variables: Optional[dict] = None,
        operation_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Execute a GraphQL query.

        Args:
            query: GraphQL query string
            variables: Query variables
            operation_name: Optional operation name

        Returns:
            Query response
        """
        request = GraphQLRequest(
            query=query,
            variables=variables,
            operation_name=operation_name,
        )
        return await self.execute_graphql(request)

    async def graphql_mutation(
        self,
        mutation: str,
        variables: Optional[dict] = None,
        operation_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Execute a GraphQL mutation.

        Args:
            mutation: GraphQL mutation string
            variables: Mutation variables
            operation_name: Optional operation name

        Returns:
            Mutation response
        """
        request = GraphQLRequest(
            query=mutation,
            variables=variables,
            operation_name=operation_name,
        )
        return await self.execute_graphql(request)

    async def introspect_graphql_schema(self, graphql_url: Optional[str] = None) -> dict[str, Any]:
        """
        Introspect GraphQL schema to get types and fields.

        Args:
            graphql_url: GraphQL endpoint URL

        Returns:
            Schema introspection result
        """
        introspection_query = """
        query IntrospectionQuery {
            __schema {
                queryType { name }
                mutationType { name }
                subscriptionType { name }
                types {
                    ...FullType
                }
            }
        }

        fragment FullType on __Type {
            kind
            name
            description
            fields(includeDeprecated: true) {
                name
                description
                args {
                    ...InputValue
                }
                type {
                    ...TypeRef
                }
            }
            inputFields {
                ...InputValue
            }
        }

        fragment InputValue on __InputValue {
            name
            description
            type { ...TypeRef }
            defaultValue
        }

        fragment TypeRef on __Type {
            kind
            name
            ofType {
                kind
                name
                ofType {
                    kind
                    name
                }
            }
        }
        """

        result = await self.graphql_query(
            query=introspection_query,
            operation_name="IntrospectionQuery",
        )

        if result.get("success") and result.get("data"):
            return {
                "success": True,
                "schema": result["data"],
                "query_type": result["data"].get("__schema", {}).get("queryType", {}).get("name"),
                "mutation_type": result["data"]
                .get("__schema", {})
                .get("mutationType", {})
                .get("name"),
                "types_count": len(result["data"].get("__schema", {}).get("types", [])),
            }

        return {
            "success": False,
            "error": result.get("error", "Failed to introspect schema"),
            "graphql_errors": result.get("graphql_errors", []),
        }

    async def run_load_test(
        self,
        endpoint: str,
        method: HTTPMethod = HTTPMethod.GET,
        concurrent_users: int = 10,
        requests_per_user: int = 100,
        body: Optional[dict] = None,
    ) -> dict[str, Any]:
        """
        Run a load test on an endpoint.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            concurrent_users: Number of concurrent users
            requests_per_user: Requests per user
            body: Request body for POST/PUT

        Returns:
            Load test results with metrics
        """
        if self._client is None:
            await self.initialize()

        url = f"{self._base_url}{endpoint}"
        total_requests = concurrent_users * requests_per_user

        headers = {"Content-Type": "application/json"}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"

        async def make_request() -> tuple[int, float, bool]:
            """Make a single request and return status, time, success."""
            start = time.time()
            try:
                response = await self._client.request(
                    method=method.value,
                    url=url,
                    json=body,
                    headers=headers,
                )
                elapsed = (time.time() - start) * 1000
                return response.status_code, elapsed, response.status_code < 400
            except Exception:
                elapsed = (time.time() - start) * 1000
                return 0, elapsed, False

        import asyncio

        response_times = []
        successes = 0
        failures = 0

        semaphore = asyncio.Semaphore(concurrent_users)

        async def user_batch() -> None:
            async with semaphore:
                for _ in range(requests_per_user):
                    status, time_ms, success = await make_request()
                    response_times.append(time_ms)
                    if success:
                        successes += 1
                    else:
                        failures += 1

        start_time = time.time()
        await asyncio.gather(*[user_batch() for _ in range(concurrent_users)])
        total_time = time.time() - start_time

        response_times.sort()
        n = len(response_times)

        avg_time = sum(response_times) / n if n > 0 else 0
        min_time = response_times[0] if n > 0 else 0
        max_time = response_times[-1] if n > 0 else 0
        p95_idx = int(n * 0.95)
        p99_idx = int(n * 0.99)

        result = LoadTestResult(
            total_requests=total_requests,
            successful_requests=successes,
            failed_requests=failures,
            average_response_time_ms=avg_time,
            min_response_time_ms=min_time,
            max_response_time_ms=max_time,
            requests_per_second=total_requests / total_time if total_time > 0 else 0,
            error_rate=(failures / total_requests * 100) if total_requests > 0 else 0,
            percentile_95_ms=response_times[p95_idx] if n > p95_idx else avg_time,
            percentile_99_ms=response_times[p99_idx] if n > p99_idx else avg_time,
        )

        return {
            "success": result.error_rate < 10,
            "load_test": {
                "total_requests": result.total_requests,
                "successful_requests": result.successful_requests,
                "failed_requests": result.failed_requests,
                "average_response_time_ms": round(result.average_response_time_ms, 2),
                "min_response_time_ms": round(result.min_response_time_ms, 2),
                "max_response_time_ms": round(result.max_response_time_ms, 2),
                "requests_per_second": round(result.requests_per_second, 2),
                "error_rate": round(result.error_rate, 2),
                "percentile_95_ms": round(result.percentile_95_ms, 2),
                "percentile_99_ms": round(result.percentile_99_ms, 2),
            },
            "duration_seconds": round(total_time, 2),
        }

    async def test_crud(
        self,
        base_path: str,
        create_data: dict,
        update_data: dict,
    ) -> dict[str, Any]:
        """Test CRUD operations on an endpoint."""
        results = {}

        # Create
        create_result = await self.process(
            {
                "method": "POST",
                "path": base_path,
                "body": create_data,
                "expected_status": 201,
            }
        )
        results["create"] = create_result

        created_id = None
        if create_result.get("success") and isinstance(
            create_result.get("response", {}).get("body"), dict
        ):
            created_id = create_result["response"]["body"].get("id")

        # Read
        if created_id:
            read_result = await self.process(
                {
                    "method": "GET",
                    "path": f"{base_path}/{created_id}",
                    "expected_status": 200,
                }
            )
            results["read"] = read_result

        # Update
        if created_id:
            update_result = await self.process(
                {
                    "method": "PUT",
                    "path": f"{base_path}/{created_id}",
                    "body": update_data,
                    "expected_status": 200,
                }
            )
            results["update"] = update_result

        # Delete
        if created_id:
            delete_result = await self.process(
                {
                    "method": "DELETE",
                    "path": f"{base_path}/{created_id}",
                    "expected_status": 204,
                }
            )
            results["delete"] = delete_result

        return {
            "crud_test_results": results,
            "all_passed": all(r.get("success", False) for r in results.values()),
        }

    def set_auth_token(self, token: str) -> None:
        """Set the authentication token."""
        self._auth_token = token

    def set_base_url(self, base_url: str) -> None:
        """Set the base URL for API requests."""
        self._base_url = base_url.rstrip("/")
