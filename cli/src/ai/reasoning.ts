/**
 * Advanced Reasoning Strategies for AI-Powered Test Generation
 *
 * This module implements:
 * 1. Chain of Thought (CoT) - Step-by-step reasoning
 * 2. Tree of Thought (ToT) - Multi-path exploration and evaluation
 */

import Anthropic from '@anthropic-ai/sdk';
import { Logger } from '../utils/logger';

// ===== Constants (QUALITY-004 fix) =====

/**
 * Default maximum number of reasoning steps for Chain of Thought
 */
const DEFAULT_MAX_REASONING_STEPS = 5;

/**
 * Default number of branches to explore in Tree of Thought
 */
const DEFAULT_BRANCHING_FACTOR = 3;

/**
 * Default maximum depth for Tree of Thought exploration
 */
const DEFAULT_MAX_DEPTH = 3;

/**
 * Bonus multiplier for deeper reasoning paths
 */
const DEPTH_BONUS_MULTIPLIER = 0.1;

// ===== Types =====

export interface ReasoningStep {
  step: number;
  thought: string;
  action?: string;
  result?: any;
  confidence?: number;
}

export interface ChainOfThoughtResult {
  steps: ReasoningStep[];
  finalAnswer: any;
  reasoning: string;
}

export interface ThoughtNode {
  id: string;
  thought: string;
  state: any;
  children: ThoughtNode[];
  evaluation: number;
  depth: number;
  isLeaf: boolean;
}

export interface TreeOfThoughtResult {
  bestPath: ThoughtNode[];
  allPaths: ThoughtNode[][];
  finalAnswer: any;
  reasoning: string;
}

export interface ReasoningConfig {
  maxSteps?: number;
  branchingFactor?: number;
  maxDepth?: number;
  evaluationCriteria?: string;
}

// ===== Chain of Thought (CoT) Implementation =====

export class ChainOfThought {
  private client: Anthropic;
  private model: string;

  constructor(client: Anthropic, model: string = 'claude-sonnet-4-5-20250929') {
    this.client = client;
    this.model = model;
  }

  /**
   * Execute Chain of Thought reasoning
   * Breaks down complex problems into sequential reasoning steps
   */
  async reason(
    prompt: string,
    context: string,
    config: ReasoningConfig = {}
  ): Promise<ChainOfThoughtResult> {
    const maxSteps = config.maxSteps || DEFAULT_MAX_REASONING_STEPS;

    const cotPrompt = this.buildCoTPrompt(prompt, context, maxSteps);

    try {
      const response = await this.client.messages.create({
        model: this.model,
        max_tokens: 4000,
        messages: [
          {
            role: 'user',
            content: cotPrompt
          }
        ]
      });

      const content = response.content[0];
      if (content.type !== 'text') {
        throw new Error('Unexpected response type from AI');
      }

      return this.parseCoTResponse(content.text);

    } catch (error) {
      Logger.error(`Chain of Thought reasoning failed: ${error}`);
      throw error;
    }
  }

  private buildCoTPrompt(prompt: string, context: string, maxSteps: number): string {
    return `You are an expert at systematic problem-solving using Chain of Thought reasoning.

Task: ${prompt}

Context: ${context}

Instructions:
1. Break down the problem into ${maxSteps} clear reasoning steps
2. For each step, explain your thought process
3. Build on previous steps to reach the final answer
4. Use logical, step-by-step thinking

Provide your response in the following JSON format:
{
  "steps": [
    {
      "step": 1,
      "thought": "Initial analysis and understanding of the problem...",
      "action": "What action to take based on this thought",
      "confidence": 0.9
    },
    // ... more steps
  ],
  "finalAnswer": "The complete solution or answer",
  "reasoning": "Summary of the reasoning process"
}

Begin your step-by-step analysis:`;
  }

  private parseCoTResponse(responseText: string): ChainOfThoughtResult {
    try {
      // Extract JSON from response (handle markdown code blocks)
      let jsonText = responseText.trim();

      // Remove markdown code block if present
      if (jsonText.startsWith('```')) {
        jsonText = jsonText.replace(/^```(?:json)?\n?/i, '').replace(/\n?```$/, '');
      }

      const parsed = JSON.parse(jsonText);

      return {
        steps: parsed.steps || [],
        finalAnswer: parsed.finalAnswer || null,
        reasoning: parsed.reasoning || ''
      };
    } catch (error) {
      Logger.error(`Failed to parse CoT response: ${error}`);
      // Return fallback structure
      return {
        steps: [{ step: 1, thought: responseText }],
        finalAnswer: responseText,
        reasoning: 'Failed to parse structured response'
      };
    }
  }
}

// ===== Tree of Thought (ToT) Implementation =====

export class TreeOfThought {
  private client: Anthropic;
  private model: string;

  constructor(client: Anthropic, model: string = 'claude-sonnet-4-5-20250929') {
    this.client = client;
    this.model = model;
  }

  /**
   * Execute Tree of Thought reasoning
   * Explores multiple reasoning paths and selects the best one
   */
  async reason(
    prompt: string,
    context: string,
    config: ReasoningConfig = {}
  ): Promise<TreeOfThoughtResult> {
    const branchingFactor = config.branchingFactor || DEFAULT_BRANCHING_FACTOR;
    const maxDepth = config.maxDepth || DEFAULT_MAX_DEPTH;
    const evaluationCriteria = config.evaluationCriteria || 'correctness and completeness';

    try {
      // Generate initial thought branches
      const rootNode: ThoughtNode = {
        id: 'root',
        thought: 'Analyzing problem...',
        state: { prompt, context },
        children: [],
        evaluation: 0,
        depth: 0,
        isLeaf: false
      };

      // Expand tree with multiple reasoning paths
      await this.expandNode(rootNode, branchingFactor, maxDepth, evaluationCriteria);

      // Find all paths from root to leaves
      const allPaths = this.getAllPaths(rootNode);

      // Evaluate and select best path
      const bestPath = this.selectBestPath(allPaths);

      // Extract final answer from best path
      const finalAnswer = await this.synthesizeFinalAnswer(bestPath, prompt, context);

      return {
        bestPath,
        allPaths,
        finalAnswer,
        reasoning: this.buildReasoningExplanation(bestPath)
      };

    } catch (error) {
      Logger.error(`Tree of Thought reasoning failed: ${error}`);
      throw error;
    }
  }

