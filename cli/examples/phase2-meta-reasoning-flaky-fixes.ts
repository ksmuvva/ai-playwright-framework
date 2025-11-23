/**
 * Examples of Phase 2 Advanced AI Features
 *
 * 1. Meta-Reasoning - AI that questions and validates itself
 * 2. Auto-Fix Flaky Tests - Automatically fix intermittent failures
 *
 * These features provide massive improvements in reliability and debugging efficiency.
 */

import { AnthropicClient } from '../src/ai/anthropic-client';
import { TestExecutionHistory } from '../src/types';

// ============================================================================
// PART 1: META-REASONING EXAMPLES
// ============================================================================

/**
 * Example 1: Basic Meta-Reasoning
 *
 * AI solves a problem and evaluates its own reasoning quality
 */
async function exampleBasicMetaReasoning() {
  console.log('\n🧠 Example 1: Basic Meta-Reasoning\n');

  const client = new AnthropicClient();

  const problem = `
    I have a test that sometimes fails with "Element not found: #submit-button".
    The button exists in the HTML but the test still fails randomly.
    What could be the issue?
  `;

  const result = await client.reasonWithMetaCognition(problem);

  console.log('Problem:', problem);
  console.log('\n=== AI Reasoning ===');
  console.log(result.reasoning);

  console.log('\n=== Final Answer ===');
  console.log(result.finalAnswer);

  console.log('\n=== Self-Evaluation ===');
  console.log(`Reasoning Quality: ${(result.selfEvaluation.reasoningQuality * 100).toFixed(0)}%`);
  console.log(`Confidence: ${(result.selfEvaluation.confidence * 100).toFixed(0)}%`);
  console.log(`Considered Alternatives: ${result.selfEvaluation.consideredAlternatives ? 'Yes' : 'No'}`);

  if (result.selfEvaluation.logicalGaps.length > 0) {
    console.log('\n⚠️  Logical Gaps Identified:');
    result.selfEvaluation.logicalGaps.forEach((gap, i) => {
      console.log(`  ${i + 1}. ${gap}`);
    });
  }

  if (result.selfEvaluation.uncertainties.length > 0) {
    console.log('\n🤔 Uncertainties:');
    result.selfEvaluation.uncertainties.forEach((u, i) => {
      console.log(`  ${i + 1}. ${u}`);
    });
  }

  console.log('\n✅ Strengths:');
  result.selfEvaluation.strengths.forEach((s, i) => {
    console.log(`  ${i + 1}. ${s}`);
  });

  if (result.selfEvaluation.weaknesses.length > 0) {
    console.log('\n⚠️  Weaknesses:');
    result.selfEvaluation.weaknesses.forEach((w, i) => {
      console.log(`  ${i + 1}. ${w}`);
    });
  }

  if (result.selfCorrection) {
    console.log('\n🔄 Self-Correction Applied:');
    console.log(`Initial Answer: ${result.selfCorrection.initialAnswer}`);
    console.log(`Detected Errors: ${result.selfCorrection.detectedErrors.join(', ')}`);
    console.log(`Corrected Answer: ${result.selfCorrection.correctedAnswer}`);
    console.log(`Improvement: ${result.selfCorrection.improvement}`);
  }
}

/**
 * Example 2: Adaptive Strategy Selection
 *
 * AI automatically selects the best reasoning strategy for a task
 */
