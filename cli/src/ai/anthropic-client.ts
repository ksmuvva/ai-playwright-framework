import Anthropic from '@anthropic-ai/sdk';
import * as dotenv from 'dotenv';
import * as path from 'path';
import { trace, context, SpanStatusCode } from '@opentelemetry/api';
import {
  AIClient,
  BDDOutput,
  LocatorContext,
  LocatorSuggestion,
  DataSchema,
  TestData,
  WaitRecommendations,
  PatternAnalysis,
  PlaywrightAction
} from '../types';
import {
  buildBDDConversionPrompt,
  buildLocatorHealingPrompt,
  buildDataGenerationPrompt,
  PROMPTS
} from './prompts';
import { Logger } from '../utils/logger';
import { createReasoningEngine, ChainOfThought, TreeOfThought } from './reasoning';
import { PhoenixTracer } from '../tracing/phoenix-tracer';

// Load environment variables from CLI root
dotenv.config({ path: path.resolve(__dirname, '../../.env') });

export class AnthropicClient implements AIClient {
  private client: Anthropic;
  private model: string;
  private chainOfThought: ChainOfThought;
  private treeOfThought: TreeOfThought;
  private tracer = trace.getTracer('ai-playwright-framework', '1.0.0');

  // Configuration constants (BUG-005, BUG-006 fixes)
  private readonly DEFAULT_TIMEOUT_MS = 30000; // 30 seconds
  private readonly MAX_RETRIES = 3;
  private readonly BASE_RETRY_DELAY_MS = 1000; // 1 second

  constructor(apiKey?: string, model?: string) {
    // Use provided API key or fallback to environment variable
    const key = apiKey || process.env.ANTHROPIC_API_KEY;
    if (!key) {
      throw new Error('Anthropic API key not provided. Please set ANTHROPIC_API_KEY in .env file or pass it to the constructor.');
    }

    // Validate API key format
    this.validateApiKey(key);

    // Use provided model or fallback to environment variable or default
    this.model = model || process.env.AI_MODEL || 'claude-sonnet-4-5-20250929';

    this.client = new Anthropic({ apiKey: key });

    // Initialize reasoning engines
    const reasoningEngine = createReasoningEngine(this.client, this.model);
    this.chainOfThought = reasoningEngine.chainOfThought;
    this.treeOfThought = reasoningEngine.treeOfThought;

    // Initialize Phoenix tracing if enabled
    if (process.env.ENABLE_PHOENIX_TRACING !== 'false') {
      try {
        PhoenixTracer.initialize();
      } catch (error) {
        Logger.warning(`Failed to initialize Phoenix tracing: ${error}`);
      }
    }

    Logger.info(`AnthropicClient initialized with model: ${this.model}`);
  }

  /**
   * Validate API key format (BUG-002 fix)
   */
  private validateApiKey(key: string): void {
    if (!key.startsWith('sk-ant-')) {
      throw new Error('Invalid Anthropic API key format. Keys should start with "sk-ant-"');
    }
    if (key.length < 20) {
      throw new Error('API key appears to be invalid (too short)');
    }
  }

  /**
   * Safely parse JSON from AI response, handling markdown-wrapped JSON (BUG-001 fix)
   */
  private safeParseJSON(jsonText: string): any {
    try {
      let cleanText = jsonText.trim();

      // Remove markdown code blocks if present
      if (cleanText.startsWith('```')) {
        cleanText = cleanText.replace(/^```(?:json)?\n?/i, '').replace(/\n?```$/, '');
      }

      const result = JSON.parse(cleanText);
      return result;
    } catch (error) {
      Logger.error(`Failed to parse AI response: ${error}`);
      Logger.error(`Raw response: ${jsonText.substring(0, 200)}...`);
      throw new Error('Invalid AI response format. The AI returned malformed JSON.');
    }
  }

