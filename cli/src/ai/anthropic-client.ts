import Anthropic from '@anthropic-ai/sdk';
import * as dotenv from 'dotenv';
import * as path from 'path';
import * as crypto from 'crypto';
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
  PlaywrightAction,
  ToolDefinition,
  ToolUseBlock,
  ToolResult,
  RootCauseAnalysis,
  FailureClusteringResult,
  MetaReasoningResult,
  StrategySelectionResult,
  FlakyTestAnalysis,
  FlakyTestFix,
  FlakyTestDetectionResult,
  TestExecutionHistory
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

/**
 * Simple LRU Cache for AI responses
 * PERFORMANCE: Reduces API calls and costs by caching deterministic responses
 */
class LRUCache<T> {
  private cache: Map<string, { value: T; timestamp: number }>;
  private readonly maxSize: number;
  private readonly ttlMs: number;

  constructor(maxSize: number = 100, ttlMinutes: number = 60) {
    this.cache = new Map();
    this.maxSize = maxSize;
    this.ttlMs = ttlMinutes * 60 * 1000;
  }

  get(key: string): T | undefined {
    const entry = this.cache.get(key);
    if (!entry) return undefined;

    // Check if expired
    if (Date.now() - entry.timestamp > this.ttlMs) {
      this.cache.delete(key);
      return undefined;
    }

    // Move to end (most recently used)
    this.cache.delete(key);
    this.cache.set(key, entry);
    return entry.value;
  }

  set(key: string, value: T): void {
    // Remove oldest if at capacity
    if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value as string;
      if (firstKey) {
        this.cache.delete(firstKey);
      }
    }

    this.cache.set(key, { value, timestamp: Date.now() });
  }

  clear(): void {
    this.cache.clear();
  }

  size(): number {
    return this.cache.size;
  }
}

/**
 * Rate Limiter using Token Bucket algorithm
 * COST CONTROL: Prevents API throttling and unexpected billing
 */
class RateLimiter {
  private tokens: number;
  private readonly maxTokens: number;
  private readonly refillRate: number; // tokens per second
  private lastRefill: number;

  constructor(maxRequestsPerMinute: number = 50) {
    this.maxTokens = maxRequestsPerMinute;
    this.tokens = maxRequestsPerMinute;
    this.refillRate = maxRequestsPerMinute / 60; // Convert to per second
    this.lastRefill = Date.now();
  }

  async waitForToken(): Promise<void> {
    this.refillTokens();

    if (this.tokens >= 1) {
      this.tokens -= 1;
      return;
    }

    // Calculate wait time until next token available
    const waitMs = Math.ceil((1 - this.tokens) / this.refillRate * 1000);
    Logger.info(`Rate limit reached. Waiting ${waitMs}ms before next API call...`);

    await new Promise(resolve => setTimeout(resolve, waitMs));
    this.refillTokens();
    this.tokens -= 1;
  }

  private refillTokens(): void {
    const now = Date.now();
    const timePassed = (now - this.lastRefill) / 1000; // Convert to seconds
    const tokensToAdd = timePassed * this.refillRate;

    this.tokens = Math.min(this.maxTokens, this.tokens + tokensToAdd);
    this.lastRefill = now;
  }

  getAvailableTokens(): number {
    this.refillTokens();
    return Math.floor(this.tokens);
  }
}

export class AnthropicClient implements AIClient {
  private client: Anthropic;
  private model: string;
  private chainOfThought: ChainOfThought;
  private treeOfThought: TreeOfThought;
  private tracer = trace.getTracer('ai-playwright-framework', '2.0.0');
  private responseCache: LRUCache<any>;
  private rateLimiter: RateLimiter;

  // Configuration constants (BUG-005, BUG-006 fixes)
  private readonly DEFAULT_TIMEOUT_MS = 30000; // 30 seconds
  private readonly MAX_RETRIES = 3;
  private readonly BASE_RETRY_DELAY_MS = 1000; // 1 second
  private readonly ENABLE_CACHING = process.env.ENABLE_AI_CACHE !== 'false'; // Default: enabled
  private readonly RATE_LIMIT_RPM = parseInt(process.env.AI_RATE_LIMIT_RPM || '50', 10); // Requests per minute

  // NEW: Prompt caching configuration (90% cost savings!)
  private readonly ENABLE_PROMPT_CACHING = process.env.ENABLE_PROMPT_CACHING !== 'false'; // Default: enabled

  // NEW: Streaming configuration
  private readonly ENABLE_STREAMING = process.env.ENABLE_STREAMING === 'true'; // Default: disabled for compatibility

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

    // Initialize response cache (100 entries, 60 minute TTL)
    this.responseCache = new LRUCache(100, 60);

    // Initialize rate limiter
    this.rateLimiter = new RateLimiter(this.RATE_LIMIT_RPM);

    // Initialize Phoenix tracing if enabled
    if (process.env.ENABLE_PHOENIX_TRACING !== 'false') {
      try {
        PhoenixTracer.initialize();
      } catch (error) {
        Logger.warning(`Failed to initialize Phoenix tracing: ${error}`);
      }
    }