async function exampleAdaptiveStrategy() {
  console.log('\n🎯 Example 2: Adaptive Strategy Selection\n');

  const client = new AnthropicClient();

  // Simple task
  const simpleTask = 'Generate a test for a login button click';
  const simpleStrategy = await client.selectReasoningStrategy(simpleTask);

  console.log('Simple Task:', simpleTask);
  console.log(`Selected Strategy: ${simpleStrategy.selectedStrategy.name}`);
  console.log(`Reasoning: ${simpleStrategy.reasoning}`);
  console.log(`Task Complexity: ${simpleStrategy.taskComplexity}`);

  // Complex task
  const complexTask = `
    Design a comprehensive test strategy for a payment system that:
    1. Handles multiple payment providers (Stripe, PayPal, Apple Pay)
    2. Supports recurring payments and refunds
    3. Integrates with inventory and shipping systems
    4. Must be PCI-DSS compliant
    5. Needs to handle edge cases like partial failures
  `;

  const complexStrategy = await client.selectReasoningStrategy(complexTask, {
    accuracyRequired: 'critical',
    maxCost: 'high'
  });

  console.log('\nComplex Task:', complexTask.substring(0, 100) + '...');
  console.log(`Selected Strategy: ${complexStrategy.selectedStrategy.name}`);
  console.log(`Reasoning: ${complexStrategy.reasoning}`);
  console.log(`Task Complexity: ${complexStrategy.taskComplexity}`);
  console.log(`Estimated Cost: ${complexStrategy.selectedStrategy.estimatedCost}`);
  console.log(`Estimated Accuracy: ${complexStrategy.selectedStrategy.estimatedAccuracy}`);
}

/**
 * Example 3: Adaptive Reasoning in Action
 *
 * AI automatically adjusts strategy based on confidence
 */
async function exampleAdaptiveReasoning() {
  console.log('\n🔄 Example 3: Adaptive Reasoning\n');

  const client = new AnthropicClient();

  const task = `
    Analyze this test failure pattern:
    - Monday: PASS
    - Tuesday: FAIL
    - Wednesday: PASS
    - Thursday: FAIL
    - Friday: PASS
    - Saturday: FAIL
    - Sunday: PASS

    What could cause this alternating pattern?
  `;

  console.log('Task:', task);
  console.log('\nExecuting with adaptive reasoning...\n');

  const result = await client.generateWithAdaptiveReasoning(task);

  console.log(`Strategy Used: ${result.strategyUsed}`);
  console.log(`\nResult: ${result.result}`);
  console.log(`\nConfidence: ${(result.metaInfo.selfEvaluation.confidence * 100).toFixed(0)}%`);

  if (result.strategyUsed.includes('auto-escalated')) {
    console.log('\n⚡ AI automatically escalated to a more robust strategy due to low confidence!');
  }
}

// ============================================================================
// PART 2: AUTO-FIX FLAKY TESTS EXAMPLES
// ============================================================================

/**
 * Example 4: Detect Single Flaky Test
 *
 * Analyze a test's execution history to detect flakiness
 */
async function exampleDetectFlakyTest() {
  console.log('\n🔍 Example 4: Detect Flaky Test\n');

  const client = new AnthropicClient();

  // Simulate test execution history
  const history: TestExecutionHistory = {
    testName: 'test_checkout_flow',
    runs: [
      { runId: '1', timestamp: new Date('2024-01-01'), result: 'pass', duration: 2500 },
      { runId: '2', timestamp: new Date('2024-01-02'), result: 'fail', duration: 3200, error: 'TimeoutError: #pay-button' },
      { runId: '3', timestamp: new Date('2024-01-03'), result: 'pass', duration: 2400 },
      { runId: '4', timestamp: new Date('2024-01-04'), result: 'fail', duration: 3500, error: 'TimeoutError: #pay-button' },
      { runId: '5', timestamp: new Date('2024-01-05'), result: 'pass', duration: 2600 },
      { runId: '6', timestamp: new Date('2024-01-06'), result: 'pass', duration: 2300 },
      { runId: '7', timestamp: new Date('2024-01-07'), result: 'fail', duration: 3100, error: 'TimeoutError: #pay-button' },
      { runId: '8', timestamp: new Date('2024-01-08'), result: 'pass', duration: 2500 },
      { runId: '9', timestamp: new Date('2024-01-09'), result: 'pass', duration: 2700 },
      { runId: '10', timestamp: new Date('2024-01-10'), result: 'fail', duration: 3400, error: 'TimeoutError: #pay-button' }
    ]
  };

  console.log(`Analyzing: ${history.testName}`);
  console.log(`Total runs: ${history.runs.length}`);

  const analysis = await client.detectFlakyTest(history.testName, history);

  console.log('\n=== Flakiness Analysis ===');
  console.log(`Is Flaky: ${analysis.isFlaky ? '❌ YES' : '✅ NO'}`);
  console.log(`Flakiness Score: ${(analysis.flakinessScore * 100).toFixed(0)}%`);
  console.log(`Confidence: ${(analysis.confidence * 100).toFixed(0)}%`);
  console.log(`Pattern: ${analysis.flakinessPattern}`);
  console.log(`Impact: ${analysis.impact.toUpperCase()}`);

  console.log('\n=== Evidence ===');
  console.log(`Failure Rate: ${(analysis.evidence.failureRate * 100).toFixed(0)}%`);
  console.log(`Pass Rate: ${(analysis.evidence.passRate * 100).toFixed(0)}%`);
  console.log(`Total Runs: ${analysis.evidence.runs}`);

  console.log('\n=== Root Causes ===');
  analysis.rootCauses.forEach((cause, i) => {
    console.log(`\n${i + 1}. ${cause.cause}`);
    console.log(`   Confidence: ${(cause.confidence * 100).toFixed(0)}%`);
    console.log(`   Category: ${cause.category}`);
    console.log(`   Evidence:`);
    cause.evidence.forEach(e => console.log(`     - ${e}`));
  });
}

