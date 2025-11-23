"""
Phoenix Tracing for Python LLM Calls

Integrates Arize Phoenix for LLM observability and tracing.
Captures all LLM API calls, responses, token usage, and latency metrics.
"""

import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
import phoenix as px


class PhoenixTracer:
    """
    Phoenix Tracing Configuration for Python
    """

    _initialized = False
    _phoenix_session = None

    @classmethod
    def initialize(
        cls,
        phoenix_endpoint: str = None,
        service_name: str = None,
        service_version: str = None,
        launch_ui: bool = True
    ):
        """
        Initialize Phoenix tracing

        Args:
            phoenix_endpoint: Phoenix collector endpoint (default: http://localhost:6006/v1/traces)
            service_name: Service name for tracing (default: ai-playwright-framework-python)
            service_version: Service version (default: 1.0.0)
            launch_ui: Whether to launch Phoenix UI (default: True)
        """
        if cls._initialized:
            print("Phoenix tracing already initialized")
            return

        # Check if Phoenix tracing is enabled
        enable_tracing = os.getenv('ENABLE_PHOENIX_TRACING', 'true').lower() != 'false'
        if not enable_tracing:
            print("Phoenix tracing is disabled via ENABLE_PHOENIX_TRACING=false")
            return

        endpoint = phoenix_endpoint or os.getenv('PHOENIX_COLLECTOR_ENDPOINT') or 'http://localhost:6006/v1/traces'
        name = service_name or os.getenv('SERVICE_NAME') or 'ai-playwright-framework-python'
        version = service_version or os.getenv('SERVICE_VERSION') or '1.0.0'

        try:
            # Launch Phoenix UI if requested
            if launch_ui and os.getenv('PHOENIX_LAUNCH_UI', 'true').lower() != 'false':
                cls._phoenix_session = px.launch_app()
                print(f"Phoenix UI launched at: http://localhost:6006")

            # Configure resource with service information
            resource = Resource.create({
                ResourceAttributes.SERVICE_NAME: name,
                ResourceAttributes.SERVICE_VERSION: version,
            })

            # Create tracer provider
            tracer_provider = TracerProvider(resource=resource)

            # Configure OTLP exporter
            otlp_exporter = OTLPSpanExporter(endpoint=endpoint)
            span_processor = BatchSpanProcessor(otlp_exporter)
            tracer_provider.add_span_processor(span_processor)

            # Set global tracer provider
            trace.set_tracer_provider(tracer_provider)

            cls._initialized = True

            print("✓ Phoenix tracing initialized successfully")
            print(f"  Service: {name} v{version}")
            print(f"  Endpoint: {endpoint}")

        except Exception as error:
            print(f"✗ Failed to initialize Phoenix tracing: {error}")
            raise error

    @classmethod
    def shutdown(cls):
        """Shutdown Phoenix tracing gracefully"""
        if not cls._initialized:
            return

        try:
            if cls._phoenix_session:
                # Phoenix session doesn't need explicit shutdown
                pass

            cls._initialized = False
            print("Phoenix tracing shutdown successfully")
        except Exception as error:
            print(f"Failed to shutdown Phoenix tracing: {error}")
            raise error

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if Phoenix tracing is initialized"""
        return cls._initialized


def get_tracer(name: str = "ai-playwright-framework", version: str = "1.0.0"):
    """
    Get a tracer instance

    Args:
        name: Tracer name
        version: Tracer version

    Returns:
        OpenTelemetry Tracer
    """
    return trace.get_tracer(name, version)


def create_llm_span_attributes(
    provider: str,
    model: str,
    prompt: str,
    max_tokens: int = None,
    temperature: float = 1.0
) -> dict:
    """
    Create span attributes for LLM calls

    Args:
        provider: LLM provider (e.g., 'anthropic', 'openai')
        model: Model name
        prompt: Input prompt
        max_tokens: Maximum tokens
        temperature: Temperature setting

    Returns:
        Dictionary of span attributes
    """
    attributes = {
        'llm.provider': provider,
        'llm.model': model,
        'llm.request.prompt': prompt[:1000],  # Truncate for storage
        'llm.temperature': temperature,
    }

    if max_tokens:
        attributes['llm.max_tokens'] = max_tokens

    return attributes


def add_llm_response_attributes(
    span,
    response: str,
    input_tokens: int = None,
    output_tokens: int = None
):
    """
    Add response attributes to span

    Args:
        span: OpenTelemetry span
        response: LLM response text
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
    """
    if span:
        span.set_attribute('llm.response', response[:1000])  # Truncate for storage

        if input_tokens:
            span.set_attribute('llm.usage.prompt_tokens', input_tokens)

        if output_tokens:
            span.set_attribute('llm.usage.completion_tokens', output_tokens)

        if input_tokens and output_tokens:
            span.set_attribute('llm.usage.total_tokens', input_tokens + output_tokens)