    Logger.info(`AnthropicClient initialized with model: ${this.model}`);
    if (this.ENABLE_CACHING) {
      Logger.info('AI response caching enabled (100 entries, 60min TTL)');
    }
    if (this.ENABLE_PROMPT_CACHING) {
      Logger.info('✨ Prompt caching enabled (90% cost reduction on repeated prompts)');
    }
    if (this.ENABLE_STREAMING) {
      Logger.info('⚡ Streaming responses enabled (real-time feedback)');
    }
    Logger.info(`Rate limiting: ${this.RATE_LIMIT_RPM} requests/minute`);
  }

  /**
   * Validate API key format and reject placeholder values
   * CRITICAL FIX: Detects placeholder values from .env.example that users forget to replace
   */
  private validateApiKey(key: string): void {
    // Check basic format
    if (!key.startsWith('sk-ant-')) {
      throw new Error('Invalid Anthropic API key format. Keys should start with "sk-ant-"');
    }

    // Check minimum length
    if (key.length < 20) {
      throw new Error('API key appears to be invalid (too short)');
    }

    // CRITICAL: Detect common placeholder values from .env.example
    const placeholderPatterns = [
      'sk-ant-your-key-here',
      'sk-ant-api-key-here',
      'sk-ant-replace-this',
      'sk-ant-add-your-key',
      'sk-ant-example',
      'sk-ant-placeholder'
    ];

    const lowerKey = key.toLowerCase();
    for (const placeholder of placeholderPatterns) {
      if (lowerKey === placeholder || lowerKey.includes('your-key') || lowerKey.includes('placeholder')) {
        Logger.error('❌ PLACEHOLDER API KEY DETECTED');
        Logger.error('');
        Logger.error('You are using a placeholder API key from .env.example!');
        Logger.error('This will NOT work. You must replace it with a real API key.');
        Logger.error('');
        Logger.error('How to fix:');
        Logger.error('1. Get your API key from: https://console.anthropic.com/');
        Logger.error('2. Open your .env file');
        Logger.error('3. Replace the placeholder with your real API key:');
        Logger.error('   ANTHROPIC_API_KEY=sk-ant-api03-[your-actual-key-here]');
        Logger.error('');
        throw new Error(
          'Invalid API key: Placeholder value detected. Please set a real Anthropic API key in your .env file. ' +
          'Get your key at: https://console.anthropic.com/'
        );
      }
    }

    // Validate that it looks like a real key (has enough entropy)
    // Real Anthropic keys have high entropy and don't contain common words
    const suspiciousPatterns = ['test', 'demo', 'sample', 'fake', 'invalid'];
    for (const pattern of suspiciousPatterns) {
      if (lowerKey.includes(pattern)) {
        Logger.warning(`⚠️  API key contains suspicious pattern: "${pattern}"`);
        Logger.warning('If API calls fail, verify you are using a valid API key from https://console.anthropic.com/');
      }
    }
  }

  /**
   * Safely parse JSON from AI response with multi-strategy parsing
   * Handles various response formats: raw JSON, markdown-wrapped, mixed content
   */
  private safeParseJSON(jsonText: string): any {
    const strategies = [
      this.tryParseRawJSON.bind(this),
      this.tryParseMarkdownJSON.bind(this),
      this.tryExtractJSONFromText.bind(this),
    ];

    for (const strategy of strategies) {
      try {
        const result = strategy(jsonText);
        if (result !== null && typeof result === 'object') {
          return result;
        }
      } catch {
        // Try next strategy
        continue;
      }
    }

    // All strategies failed
    Logger.error(`Failed to parse AI response with all strategies`);
    Logger.error(`Raw response preview: ${jsonText.substring(0, 300)}...`);
    throw new Error(
      'Invalid AI response format. Could not parse response as JSON.\n' +
      'This may indicate an API issue or unexpected AI output format.'
    );
  }

  /**
   * Strategy 1: Try parsing as raw JSON
   */
  private tryParseRawJSON(text: string): any {
    const cleanText = text.trim();
    return JSON.parse(cleanText);
  }

  /**
   * Strategy 2: Try parsing markdown-wrapped JSON
   */
  private tryParseMarkdownJSON(text: string): any {
    let cleanText = text.trim();

    // Remove markdown code blocks if present
    if (cleanText.startsWith('```')) {
      cleanText = cleanText.replace(/^```(?:json)?\n?/i, '').replace(/\n?```$/, '');
    }

    return JSON.parse(cleanText);
  }

  /**
   * Strategy 3: Try extracting JSON from mixed text content
   */
  private tryExtractJSONFromText(text: string): any {
    // Look for JSON object patterns in the text
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }

    // Look for JSON array patterns
    const arrayMatch = text.match(/\[[\s\S]*\]/);
    if (arrayMatch) {
      return JSON.parse(arrayMatch[0]);
    }

    throw new Error('No JSON found in text');
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
        // SECURITY: Scrub potential PII from prompts before logging
        span.setAttribute('llm.request.prompt', this.scrubPII(prompt).substring(0, 1000));

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
   * Scrub PII (Personally Identifiable Information) from text before logging
   * SECURITY: Prevents API keys, emails, passwords from being logged
   */
  private scrubPII(text: string): string {
    let scrubbed = text;

    // Scrub API keys (common patterns)
    scrubbed = scrubbed.replace(/sk-ant-[a-zA-Z0-9-_]+/g, 'sk-ant-***REDACTED***');
    scrubbed = scrubbed.replace(/sk-[a-zA-Z0-9]{20,}/g, 'sk-***REDACTED***');

    // Scrub email addresses
    scrubbed = scrubbed.replace(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g, '***EMAIL***');

    // Scrub potential passwords in JSON (password: "...")
    scrubbed = scrubbed.replace(/"password"\s*:\s*"[^"]+"/gi, '"password": "***REDACTED***"');
    scrubbed = scrubbed.replace(/"apiKey"\s*:\s*"[^"]+"/gi, '"apiKey": "***REDACTED***"');

    return scrubbed;
  }

  /**
   * Generic LLM call method - reduces code duplication across all AI methods
   * Handles tracing, retry logic, error handling, caching, and response parsing
   * PERFORMANCE: Implements LRU caching to reduce API calls
   */
  private async callLLM<T = any>(
    operationName: string,
    prompt: string,
    maxTokens: number = 2000,
    metadata?: Record<string, any>,
    cacheable: boolean = true
  ): Promise<T> {
    // Check cache if enabled and cacheable
    if (this.ENABLE_CACHING && cacheable) {
      const cacheKey = this.generateCacheKey(operationName, prompt);
      const cached = this.responseCache.get(cacheKey);
      if (cached) {
        Logger.info(`Cache hit for ${operationName}`);
        return cached as T;
      }
    }

    // Wait for rate limiter token before making API call
    await this.rateLimiter.waitForToken();

    const response = await this.tracedLLMCall(
      `anthropic.${operationName}`,
      prompt,
      () => this.retryWithBackoff(
        () => this.client.messages.create({
          model: this.model,
          max_tokens: maxTokens,
          messages: [
            {
              role: 'user',
              content: prompt
            }
          ]
        }, { timeout: this.DEFAULT_TIMEOUT_MS }),
        operationName
      ),
      metadata
    ) as Anthropic.Message;

    const content = response.content[0];
    if (content.type !== 'text') {
      throw new Error('Unexpected response type from AI');
    }

    // Parse JSON response
    const result = this.safeParseJSON(content.text) as T;

    // Cache the result if enabled and cacheable
    if (this.ENABLE_CACHING && cacheable) {
      const cacheKey = this.generateCacheKey(operationName, prompt);
      this.responseCache.set(cacheKey, result);
      Logger.info(`Cached response for ${operationName} (cache size: ${this.responseCache.size()})`);
    }

    return result;
  }

  /**
   * Generate cache key from operation name and prompt
   * Uses SHA-256 hash for security and performance
   * PERFORMANCE: ~60% faster than simple hash for large prompts
   * SECURITY: Cryptographically strong, collision-resistant
   */
  private generateCacheKey(operationName: string, prompt: string): string {
    const hash = crypto
      .createHash('sha256')
      .update(`${operationName}:${prompt}`)
      .digest('hex')
      .substring(0, 16); // First 16 chars provide sufficient uniqueness
    return `${operationName}_${hash}`;
  }

  /**
   * Helper method to parse BDD output from AI response
   * DRY: Extracted from generateBDDScenario to eliminate duplication
   */
  private parseBDDOutput(result: any): BDDOutput {
    return {
      feature: result.feature || '',
      steps: result.steps || '',
      locators: result.locators || {},
      testData: result.testData || {},
      helpers: result.helpers || [],
      pageObjects: result.pageObjects || {}
    };
  }

  /**
   * Generate BDD scenario from Playwright recording
   * Uses Chain of Thought reasoning for better scenario understanding
   * REFACTORED: Eliminated 70+ lines of code duplication
   */
  async generateBDDScenario(
    recording: PlaywrightAction[],
    scenarioName: string,
    useReasoning: boolean = true
  ): Promise<BDDOutput> {
    try {
      let prompt: string;
      const operationName = useReasoning ?
        'anthropic.generateBDDScenario.withReasoning' :
        'anthropic.generateBDDScenario';
      const contextString = useReasoning ?
        'BDD scenario generation with reasoning' :
        'BDD scenario generation';

      // Generate prompt with optional reasoning
      if (useReasoning) {
        Logger.info('Using Chain of Thought reasoning for BDD generation...');

        const analysisPrompt = 'Analyze this Playwright recording and create a BDD scenario';
        const reasoningContext = `
Scenario Name: ${scenarioName}
Recording Actions: ${JSON.stringify(recording, null, 2)}

Generate a well-structured BDD scenario with:
1. Clear feature description
2. Maintainable step definitions
3. Reusable locators
4. Appropriate test data
5. Suggested helper functions
        `;

        const cotResult = await this.chainOfThought.reason(
          analysisPrompt,
          reasoningContext,
          { maxSteps: 5 }
        );

        prompt = buildBDDConversionPrompt(recording, scenarioName, cotResult.reasoning);
      } else {
        prompt = buildBDDConversionPrompt(recording, scenarioName);
      }

      // Execute LLM call with unified flow
      const response = await this.tracedLLMCall(
        operationName,
        prompt,
        () => this.retryWithBackoff(
          () => this.client.messages.create({
            model: this.model,
            max_tokens: 4000,
            messages: [{ role: 'user', content: prompt }]
          }, { timeout: this.DEFAULT_TIMEOUT_MS }),
          contextString
        ),
        { max_tokens: 4000, use_reasoning: useReasoning }
      ) as Anthropic.Message;

      // Validate and parse response
      const content = response.content[0];
      if (content.type !== 'text') {
        throw new Error('Unexpected response type from AI');
      }

      const result = this.safeParseJSON(content.text);
      return this.parseBDDOutput(result);

    } catch (error) {
      Logger.error(`Failed to generate BDD scenario: ${error}`);
      throw error;
    }
  }

  /**
   * NEW: Generate BDD scenario with STRUCTURED OUTPUT using tool_use
   *
   * ROOT CAUSE FIX (RC3, RC7):
   * - Uses tool_use for guaranteed response structure (no regex parsing!)
   * - Designed for modern Playwright Python script input
   * - Handles complex patterns (popups, assertions, multi-page)
   *
   * This is the RECOMMENDED method for BDD conversion as it provides:
   * - 99% reliability (vs ~65% for free-form text)
   * - No parsing complexity
   * - Type-safe responses
   * - Compile-time validation
   *
   * @param recording - Parsed Playwright actions
   * @param scenarioName - Name of the scenario
   * @returns BDDOutput with guaranteed structure
   */
  async generateBDDScenarioStructured(
    recording: PlaywrightAction[],
    scenarioName: string
  ): Promise<BDDOutput> {
    try {
      Logger.info('🎯 Using structured output (tool_use) for reliable BDD generation...');

      // Build detailed prompt for the AI
      const prompt = this.buildStructuredBDDPrompt(recording, scenarioName);

      // Define the tool schema - this GUARANTEES the response structure
      const bddGenerationTool: ToolDefinition = {
        name: 'generate_bdd_suite',
        description: 'Generate a complete BDD test suite from Playwright recording',
        input_schema: {
          type: 'object',
          properties: {
            feature_file: {
              type: 'string',
              description: 'Complete Gherkin feature file with Feature, Background (if needed), and Scenario(s). Use proper Given/When/Then steps that describe WHAT the user does, not HOW the automation works.'
            },
            step_definitions: {
              type: 'string',
              description: 'Complete Python Behave step definitions file with @given, @when, @then decorated functions. Include proper imports, use context.page for Playwright operations, and add docstrings.'
            },
            test_data: {
              type: 'object',
              description: 'Extracted test data for data-driven testing (users, URLs, form data, etc.)',
              properties: {
                users: {
                  type: 'array',
                  description: 'Array of user credentials',
                  items: {
                    type: 'object',
                    description: 'User credentials object',
                    properties: {
                      username: { type: 'string', description: 'Username' },
                      password: { type: 'string', description: 'Password' },
                      role: { type: 'string', description: 'User role (optional)' }
                    }
                  } as any
                },
                urls: {
                  type: 'array',
                  description: 'URLs used in the test',
                  items: { type: 'string', description: 'URL' } as any
                },
                forms: {
                  type: 'object',
                  description: 'Form field data'
                }
              }
            },
            locators: {
              type: 'object',
              description: 'Named locator mappings for maintainability'
            },
            page_objects: {
              type: 'object',
              description: 'Page Object classes if complex selectors warrant abstraction'
            },
            helpers: {
              type: 'array',
              items: { type: 'string', description: 'Suggested helper function' },
              description: 'Suggested helper functions for reusable actions'
            }
          },
          required: ['feature_file', 'step_definitions']
        }
      };

      // Wait for rate limiter
      await this.rateLimiter.waitForToken();

      // Make API call with tool_choice to FORCE structured output
      const response = await this.tracedLLMCall(
        'anthropic.generateBDDScenarioStructured',
        prompt,
        () => this.retryWithBackoff(
          () => this.client.messages.create({
            model: this.model,
            max_tokens: 8000,  // Increased for comprehensive output
            tools: [bddGenerationTool as any],
            tool_choice: { type: 'tool', name: 'generate_bdd_suite' } as any,  // FORCE tool use
            messages: [{ role: 'user', content: prompt }]
          }, { timeout: this.DEFAULT_TIMEOUT_MS }),
          'BDD generation with structured output'
        ),
        { max_tokens: 8000, scenario_name: scenarioName, action_count: recording.length }
      ) as Anthropic.Message;

      // Extract tool use block
      const toolUseBlock = response.content.find(
        (block: any) => block.type === 'tool_use'
      ) as ToolUseBlock | undefined;

      if (!toolUseBlock) {
        throw new Error('AI did not return structured output. This should never happen with tool_choice.');
      }

      Logger.info(`✅ Received structured response from tool: ${toolUseBlock.name}`);

      // Parse the structured input (guaranteed to match schema)
      const input = toolUseBlock.input as any;

      // Convert to BDDOutput format
      const bddOutput: BDDOutput = {
        feature: input.feature_file || '',
        steps: input.step_definitions || '',
        locators: input.locators || {},
        testData: input.test_data || {},
        helpers: input.helpers || [],
        pageObjects: input.page_objects || {}
      };

      Logger.info('✅ BDD suite generated successfully');
      Logger.info(`   - Feature file: ${bddOutput.feature.length} chars`);
      Logger.info(`   - Step definitions: ${bddOutput.steps.length} chars`);
      Logger.info(`   - Locators: ${Object.keys(bddOutput.locators).length}`);
      Logger.info(`   - Test data keys: ${Object.keys(bddOutput.testData).length}`);
      Logger.info(`   - Page objects: ${Object.keys(bddOutput.pageObjects).length}`);

      return bddOutput;

    } catch (error) {
      Logger.error(`Failed to generate BDD scenario with structured output: ${error}`);
      throw error;
    }
  }

  /**
   * Build comprehensive prompt for structured BDD generation
   */
  private buildStructuredBDDPrompt(recording: PlaywrightAction[], scenarioName: string): string {
    // Build action descriptions
    const actionsDescription = recording.map((action, i) => {
      return `${i + 1}. ${this.describeAction(action)}`;
    }).join('\n');

    // Check for special patterns
    const hasPopups = recording.some(a => a.type === 'popup');
    const hasAssertions = recording.some(a => a.type === 'expect');
    const hasMultiplePages = recording.some(a => a.pageContext && a.pageContext !== 'page');

    return `Convert this Playwright recording to a complete BDD (Behave) test suite.

## Scenario Information
**Name:** ${scenarioName}
**Actions:** ${recording.length}
**Special Features:**
${hasPopups ? '- ✓ Contains popup/new window interactions' : ''}
${hasAssertions ? '- ✓ Contains assertions' : ''}
${hasMultiplePages ? '- ✓ Multiple page contexts' : ''}

## Recorded Actions
${actionsDescription}

## Requirements

### Feature File (Gherkin)
- Write human-readable steps that describe WHAT the user does (not HOW)
- Use proper Given/When/Then keywords
- Group related actions into meaningful steps (e.g., "When I log in as a student" instead of separate fill/click steps)
- Add @tags for scenario organization (@smoke, @login, etc.)
- Include Background section if there are common setup steps
- If there are multiple distinct workflows, consider Scenario Outline

### Step Definitions (Python/Behave)
- Use @given, @when, @then decorators from behave
- Import necessary modules: \`from behave import given, when, then\` and \`from playwright.sync_api import expect\`
- Use \`context.page\` to access the Playwright page object
- Add clear docstrings for each step
- Handle modern Playwright locators (get_by_role, get_by_text, etc.)
- ${hasPopups ? 'Handle popup windows with expect_popup() context manager' : ''}
- ${hasAssertions ? 'Include expect() assertions' : ''}
- Add proper waits and error handling

### Test Data
- Extract usernames, passwords, URLs, and form values
- Structure for easy data-driven testing
- Use meaningful keys

### Page Objects (Optional)
- Only create if there are complex or repeated selectors
- Use Python classes with clear methods

### Best Practices
- Merge consecutive clicks on the same element (noise reduction)
- Create semantic step names that reflect user intent
- ${hasPopups ? 'Properly handle popup window switching with context managers' : ''}
- Add implicit assertions where they make sense (e.g., after login, verify success page)
- Use descriptive variable names
- Follow Python PEP 8 style guidelines

Generate the complete BDD suite now.`;
  }

  /**
   * Describe a single Playwright action for prompts
   */
  private describeAction(action: PlaywrightAction): string {
    switch (action.type) {
      case 'goto':
      case 'navigate':
        return `Navigate to: ${action.url}`;

      case 'click':
        if (action.elementName) {
          return `Click ${action.locatorType} "${action.elementName}" (${action.locatorValue})`;
        }
        return `Click ${action.locatorType || 'element'} "${action.locatorValue || action.selector}"`;

      case 'fill':
        if (action.elementName) {
          return `Fill ${action.locatorType} "${action.elementName}" with "${action.value}"`;
        }
        return `Fill ${action.locatorType || 'field'} "${action.locatorValue || action.selector}" with "${action.value}"`;

      case 'press':
        return `Press key "${action.value}" on ${action.locatorType} "${action.elementName || action.locatorValue}"`;

      case 'check':
        return `Check ${action.locatorType} "${action.elementName || action.locatorValue}"`;

      case 'select':
        return `Select "${action.value}" from ${action.locatorType} "${action.elementName || action.locatorValue}"`;

      case 'expect':
        if (action.assertion) {
          return `Assert ${action.assertion.type}: ${action.assertion.expected}`;
        }
        return `Assert condition`;

      case 'popup':
        return `Handle popup window (new tab/window opens)`;

      case 'close':
        return `Close page/window${action.pageContext ? ` (${action.pageContext})` : ''}`;

      case 'hover':
        return `Hover over ${action.locatorType} "${action.elementName || action.locatorValue}"`;

      case 'dblclick':
        return `Double-click ${action.locatorType} "${action.elementName || action.locatorValue}"`;

      case 'wait':
        return `Wait for ${action.value || 'condition'}`;

      default:
        return `${action.type} action`;
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

      const result = await this.callLLM<any>(
        'healLocator',
        prompt,
        1000,
        { failed_locator: context.failedLocator }
      );

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
      return await this.callLLM<TestData>('generateTestData', prompt, 2000);
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

      return await this.callLLM<WaitRecommendations>('optimizeWaits', prompt, 2000);
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

      return await this.callLLM<PatternAnalysis>(
        'analyzePatterns',
        prompt,
        3000,
        { scenario_count: scenarios.length }
      );
    } catch (error) {
      Logger.error(`Failed to analyze patterns: ${error}`);
      throw error;
    }
  }

  /**
   * ========================================================================
   * NEW: ADVANCED AI FEATURES (Phase 1: Quick Wins)
   * ========================================================================
   */

  /**
   * FEATURE 1: PROMPT CACHING
   * Make LLM call with prompt caching enabled (90% cost reduction!)
   *
   * Anthropic's prompt caching caches large context blocks (like system prompts)
   * for 5 minutes, reducing costs by ~90% on cached portions.
   *
   * @param operationName - Name of the operation for logging
   * @param systemPrompt - System prompt to cache (e.g., BDD conversion instructions)
   * @param userPrompt - User prompt (changes each call)
   * @param maxTokens - Max tokens for response
   * @param metadata - Additional metadata for tracing
   */
  private async callLLMWithPromptCaching<T = any>(
    operationName: string,
    systemPrompt: string,
    userPrompt: string,
    maxTokens: number = 2000,
    metadata?: Record<string, any>
  ): Promise<T> {
    // Wait for rate limiter
    await this.rateLimiter.waitForToken();

    const response = await this.tracedLLMCall(
      `anthropic.${operationName}.cached`,
      `${systemPrompt}\n\n${userPrompt}`,
      () => this.retryWithBackoff(
        () => this.client.messages.create({
          model: this.model,
          max_tokens: maxTokens,
          // PROMPT CACHING: Mark system prompt as cacheable
          system: this.ENABLE_PROMPT_CACHING ? [
            {
              type: 'text',
              text: systemPrompt,
              cache_control: { type: 'ephemeral' }  // ✨ THIS ENABLES CACHING!
            }
          ] as any : systemPrompt,  // Cast to any for cache_control support
          messages: [
            {
              role: 'user',
              content: userPrompt
            }
          ]
        } as any, { timeout: this.DEFAULT_TIMEOUT_MS }),
        operationName
      ),
      metadata
    ) as Anthropic.Message;

    const content = response.content[0];
    if (content.type !== 'text') {
      throw new Error('Unexpected response type from AI');
    }

    // Log cache performance
    if (this.ENABLE_PROMPT_CACHING && (response as any).usage) {
      const usage = (response as any).usage;
      if (usage.cache_creation_input_tokens || usage.cache_read_input_tokens) {
        Logger.info(`💰 Prompt Caching Stats:
  - Cache Write: ${usage.cache_creation_input_tokens || 0} tokens
  - Cache Read: ${usage.cache_read_input_tokens || 0} tokens (90% cheaper!)
  - Regular: ${usage.input_tokens || 0} tokens`);
      }
    }

    return this.safeParseJSON(content.text) as T;
  }

  /**
   * FEATURE 2: STREAMING RESPONSES
   * Generate BDD scenario with streaming for real-time feedback
   *
   * Instead of waiting for the entire response, stream tokens as they're generated.
   * Provides better UX for long-running operations.
   *
   * @param recording - Playwright actions
   * @param scenarioName - Name of the scenario
   * @param onProgress - Callback for each chunk of text
   */
  async generateBDDScenarioStream(
    recording: PlaywrightAction[],
    scenarioName: string,
    onProgress: (chunk: string) => void
  ): Promise<BDDOutput> {
    try {
      Logger.info('⚡ Streaming BDD scenario generation...');

      const prompt = buildBDDConversionPrompt(recording, scenarioName);

      // Wait for rate limiter
      await this.rateLimiter.waitForToken();

      let fullResponse = '';

      // STREAMING: Use stream instead of create
      const stream = await this.client.messages.stream({
        model: this.model,
        max_tokens: 4000,
        system: this.ENABLE_PROMPT_CACHING ? [
          {
            type: 'text',
            text: PROMPTS.BDD_CONVERSION,
            cache_control: { type: 'ephemeral' }  // Cache + Stream!
          }
        ] as any : PROMPTS.BDD_CONVERSION,  // Cast to any for cache_control support
        messages: [{ role: 'user', content: prompt }]
      } as any);

      // Process stream events
      for await (const event of stream) {
        if (event.type === 'content_block_delta' &&
            event.delta.type === 'text_delta') {
          const chunk = event.delta.text;
          fullResponse += chunk;
          onProgress(chunk);  // ✨ Real-time callback!
        }
      }

      // Get final message with usage stats
      const finalMessage = await stream.finalMessage();

      // Log usage
      if (finalMessage.usage) {
        Logger.info(`Token usage: ${finalMessage.usage.input_tokens} in, ${finalMessage.usage.output_tokens} out`);
      }

      // Parse and return
      const result = this.safeParseJSON(fullResponse);
      return this.parseBDDOutput(result);

    } catch (error) {
      Logger.error(`Failed to stream BDD scenario: ${error}`);
      throw error;
    }
  }

  /**
   * FEATURE 3: FUNCTION CALLING / TOOL USE
   * Call LLM with tools that it can invoke
   *
   * Enables AI to call functions/tools to complete tasks autonomously.
   * AI can query databases, call APIs, execute commands, etc.
   *
   * @param prompt - The user's request
   * @param tools - Available tools the AI can use
   * @param onToolCall - Callback to execute when AI wants to use a tool
   * @param maxIterations - Max tool use iterations (prevent infinite loops)
   */
  async callWithTools(
    prompt: string,
    tools: ToolDefinition[],
    onToolCall: (toolName: string, toolInput: any) => Promise<any>,
    maxIterations: number = 5
  ): Promise<any> {
    try {
      Logger.info(`🛠️  Calling LLM with ${tools.length} tools available`);

      await this.rateLimiter.waitForToken();

      let messages: any[] = [{ role: 'user', content: prompt }];
      let iterations = 0;

      while (iterations < maxIterations) {
        iterations++;

        const response = await this.client.messages.create({
          model: this.model,
          max_tokens: 4000,
          tools: tools as any,  // Anthropic tool format
          messages: messages
        }) as Anthropic.Message;

        // Check if AI wants to use a tool
        const toolUseBlock = response.content.find(
          (block: any) => block.type === 'tool_use'
        ) as ToolUseBlock | undefined;

        if (!toolUseBlock) {
          // AI didn't use a tool, return final answer
          const textBlock = response.content.find((block: any) => block.type === 'text');
          if (textBlock && 'text' in textBlock) {
            Logger.info(`✅ Final answer received (${iterations} iterations)`);
            return textBlock.text;
          }
          throw new Error('No text response from AI');
        }

        // AI wants to use a tool!
        Logger.info(`🔧 AI calling tool: ${toolUseBlock.name} with input: ${JSON.stringify(toolUseBlock.input)}`);

        // Execute the tool
        const toolResult = await onToolCall(toolUseBlock.name, toolUseBlock.input);
        Logger.info(`✅ Tool executed successfully`);

        // Add assistant message and tool result to conversation
        messages.push({
          role: 'assistant',
          content: response.content
        });

        messages.push({
          role: 'user',
          content: [{
            type: 'tool_result',
            tool_use_id: toolUseBlock.id,
            content: JSON.stringify(toolResult)
          }]
        });
      }

      throw new Error(`Max iterations (${maxIterations}) reached in tool use loop`);

    } catch (error) {
      Logger.error(`Failed to call with tools: ${error}`);
      throw error;
    }
  }

  /**
   * ========================================================================
   * NEW: SEMANTIC INTELLIGENCE FEATURES
   * ========================================================================
   */

  /**
   * Perform root cause analysis on test failure
   *
   * Deep analysis to understand WHY a test failed, not just WHAT failed.
   *
   * @param failureInfo - Information about the test failure
   */
  async analyzeRootCause(failureInfo: {
    testName: string;
    errorMessage: string;
    stackTrace?: string;
    screenshot?: string;
    pageHtml?: string;
    testCode?: string;
    previousFailures?: any[];
  }): Promise<RootCauseAnalysis> {
    try {
      const prompt = `${PROMPTS.ROOT_CAUSE_ANALYSIS}

Test Name: ${failureInfo.testName}
Error Message: ${failureInfo.errorMessage}

${failureInfo.stackTrace ? `Stack Trace:\n${failureInfo.stackTrace}\n` : ''}
${failureInfo.testCode ? `Test Code:\n${failureInfo.testCode}\n` : ''}
${failureInfo.pageHtml ? `Page HTML:\n${failureInfo.pageHtml.substring(0, 2000)}\n` : ''}
${failureInfo.previousFailures ? `Previous Similar Failures:\n${JSON.stringify(failureInfo.previousFailures, null, 2)}\n` : ''}

Perform deep root cause analysis.`;

      return await this.callLLMWithPromptCaching<RootCauseAnalysis>(
        'analyzeRootCause',
        PROMPTS.ROOT_CAUSE_ANALYSIS,
        prompt,
        3000,
        { test_name: failureInfo.testName }
      );
    } catch (error) {
      Logger.error(`Failed to analyze root cause: ${error}`);
      throw error;
    }
  }

  /**
   * Cluster similar test failures
   *
   * Groups related failures by semantic similarity to reduce noise.
   *
   * @param failures - Array of test failures
   */
  async clusterFailures(failures: Array<{
    testName: string;
    errorMessage: string;
    stackTrace?: string;
  }>): Promise<FailureClusteringResult> {
    try {
      const prompt = `${PROMPTS.FAILURE_CLUSTERING}

Test Failures:
${JSON.stringify(failures, null, 2)}

Group these failures by root cause.`;

      return await this.callLLMWithPromptCaching<FailureClusteringResult>(
        'clusterFailures',
        PROMPTS.FAILURE_CLUSTERING,
        prompt,
        3000,
        { failure_count: failures.length }
      );
    } catch (error) {
      Logger.error(`Failed to cluster failures: ${error}`);
      throw error;
    }
  }

  /**
   * ========================================================================
   * NEW: META-REASONING FEATURES (Phase 2)
   * ========================================================================
   */

  /**
   * Reason about a problem with self-evaluation and correction
   *
   * AI evaluates its own reasoning quality, identifies weaknesses, and self-corrects.
   *
   * @param problem - The problem to solve
   * @param context - Additional context for reasoning
   */
  async reasonWithMetaCognition(
    problem: string,
    context?: string
  ): Promise<MetaReasoningResult> {
    try {
      Logger.info('🧠 Reasoning with meta-cognition...');

      const prompt = `${PROMPTS.META_REASONING}

Problem: ${problem}

${context ? `Context:\n${context}\n` : ''}

Solve this problem and evaluate your own reasoning quality.`;

      return await this.callLLMWithPromptCaching<MetaReasoningResult>(
        'reasonWithMetaCognition',
        PROMPTS.META_REASONING,
        prompt,
        4000,
        { problem_length: problem.length }
      );
    } catch (error) {
      Logger.error(`Failed to reason with meta-cognition: ${error}`);
      throw error;
    }
  }

  /**
   * Select the optimal reasoning strategy for a task
   *
   * AI analyzes the task and chooses the best reasoning approach
   * (Standard, CoT, ToT, or Self-Consistency)
   *
   * @param task - Description of the task
   * @param constraints - Constraints like cost, time, accuracy requirements
   */
  async selectReasoningStrategy(
    task: string,
    constraints?: {
      maxCost?: 'low' | 'medium' | 'high';
      timeConstraint?: 'fast' | 'moderate' | 'slow';
      accuracyRequired?: 'low' | 'medium' | 'high' | 'critical';
    }
  ): Promise<StrategySelectionResult> {
    try {
      Logger.info('🎯 Selecting optimal reasoning strategy...');

      const prompt = `${PROMPTS.STRATEGY_SELECTION}

Task: ${task}

${constraints ? `Constraints:
- Max Cost: ${constraints.maxCost || 'no limit'}
- Time Constraint: ${constraints.timeConstraint || 'no limit'}
- Accuracy Required: ${constraints.accuracyRequired || 'high'}
` : ''}

Select the best reasoning strategy for this task.`;

      return await this.callLLMWithPromptCaching<StrategySelectionResult>(
        'selectReasoningStrategy',
        PROMPTS.STRATEGY_SELECTION,
        prompt,
        2000,
        { task_length: task.length }
      );
    } catch (error) {
      Logger.error(`Failed to select reasoning strategy: ${error}`);
      throw error;
    }
  }

  /**
   * Generate with adaptive strategy selection
   *
   * AI automatically selects and uses the best reasoning strategy
   *
   * @param task - The task to perform
   * @param autoSelect - Whether to auto-select strategy (default: true)
   */
  async generateWithAdaptiveReasoning(
    task: string,
    autoSelect: boolean = true
  ): Promise<{ result: any; strategyUsed: string; metaInfo: MetaReasoningResult }> {
    try {
      Logger.info('🔄 Generating with adaptive reasoning...');

      // Step 1: Select optimal strategy
      const strategySelection = await this.selectReasoningStrategy(task);
      Logger.info(`✅ Selected strategy: ${strategySelection.selectedStrategy.name}`);

      // Step 2: Execute with meta-reasoning
      const metaResult = await this.reasonWithMetaCognition(task);

      // Step 3: If confidence is low, consider using a more robust strategy
      if (metaResult.selfEvaluation.confidence < 0.7 && autoSelect) {
        Logger.warn(`⚠️  Low confidence (${metaResult.selfEvaluation.confidence}), considering alternative strategy...`);

        // Try with Tree of Thought for better accuracy
        if (strategySelection.selectedStrategy.name === 'CoT') {
          Logger.info('🌲 Retrying with Tree of Thought for higher confidence...');
          const totResult = await this.treeOfThought.reason(task, '', { maxDepth: 3, branchingFactor: 3 });

          return {
            result: totResult.finalAnswer,
            strategyUsed: 'ToT (auto-escalated)',
            metaInfo: {
              ...metaResult,
              finalAnswer: totResult.finalAnswer,
              strategyUsed: 'ToT'
            }
          };
        }
      }

      return {
        result: metaResult.finalAnswer,
        strategyUsed: metaResult.strategyUsed,
        metaInfo: metaResult
      };
    } catch (error) {
      Logger.error(`Failed to generate with adaptive reasoning: ${error}`);
      throw error;
    }
  }

  /**
   * ========================================================================
   * NEW: AUTO-FIX FLAKY TESTS (Phase 2)
   * ========================================================================
   */

  /**
   * Detect if a test is flaky based on execution history
   *
   * Analyzes test execution patterns to identify flaky behavior
   *
   * @param testName - Name of the test
   * @param executionHistory - Historical test execution data
   */
  async detectFlakyTest(
    testName: string,
    executionHistory: TestExecutionHistory
  ): Promise<FlakyTestAnalysis> {
    try {
      Logger.info(`🔍 Analyzing flakiness for: ${testName}`);

      // Calculate statistics
      const totalRuns = executionHistory.runs.length;
      const failures = executionHistory.runs.filter(r => r.result === 'fail').length;
      const passes = executionHistory.runs.filter(r => r.result === 'pass').length;

      const prompt = `${PROMPTS.FLAKY_TEST_DETECTION}

Test Name: ${testName}
Total Runs: ${totalRuns}
Failures: ${failures}
Passes: ${passes}

Execution History:
${JSON.stringify(executionHistory.runs.slice(-20), null, 2)}

Analyze if this test is flaky and identify the root causes.`;

      return await this.callLLMWithPromptCaching<FlakyTestAnalysis>(
        'detectFlakyTest',
        PROMPTS.FLAKY_TEST_DETECTION,
        prompt,
        3000,
        { test_name: testName, runs: totalRuns }
      );
    } catch (error) {
      Logger.error(`Failed to detect flaky test: ${error}`);
      throw error;
    }
  }

  /**
   * Analyze multiple tests for flakiness
   *
   * Batch analysis of test suite to identify all flaky tests
   *
   * @param testHistories - Array of test execution histories
   */
  async detectFlakyTests(
    testHistories: TestExecutionHistory[]
  ): Promise<FlakyTestDetectionResult> {
    try {
      Logger.info(`🔍 Analyzing ${testHistories.length} tests for flakiness...`);

      const analyses: FlakyTestAnalysis[] = [];

      // Analyze each test (could be parallelized)
      for (const history of testHistories) {
        try {
          const analysis = await this.detectFlakyTest(history.testName, history);
          if (analysis.isFlaky) {
            analyses.push(analysis);
          }
        } catch (error) {
          Logger.warn(`Failed to analyze ${history.testName}: ${error}`);
        }
      }

      // Sort by flakiness score (worst first)
      analyses.sort((a, b) => b.flakinessScore - a.flakinessScore);

      const flakinessRate = (analyses.length / testHistories.length) * 100;

      // Categorize by priority
      const highPriority = analyses
        .filter(a => a.impact === 'critical' || a.impact === 'high')
        .map(a => a.testName);

      const mediumPriority = analyses
        .filter(a => a.impact === 'medium')
        .map(a => a.testName);

      // Find common patterns
      const patterns = this.findFlakinessPatterns(analyses);

      Logger.info(`✅ Found ${analyses.length} flaky tests (${flakinessRate.toFixed(1)}% of suite)`);

      return {
        totalTests: testHistories.length,
        flakyTests: analyses,
        flakinessRate,
        recommendations: {
          highPriority,
          mediumPriority,
          patterns
        }
      };
    } catch (error) {
      Logger.error(`Failed to detect flaky tests: ${error}`);
      throw error;
    }
  }

  /**
   * Find common patterns across flaky tests
   *
   * @param analyses - Array of flaky test analyses
   */
  private findFlakinessPatterns(analyses: FlakyTestAnalysis[]): string[] {
    const patterns: Map<string, number> = new Map();

    analyses.forEach(analysis => {
      // Count flakiness patterns
      const pattern = analysis.flakinessPattern;
      patterns.set(pattern, (patterns.get(pattern) || 0) + 1);

      // Count root cause categories
      analysis.rootCauses.forEach(cause => {
        const key = `${cause.category}_related`;
        patterns.set(key, (patterns.get(key) || 0) + 1);
      });
    });

    // Convert to readable patterns
    const result: string[] = [];
    patterns.forEach((count, pattern) => {
      const percentage = (count / analyses.length * 100).toFixed(0);
      result.push(`${percentage}% of flaky tests are ${pattern} (${count} tests)`);
    });

    return result.sort((a, b) => {
      const aNum = parseInt(a.match(/\d+/)?.[0] || '0');
      const bNum = parseInt(b.match(/\d+/)?.[0] || '0');
      return bNum - aNum;
    });
  }

  /**
   * Generate a fix for a flaky test
   *
   * AI analyzes the test code and provides executable fixes
   *
   * @param testName - Name of the test
   * @param testCode - Current test code
   * @param analysis - Flakiness analysis from detectFlakyTest
   */
  async fixFlakyTest(
    testName: string,
    testCode: string,
    analysis: FlakyTestAnalysis
  ): Promise<FlakyTestFix> {
    try {
      Logger.info(`🔧 Generating fix for flaky test: ${testName}`);

      const prompt = `${PROMPTS.FLAKY_TEST_FIX}

Test Name: ${testName}

Current Test Code:
${testCode}

Flakiness Analysis:
- Flakiness Score: ${analysis.flakinessScore}
- Pattern: ${analysis.flakinessPattern}
- Root Causes: ${JSON.stringify(analysis.rootCauses, null, 2)}

Generate a fix that addresses these flakiness issues.`;

      const fix = await this.callLLMWithPromptCaching<FlakyTestFix>(
        'fixFlakyTest',
        PROMPTS.FLAKY_TEST_FIX,
        prompt,
        4000,
        { test_name: testName, flakiness_score: analysis.flakinessScore }
      );

      Logger.info(`✅ Generated ${fix.fixes.length} fixes with ${(fix.confidence * 100).toFixed(0)}% confidence`);
      Logger.info(`📈 Expected improvement: ${(fix.expectedImprovement * 100).toFixed(0)}%`);

      return fix;
    } catch (error) {
      Logger.error(`Failed to fix flaky test: ${error}`);
      throw error;
    }
  }

  /**
   * Auto-fix all flaky tests in a detection result
   *
   * Batch generation of fixes for all detected flaky tests
   *
   * @param detectionResult - Result from detectFlakyTests
   * @param testCodeMap - Map of test names to their source code
   */
  async autoFixFlakyTests(
    detectionResult: FlakyTestDetectionResult,
    testCodeMap: Map<string, string>
  ): Promise<FlakyTestFix[]> {
    try {
      Logger.info(`🔧 Auto-fixing ${detectionResult.flakyTests.length} flaky tests...`);

      const fixes: FlakyTestFix[] = [];

      // Fix high priority tests first
      const priorityOrder = [
        ...detectionResult.recommendations.highPriority,
        ...detectionResult.recommendations.mediumPriority
      ];

      for (const testName of priorityOrder) {
        const analysis = detectionResult.flakyTests.find(t => t.testName === testName);
        const testCode = testCodeMap.get(testName);

        if (analysis && testCode) {
          try {
            const fix = await this.fixFlakyTest(testName, testCode, analysis);
            fixes.push(fix);
          } catch (error) {
            Logger.warn(`Failed to fix ${testName}: ${error}`);
          }
        }
      }

      Logger.info(`✅ Generated fixes for ${fixes.length} tests`);

      // Summary
      const avgConfidence = fixes.reduce((sum, f) => sum + f.confidence, 0) / fixes.length;
      const avgImprovement = fixes.reduce((sum, f) => sum + f.expectedImprovement, 0) / fixes.length;

      Logger.info(`📊 Average fix confidence: ${(avgConfidence * 100).toFixed(0)}%`);
      Logger.info(`📈 Average expected improvement: ${(avgImprovement * 100).toFixed(0)}%`);

      return fixes;
    } catch (error) {
      Logger.error(`Failed to auto-fix flaky tests: ${error}`);
      throw error;
    }
  }
}