/**
 * Example 5: Fix Flaky Test
 *
 * Generate executable fix for a flaky test
 */
async function exampleFixFlakyTest() {
  console.log('\n🔧 Example 5: Fix Flaky Test\n');

  const client = new AnthropicClient();

  const testName = 'test_checkout_flow';

  const testCode = `
def test_checkout_flow(page):
    # Navigate to checkout
    page.goto('https://example.com/checkout')

    # Fill payment details
    page.fill('#card-number', '4111111111111111')
    page.fill('#expiry', '12/25')
    page.fill('#cvv', '123')

    # Click pay button
    page.click('#pay-button')  # ← FLAKY: Sometimes fails here

    # Verify success
    assert page.locator('.success-message').is_visible()
  `;

  const analysis = {
    testName,
    isFlaky: true,
    flakinessScore: 0.4,
    confidence: 0.92,
    flakinessPattern: 'race-condition' as const,
    evidence: {
      failureRate: 0.4,
      passRate: 0.6,
      runs: 10,
      consecutiveFailures: 2,
      consecutivePasses: 3
    },
    rootCauses: [
      {
        cause: 'Payment button not always loaded before click',
        confidence: 0.9,
        category: 'timing' as const,
        evidence: ['TimeoutError in 40% of runs', 'Slower in failing runs']
      }
    ],
    impact: 'high' as const
  };

  console.log(`Fixing: ${testName}`);
  console.log(`Current flakiness: ${(analysis.flakinessScore * 100).toFixed(0)}%\n`);

  const fix = await client.fixFlakyTest(testName, testCode, analysis);

  console.log('=== Generated Fix ===\n');

  console.log('Issues Found:');
  fix.fixes.forEach((f, i) => {
    console.log(`\n${i + 1}. ${f.issue}`);
    console.log(`   Type: ${f.type}`);
    console.log(`   Fix: ${f.fix}`);
    console.log(`   Explanation: ${f.explanation}`);
    if (f.lineNumber) {
      console.log(`   Line: ${f.lineNumber}`);
    }
  });

  console.log('\n=== Fixed Code ===');
  console.log(fix.fixedCode);

  console.log('\n=== Expected Results ===');
  console.log(`Fix Confidence: ${(fix.confidence * 100).toFixed(0)}%`);
  console.log(`Expected Improvement: ${(fix.expectedImprovement * 100).toFixed(0)}%`);
  console.log(`New Flakiness Rate: ~${((1 - fix.expectedImprovement) * analysis.flakinessScore * 100).toFixed(0)}%`);

  console.log('\n=== Test Plan ===');
  console.log(fix.testPlan);

  if (fix.additionalRecommendations.length > 0) {
    console.log('\n=== Additional Recommendations ===');
    fix.additionalRecommendations.forEach((rec, i) => {
      console.log(`${i + 1}. ${rec}`);
    });
  }
}

