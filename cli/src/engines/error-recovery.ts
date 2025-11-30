/**
 * Comprehensive Error Recovery Engine
 *
 * Program of Thoughts Implementation:
 * 1. Categorize errors by type (network, API, validation, etc.)
 * 2. Determine if error is recoverable
 * 3. Apply appropriate recovery strategy
 * 4. Track recovery attempts and success rates
 * 5. Provide user guidance for unrecoverable errors
 *
 * Uplift Feature: PILLAR 4 - Framework Resilience (ROI: 9.8/10)
 * Addresses: Multiple P0/P1 failures (FAILURE-007, 008, BUG-006, etc.)
 */

import { Logger } from '../utils/logger';

/**
 * Error categories for classification
 */
export enum ErrorCategory {
  NETWORK = 'network',
  API = 'api',
  VALIDATION = 'validation',
  FILE_SYSTEM = 'file_system',
  PARSING = 'parsing',
  GENERATION = 'generation',
  PERMISSION = 'permission',
  RESOURCE = 'resource'
}

/**
 * Error context for detailed diagnostics
 */
export interface ErrorContext {
  category: ErrorCategory;
  operation: string;
  recoverable: boolean;
  userAction?: string;
  technicalDetails: any;
  attemptNumber?: number;
  timestamp?: Date;
}

/**
 * Recovery result
 */
export interface RecoveryResult {
  success: boolean;
  result?: any;
  error?: Error;
  attemptsUsed: number;
  recoveryStrategy?: string;
}

/**
 * Framework error with rich context
 */
export class FrameworkError extends Error {
  constructor(
    message: string,
    public context: ErrorContext
  ) {
    super(message);
    this.name = 'FrameworkError';
    this.context.timestamp = new Date();
  }

  toString(): string {
    const lines = [
      '',
      '═'.repeat(70),
      '❌ FRAMEWORK ERROR',
      '═'.repeat(70),
      '',
      `Category: ${this.context.category}`,
      `Operation: ${this.context.operation}`,
      `Error: ${this.message}`,
      `Recoverable: ${this.context.recoverable ? 'Yes' : 'No'}`,
    ];

    if (this.context.userAction) {
      lines.push('', `💡 Action: ${this.context.userAction}`);
    }

    if (this.context.technicalDetails) {
      lines.push('', `Details: ${JSON.stringify(this.context.technicalDetails, null, 2)}`);
    }

    lines.push('', '═'.repeat(70), '');
    return lines.join('\n');
  }
}

/**
 * Error Recovery Engine
 *
 * PoT:
 * 1. Intercept errors
 * 2. Classify and analyze
 * 3. Attempt recovery if possible
 * 4. Track metrics
 * 5. Provide guidance
 */
export class ErrorRecoveryEngine {
  private recoveryAttempts: Map<string, number> = new Map();
  private recoveryStats: Map<ErrorCategory, { attempts: number; successes: number }> = new Map();

  /**
   * Handle error with automatic recovery
   *
   * PoT:
   * 1. Classify error
   * 2. Check if recoverable
   * 3. Apply recovery strategy
   * 4. Track attempts
   * 5. Return result or throw
   */
  async handleError<T>(
    error: Error | FrameworkError,
    operation: string,
    operationFn?: () => Promise<T>
  ): Promise<RecoveryResult> {

    // Convert to FrameworkError if needed
    const frameworkError = error instanceof FrameworkError
      ? error
      : this.classifyError(error, operation);

    // Log error
    Logger.error(`Error in ${frameworkError.context.operation}: ${frameworkError.message}`);

    // Update stats
    this.updateStats(frameworkError.context.category, false);

    // Attempt recovery if possible
    if (frameworkError.context.recoverable && operationFn) {
      const recovered = await this.attemptRecovery(frameworkError, operationFn);

      if (recovered.success) {
        Logger.success('✓ Error recovered automatically');
        this.updateStats(frameworkError.context.category, true);
        return recovered;
      }
    }

    // Provide user guidance
    this.provideUserGuidance(frameworkError);

    return {
      success: false,
      error: frameworkError,
      attemptsUsed: frameworkError.context.attemptNumber || 0
    };
  }

