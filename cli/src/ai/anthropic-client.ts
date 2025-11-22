import Anthropic from '@anthropic-ai/sdk';
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

export class AnthropicClient implements AIClient {
  private client: Anthropic;
  private model: string;

  constructor(apiKey: string, model: string = 'claude-sonnet-4-5-20250929') {
    this.client = new Anthropic({ apiKey });
    this.model = model;
  }

  /**
   * Generate BDD scenario from Playwright recording
   */
  async generateBDDScenario(
    recording: PlaywrightAction[],
    scenarioName: string
  ): Promise<BDDOutput> {
    try {
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