/**
 * Example 6: Batch Flaky Test Detection
 *
 * Analyze entire test suite for flakiness
 */
async function exampleBatchFlakyDetection() {
  console.log('\n📊 Example 6: Batch Flaky Test Detection\n');

  const client = new AnthropicClient();

  // Simulate test suite execution histories
  const testHistories: TestExecutionHistory[] = [
    {
      testName: 'test_login',
      runs: generateMockRuns(20, 0.95) // 95% pass rate
    },
    {
      testName: 'test_checkout',
      runs: generateMockRuns(20, 0.60) // 60% pass rate (FLAKY)
    },
    {
      testName: 'test_search',
      runs: generateMockRuns(20, 0.98) // 98% pass rate
    },
    {
      testName: 'test_api_call',
      runs: generateMockRuns(20, 0.55) // 55% pass rate (VERY FLAKY)
    },
    {
      testName: 'test_navigation',
      runs: generateMockRuns(20, 1.00) // 100% pass rate (STABLE)
    }
  ];

  console.log(`Analyzing ${testHistories.length} tests...\n`);

  const result = await client.detectFlakyTests(testHistories);

  console.log('=== Detection Results ===');
  console.log(`Total Tests: ${result.totalTests}`);
  console.log(`Flaky Tests Found: ${result.flakyTests.length}`);
  console.log(`Flakiness Rate: ${result.flakinessRate.toFixed(1)}%\n`);

  console.log('=== Flaky Tests (sorted by severity) ===');
  result.flakyTests.forEach((test, i) => {
    console.log(`\n${i + 1}. ${test.testName}`);
    console.log(`   Flakiness Score: ${(test.flakinessScore * 100).toFixed(0)}%`);
    console.log(`   Pattern: ${test.flakinessPattern}`);
    console.log(`   Impact: ${test.impact.toUpperCase()}`);
    console.log(`   Root Cause: ${test.rootCauses[0]?.cause || 'Unknown'}`);
  });

  console.log('\n=== Recommendations ===');

  if (result.recommendations.highPriority.length > 0) {
    console.log('\n🔴 High Priority (Fix Immediately):');
    result.recommendations.highPriority.forEach(test => {
      console.log(`   - ${test}`);
    });
  }

  if (result.recommendations.mediumPriority.length > 0) {
    console.log('\n🟡 Medium Priority (Fix Soon):');
    result.recommendations.mediumPriority.forEach(test => {
      console.log(`   - ${test}`);
    });
  }

  console.log('\n=== Common Patterns ===');
  result.recommendations.patterns.forEach(pattern => {
    console.log(`   • ${pattern}`);
  });
}

/**
 * Example 7: Auto-Fix Multiple Flaky Tests
 *
 * Automatically generate fixes for all flaky tests
 */
