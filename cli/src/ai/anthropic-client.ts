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

  constructor(apiKey?: string, model?: string) {
    // Use provided API key or fallback to environment variable
    const key = apiKey || process.env.ANTHROPIC_API_KEY;
    if (!key) {
      throw new Error('Anthropic API key not provided. Please set ANTHROPIC_API_KEY in .env file or pass it to the constructor.');
    }

    // Use provided model or fallback to environment variable or default
    this.model = model || process.env.AI_MODEL || 'claude-sonnet-4-5-20250929';

    this.client = new Anthropic({ apiKey: key });

    // Initialize reasoning engines
    const reasoningEngine = createReasoningEngine(this.client, this.model);
    this.chainOfThought = reasoningEngine.chainOfThought;
    this.treeOfThought = reasoningEngine.treeOfThought;

    Logger.info(`AnthropicClient initialized with model: ${this.model}`);
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

        const response = await this.client.messages.create({
          model: this.model,
          max_tokens: 4000,
          messages: [
            {
              role: 'user',
              content: prompt
            }
          ]
        });

        const content = response.content[0];
        if (content.type !== 'text') {
          throw new Error('Unexpected response type from AI');
        }

        // Parse JSON response
        const result = JSON.parse(content.text);

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

        const response = await this.client.messages.create({
          model: this.model,
          max_tokens: 4000,
          messages: [
            {
              role: 'user',
              content: prompt
            }
          ]
        });

        const content = response.content[0];
        if (content.type !== 'text') {
          throw new Error('Unexpected response type from AI');
        }

        // Parse JSON response
        const result = JSON.parse(content.text);

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

      const response = await this.client.messages.create({
        model: this.model,
        max_tokens: 1000,
        messages: [
          {
            role: 'user',
            content: prompt
          }
        ]
      });

      const content = response.content[0];
      if (content.type !== 'text') {
        throw new Error('Unexpected response type from AI');
      }

      const result = JSON.parse(content.text);

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

      const response = await this.client.messages.create({
        model: this.model,
        max_tokens: 2000,
        messages: [
          {
            role: 'user',
            content: prompt
          }
        ]
      });

      const content = response.content[0];
      if (content.type !== 'text') {
        throw new Error('Unexpected response type from AI');
      }

      return JSON.parse(content.text);
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

      const response = await this.client.messages.create({
        model: this.model,
        max_tokens: 2000,
        messages: [
          {
            role: 'user',
            content: prompt
          }
        ]
      });

      const content = response.content[0];
      if (content.type !== 'text') {
        throw new Error('Unexpected response type from AI');
      }

      return JSON.parse(content.text);
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

      const response = await this.client.messages.create({
        model: this.model,
        max_tokens: 3000,
        messages: [
          {
            role: 'user',
            content: prompt
          }
        ]
      });

      const content = response.content[0];
      if (content.type !== 'text') {
        throw new Error('Unexpected response type from AI');
      }

      return JSON.parse(content.text);
    } catch (error) {
      Logger.error(`Failed to analyze patterns: ${error}`);
      throw error;
    }
  }
}
