/**
 * Step Registry for Framework Injection
 *
 * ROOT CAUSE FIX (P1): Implements step tracking and reuse
 *
 * Purpose:
 * - Track existing step definitions across the framework
 * - Prevent duplicate steps
 * - Enable step reuse across scenarios
 * - Support incremental framework building
 *
 * Features:
 * - Scans existing step files
 * - Parses @given/@when/@then decorators
 * - Detects duplicate and similar steps
 * - Supports step merging
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import { Logger } from './logger';

export interface StepDefinition {
  pattern: string;           // Step pattern (e.g., "I am on the login page")
  decorator: 'given' | 'when' | 'then';  // Behave decorator type
  filePath: string;          // Source file containing this step
  lineNumber: number;        // Line number in source file
  functionName: string;      // Python function name
  hasParameters: boolean;    // True if step has parameters like {username}
  code: string;              // Full function code
}

export interface StepAnalysis {
  totalSteps: number;
  reusableSteps: string[];   // Steps that can be reused
  newStepsNeeded: string[];  // New steps that need to be created
  duplicates: string[];      // Duplicate step patterns found
}

export class StepRegistry {
  private steps: Map<string, StepDefinition>;
  private projectRoot: string;
  private stepsDirectory: string;
  private registryFile: string;
  private lockFile: string;

  constructor(projectRoot: string) {
    this.projectRoot = projectRoot;
    this.stepsDirectory = path.join(projectRoot, 'features', 'steps');
    this.registryFile = path.join(projectRoot, '.step-registry.json');
    this.lockFile = `${this.registryFile}.lock`;
    this.steps = new Map();
  }

  /**
   * Initialize registry by scanning existing step files
   */
  async initialize(): Promise<void> {
    Logger.info('Initializing Step Registry...');

    try {
      // Check if steps directory exists
      await fs.access(this.stepsDirectory);

      // Scan all Python files in steps directory
      const files = await this.findStepFiles();

      for (const file of files) {
        await this.parseStepFile(file);
      }

      Logger.info(`✓ Loaded ${this.steps.size} existing steps from ${files.length} files`);
    } catch (error) {
      // Directory doesn't exist - this is a new project
      Logger.info('No existing steps found - initializing new project');
    }
  }

  /**
   * Find all Python step files
   */
  private async findStepFiles(): Promise<string[]> {
    const files: string[] = [];

    try {
      const entries = await fs.readdir(this.stepsDirectory);

      for (const entry of entries) {
        if (entry.endsWith('.py') && entry !== '__init__.py') {
          files.push(path.join(this.stepsDirectory, entry));
        }
      }
    } catch (error) {
      // Directory doesn't exist
    }

    return files;
  }

  /**
   * Parse a step file and extract step definitions
   */
  private async parseStepFile(filePath: string): Promise<void> {
    try {
      const content = await fs.readFile(filePath, 'utf-8');
      const lines = content.split('\n');

      let currentDecorator: 'given' | 'when' | 'then' | null = null;
      let currentPattern: string | null = null;
      let currentFunctionName: string | null = null;
      let currentLineNumber = 0;
      let functionCode: string[] = [];
      let inFunction = false;
      let indentLevel = 0;

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trim();

        // Parse decorator (@given, @when, @then)
        const decoratorMatch = trimmed.match(/^@(given|when|then)\(['"](.+?)['"]\)/);
        if (decoratorMatch) {
          // Save previous function if any
          if (currentDecorator && currentPattern && currentFunctionName) {
            this.addStep({
              pattern: currentPattern,
              decorator: currentDecorator,
              filePath,
              lineNumber: currentLineNumber,
              functionName: currentFunctionName,
              hasParameters: this.hasParameters(currentPattern),
              code: functionCode.join('\n')
            });
          }

          currentDecorator = decoratorMatch[1] as 'given' | 'when' | 'then';
          currentPattern = decoratorMatch[2];
          currentLineNumber = i + 1;
          functionCode = [line];
          inFunction = false;
          continue;
        }

        // Parse function definition
        if (currentDecorator && trimmed.startsWith('def ')) {
          const funcMatch = trimmed.match(/def\s+(\w+)\(/);
          if (funcMatch) {
            currentFunctionName = funcMatch[1];
            functionCode.push(line);
            inFunction = true;
            indentLevel = line.search(/\S/);  // Get indentation level
            continue;
          }
        }

        // Collect function body
        if (inFunction) {
          const currentIndent = line.search(/\S/);

          // End of function (dedent or empty line followed by dedent)
          if (trimmed && currentIndent > 0 && currentIndent <= indentLevel) {
            // Save function
            if (currentDecorator && currentPattern && currentFunctionName) {
              this.addStep({
                pattern: currentPattern,
                decorator: currentDecorator,
                filePath,
                lineNumber: currentLineNumber,
                functionName: currentFunctionName,
                hasParameters: this.hasParameters(currentPattern),
                code: functionCode.join('\n')
              });
            }

            // Reset
            currentDecorator = null;
            currentPattern = null;
            currentFunctionName = null;
            functionCode = [];
            inFunction = false;
          } else {
            functionCode.push(line);
          }
        }
      }

      // Save last function if any
      if (currentDecorator && currentPattern && currentFunctionName) {
        this.addStep({
          pattern: currentPattern,
          decorator: currentDecorator,
          filePath,
          lineNumber: currentLineNumber,
          functionName: currentFunctionName,
          hasParameters: this.hasParameters(currentPattern),
          code: functionCode.join('\n')
        });
      }

    } catch (error) {
      Logger.warning(`Could not parse step file ${filePath}: ${error}`);
    }
  }

  /**
   * Add a step to registry
   */
  private addStep(step: StepDefinition): void {
    const key = this.normalizePattern(step.pattern);

    if (this.steps.has(key)) {
      const existing = this.steps.get(key)!;
      Logger.warning(
        `Duplicate step found:\n` +
        `  Pattern: "${step.pattern}"\n` +
        `  Existing: ${existing.filePath}:${existing.lineNumber}\n` +
        `  Duplicate: ${step.filePath}:${step.lineNumber}`
      );
    } else {
      this.steps.set(key, step);
    }
  }

  /**
   * Normalize step pattern for comparison
   */
  private normalizePattern(pattern: string): string {
    // Remove parameter placeholders for comparison
    // "I enter {username} and {password}" -> "I enter and"
    return pattern
      .replace(/\{[^}]+\}/g, '')     // Remove {param}
      .replace(/["'][^"']*["']/g, '') // Remove quoted strings
      .replace(/\s+/g, ' ')           // Normalize whitespace
      .trim()
      .toLowerCase();
  }

  /**
   * Check if pattern has parameters
   */
  private hasParameters(pattern: string): boolean {
    return /\{[^}]+\}/.test(pattern);
  }

  /**
   * Check if a step exists
   */
  stepExists(pattern: string): boolean {
    const key = this.normalizePattern(pattern);
    return this.steps.has(key);
  }

  /**
   * Get step definition
   */
  getStep(pattern: string): StepDefinition | undefined {
    const key = this.normalizePattern(pattern);
    return this.steps.get(key);
  }

  /**
   * Get all steps
   */
  getAllSteps(): StepDefinition[] {
    return Array.from(this.steps.values());
  }

  /**
   * Find similar steps (fuzzy matching)
   */
  findSimilarSteps(pattern: string, threshold: number = 0.7): StepDefinition[] {
    const normalized = this.normalizePattern(pattern);
    const similar: Array<{ step: StepDefinition; similarity: number }> = [];

    for (const step of this.steps.values()) {
      const stepNormalized = this.normalizePattern(step.pattern);
      const similarity = this.calculateSimilarity(normalized, stepNormalized);

      if (similarity >= threshold) {
        similar.push({ step, similarity });
      }
    }

    // Sort by similarity (highest first)
    similar.sort((a, b) => b.similarity - a.similarity);

    return similar.map(item => item.step);
  }

  /**
   * Calculate string similarity (Levenshtein distance based)
   */
  private calculateSimilarity(str1: string, str2: string): number {
    const maxLen = Math.max(str1.length, str2.length);
    if (maxLen === 0) return 1.0;

    const distance = this.levenshteinDistance(str1, str2);
    return 1.0 - distance / maxLen;
  }

  /**
   * Calculate Levenshtein distance between two strings
   */
  private levenshteinDistance(str1: string, str2: string): number {
    const m = str1.length;
    const n = str2.length;
    const dp: number[][] = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));

    for (let i = 0; i <= m; i++) dp[i][0] = i;
    for (let j = 0; j <= n; j++) dp[0][j] = j;

    for (let i = 1; i <= m; i++) {
      for (let j = 1; j <= n; j++) {
        if (str1[i - 1] === str2[j - 1]) {
          dp[i][j] = dp[i - 1][j - 1];
        } else {
          dp[i][j] = 1 + Math.min(
            dp[i - 1][j],      // deletion
            dp[i][j - 1],      // insertion
            dp[i - 1][j - 1]   // substitution
          );
        }
      }
    }

    return dp[m][n];
  }

  /**
   * Analyze steps for a new scenario
   * Returns which steps can be reused and which are new
   */
  analyzeSteps(newSteps: string[]): StepAnalysis {
    const reusableSteps: string[] = [];
    const newStepsNeeded: string[] = [];

    for (const step of newSteps) {
      if (this.stepExists(step)) {
        reusableSteps.push(step);
      } else {
        newStepsNeeded.push(step);
      }
    }

    return {
      totalSteps: newSteps.length,
      reusableSteps,
      newStepsNeeded,
      duplicates: []
    };
  }

  /**
   * Get reuse statistics
   */
  getReuseStats(): { totalSteps: number; reusePercentage: number } {
    return {
      totalSteps: this.steps.size,
      reusePercentage: 0  // Will be calculated based on analysis
    };
  }

  /**
   * Export registry to JSON for debugging
   */
  exportToJSON(): string {
    const stepsArray = Array.from(this.steps.entries()).map(([key, step]) => ({
      key,
      pattern: step.pattern,
      decorator: step.decorator,
      filePath: step.filePath,
      lineNumber: step.lineNumber,
      functionName: step.functionName,
      hasParameters: step.hasParameters
    }));

    return JSON.stringify(stepsArray, null, 2);
  }

  /**
   * FAILURE-014 FIX: Acquire file lock with retry and timeout
   * Uses simple file-based locking without external dependencies
   */
  private async acquireLock(maxRetries: number = 10, retryDelayMs: number = 100): Promise<() => Promise<void>> {
    for (let i = 0; i < maxRetries; i++) {
      try {
        // Try to create lock file exclusively (fails if exists)
        await fs.writeFile(this.lockFile, process.pid.toString(), { flag: 'wx' });

        // Successfully acquired lock, return release function
        return async () => {
          try {
            await fs.unlink(this.lockFile);
          } catch (error) {
            // Lock file already removed or doesn't exist
          }
        };
      } catch (error: any) {
        if (error.code === 'EEXIST') {
          // Lock file exists, check if it's stale
          try {
            const lockContent = await fs.readFile(this.lockFile, 'utf-8');
            const lockPid = parseInt(lockContent, 10);

            // Check if process still exists (on Unix-like systems)
            try {
              process.kill(lockPid, 0); // Signal 0 checks existence without killing
              // Process exists, wait and retry
            } catch {
              // Process doesn't exist, remove stale lock
              await fs.unlink(this.lockFile);
              continue; // Retry acquiring lock
            }
          } catch {
            // Can't read lock file, assume it's stale
            try {
              await fs.unlink(this.lockFile);
            } catch {
              // Ignore
            }
          }

          // Wait before retry
          await new Promise(resolve => setTimeout(resolve, retryDelayMs));
        } else {
          throw error;
        }
      }
    }

    throw new Error('Failed to acquire registry lock after multiple retries');
  }

  /**
   * Internal: Save registry to file (caller must hold lock)
   */
  private async saveInternal(): Promise<void> {
    const data = this.exportToJSON();
    await fs.writeFile(this.registryFile, data, 'utf-8');
  }

  /**
   * Internal: Load registry from file (caller must hold lock)
   */
  private async loadInternal(): Promise<void> {
    try {
      const data = await fs.readFile(this.registryFile, 'utf-8');
      const stepsArray = JSON.parse(data);

      this.steps.clear();
      for (const item of stepsArray) {
        this.steps.set(item.key, {
          pattern: item.pattern,
          decorator: item.decorator,
          filePath: item.filePath,
          lineNumber: item.lineNumber,
          functionName: item.functionName,
          hasParameters: item.hasParameters,
          code: '' // Code not stored in registry
        });
      }
    } catch (error: any) {
      if (error.code !== 'ENOENT') {
        // File doesn't exist is OK, other errors are not
        throw error;
      }
    }
  }

  /**
   * FAILURE-014 FIX: Register new steps with file locking
   * Prevents race conditions when multiple processes update the registry
   */
  async registerSteps(patterns: string[]): Promise<void> {
    const release = await this.acquireLock();

    try {
      // Re-load to get latest state from disk
      await this.loadInternal();

      // Update steps
      for (const pattern of patterns) {
        const key = this.normalizePattern(pattern);
        if (!this.steps.has(key)) {
          this.steps.set(key, {
            pattern,
            decorator: 'when', // Default decorator
            filePath: '',
            lineNumber: 0,
            functionName: '',
            hasParameters: this.hasParameters(pattern),
            code: ''
          });
        }
      }

      // Save updated registry
      await this.saveInternal();
    } finally {
      await release();
    }
  }
}