async function exampleAutoFixBatch() {
  console.log('\n🔧 Example 7: Auto-Fix Multiple Flaky Tests\n');

  const client = new AnthropicClient();

  // Mock detection result
  const detectionResult = {
    totalTests: 5,
    flakyTests: [
      {
        testName: 'test_checkout',
        isFlaky: true,
        flakinessScore: 0.4,
        confidence: 0.92,
        flakinessPattern: 'race-condition' as const,
        evidence: {
          failureRate: 0.4,
          passRate: 0.6,
          runs: 20,
          consecutiveFailures: 2,
          consecutivePasses: 3
        },
        rootCauses: [
          {
            cause: 'Button not loaded',
            confidence: 0.9,
            category: 'timing' as const,
            evidence: ['TimeoutError']
          }
        ],
        impact: 'high' as const
      },
      {
        testName: 'test_api_call',
        isFlaky: true,
        flakinessScore: 0.45,
        confidence: 0.88,
        flakinessPattern: 'intermittent' as const,
        evidence: {
          failureRate: 0.45,
          passRate: 0.55,
          runs: 20,
          consecutiveFailures: 3,
          consecutivePasses: 2
        },
        rootCauses: [
          {
            cause: 'Network timeout',
            confidence: 0.85,
            category: 'resource' as const,
            evidence: ['ConnectionError']
          }
        ],
        impact: 'critical' as const
      }
    ],
    flakinessRate: 40,
    recommendations: {
      highPriority: ['test_api_call'],
      mediumPriority: ['test_checkout'],
      patterns: ['55% are timing_related']
    }
  };

  // Mock test code
  const testCodeMap = new Map([
    ['test_checkout', 'def test_checkout(page): page.click("#button")'],
    ['test_api_call', 'def test_api_call(): response = requests.get("http://api.com")']
  ]);

  console.log(`Auto-fixing ${detectionResult.flakyTests.length} flaky tests...\n`);

  const fixes = await client.autoFixFlakyTests(detectionResult, testCodeMap);

  console.log(`\n✅ Generated ${fixes.length} fixes\n`);

  fixes.forEach((fix, i) => {
    console.log(`\n=== Fix ${i + 1}: ${fix.testName} ===`);
    console.log(`Confidence: ${(fix.confidence * 100).toFixed(0)}%`);
    console.log(`Expected Improvement: ${(fix.expectedImprovement * 100).toFixed(0)}%`);
    console.log(`Issues Fixed: ${fix.fixes.length}`);
    fix.fixes.forEach(f => {
      console.log(`   - ${f.issue}`);
    });
  });

  // Calculate overall improvement
  const avgImprovement = fixes.reduce((sum, f) => sum + f.expectedImprovement, 0) / fixes.length;
  console.log(`\n📈 Average Expected Improvement: ${(avgImprovement * 100).toFixed(0)}%`);
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Generate mock test runs with specified pass rate
 */
function generateMockRuns(count: number, passRate: number) {
  const runs = [];
  for (let i = 0; i < count; i++) {
    const isPass = Math.random() < passRate;
    runs.push({
      runId: `${i + 1}`,
      timestamp: new Date(Date.now() - (count - i) * 24 * 60 * 60 * 1000),
      result: isPass ? 'pass' as const : 'fail' as const,
      duration: isPass ? 2000 + Math.random() * 500 : 3000 + Math.random() * 500,
      error: isPass ? undefined : 'TimeoutError: Element not found',
      stackTrace: isPass ? undefined : 'at line 42'
    });
  }
  return runs;
}

// ============================================================================
// RUN ALL EXAMPLES
// ============================================================================

async function runAllExamples() {
  try {
    console.log('╔═══════════════════════════════════════════════════════════╗');
    console.log('║   Phase 2: Meta-Reasoning + Auto-Fix Flaky Tests         ║');
    console.log('╚═══════════════════════════════════════════════════════════╝');

    // Meta-Reasoning Examples
    await exampleBasicMetaReasoning();
    await exampleAdaptiveStrategy();
    await exampleAdaptiveReasoning();

    // Auto-Fix Flaky Tests Examples
    await exampleDetectFlakyTest();
    await exampleFixFlakyTest();
    await exampleBatchFlakyDetection();
    await exampleAutoFixBatch();

    console.log('\n╔═══════════════════════════════════════════════════════════╗');
    console.log('║   All examples completed successfully! ✅                 ║');
    console.log('╚═══════════════════════════════════════════════════════════╝\n');

  } catch (error) {
    console.error('Error running examples:', error);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  runAllExamples();
}

export {
  exampleBasicMetaReasoning,
  exampleAdaptiveStrategy,
  exampleAdaptiveReasoning,
  exampleDetectFlakyTest,
  exampleFixFlakyTest,
  exampleBatchFlakyDetection,
  exampleAutoFixBatch
};