  /**
   * Retry a function with exponential backoff (BUG-006 fix)
   */
  private async retryWithBackoff<T>(
    fn: () => Promise<T>,
    context: string,
    maxRetries: number = this.MAX_RETRIES
  ): Promise<T> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        return await fn();
      } catch (error: any) {
        lastError = error;

        // Don't retry on validation errors or client errors
        if (error.status && error.status >= 400 && error.status < 500) {
          throw error;
        }

        if (attempt < maxRetries - 1) {
          const delay = this.BASE_RETRY_DELAY_MS * Math.pow(2, attempt);
          Logger.warn(`${context} failed (attempt ${attempt + 1}/${maxRetries}). Retrying in ${delay}ms...`);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }

    Logger.error(`${context} failed after ${maxRetries} attempts`);
    throw lastError;
  }

  /**
   * Wrapper for LLM API calls with Phoenix tracing
   */
  private async tracedLLMCall<T>(
    spanName: string,
    prompt: string,
    fn: () => Promise<T>,
    metadata?: Record<string, any>
  ): Promise<T> {
    const startTime = Date.now();

    return this.tracer.startActiveSpan(spanName, async (span) => {
      try {
        // Set span attributes
        span.setAttribute('llm.provider', 'anthropic');
        span.setAttribute('llm.model', this.model);
        span.setAttribute('llm.request.prompt', prompt.substring(0, 1000)); // Truncate for storage

        if (metadata) {
          Object.entries(metadata).forEach(([key, value]) => {
            span.setAttribute(`llm.${key}`, value);
          });
        }

        // Execute the LLM call
        const result = await fn();

        // Extract token usage if available
        if (result && typeof result === 'object' && 'usage' in result) {
          const usage = (result as any).usage;
          if (usage) {
            span.setAttribute('llm.usage.prompt_tokens', usage.input_tokens || 0);
            span.setAttribute('llm.usage.completion_tokens', usage.output_tokens || 0);
            span.setAttribute('llm.usage.total_tokens', (usage.input_tokens || 0) + (usage.output_tokens || 0));
          }
        }

        // Record latency
        const latency = Date.now() - startTime;
        span.setAttribute('llm.latency_ms', latency);

        // Mark span as successful
        span.setStatus({ code: SpanStatusCode.OK });

        return result;
      } catch (error: any) {
        // Record error in span
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: error.message || 'Unknown error'
        });
        span.recordException(error);
        throw error;
      } finally {
        span.end();
      }
    });
  }

  /**
   * Generate BDD scenario from Playwright recording
   * Uses Chain of Thought reasoning for better scenario understanding
   */
  async generateBDDScenario(
    recording: PlaywrightAction[],
    scenarioName: string,
    useReasoning: boolean = true
  ): Promise<BDDOutput> {
    try {
      if (useReasoning) {
        Logger.info('Using Chain of Thought reasoning for BDD generation...');

        // Use CoT to analyze recording and generate better scenarios
        const analysisPrompt = `Analyze this Playwright recording and create a BDD scenario`;
        const context = `
Scenario Name: ${scenarioName}
Recording Actions: ${JSON.stringify(recording, null, 2)}

Generate a well-structured BDD scenario with:
1. Clear feature description
2. Maintainable step definitions
3. Reusable locators
4. Appropriate test data
5. Suggested helper functions
        `;

        const cotResult = await this.chainOfThought.reason(analysisPrompt, context, {
          maxSteps: 5
        });

        // Now use the reasoning to generate the actual BDD output
        const prompt = buildBDDConversionPrompt(recording, scenarioName, cotResult.reasoning);

        const response = await this.tracedLLMCall(
          'anthropic.generateBDDScenario.withReasoning',
          prompt,
          () => this.retryWithBackoff(
            () => this.client.messages.create({
              model: this.model,
              max_tokens: 4000,
              messages: [
                {
                  role: 'user',
                  content: prompt
                }
              ]
            }, { timeout: this.DEFAULT_TIMEOUT_MS }),
            'BDD scenario generation with reasoning'
          ),
          { max_tokens: 4000, use_reasoning: true }
        ) as Anthropic.Message;

        const content = response.content[0];
        if (content.type !== 'text') {
          throw new Error('Unexpected response type from AI');
        }

        // Parse JSON response
        const result = this.safeParseJSON(content.text);

        return {
          feature: result.feature || '',
          steps: result.steps || '',
          locators: result.locators || {},
          testData: result.testData || {},
          helpers: result.helpers || []
        };

      } else {
        // Standard generation without reasoning
        const prompt = buildBDDConversionPrompt(recording, scenarioName);

        const response = await this.tracedLLMCall(
          'anthropic.generateBDDScenario',
          prompt,
          () => this.retryWithBackoff(
            () => this.client.messages.create({
              model: this.model,
              max_tokens: 4000,
              messages: [
                {
                  role: 'user',
                  content: prompt
                }
              ]
            }, { timeout: this.DEFAULT_TIMEOUT_MS }),
            'BDD scenario generation'
          ),
          { max_tokens: 4000, use_reasoning: false }
        ) as Anthropic.Message;

        const content = response.content[0];
        if (content.type !== 'text') {
          throw new Error('Unexpected response type from AI');
        }

        // Parse JSON response
        const result = this.safeParseJSON(content.text);

        return {
          feature: result.feature || '',
          steps: result.steps || '',
          locators: result.locators || {},
          testData: result.testData || {},
          helpers: result.helpers || []
        };
      }
    } catch (error) {
      Logger.error(`Failed to generate BDD scenario: ${error}`);
      throw error;
    }
  }

  /**
   * Heal a failed locator by suggesting alternatives
   */
  async healLocator(context: LocatorContext): Promise<LocatorSuggestion> {
    try {
      const prompt = buildLocatorHealingPrompt({
        failedLocator: context.failedLocator,
        elementDescription: context.elementDescription,
        pageHtml: context.pageHtml
      });

      const response = await this.tracedLLMCall(
        'anthropic.healLocator',
        prompt,
        () => this.retryWithBackoff(
          () => this.client.messages.create({
            model: this.model,
            max_tokens: 1000,
            messages: [
              {
                role: 'user',
                content: prompt
              }
            ]
          }, { timeout: this.DEFAULT_TIMEOUT_MS }),
          'Locator healing'
        ),
        { max_tokens: 1000, failed_locator: context.failedLocator }
      ) as Anthropic.Message;

      const content = response.content[0];
      if (content.type !== 'text') {
        throw new Error('Unexpected response type from AI');
      }

      const result = this.safeParseJSON(content.text);

      return {
        locator: result.locator || '',
        confidence: result.confidence || 0,
        alternatives: result.alternatives || []
      };
    } catch (error) {
      Logger.error(`Failed to heal locator: ${error}`);
      throw error;
    }
  }

  /**
   * Generate test data from schema
   */
  async generateTestData(schema: DataSchema): Promise<TestData> {
    try {
      const prompt = buildDataGenerationPrompt(schema);

      const response = await this.tracedLLMCall(
        'anthropic.generateTestData',
        prompt,
        () => this.retryWithBackoff(
          () => this.client.messages.create({
            model: this.model,
            max_tokens: 2000,
            messages: [
              {
                role: 'user',
                content: prompt
              }
            ]
          }, { timeout: this.DEFAULT_TIMEOUT_MS }),
          'Test data generation'
        ),
        { max_tokens: 2000 }
      ) as Anthropic.Message;

      const content = response.content[0];
      if (content.type !== 'text') {
        throw new Error('Unexpected response type from AI');
      }

      return this.safeParseJSON(content.text);
    } catch (error) {
      Logger.error(`Failed to generate test data: ${error}`);
      throw error;
    }
  }

  /**
   * Optimize wait times based on test logs
   */
  async optimizeWaits(testLog: any): Promise<WaitRecommendations> {
    try {
      const prompt = `${PROMPTS.WAIT_OPTIMIZATION}

Test Execution Log:
${JSON.stringify(testLog, null, 2)}

Analyze and suggest wait optimizations.`;

      const response = await this.tracedLLMCall(
        'anthropic.optimizeWaits',
        prompt,
        () => this.retryWithBackoff(
          () => this.client.messages.create({
            model: this.model,
            max_tokens: 2000,
            messages: [
              {
                role: 'user',
                content: prompt
              }
            ]
          }, { timeout: this.DEFAULT_TIMEOUT_MS }),
          'Wait optimization'
        ),
        { max_tokens: 2000 }
      ) as Anthropic.Message;

      const content = response.content[0];
      if (content.type !== 'text') {
        throw new Error('Unexpected response type from AI');
      }

      return this.safeParseJSON(content.text);
    } catch (error) {
      Logger.error(`Failed to optimize waits: ${error}`);
      throw error;
    }
  }

  /**
   * Analyze test patterns to find reusable code
   */
  async analyzePatterns(scenarios: any[]): Promise<PatternAnalysis> {
    try {
      const prompt = `${PROMPTS.PATTERN_ANALYSIS}

Test Scenarios:
${JSON.stringify(scenarios, null, 2)}

Analyze patterns and suggest optimizations.`;

      const response = await this.tracedLLMCall(
        'anthropic.analyzePatterns',
        prompt,
        () => this.retryWithBackoff(
          () => this.client.messages.create({
            model: this.model,
            max_tokens: 3000,
            messages: [
              {
                role: 'user',
                content: prompt
              }
            ]
          }, { timeout: this.DEFAULT_TIMEOUT_MS }),
          'Pattern analysis'
        ),
        { max_tokens: 3000, scenario_count: scenarios.length }
      ) as Anthropic.Message;

      const content = response.content[0];
      if (content.type !== 'text') {
        throw new Error('Unexpected response type from AI');
      }

      return this.safeParseJSON(content.text);
    } catch (error) {
      Logger.error(`Failed to analyze patterns: ${error}`);
      throw error;
    }
  }
}
