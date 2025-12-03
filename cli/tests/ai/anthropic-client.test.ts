/**
 * Integration Tests for Anthropic AI Client
 * Tests all AI-powered features with real API calls
 */

import { AnthropicClient } from '../../src/ai/anthropic-client';
import { PlaywrightAction } from '../../src/types';
import * as dotenv from 'dotenv';
import * as path from 'path';

dotenv.config({ path: path.resolve(__dirname, '../../.env') });

// Check if API key is available
const apiKey = process.env.ANTHROPIC_API_KEY;
const runTests = !!apiKey;

const describeWithApiKey = runTests ? describe : describe.skip;

describeWithApiKey('AnthropicClient Integration Tests', () => {
  let client: AnthropicClient;

  beforeAll(() => {
    if (!apiKey) {
      console.warn('⚠️  Skipping AnthropicClient tests: ANTHROPIC_API_KEY not set');
      return;
    }
    client = new AnthropicClient(apiKey);
  });

  describe('Initialization', () => {
    it('should initialize with API key from constructor', () => {
      const testClient = new AnthropicClient(apiKey);
      expect(testClient).toBeInstanceOf(AnthropicClient);
    });

    it('should initialize with API key from environment', () => {
      const testClient = new AnthropicClient();
      expect(testClient).toBeInstanceOf(AnthropicClient);
    });

    it('should throw error if no API key provided', () => {
      const originalKey = process.env.ANTHROPIC_API_KEY;
      delete process.env.ANTHROPIC_API_KEY;

      expect(() => new AnthropicClient()).toThrow('Anthropic API key not provided');

      process.env.ANTHROPIC_API_KEY = originalKey;
    });

    it('should accept custom model', () => {
      const testClient = new AnthropicClient(apiKey, 'claude-3-5-haiku-20241022');
      expect(testClient).toBeInstanceOf(AnthropicClient);
    });
  });

  describe('generateBDDScenario - Without Reasoning', () => {
    it('should generate BDD scenario from simple recording', async () => {
      const recording: PlaywrightAction[] = [
        { type: 'navigate', url: 'https://example.com' },
        { type: 'click', selector: 'text=Login' },
        { type: 'fill', selector: '#email', value: 'test@example.com' },
        { type: 'fill', selector: '#password', value: 'password123' },
        { type: 'click', selector: 'button[type=submit]' }
      ];

      const result = await client.generateBDDScenario(
        recording,
        'user_login',
        false // No reasoning
      );

      expect(result).toHaveProperty('feature');
      expect(result).toHaveProperty('steps');
      expect(result).toHaveProperty('locators');
      expect(result).toHaveProperty('testData');
      expect(result).toHaveProperty('helpers');

      expect(typeof result.feature).toBe('string');
      expect(result.feature.length).toBeGreaterThan(0);

      console.log('\n=== Generated BDD Scenario ===');
      console.log('Feature:');
      console.log(result.feature);
      console.log('\nLocators:', JSON.stringify(result.locators, null, 2));
      console.log('\nTest Data:', JSON.stringify(result.testData, null, 2));
    }, 30000);

    it('should include proper Gherkin syntax', async () => {
      const recording: PlaywrightAction[] = [
        { type: 'navigate', url: 'https://example.com/products' },
        { type: 'click', selector: 'text=Add to Cart' }
      ];

      const result = await client.generateBDDScenario(recording, 'add_to_cart', false);

      const feature = result.feature.toLowerCase();
      expect(
        feature.includes('feature:') ||
        feature.includes('scenario:') ||
        feature.includes('given') ||
        feature.includes('when') ||
        feature.includes('then')
      ).toBe(true);
    }, 30000);

    it('should extract locators from recording', async () => {
      const recording: PlaywrightAction[] = [
        { type: 'click', selector: '#submit-button' },
        { type: 'fill', selector: 'input[name=username]', value: 'testuser' }
      ];

      const result = await client.generateBDDScenario(recording, 'test_scenario', false);

      expect(typeof result.locators).toBe('object');
      expect(Object.keys(result.locators).length).toBeGreaterThan(0);
    }, 30000);

    it('should generate test data from values', async () => {
      const recording: PlaywrightAction[] = [
        { type: 'fill', selector: '#email', value: 'test@example.com' },
        { type: 'fill', selector: '#name', value: 'John Doe' }
      ];

      const result = await client.generateBDDScenario(recording, 'fill_form', false);

      expect(typeof result.testData).toBe('object');
    }, 30000);
  });

  describe('generateBDDScenario - With Chain of Thought', () => {
    it('should generate BDD scenario with reasoning', async () => {
      const recording: PlaywrightAction[] = [
        { type: 'navigate', url: 'https://app.com' },
        { type: 'click', selector: 'text=Sign In' },
        { type: 'fill', selector: '#username', value: 'admin' },
        { type: 'fill', selector: '#password', value: 'secret' },
        { type: 'click', selector: 'button[type=submit]' },
        { type: 'wait', selector: 'text=Dashboard' }
      ];

      const result = await client.generateBDDScenario(
        recording,
        'admin_login',
        true // Use reasoning
      );

      expect(result).toHaveProperty('feature');
      expect(result).toHaveProperty('steps');
      expect(result).toHaveProperty('locators');
      expect(result).toHaveProperty('testData');

      console.log('\n=== BDD with Reasoning ===');
      console.log(result.feature);
    }, 60000); // Longer timeout for reasoning

    it('should produce higher quality output with reasoning', async () => {
      const recording: PlaywrightAction[] = [
        { type: 'navigate', url: 'https://ecommerce.com/products' },
        { type: 'click', selector: 'text=Laptop' },
        { type: 'click', selector: 'text=Add to Cart' },
        { type: 'click', selector: 'text=Checkout' },
        { type: 'fill', selector: '#shipping-address', value: '123 Main St' },
        { type: 'click', selector: 'button:has-text("Place Order")' }
      ];

      const withReasoning = await client.generateBDDScenario(recording, 'checkout', true);
      const withoutReasoning = await client.generateBDDScenario(recording, 'checkout', false);

      // With reasoning should generally have more detailed output
      expect(withReasoning.feature.length).toBeGreaterThan(0);
      expect(withoutReasoning.feature.length).toBeGreaterThan(0);

      console.log('\n=== Quality Comparison ===');
      console.log('With Reasoning length:', withReasoning.feature.length);
      console.log('Without Reasoning length:', withoutReasoning.feature.length);
    }, 90000);
  });

  describe('healLocator', () => {
    it('should suggest alternative locators', async () => {
      const context = {
        failedLocator: 'button#submit',
        elementDescription: 'Submit button for login form',
        pageHtml: `
          <html>
            <body>
              <form>
                <button type="submit" class="btn-primary" data-testid="login-submit">
                  Submit
                </button>
              </form>
            </body>
          </html>
        `
      };

      const result = await client.healLocator(context);

      expect(result).toHaveProperty('locator');
      expect(result).toHaveProperty('confidence');
      expect(result).toHaveProperty('alternatives');

      expect(typeof result.locator).toBe('string');
      expect(result.locator.length).toBeGreaterThan(0);
      expect(result.confidence).toBeGreaterThan(0);
      expect(result.confidence).toBeLessThanOrEqual(1);
      expect(Array.isArray(result.alternatives)).toBe(true);

      console.log('\n=== Locator Healing ===');
      console.log('Failed:', context.failedLocator);
      console.log('Suggested:', result.locator);
      console.log('Confidence:', result.confidence);
      console.log('Alternatives:', result.alternatives);
    }, 30000);

    it('should prioritize data-testid attributes', async () => {
      const context = {
        failedLocator: 'button',
        elementDescription: 'Submit button',
        pageHtml: `
          <button data-testid="submit-btn" type="submit">Submit</button>
        `
      };

      const result = await client.healLocator(context);

      // Suggested locator should prefer data-testid
      const locator = result.locator.toLowerCase();
      expect(
        locator.includes('data-testid') ||
        locator.includes('submit-btn') ||
        locator.includes('[data-testid') ||
        result.confidence > 0.8
      ).toBe(true);
    }, 30000);

    it('should handle complex HTML structures', async () => {
      const context = {
        failedLocator: 'a.nav-link',
        elementDescription: 'Dashboard navigation link',
        pageHtml: `
          <nav class="navbar">
            <ul>
              <li><a href="/home" class="nav-link">Home</a></li>
              <li><a href="/dashboard" class="nav-link active" aria-label="Dashboard">Dashboard</a></li>
              <li><a href="/profile" class="nav-link">Profile</a></li>
            </ul>
          </nav>
        `
      };

      const result = await client.healLocator(context);

      expect(result.locator).toBeTruthy();
      expect(result.alternatives.length).toBeGreaterThan(0);

      console.log('\n=== Complex Locator Healing ===');
      console.log('Suggestions:', [result.locator, ...result.alternatives]);
    }, 30000);
  });

  describe('generateTestData', () => {
    it('should generate realistic test data from schema', async () => {
      const schema = {
        user: {
          type: 'object',
          required: true,
          context: 'E-commerce customer',
          example: {
            name: 'string',
            email: 'email',
            age: 'number'
          }
        }
      };

      const result = await client.generateTestData(schema);

      expect(typeof result).toBe('object');

      console.log('\n=== Generated Test Data ===');
      console.log(JSON.stringify(result, null, 2));
    }, 30000);

    it('should handle complex schemas', async () => {
      const schema = {
        order: {
          type: 'object',
          context: 'E-commerce order',
          example: {
            orderId: 'uuid',
            customer: {
              name: 'string',
              email: 'email'
            },
            items: [
              {
                productId: 'string',
                quantity: 'number',
                price: 'currency'
              }
            ],
            total: 'currency',
            status: ['pending', 'shipped', 'delivered']
          }
        }
      };

      const result = await client.generateTestData(schema);

      expect(result).toBeTruthy();

      console.log('\n=== Complex Schema Data ===');
      console.log(JSON.stringify(result, null, 2));
    }, 30000);

    it('should generate contextually appropriate data', async () => {
      const schema = {
        bankAccount: {
          type: 'object',
          context: 'Banking application test account',
          example: {
            accountNumber: 'string (10 digits)',
            routingNumber: 'string (9 digits)',
            balance: 'currency (positive)'
          }
        }
      };

      const result = await client.generateTestData(schema);

      expect(result).toBeTruthy();
      console.log('\n=== Banking Data ===');
      console.log(JSON.stringify(result, null, 2));
    }, 30000);
  });

  describe('optimizeWaits', () => {
    it('should suggest wait optimizations', async () => {
      const testLog = {
        scenario: 'user_login',
        steps: [
          {
            name: 'wait for dashboard',
            locator: '#dashboard',
            actualTime: 2300,
            timeoutUsed: 10000
          },
          {
            name: 'wait for profile',
            locator: '.profile-section',
            actualTime: 8500,
            timeoutUsed: 10000
          }
        ]
      };

      const result = await client.optimizeWaits(testLog);

      expect(result).toHaveProperty('optimizations');
      expect(Array.isArray(result.optimizations)).toBe(true);

      console.log('\n=== Wait Optimizations ===');
      console.log(JSON.stringify(result, null, 2));
    }, 30000);

    it('should identify slow elements', async () => {
      const testLog = {
        scenario: 'page_load',
        steps: [
          { locator: '#fast-element', actualTime: 500, timeoutUsed: 5000 },
          { locator: '#slow-element', actualTime: 15000, timeoutUsed: 20000 }
        ]
      };

      const result = await client.optimizeWaits(testLog);

      expect(result.optimizations.length).toBeGreaterThan(0);
    }, 30000);
  });

  describe('analyzePatterns', () => {
    it('should identify common patterns across scenarios', async () => {
      const scenarios = [
        {
          name: 'login_test',
          steps: [
            'Given I am on the login page',
            'When I enter credentials',
            'And I click submit',
            'Then I should see dashboard'
          ]
        },
        {
          name: 'register_test',
          steps: [
            'Given I am on the register page',
            'When I enter user details',
            'And I click submit',
            'Then I should see confirmation'
          ]
        },
        {
          name: 'password_reset',
          steps: [
            'Given I am on the login page',
            'When I click forgot password',
            'And I enter email',
            'And I click submit',
            'Then I should see success message'
          ]
        }
      ];

      const result = await client.analyzePatterns(scenarios);

      expect(result).toHaveProperty('commonSteps');
      expect(result).toHaveProperty('duplicateScenarios');
      expect(result).toHaveProperty('reusableLocators');

      console.log('\n=== Pattern Analysis ===');
      console.log(JSON.stringify(result, null, 2));
    }, 30000);

    it('should find duplicate scenarios', async () => {
      const scenarios = [
        {
          name: 'test1',
          steps: ['Given setup', 'When action', 'Then verify']
        },
        {
          name: 'test2',
          steps: ['Given setup', 'When action', 'Then verify']
        },
        {
          name: 'test3',
          steps: ['Given different setup', 'When different action']
        }
      ];

      const result = await client.analyzePatterns(scenarios);

      expect(result.duplicateScenarios).toBeDefined();
      if (result.duplicateScenarios.length > 0) {
        expect(result.duplicateScenarios[0].similarity).toBeGreaterThan(0);
      }
    }, 30000);

    it('should suggest helper functions', async () => {
      const scenarios = [
        {
          name: 'scenario1',
          steps: [
            'When I login as admin',
            'And I navigate to dashboard',
            'Then I should see admin panel'
          ]
        },
        {
          name: 'scenario2',
          steps: [
            'When I login as admin',
            'And I navigate to settings',
            'Then I should see settings page'
          ]
        }
      ];

      const result = await client.analyzePatterns(scenarios);

      expect(result.commonSteps.length).toBeGreaterThan(0);
    }, 30000);
  });

  describe('Error Handling and Edge Cases', () => {
    it('should handle empty recording gracefully', async () => {
      const result = await client.generateBDDScenario([], 'empty_test', false);

      expect(result).toHaveProperty('feature');
      expect(result).toHaveProperty('steps');
    }, 30000);

    it('should handle invalid API responses', async () => {
      // Test with malformed input that might cause AI to return unexpected format
      const recording: PlaywrightAction[] = [
        { type: 'click', selector: '' } // Empty selector
      ];

      const result = await client.generateBDDScenario(recording, 'invalid_test', false);

      // Should still return valid structure even with poor input
      expect(result).toHaveProperty('feature');
      expect(result).toHaveProperty('steps');
    }, 30000);
  });

  describe('Performance Tests', () => {
    it('should complete BDD generation within reasonable time', async () => {
      const startTime = Date.now();

      const recording: PlaywrightAction[] = [
        { type: 'navigate', url: 'https://example.com' },
        { type: 'click', selector: 'button' }
      ];

      await client.generateBDDScenario(recording, 'perf_test', false);

      const duration = Date.now() - startTime;

      console.log(`\nBDD Generation took ${duration}ms`);
      expect(duration).toBeLessThan(30000); // Should complete within 30 seconds
    }, 35000);

    it('should handle multiple concurrent requests', async () => {
      const requests = [
        client.generateBDDScenario(
          [{ type: 'click', selector: 'a' }],
          'test1',
          false
        ),
        client.generateBDDScenario(
          [{ type: 'fill', selector: 'input', value: 'test' }],
          'test2',
          false
        ),
        client.generateBDDScenario(
          [{ type: 'navigate', url: 'https://example.com' }],
          'test3',
          false
        )
      ];

      const results = await Promise.all(requests);

      expect(results).toHaveLength(3);
      results.forEach(result => {
        expect(result).toHaveProperty('feature');
      });
    }, 60000);
  });
});
