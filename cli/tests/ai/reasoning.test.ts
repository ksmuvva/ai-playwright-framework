/**
 * Unit and Integration Tests for AI Reasoning
 * Tests Chain of Thought and Tree of Thought reasoning strategies
 * Including real API calls to test reasoning capabilities
 */

import { ChainOfThought, TreeOfThought, createReasoningEngine } from '../../src/ai/reasoning';
import Anthropic from '@anthropic-ai/sdk';
import * as dotenv from 'dotenv';
import * as path from 'path';

// Load environment variables
dotenv.config({ path: path.resolve(__dirname, '../../.env') });

describe('Reasoning Module', () => {
  let client: Anthropic;
  const model = 'claude-sonnet-4-5-20250929';

  beforeAll(() => {
    const apiKey = process.env.ANTHROPIC_API_KEY;
    if (!apiKey) {
      throw new Error('ANTHROPIC_API_KEY not set in environment');
    }
    client = new Anthropic({ apiKey });
  });

  describe('ChainOfThought', () => {
    let cot: ChainOfThought;

    beforeEach(() => {
      cot = new ChainOfThought(client, model);
    });

    it('should initialize with client and model', () => {
      expect(cot).toBeInstanceOf(ChainOfThought);
    });

    describe('buildCoTPrompt', () => {
      it('should build proper CoT prompt', () => {
        const prompt = 'Analyze this test scenario';
        const context = 'User clicks login button';
        const maxSteps = 5;

        // Access private method through any type for testing
        const cotPrompt = (cot as any).buildCoTPrompt(prompt, context, maxSteps);

        expect(cotPrompt).toContain('Chain of Thought reasoning');
        expect(cotPrompt).toContain(prompt);
        expect(cotPrompt).toContain(context);
        expect(cotPrompt).toContain('5 clear reasoning steps');
        expect(cotPrompt).toContain('JSON format');
      });
    });

    describe('parseCoTResponse', () => {
      it('should parse valid JSON response', () => {
        const response = JSON.stringify({
          steps: [
            {
              step: 1,
              thought: 'Analyze the problem',
              action: 'Identify key elements',
              confidence: 0.9
            }
          ],
          finalAnswer: 'Test scenario is valid',
          reasoning: 'Based on step-by-step analysis'
        });

        const result = (cot as any).parseCoTResponse(response);

        expect(result.steps).toHaveLength(1);
        expect(result.steps[0].thought).toBe('Analyze the problem');
        expect(result.finalAnswer).toBe('Test scenario is valid');
        expect(result.reasoning).toBe('Based on step-by-step analysis');
      });

      it('should handle markdown-wrapped JSON', () => {
        const response = '```json\n' + JSON.stringify({
          steps: [],
          finalAnswer: 'answer',
          reasoning: 'reasoning'
        }) + '\n```';

        const result = (cot as any).parseCoTResponse(response);

        expect(result.steps).toEqual([]);
        expect(result.finalAnswer).toBe('answer');
      });

      it('should handle malformed JSON gracefully', () => {
        const response = 'This is not JSON';

        const result = (cot as any).parseCoTResponse(response);

        expect(result.steps).toHaveLength(1);
        expect(result.steps[0].thought).toBe(response);
        expect(result.reasoning).toBe('Failed to parse structured response');
      });
    });

    describe('reason - Real API Tests', () => {
      it('should perform Chain of Thought reasoning on simple problem', async () => {
        const prompt = 'How should I structure a BDD scenario for user login?';
        const context = `
          Actions recorded:
          1. Navigate to https://app.com
          2. Click "Sign In" button
          3. Fill email field
          4. Fill password field
          5. Click submit
          6. Verify dashboard appears
        `;

        const result = await cot.reason(prompt, context, { maxSteps: 3 });

        expect(result).toHaveProperty('steps');
        expect(result).toHaveProperty('finalAnswer');
        expect(result).toHaveProperty('reasoning');
        expect(result.steps.length).toBeGreaterThan(0);
        expect(result.steps.length).toBeLessThanOrEqual(3);

        // Verify step structure
        result.steps.forEach(step => {
          expect(step).toHaveProperty('step');
          expect(step).toHaveProperty('thought');
          expect(step.step).toBeGreaterThan(0);
          expect(typeof step.thought).toBe('string');
        });

        console.log('\n=== Chain of Thought Result ===');
        console.log('Steps:', JSON.stringify(result.steps, null, 2));
        console.log('Final Answer:', result.finalAnswer);
        console.log('Reasoning:', result.reasoning);
      }, 30000);

      it('should use max steps configuration', async () => {
        const result = await cot.reason(
          'Break down a complex test scenario',
          'Multi-step workflow with user authentication',
          { maxSteps: 5 }
        );

        expect(result.steps.length).toBeGreaterThan(0);
        expect(result.steps.length).toBeLessThanOrEqual(5);
      }, 30000);
    });
  });

  describe('TreeOfThought', () => {
    let tot: TreeOfThought;

    beforeEach(() => {
      tot = new TreeOfThought(client, model);
    });

    it('should initialize with client and model', () => {
      expect(tot).toBeInstanceOf(TreeOfThought);
    });

    describe('selectBestPath', () => {
      it('should select path with highest score', () => {
        const paths = [
          [
            { id: '1', thought: 'Path 1', state: {}, children: [], evaluation: 0.5, depth: 1, isLeaf: true },
            { id: '2', thought: 'Path 1 cont', state: {}, children: [], evaluation: 0.6, depth: 2, isLeaf: true }
          ],
          [
            { id: '3', thought: 'Path 2', state: {}, children: [], evaluation: 0.9, depth: 1, isLeaf: true },
            { id: '4', thought: 'Path 2 cont', state: {}, children: [], evaluation: 0.8, depth: 2, isLeaf: true }
          ]
        ];

        const bestPath = (tot as any).selectBestPath(paths);

        // Path 2 should be selected (higher average evaluation)
        expect(bestPath[0].id).toBe('3');
      });

      it('should prefer deeper paths with depth bonus', () => {
        const paths = [
          [
            { id: '1', thought: 'Short path', state: {}, children: [], evaluation: 0.7, depth: 1, isLeaf: true }
          ],
          [
            { id: '2', thought: 'Deep path 1', state: {}, children: [], evaluation: 0.6, depth: 1, isLeaf: false },
            { id: '3', thought: 'Deep path 2', state: {}, children: [], evaluation: 0.6, depth: 2, isLeaf: false },
            { id: '4', thought: 'Deep path 3', state: {}, children: [], evaluation: 0.6, depth: 3, isLeaf: true }
          ]
        ];

        const bestPath = (tot as any).selectBestPath(paths);

        // Deeper path gets bonus
        expect(bestPath.length).toBeGreaterThan(1);
      });
    });

    describe('getAllPaths', () => {
      it('should extract all root-to-leaf paths', () => {
        const root = {
          id: 'root',
          thought: 'Start',
          state: {},
          children: [
            {
              id: 'child1',
              thought: 'Branch 1',
              state: {},
              children: [],
              evaluation: 0.8,
              depth: 1,
              isLeaf: true
            },
            {
              id: 'child2',
              thought: 'Branch 2',
              state: {},
              children: [
                {
                  id: 'grandchild1',
                  thought: 'Branch 2.1',
                  state: {},
                  children: [],
                  evaluation: 0.9,
                  depth: 2,
                  isLeaf: true
                }
              ],
              evaluation: 0.7,
              depth: 1,
              isLeaf: false
            }
          ],
          evaluation: 0,
          depth: 0,
          isLeaf: false
        };

        const paths = (tot as any).getAllPaths(root);

        expect(paths).toHaveLength(2);
        expect(paths[0].length).toBe(2); // root -> child1
        expect(paths[1].length).toBe(3); // root -> child2 -> grandchild1
      });
    });

    describe('reason - Real API Tests', () => {
      it('should perform Tree of Thought reasoning with multiple branches', async () => {
        const prompt = 'What are different approaches to test a complex multi-step workflow?';
        const context = `
          Workflow: E-commerce checkout
          Steps: Add to cart, proceed to checkout, enter shipping, enter payment, confirm order
        `;

        const result = await tot.reason(prompt, context, {
          branchingFactor: 3,
          maxDepth: 2
        });

        expect(result).toHaveProperty('bestPath');
        expect(result).toHaveProperty('allPaths');
        expect(result).toHaveProperty('finalAnswer');
        expect(result).toHaveProperty('reasoning');

        expect(result.bestPath.length).toBeGreaterThan(0);
        expect(result.allPaths.length).toBeGreaterThan(0);

        // Verify thought tree structure
        result.bestPath.forEach(node => {
          expect(node).toHaveProperty('id');
          expect(node).toHaveProperty('thought');
          expect(node).toHaveProperty('evaluation');
          expect(node).toHaveProperty('depth');
        });

        console.log('\n=== Tree of Thought Result ===');
        console.log('Best Path Length:', result.bestPath.length);
        console.log('Total Paths:', result.allPaths.length);
        console.log('Best Path:');
        result.bestPath.forEach(node => {
          console.log(`  Depth ${node.depth}: ${node.thought} (eval: ${node.evaluation})`);
        });
        console.log('Final Answer:', result.finalAnswer);
        console.log('Reasoning:', result.reasoning);
      }, 60000); // Longer timeout for complex reasoning

      it('should respect branching factor configuration', async () => {
        const result = await tot.reason(
          'Analyze test approaches',
          'Simple login test',
          {
            branchingFactor: 2,
            maxDepth: 2
          }
        );

        // With branching factor 2 and max depth 2, we expect at most 4 paths (2^2)
        expect(result.allPaths.length).toBeLessThanOrEqual(4);
      }, 60000);

      it('should respect max depth configuration', async () => {
        const result = await tot.reason(
          'Deep analysis of test strategy',
          'Complex application testing',
          {
            branchingFactor: 2,
            maxDepth: 3
          }
        );

        // All paths should have depth <= 3 (root + maxDepth)
        result.allPaths.forEach(path => {
          const maxNodeDepth = Math.max(...path.map(node => node.depth));
          expect(maxNodeDepth).toBeLessThanOrEqual(3);
        });
      }, 60000);
    });
  });

  describe('createReasoningEngine', () => {
    it('should create reasoning engine with both strategies', () => {
      const engine = createReasoningEngine(client, model);

      expect(engine).toHaveProperty('chainOfThought');
      expect(engine).toHaveProperty('treeOfThought');
      expect(engine.chainOfThought).toBeInstanceOf(ChainOfThought);
      expect(engine.treeOfThought).toBeInstanceOf(TreeOfThought);
    });
  });

  describe('Real-World Reasoning Scenarios', () => {
    let cot: ChainOfThought;
    let tot: TreeOfThought;

    beforeAll(() => {
      const engine = createReasoningEngine(client, model);
      cot = engine.chainOfThought;
      tot = engine.treeOfThought;
    });

    it('should reason about BDD scenario structure using CoT', async () => {
      const prompt = 'How should I convert this Playwright recording to BDD?';
      const context = `
        Recording:
        - page.goto('https://app.com')
        - page.click('text=Login')
        - page.fill('#email', 'user@test.com')
        - page.fill('#password', 'password123')
        - page.click('button[type=submit]')
        - page.waitForSelector('text=Welcome')
      `;

      const result = await cot.reason(prompt, context, { maxSteps: 4 });

      expect(result.finalAnswer).toBeTruthy();
      expect(result.steps.length).toBeGreaterThan(0);

      // Verify reasoning is relevant to BDD
      const reasoning = JSON.stringify(result).toLowerCase();
      const hasRelevantTerms =
        reasoning.includes('given') ||
        reasoning.includes('when') ||
        reasoning.includes('then') ||
        reasoning.includes('scenario') ||
        reasoning.includes('feature');

      expect(hasRelevantTerms).toBe(true);

      console.log('\n=== BDD Conversion Reasoning ===');
      console.log(JSON.stringify(result, null, 2));
    }, 30000);

    it('should explore multiple test strategies using ToT', async () => {
      const prompt = 'What are the best ways to test a file upload feature?';
      const context = `
        Feature: Users can upload profile pictures
        Requirements:
        - Support JPEG, PNG formats
        - Max size 5MB
        - Validate dimensions
        - Show preview before upload
      `;

      const result = await tot.reason(prompt, context, {
        branchingFactor: 3,
        maxDepth: 2,
        evaluationCriteria: 'comprehensiveness and practicality'
      });

      expect(result.allPaths.length).toBeGreaterThan(0);
      expect(result.bestPath.length).toBeGreaterThan(0);

      console.log('\n=== File Upload Test Strategies ===');
      console.log(`Explored ${result.allPaths.length} different approaches`);
      console.log('Selected approach:', result.reasoning);
    }, 60000);

    it('should use Program of Thought reasoning for complex logic', async () => {
      // Simulate PoT by asking AI to generate executable reasoning
      const prompt = 'Calculate optimal test data set size for this scenario';
      const context = `
        Test: Form validation with 5 fields
        Each field: 3 states (empty, invalid, valid)
        Need: Representative coverage without exhaustive testing
      `;

      const result = await cot.reason(prompt, context, { maxSteps: 5 });

      expect(result.finalAnswer).toBeTruthy();

      // Verify reasoning includes calculation/logic
      const reasoning = JSON.stringify(result);
      const hasQuantitativeReasoning =
        reasoning.match(/\d+/g) !== null; // Contains numbers

      expect(hasQuantitativeReasoning).toBe(true);

      console.log('\n=== Program of Thought Reasoning ===');
      console.log(JSON.stringify(result, null, 2));
    }, 30000);
  });

  describe('Error Handling', () => {
    let cot: ChainOfThought;

    beforeAll(() => {
      const engine = createReasoningEngine(client, model);
      cot = engine.chainOfThought;
    });

    it('should handle API errors gracefully', async () => {
      // Create client with invalid key to trigger error
      const badClient = new Anthropic({ apiKey: 'sk-ant-invalid-key' });
      const badCoT = new ChainOfThought(badClient, model);

      await expect(
        badCoT.reason('test prompt', 'test context')
      ).rejects.toThrow();
    }, 10000);

    it('should handle empty responses', async () => {
      const result = await cot.reason('', '', { maxSteps: 1 });

      // Should still return valid structure even with empty input
      expect(result).toHaveProperty('steps');
      expect(result).toHaveProperty('finalAnswer');
      expect(result).toHaveProperty('reasoning');
    }, 30000);
  });
});