  private async expandNode(
    node: ThoughtNode,
    branchingFactor: number,
    maxDepth: number,
    evaluationCriteria: string
  ): Promise<void> {
    if (node.depth >= maxDepth) {
      node.isLeaf = true;
      return;
    }

    // Generate alternative thoughts/approaches
    const thoughts = await this.generateThoughts(node, branchingFactor);

    // Create child nodes for each thought
    for (const thought of thoughts) {
      const childNode: ThoughtNode = {
        id: `${node.id}-${node.children.length}`,
        thought: thought.text,
        state: thought.state,
        children: [],
        evaluation: thought.evaluation,
        depth: node.depth + 1,
        isLeaf: false
      };

      node.children.push(childNode);

      // Recursively expand promising nodes
      if (thought.evaluation > 0.5) {
        await this.expandNode(childNode, branchingFactor, maxDepth, evaluationCriteria);
      } else {
        childNode.isLeaf = true;
      }
    }
  }

  private async generateThoughts(
    node: ThoughtNode,
    branchingFactor: number
  ): Promise<Array<{ text: string; state: any; evaluation: number }>> {
    const prompt = `Given the current reasoning state:
${JSON.stringify(node.state, null, 2)}

Current thought: ${node.thought}

Generate ${branchingFactor} different alternative reasoning approaches or next steps.
Each should explore a different angle or strategy.

Provide your response in JSON format:
{
  "thoughts": [
    {
      "text": "Description of this reasoning approach",
      "evaluation": 0.85,
      "state": { "updated": "state" }
    }
  ]
}`;

    try {
      const response = await this.client.messages.create({
        model: this.model,
        max_tokens: 2000,
        messages: [{ role: 'user', content: prompt }]
      });

      const content = response.content[0];
      if (content.type !== 'text') {
        throw new Error('Unexpected response type');
      }

      let jsonText = content.text.trim();
      if (jsonText.startsWith('```')) {
        jsonText = jsonText.replace(/^```(?:json)?\n?/i, '').replace(/\n?```$/, '');
      }

      const parsed = JSON.parse(jsonText);
      return parsed.thoughts || [];

    } catch (error) {
      Logger.warning(`Failed to generate thoughts: ${error}`);
      // Return fallback thoughts
      return [
        { text: 'Continue with current approach', state: node.state, evaluation: 0.6 }
      ];
    }
  }

  private getAllPaths(node: ThoughtNode, currentPath: ThoughtNode[] = []): ThoughtNode[][] {
    const newPath = [...currentPath, node];

    if (node.isLeaf || node.children.length === 0) {
      return [newPath];
    }

    const allPaths: ThoughtNode[][] = [];
    for (const child of node.children) {
      const childPaths = this.getAllPaths(child, newPath);
      allPaths.push(...childPaths);
    }

    return allPaths;
  }

  private selectBestPath(paths: ThoughtNode[][]): ThoughtNode[] {
    let bestPath = paths[0];
    let bestScore = 0;

    for (const path of paths) {
      // Calculate path score (average evaluation + depth bonus)
      const avgEval = path.reduce((sum, node) => sum + node.evaluation, 0) / path.length;
      const depthBonus = path.length * DEPTH_BONUS_MULTIPLIER; // Prefer deeper, more thorough reasoning
      const score = avgEval + depthBonus;

      if (score > bestScore) {
        bestScore = score;
        bestPath = path;
      }
    }

    return bestPath;
  }

  private async synthesizeFinalAnswer(
    path: ThoughtNode[],
    originalPrompt: string,
    context: string
  ): Promise<any> {
    const pathDescription = path.map((node, i) =>
      `Step ${i + 1}: ${node.thought}`
    ).join('\n');

    const synthesisPrompt = `Based on this reasoning path:

${pathDescription}

Original task: ${originalPrompt}
Context: ${context}

Synthesize the final answer or solution based on this reasoning path.
Provide a clear, actionable result.`;

    try {
      const response = await this.client.messages.create({
        model: this.model,
        max_tokens: 2000,
        messages: [{ role: 'user', content: synthesisPrompt }]
      });

      const content = response.content[0];
      if (content.type === 'text') {
        return content.text;
      }
    } catch (error) {
      Logger.warning(`Failed to synthesize final answer: ${error}`);
    }

    return path[path.length - 1].thought;
  }

  private buildReasoningExplanation(path: ThoughtNode[]): string {
    return path.map((node, i) => {
      const prefix = i === 0 ? '🌱 Initial:' :
                     i === path.length - 1 ? '🎯 Conclusion:' :
                     `🔗 Step ${i}:`;
      return `${prefix} ${node.thought}`;
    }).join('\n\n');
  }
}

// ===== Factory Function =====

/**
 * Create reasoning instances with proper configuration
 */
export function createReasoningEngine(
  client: Anthropic,
  model: string = 'claude-sonnet-4-5-20250929'
) {
  return {
    chainOfThought: new ChainOfThought(client, model),
    treeOfThought: new TreeOfThought(client, model)
  };
}
