"""
Phoenix Tracing for Python LLM Calls

Integrates Arize Phoenix for LLM observability and tracing.
Captures all LLM API calls, responses, token usage, and latency metrics.
"""

import os
import sys
import atexit
import platform
from pathlib import Path
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
import phoenix as px

# Import structured logger
try:
    from helpers.logger import get_logger
    logger = get_logger("phoenix_tracer")
except ImportError:
    # Fallback if logger not available
    import logging
    logger = logging.getLogger("phoenix_tracer")
    logger.setLevel(logging.INFO)


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
            service_version: Service version (default: 2.0.0)
            launch_ui: Whether to launch Phoenix UI (default: True)
        """
        logger.info(
            "phoenix_initialization_started",
            message="Starting Phoenix tracing initialization..."
        )

        if cls._initialized:
            logger.warning(
                "phoenix_already_initialized",
                message="Phoenix tracing is already initialized, skipping..."
            )
            return

        # Check if Phoenix tracing is enabled
        enable_tracing = os.getenv('ENABLE_PHOENIX_TRACING', 'true').lower() != 'false'
        if not enable_tracing:
            logger.warning(
                "phoenix_disabled",
                message="Phoenix tracing is disabled via ENABLE_PHOENIX_TRACING=false",
                reason="Environment variable ENABLE_PHOENIX_TRACING is set to false"
            )
            return

        endpoint = phoenix_endpoint or os.getenv('PHOENIX_COLLECTOR_ENDPOINT') or 'http://localhost:6006/v1/traces'
        name = service_name or os.getenv('SERVICE_NAME') or 'ai-playwright-framework-python'
        version = service_version or os.getenv('SERVICE_VERSION') or '2.0.0'

        logger.debug(
            "phoenix_configuration",
            service_name=name,
            service_version=version,
            endpoint=endpoint,
            launch_ui=launch_ui,
        )

        try:
            # FIX: Issue #6 - Configure Phoenix to use persistent directory (not temp) to avoid Windows cleanup errors
            # Set up persistent Phoenix working directory
            is_windows = platform.system() == 'Windows'
            if is_windows:
                # On Windows, use user's home directory to avoid temp file cleanup issues
                phoenix_dir = Path.home() / '.phoenix'
            else:
                # On Unix, use standard location
                phoenix_dir = Path.home() / '.phoenix'

            phoenix_dir.mkdir(parents=True, exist_ok=True)

            logger.debug(
                "phoenix_working_directory",
                path=str(phoenix_dir),
                message=f"📋 Ensuring phoenix working directory: {phoenix_dir}"
            )
            print(f"📋 Ensuring phoenix working directory: {phoenix_dir}")

            # Set Phoenix working directory environment variable
            os.environ['PHOENIX_WORKING_DIR'] = str(phoenix_dir)

            # Launch Phoenix UI if requested
            should_launch_ui = launch_ui and os.getenv('PHOENIX_LAUNCH_UI', 'true').lower() != 'false'

            if should_launch_ui:
                logger.info(
                    "phoenix_ui_launching",
                    message="Launching Phoenix UI server..."
                )
                # FIX: Phoenix API changed - launch_app() no longer accepts working_dir parameter
                # The PHOENIX_WORKING_DIR environment variable (set above) is used instead
                cls._phoenix_session = px.launch_app()
                logger.info(
                    "phoenix_ui_launched",
                    ui_url="http://localhost:6006",
                    message="🎯 Phoenix UI is now running - open http://localhost:6006 in your browser"
                )
            else:
                logger.info(
                    "phoenix_ui_skipped",
                    message="Phoenix UI launch skipped (PHOENIX_LAUNCH_UI=false)"
                )

            # Configure resource with service information
            logger.debug(
                "phoenix_resource_creation",
                message="Creating OpenTelemetry resource..."
            )

            resource = Resource.create({
                ResourceAttributes.SERVICE_NAME: name,
                ResourceAttributes.SERVICE_VERSION: version,
            })

            # Create tracer provider
            logger.debug(
                "phoenix_tracer_provider",
                message="Creating tracer provider..."
            )
            tracer_provider = TracerProvider(resource=resource)

            # Configure OTLP exporter
            logger.debug(
                "phoenix_otlp_exporter",
                endpoint=endpoint,
                message="Configuring OTLP exporter..."
            )
            otlp_exporter = OTLPSpanExporter(endpoint=endpoint)
            span_processor = BatchSpanProcessor(otlp_exporter)
            tracer_provider.add_span_processor(span_processor)

            # Set global tracer provider
            trace.set_tracer_provider(tracer_provider)

            cls._initialized = True

            logger.info(
                "phoenix_initialized",
                service_name=name,
                service_version=version,
                endpoint=endpoint,
                ui_launched=should_launch_ui,
                message="✅ Phoenix tracing initialized successfully - All LLM calls will now be traced",
            )

            # Log what Phoenix will capture
            logger.info(
                "phoenix_capabilities",
                capabilities=[
                    "LLM request prompts and responses",
                    "Token usage (input/output/total)",
                    "Latency metrics",
                    "Model and provider information",
                    "Error tracking",
                    "Chain of thought reasoning traces"
                ],
                message="Phoenix will capture the following metrics"
            )

        except Exception as error:
            logger.error(
                "phoenix_initialization_failed",
                error_type=type(error).__name__,
                error_message=str(error),
                endpoint=endpoint,
                message="❌ Failed to initialize Phoenix tracing",
                exc_info=True
            )
            raise error

    @classmethod
    def shutdown(cls):
        """
        Shutdown Phoenix tracing gracefully
        FIX: Issue #6 - Handle Windows file locking errors gracefully
        """
        if not cls._initialized:
            logger.debug(
                "phoenix_shutdown_skipped",
                message="Phoenix tracing not initialized, skipping shutdown"
            )
            return

        logger.info(
            "phoenix_shutdown_started",
            message="Shutting down Phoenix tracing..."
        )

        try:
            if cls._phoenix_session:
                # Phoenix session doesn't need explicit shutdown
                # It will clean up automatically when the process ends
                logger.debug(
                    "phoenix_session_cleanup",
                    message="Phoenix session will cleanup automatically"
                )

                # FIX: On Windows, force flush any pending writes to avoid file locking
                is_windows = platform.system() == 'Windows'
                if is_windows:
                    try:
                        # Give Phoenix time to close database connections gracefully
                        import time
                        time.sleep(0.1)
                    except Exception:
                        pass  # Ignore timing errors

            cls._initialized = False
            logger.info(
                "phoenix_shutdown_complete",
                message="✅ Phoenix tracing shutdown successfully"
            )
        except Exception as error:
            # FIX: On Windows, PermissionError during cleanup is expected and can be safely ignored
            is_windows = platform.system() == 'Windows'
            if is_windows and isinstance(error, PermissionError):
                logger.warning(
                    "phoenix_shutdown_permission_warning",
                    error_message=str(error),
                    message="⚠️  Phoenix cleanup warning on Windows (can be safely ignored)"
                )
                cls._initialized = False
                # Don't raise the error on Windows - it's a known issue with temp file cleanup
            else:
                logger.error(
                    "phoenix_shutdown_failed",
                    error_type=type(error).__name__,
                    error_message=str(error),
                    message="❌ Failed to shutdown Phoenix tracing",
                    exc_info=True
                )
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