  /**
   * Classify error into category
   *
   * PoT:
   * 1. Analyze error message and type
   * 2. Check error code if available
   * 3. Determine category
   * 4. Set recoverability
   */
  private classifyError(error: Error, operation: string): FrameworkError {
    const message = error.message.toLowerCase();

    // Network errors
    if (
      message.includes('econnrefused') ||
      message.includes('econnreset') ||
      message.includes('etimedout') ||
      message.includes('network') ||
      message.includes('fetch failed')
    ) {
      return new FrameworkError(error.message, {
        category: ErrorCategory.NETWORK,
        operation,
        recoverable: true,
        userAction: 'Check your network connection and try again',
        technicalDetails: { originalError: error.message }
      });
    }

    // API errors
    if (
      message.includes('api') ||
      message.includes('rate limit') ||
      message.includes('quota') ||
      message.includes('401') ||
      message.includes('403')
    ) {
      return new FrameworkError(error.message, {
        category: ErrorCategory.API,
        operation,
        recoverable: message.includes('rate limit') || message.includes('500'),
        userAction: message.includes('401') || message.includes('403')
          ? 'Check your API key configuration'
          : 'Wait a moment and try again',
        technicalDetails: { originalError: error.message }
      });
    }

    // File system errors
    if (
      message.includes('enoent') ||
      message.includes('file not found') ||
      message.includes('eacces') ||
      message.includes('permission denied')
    ) {
      return new FrameworkError(error.message, {
        category: message.includes('eacces') || message.includes('permission')
          ? ErrorCategory.PERMISSION
          : ErrorCategory.FILE_SYSTEM,
        operation,
        recoverable: false,
        userAction: message.includes('eacces')
          ? 'Check file permissions and run with appropriate access'
          : 'Ensure the file path is correct',
        technicalDetails: { originalError: error.message }
      });
    }

    // Parsing errors
    if (
      message.includes('parse') ||
      message.includes('syntax') ||
      message.includes('unexpected token') ||
      message.includes('invalid json')
    ) {
      return new FrameworkError(error.message, {
        category: ErrorCategory.PARSING,
        operation,
        recoverable: false,
        userAction: 'Check the input file format is valid',
        technicalDetails: { originalError: error.message }
      });
    }

    // Validation errors
    if (
      message.includes('validation') ||
      message.includes('invalid') ||
      message.includes('missing required')
    ) {
      return new FrameworkError(error.message, {
        category: ErrorCategory.VALIDATION,
        operation,
        recoverable: false,
        userAction: 'Check input parameters and try again',
        technicalDetails: { originalError: error.message }
      });
    }

    // Default: unknown error (not recoverable by default)
    return new FrameworkError(error.message, {
      category: ErrorCategory.RESOURCE,
      operation,
      recoverable: false,
      userAction: 'Please report this error to the maintainers',
      technicalDetails: { originalError: error.message, stack: error.stack }
    });
  }

  /**
   * Attempt automatic recovery
   *
   * PoT:
   * 1. Determine recovery strategy based on category
   * 2. Execute recovery with retry logic
   * 3. Track attempts
   * 4. Return result
   */
  private async attemptRecovery<T>(
    error: FrameworkError,
    operationFn: () => Promise<T>
  ): Promise<RecoveryResult> {

    const operationKey = error.context.operation;
    const currentAttempts = this.recoveryAttempts.get(operationKey) || 0;

    switch (error.context.category) {
      case ErrorCategory.NETWORK:
        return this.recoverNetwork(error, operationFn, currentAttempts);

      case ErrorCategory.API:
        return this.recoverAPI(error, operationFn, currentAttempts);

      case ErrorCategory.FILE_SYSTEM:
        return this.recoverFileSystem(error, operationFn, currentAttempts);

      default:
        return {
          success: false,
          error,
          attemptsUsed: 0
        };
    }
  }

  /**
   * Recover from network errors
   *
   * PoT (Exponential backoff):
   * 1. Wait with exponential backoff
   * 2. Retry operation
   * 3. Max 3 retries
   * 4. Return result
   */
  private async recoverNetwork<T>(
    error: FrameworkError,
    operationFn: () => Promise<T>,
    currentAttempts: number
  ): Promise<RecoveryResult> {

    const maxRetries = 3;

    for (let i = 0; i < maxRetries; i++) {
      const delay = Math.pow(2, i) * 1000; // 1s, 2s, 4s
      Logger.info(`Retrying in ${delay/1000}s... (attempt ${i+1}/${maxRetries})`);

      await this.sleep(delay);

      try {
        const result = await operationFn();
        return {
          success: true,
          result,
          attemptsUsed: i + 1,
          recoveryStrategy: 'exponential_backoff'
        };
      } catch (retryError) {
        if (i === maxRetries - 1) {
          return {
            success: false,
            error: retryError instanceof Error ? retryError : new Error(String(retryError)),
            attemptsUsed: maxRetries,
            recoveryStrategy: 'exponential_backoff'
          };
        }
      }
    }

    return { success: false, error, attemptsUsed: maxRetries };
  }

