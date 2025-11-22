import Anthropic from '@anthropic-ai/sdk';
import * as dotenv from 'dotenv';
import * as path from 'path';
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

// Load environment variables from CLI root
dotenv.config({ path: path.resolve(__dirname, '../../.env') });

export class AnthropicClient implements AIClient {
  private client: Anthropic;
  private model: string;
  private chainOfThought: ChainOfThought;
  private treeOfThought: TreeOfThought;
  private readonly DEFAULT_TIMEOUT = 60000; // 60 seconds
  private readonly DEFAULT_MAX_RETRIES = 3;
  private readonly DEFAULT_BASE_DELAY = 1000; // 1 second

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

    // Initialize client with timeout configuration
    this.client = new Anthropic({
      apiKey: key,
      timeout: this.DEFAULT_TIMEOUT,
      maxRetries: 0 // We'll handle retries ourselves for better control
    });

    // Initialize reasoning engines
    const reasoningEngine = createReasoningEngine(this.client, this.model);
    this.chainOfThought = reasoningEngine.chainOfThought;
    this.treeOfThought = reasoningEngine.treeOfThought;

    Logger.info(`AnthropicClient initialized with model: ${this.model}`);
  }

  /**
   * Validate Anthropic API key format
   * @private
   */
  private validateApiKey(key: string): void {
    // Check key format
    if (!key.startsWith('sk-ant-')) {
      throw new Error(
        'Invalid Anthropic API key format. Keys should start with "sk-ant-". ' +
        'Get your API key at: https://console.anthropic.com/'
      );
    }

    // Check key length (Anthropic keys are typically 100+ characters)
    if (key.length < 50) {
      throw new Error(
        'API key appears to be invalid (too short). ' +
        'Please verify your key at: https://console.anthropic.com/'
      );
    }

    // Check for common mistakes
    if (key.includes(' ') || key.includes('\n') || key.includes('\t')) {
      throw new Error(
        'API key contains whitespace characters. ' +
        'Please remove any spaces, newlines, or tabs from your API key.'
      );
    }

    // Check if it's a placeholder
    if (key.includes('your-key') || key.includes('xxx') || key === 'sk-ant-') {
      throw new Error(
        'API key appears to be a placeholder. ' +
        'Please replace it with your actual API key from: https://console.anthropic.com/'
      );
    }
  }

  /**
   * Safely parse JSON from AI response, handling markdown code blocks and errors
   * @private
   */
  private safeJsonParse<T = any>(text: string, context: string = 'AI response'): T {
    try {
      let jsonText = text.trim();

      // Remove markdown code blocks if present
      if (jsonText.startsWith('```')) {
        jsonText = jsonText.replace(/^```(?:json)?\n?/i, '').replace(/\n?```$/,'');
        jsonText = jsonText.trim();
      }

      // Additional cleanup for nested markdown blocks
      if (jsonText.includes('```json')) {
        jsonText = jsonText.replace(/```json\s*/g, '').replace(/```\s*/g, '');
        jsonText = jsonText.trim();
      }

      const parsed = JSON.parse(jsonText);
      return parsed as T;
    } catch (error) {
      Logger.error(`Failed to parse ${context}: ${error}`);
      Logger.error(`Raw response: ${text.substring(0, 200)}...`);
      throw new Error(`Invalid JSON in ${context}. The AI response could not be parsed.`);
    }
  }

  /**
   * Retry a function with exponential backoff
   * Handles rate limiting, timeouts, and transient network errors
   * @private
   */
  private async retryWithBackoff<T>(
    fn: () => Promise<T>,
    operation: string,
    maxRetries: number = this.DEFAULT_MAX_RETRIES,
    baseDelay: number = this.DEFAULT_BASE_DELAY
  ): Promise<T> {
    let lastError: any;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await fn();
      } catch (error: any) {
        lastError = error;

        // Don't retry on certain errors
        if (this.isNonRetryableError(error)) {
          Logger.error(`Non-retryable error in ${operation}: ${error.message}`);
          throw error;
        }

        // Check if we've exhausted retries
        if (attempt === maxRetries) {
          Logger.error(`Max retries (${maxRetries}) exceeded for ${operation}`);
          throw error;
        }

        // Calculate delay with exponential backoff and jitter
        const delay = baseDelay * Math.pow(2, attempt);
        const jitter = Math.random() * 0.3 * delay; // Add up to 30% jitter
        const totalDelay = delay + jitter;

        // Log retry attempt
        Logger.warning(
          `${operation} failed (attempt ${attempt + 1}/${maxRetries + 1}): ${error.message}. ` +
          `Retrying in ${Math.round(totalDelay)}ms...`
        );

        // Handle rate limiting with specific delay
        if (this.isRateLimitError(error)) {
          const rateLimitDelay = this.getRateLimitDelay(error) || totalDelay;
          Logger.warning(`Rate limit hit. Waiting ${Math.round(rateLimitDelay)}ms...`);
          await this.sleep(rateLimitDelay);
        } else {
          await this.sleep(totalDelay);
        }
      }
    }

    throw lastError;
  }

  /**
   * Check if error is non-retryable (authentication, invalid input, etc.)
   * @private
   */
  private isNonRetryableError(error: any): boolean {
    const errorMessage = error.message?.toLowerCase() || '';
    const errorStatus = error.status || error.statusCode;

    // Don't retry on authentication or authorization errors
    if (errorStatus === 401 || errorStatus === 403) {
      return true;
    }

    // Don't retry on invalid request errors
    if (errorStatus === 400 || errorStatus === 422) {
      return true;
    }

    // Don't retry on API key validation errors
    if (errorMessage.includes('api key') || errorMessage.includes('invalid key')) {
      return true;
    }

    return false;
  }

  /**
   * Check if error is a rate limit error
   * @private
   */
  private isRateLimitError(error: any): boolean {
    const errorStatus = error.status || error.statusCode;
    const errorMessage = error.message?.toLowerCase() || '';

    return (
      errorStatus === 429 ||
      errorMessage.includes('rate limit') ||
      errorMessage.includes('too many requests')
    );
  }

  /**
   * Extract retry delay from rate limit error headers
   * @private
   */
  private getRateLimitDelay(error: any): number | null {
    // Check for Retry-After header
    const retryAfter = error.headers?.['retry-after'];
    if (retryAfter) {
      const delay = parseInt(retryAfter, 10);
      if (!isNaN(delay)) {
        return delay * 1000; // Convert seconds to milliseconds
      }
    }
    return null;
  }

  /**
   * Sleep for specified milliseconds
   * @private
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
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

        const response = await this.retryWithBackoff(
          () => this.client.messages.create({
            model: this.model,
            max_tokens: 4000,
            messages: [
              {
                role: 'user',
                content: prompt
              }
            ]
          }),
          'BDD scenario generation with reasoning'
        );

        const content = response.content[0];
        if (content.type !== 'text') {
          throw new Error('Unexpected response type from AI');
        }

        // Parse JSON response with error handling
        const result = this.safeJsonParse<any>(content.text, 'BDD scenario generation');

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

        const response = await this.retryWithBackoff(
          () => this.client.messages.create({
            model: this.model,
            max_tokens: 4000,
            messages: [
              {
                role: 'user',
                content: prompt
              }
            ]
          }),
          'BDD scenario generation'
        );

        const content = response.content[0];
        if (content.type !== 'text') {
          throw new Error('Unexpected response type from AI');
        }

        // Parse JSON response with error handling
        const result = this.safeJsonParse<any>(content.text, 'BDD scenario generation');

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

      const response = await this.retryWithBackoff(
        () => this.client.messages.create({
          model: this.model,
          max_tokens: 1000,
          messages: [
            {
              role: 'user',
              content: prompt
            }
          ]
        }),
        'Locator healing'
      );

      const content = response.content[0];
      if (content.type !== 'text') {
        throw new Error('Unexpected response type from AI');
      }

      const result = this.safeJsonParse<any>(content.text, 'locator healing');

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

      const response = await this.retryWithBackoff(
        () => this.client.messages.create({
          model: this.model,
          max_tokens: 2000,
          messages: [
            {
              role: 'user',
              content: prompt
            }
          ]
        }),
        'Test data generation'
      );

      const content = response.content[0];
      if (content.type !== 'text') {
        throw new Error('Unexpected response type from AI');
      }

      return this.safeJsonParse<any>(content.text, 'AI response');
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

      const response = await this.retryWithBackoff(
        () => this.client.messages.create({
          model: this.model,
          max_tokens: 2000,
          messages: [
            {
              role: 'user',
              content: prompt
            }
          ]
        }),
        'Wait optimization analysis'
      );

      const content = response.content[0];
      if (content.type !== 'text') {
        throw new Error('Unexpected response type from AI');
      }

      return this.safeJsonParse<any>(content.text, 'AI response');
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

      const response = await this.retryWithBackoff(
        () => this.client.messages.create({
          model: this.model,
          max_tokens: 3000,
          messages: [
            {
              role: 'user',
              content: prompt
            }
          ]
        }),
        'Pattern analysis'
      );

      const content = response.content[0];
      if (content.type !== 'text') {
        throw new Error('Unexpected response type from AI');
      }

      return this.safeJsonParse<any>(content.text, 'AI response');
    } catch (error) {
      Logger.error(`Failed to analyze patterns: ${error}`);
      throw error;
    }
  }
}
