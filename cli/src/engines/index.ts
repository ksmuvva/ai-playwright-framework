/**
 * Framework Engines - Autonomous Intelligence Layer
 *
 * This module exports all framework engines that provide autonomous capabilities:
 * - Error Recovery: Automatic error handling and recovery
 * - Incremental Updates: Fast framework updates without full regeneration
 * - Autonomous Maintenance: Self-healing tests and automatic fixes
 * - Semantic Reuse: Intelligent code reuse across features
 * - Self-Improvement: Framework learns and optimizes itself
 *
 * Uplift Implementation: All 4 Strategic Pillars
 * - Pillar 1: Autonomous Framework Evolution
 * - Pillar 2: Recording Intelligence (parsers)
 * - Pillar 3: Reusability Maximization
 * - Pillar 4: Framework Resilience
 */

// Error Recovery Engine
export {
  ErrorRecoveryEngine,
  errorRecovery,
  FrameworkError,
  ErrorCategory,
  type ErrorContext,
  type RecoveryResult
} from './error-recovery';

// Incremental Update Engine
export {
  IncrementalUpdateEngine,
  type ComponentType,
  type MergeStrategy,
  type DependencyNode,
  type FrameworkDependencyGraph,
  type UpdatePlan,
  type UpdateResult
} from './incremental-update';

// Autonomous Test Maintenance
export {
  AutonomousTestMaintainer,
  autonomousMaintainer,
  type FailureType,
  type TestFailureAnalysis,
  type Fix,
  type TestResult,
  type MaintenanceReport
} from './autonomous-maintenance';

// Semantic Reuse Engine
export {
  SemanticReuseEngine,
  semanticReuse,
  type StepDefinition,
  type ReusableStep,
  type ReuseStatistics
} from './semantic-reuse';

// Self-Improvement Engine
export {
  SelfImprovementEngine,
  selfImprovement,
  type UsageMetrics,
  type Optimization,
  type UsagePattern,
  type ImprovementReport
} from './self-improvement';

/**
 * Quick access to all global engine instances
 */
import { errorRecovery as errorRecoveryInstance } from './error-recovery';
import { autonomousMaintainer as autonomousMaintainerInstance } from './autonomous-maintenance';
import { semanticReuse as semanticReuseInstance } from './semantic-reuse';
import { selfImprovement as selfImprovementInstance } from './self-improvement';

export const engines = {
  errorRecovery: errorRecoveryInstance,
  autonomousMaintainer: autonomousMaintainerInstance,
  semanticReuse: semanticReuseInstance,
  selfImprovement: selfImprovementInstance
};

/**
 * Engine capabilities summary
 */
export const CAPABILITIES = {
  errorRecovery: {
    name: 'Error Recovery Engine',
    purpose: 'Automatic error handling with retry logic',
    features: [
      'Network error recovery with exponential backoff',
      'API rate limit handling',
      'Automatic retry with smart delays',
      'User guidance for unrecoverable errors'
    ],
    roi: 9.8
  },
  incrementalUpdate: {
    name: 'Incremental Update Engine',
    purpose: '90% faster framework updates',
    features: [
      'Dependency tracking',
      'Smart merge strategies',
      'Backup and rollback support',
      'Preserves user customizations'
    ],
    roi: 8.5
  },
  autonomousMaintenance: {
    name: 'Autonomous Test Maintenance',
    purpose: 'Self-healing tests with 80% automation',
    features: [
      'Automatic failure analysis',
      'Locator healing',
      'Timing issue fixes',
      'Pattern learning'
    ],
    roi: 9.0
  },
  semanticReuse: {
    name: 'Semantic Reuse Engine',
    purpose: '95% code reuse through semantic analysis',
    features: [
      'Semantic similarity matching',
      'Cross-feature reuse',
      'Adaptation suggestions',
      'Usage tracking'
    ],
    roi: 7.8
  },
  selfImprovement: {
    name: 'Self-Improvement Engine',
    purpose: 'Framework learns and optimizes itself',
    features: [
      'Usage pattern analysis',
      'Performance optimization',
      'Code cleanup suggestions',
      'Automatic improvements'
    ],
    roi: 7.0
  }
};