  /**
   * Recover from API errors (rate limiting)
   *
   * PoT:
   * 1. Check if rate limit error
   * 2. Wait longer (30s, 60s)
   * 3. Retry with exponential backoff
   */
  private async recoverAPI<T>(
    error: FrameworkError,
    operationFn: () => Promise<T>,
    currentAttempts: number
  ): Promise<RecoveryResult> {

    const isRateLimit = error.message.toLowerCase().includes('rate limit');

    if (isRateLimit) {
      const maxRetries = 2;

      for (let i = 0; i < maxRetries; i++) {
        const delay = (i + 1) * 30 * 1000; // 30s, 60s
        Logger.info(`Rate limited. Waiting ${delay/1000}s before retry...`);

        await this.sleep(delay);

        try {
          const result = await operationFn();
          return {
            success: true,
            result,
            attemptsUsed: i + 1,
            recoveryStrategy: 'rate_limit_backoff'
          };
        } catch (retryError) {
          if (i === maxRetries - 1) {
            return {
              success: false,
              error: retryError instanceof Error ? retryError : new Error(String(retryError)),
              attemptsUsed: maxRetries
            };
          }
        }
      }
    }

    return { success: false, error, attemptsUsed: 0 };
  }

  /**
   * Recover from file system errors
   *
   * PoT:
   * 1. Check if file doesn't exist
   * 2. Try alternative paths
   * 3. Create directories if needed
   */
  private async recoverFileSystem<T>(
    error: FrameworkError,
    operationFn: () => Promise<T>,
    currentAttempts: number
  ): Promise<RecoveryResult> {

    // For now, file system errors are not auto-recoverable
    // Future: Could implement auto-directory creation, path resolution, etc.

    return { success: false, error, attemptsUsed: 0 };
  }

  /**
   * Provide user guidance for unrecoverable errors
   */
  private provideUserGuidance(error: FrameworkError): void {
    if (error.context.userAction) {
      Logger.info(`\n💡 ${error.context.userAction}\n`);
    }

    // Category-specific guidance
    switch (error.context.category) {
      case ErrorCategory.API:
        Logger.info('API Error Troubleshooting:');
        Logger.info('  1. Check your API key is set in .env file');
        Logger.info('  2. Verify you have API credits remaining');
        Logger.info('  3. Check API service status');
        break;

      case ErrorCategory.NETWORK:
        Logger.info('Network Error Troubleshooting:');
        Logger.info('  1. Check your internet connection');
        Logger.info('  2. Verify firewall settings');
        Logger.info('  3. Try again in a few moments');
        break;

      case ErrorCategory.PARSING:
        Logger.info('Parsing Error Troubleshooting:');
        Logger.info('  1. Verify recording file format is correct');
        Logger.info('  2. Re-generate the recording');
        Logger.info('  3. Check for special characters in file');
        break;
    }
  }

  /**
   * Update recovery statistics
   */
  private updateStats(category: ErrorCategory, success: boolean): void {
    const stats = this.recoveryStats.get(category) || { attempts: 0, successes: 0 };
    stats.attempts++;
    if (success) stats.successes++;
    this.recoveryStats.set(category, stats);
  }

  /**
   * Get recovery statistics
   */
  getStats(): Map<ErrorCategory, { attempts: number; successes: number; rate: number }> {
    const statsWithRate = new Map<ErrorCategory, { attempts: number; successes: number; rate: number }>();

    this.recoveryStats.forEach((stats, category) => {
      statsWithRate.set(category, {
        ...stats,
        rate: stats.attempts > 0 ? stats.successes / stats.attempts : 0
      });
    });

    return statsWithRate;
  }

  /**
   * Sleep utility
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Create a recoverable wrapper for operations
   *
   * Usage:
   * ```
   * const result = await errorEngine.withRecovery(
   *   'API call',
   *   () => apiClient.generate(...)
   * );
   * ```
   */
  async withRecovery<T>(
    operation: string,
    fn: () => Promise<T>
  ): Promise<T> {
    try {
      return await fn();
    } catch (error) {
      const result = await this.handleError(
        error instanceof Error ? error : new Error(String(error)),
        operation,
        fn
      );

      if (result.success && result.result !== undefined) {
        return result.result as T;
      }

      throw result.error || error;
    }
  }
}

/**
 * Global error recovery instance
 */
export const errorRecovery = new ErrorRecoveryEngine();
