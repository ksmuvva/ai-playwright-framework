import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-proto';
import { Resource } from '@opentelemetry/resources';
import { ATTR_SERVICE_NAME, ATTR_SERVICE_VERSION } from '@opentelemetry/semantic-conventions';
import { Logger } from '../utils/logger';

/**
 * Phoenix Tracing Configuration
 *
 * Integrates Arize Phoenix for LLM observability and tracing.
 * Captures all LLM API calls, responses, token usage, and latency metrics.
 */
export class PhoenixTracer {
  private static sdk: NodeSDK | null = null;
  private static isInitialized = false;

  /**
   * Initialize Phoenix tracing
   * @param phoenixEndpoint - Phoenix collector endpoint (default: http://localhost:6006/v1/traces)
   * @param serviceName - Service name for tracing (default: ai-playwright-framework)
   * @param serviceVersion - Service version (default: 1.0.0)
   */
  static initialize(
    phoenixEndpoint?: string,
    serviceName?: string,
    serviceVersion?: string
  ): void {
    if (this.isInitialized) {
      Logger.warning('Phoenix tracing already initialized');
      return;
    }

    // Check if Phoenix tracing is enabled
    const enableTracing = process.env.ENABLE_PHOENIX_TRACING !== 'false';
    if (!enableTracing) {
      Logger.info('Phoenix tracing is disabled via ENABLE_PHOENIX_TRACING=false');
      return;
    }

    const endpoint = phoenixEndpoint || process.env.PHOENIX_COLLECTOR_ENDPOINT || 'http://localhost:6006/v1/traces';
    const name = serviceName || process.env.SERVICE_NAME || 'ai-playwright-framework';
    const version = serviceVersion || process.env.SERVICE_VERSION || '1.0.0';

    try {
      // Configure OTLP trace exporter
      const traceExporter = new OTLPTraceExporter({
        url: endpoint,
        headers: {},
      });

      // Create resource with service information
      const resource = Resource.default().merge(
        new Resource({
          [ATTR_SERVICE_NAME]: name,
          [ATTR_SERVICE_VERSION]: version,
        })
      );

      // Initialize OpenTelemetry SDK
      this.sdk = new NodeSDK({
        resource,
        traceExporter,
      });

      this.sdk.start();
      this.isInitialized = true;

      Logger.success(`Phoenix tracing initialized successfully`);
      Logger.info(`  Service: ${name} v${version}`);
      Logger.info(`  Endpoint: ${endpoint}`);
      Logger.info(`  View traces at: ${endpoint.replace('/v1/traces', '')}`);
    } catch (error) {
      Logger.error(`Failed to initialize Phoenix tracing: ${error}`);
      throw error;
    }
  }

  /**
   * Shutdown Phoenix tracing gracefully
   */
  static async shutdown(): Promise<void> {
    if (!this.isInitialized || !this.sdk) {
      return;
    }

    try {
      await this.sdk.shutdown();
      this.isInitialized = false;
      Logger.info('Phoenix tracing shutdown successfully');
    } catch (error) {
      Logger.error(`Failed to shutdown Phoenix tracing: ${error}`);
      throw error;
    }
  }

  /**
   * Check if Phoenix tracing is initialized
   */
  static get initialized(): boolean {
    return this.isInitialized;
  }
}

/**
 * Helper function to create span attributes for LLM calls
 */
export function createLLMSpanAttributes(
  provider: string,
  model: string,
  prompt: string,
  maxTokens?: number
): Record<string, any> {
  return {
    'llm.provider': provider,
    'llm.model': model,
    'llm.prompt': prompt,
    'llm.max_tokens': maxTokens,
    'llm.temperature': 1.0,
  };
}

/**
 * Helper function to add response attributes to span
 */
export function addLLMResponseAttributes(
  span: any,
  response: string,
  usage?: {
    promptTokens?: number;
    completionTokens?: number;
    totalTokens?: number;
  }
): void {
  if (span && span.setAttribute) {
    span.setAttribute('llm.response', response);
    if (usage) {
      if (usage.promptTokens) {
        span.setAttribute('llm.usage.prompt_tokens', usage.promptTokens);
      }
      if (usage.completionTokens) {
        span.setAttribute('llm.usage.completion_tokens', usage.completionTokens);
      }
      if (usage.totalTokens) {
        span.setAttribute('llm.usage.total_tokens', usage.totalTokens);
      }
    }
  }
}
