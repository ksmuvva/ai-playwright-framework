/**
 * Examples of using advanced AI features in the Playwright Framework
 *
 * Phase 1: Quick Wins
 * 1. Prompt Caching - 90% cost reduction
 * 2. Streaming Responses - Real-time feedback
 * 3. Function Calling - AI can execute tools
 * 4. Root Cause Analysis - Deep failure understanding
 * 5. Failure Clustering - Group related failures
 */

import { AnthropicClient } from '../src/ai/anthropic-client';
import { ToolDefinition } from '../src/types';
import * as fs from 'fs';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

// ============================================================================
// Example 1: Using Prompt Caching for Cost Savings
// ============================================================================

async function examplePromptCaching() {
  console.log('\n📊 Example 1: Prompt Caching\n');

  const client = new AnthropicClient();

  // The system prompt will be cached for 5 minutes
  // First call: pays full price
  // Subsequent calls: 90% cheaper!

  const recording1 = [
    { type: 'navigate' as const, url: 'https://example.com/login' },
    { type: 'fill' as const, selector: '#email', value: 'user@example.com' },
    { type: 'click' as const, selector: '#submit' }
  ];

  console.log('First call (cache miss - full price)...');
  const result1 = await client.generateBDDScenario(recording1, 'Login Test 1');

  // Second call uses the cached system prompt (90% cheaper!)
  const recording2 = [
    { type: 'navigate' as const, url: 'https://example.com/signup' },
    { type: 'fill' as const, selector: '#name', value: 'John Doe' },
    { type: 'click' as const, selector: '#register' }
  ];

  console.log('\nSecond call (cache hit - 90% cheaper!)...');
  const result2 = await client.generateBDDScenario(recording2, 'Signup Test');

  console.log('\n✅ Prompt caching saved ~90% on the second call!');
  console.log('💡 The system prompt (BDD conversion instructions) is cached for 5 minutes');
}

// ============================================================================
// Example 2: Streaming Responses for Real-Time Feedback
// ============================================================================

async function exampleStreaming() {
  console.log('\n⚡ Example 2: Streaming Responses\n');

  const client = new AnthropicClient();

  const recording = [
    { type: 'navigate' as const, url: 'https://example.com' },
    { type: 'click' as const, selector: '.product' },
    { type: 'click' as const, selector: '.add-to-cart' },
    { type: 'click' as const, selector: '.checkout' },
    { type: 'fill' as const, selector: '#card-number', value: '4111111111111111' },
    { type: 'click' as const, selector: '#confirm-purchase' }
  ];

  console.log('Generating BDD scenario with streaming...\n');

  // Stream the response in real-time!
  const result = await client.generateBDDScenarioStream(
    recording,
    'E-commerce Checkout',
    (chunk: string) => {
      // This callback is called for each chunk as it's generated
      process.stdout.write(chunk);  // Real-time output!
    }
  );

  console.log('\n\n✅ Streaming complete! Better UX for long-running operations.');
}

// ============================================================================
// Example 3: Function Calling - AI Can Execute Tools
// ============================================================================

async function exampleFunctionCalling() {
  console.log('\n🛠️  Example 3: Function Calling / Tool Use\n');

  const client = new AnthropicClient();

  // Define tools that AI can use
  const tools: ToolDefinition[] = [
    {
      name: 'query_database',
      description: 'Execute SQL query against the test database',
      input_schema: {
        type: 'object',
        properties: {
          query: {
            type: 'string',
            description: 'SQL query to execute'
          },
          database: {
            type: 'string',
            description: 'Database name',
            enum: ['test', 'staging']
          }
        },
        required: ['query', 'database']
      }
    },
    {
      name: 'call_api',
      description: 'Make HTTP API call',
      input_schema: {
        type: 'object',
        properties: {
          method: {
            type: 'string',
            description: 'HTTP method',
            enum: ['GET', 'POST', 'PUT', 'DELETE']
          },
          endpoint: {
            type: 'string',
            description: 'API endpoint URL'
          },
          body: {
            type: 'object',
            description: 'Request body (for POST/PUT)'
          }
        },
        required: ['method', 'endpoint']
      }
    },
    {
      name: 'execute_shell',
      description: 'Run shell command',
      input_schema: {
        type: 'object',
        properties: {
          command: {
            type: 'string',
            description: 'Shell command to execute'
          }
        },
        required: ['command']
      }
    },
    {
      name: 'read_file',
      description: 'Read contents of a file',
      input_schema: {
        type: 'object',
        properties: {
          path: {
            type: 'string',
            description: 'File path to read'
          }
        },
        required: ['path']
      }
    }
  ];

  // Tool execution handler
  const handleToolCall = async (toolName: string, toolInput: any) => {
    console.log(`\n🔧 AI requested tool: ${toolName}`);
    console.log(`   Input:`, JSON.stringify(toolInput, null, 2));

    switch (toolName) {
      case 'query_database':
        // Simulate database query
        return {
          rows: [
            { id: 1, email: 'user@example.com', status: 'active' },
            { id: 2, email: 'admin@example.com', status: 'active' }
          ],
          count: 2
        };

      case 'call_api':
        // Simulate API call
        return {
          status: 200,
          data: { success: true, message: 'API call successful' }
        };

      case 'execute_shell':
        // Execute actual shell command (be careful!)
        try {
          const { stdout, stderr } = await execAsync(toolInput.command);
          return { stdout, stderr, exitCode: 0 };
        } catch (error: any) {
          return { stdout: '', stderr: error.message, exitCode: 1 };
        }

      case 'read_file':
        // Read actual file
        try {
          const content = fs.readFileSync(toolInput.path, 'utf-8');
          return { content, size: content.length };
        } catch (error: any) {
          return { error: error.message };
        }

      default:
        throw new Error(`Unknown tool: ${toolName}`);
    }
  };

  // AI can now use tools autonomously!
  const prompt = `
    I need to verify that the user 'user@example.com' exists in the test database,
    then create a test data file with their information.

    Use the available tools to:
    1. Query the database to find the user
    2. Read the template file at './templates/user_template.json'
    3. Create a test explaining what you found
  `;

  console.log('Prompt:', prompt);

  const result = await client.callWithTools(
    prompt,
    tools,
    handleToolCall
  );

  console.log('\n✅ AI completed the task autonomously using tools!');
  console.log('\nFinal result:', result);
}

// ============================================================================
// Example 4: Root Cause Analysis - Deep Failure Understanding
// ============================================================================

async function exampleRootCauseAnalysis() {
  console.log('\n🔍 Example 4: Root Cause Analysis\n');

  const client = new AnthropicClient();

  // Simulate a test failure
  const failureInfo = {
    testName: 'test_user_login',
    errorMessage: 'TimeoutError: Waiting for selector "#submit-button" failed: timeout 30000ms exceeded',
    stackTrace: `
      at Page.waitForSelector (/node_modules/playwright/lib/page.js:234:15)
      at test_user_login (/tests/auth.spec.ts:45:20)
    `,
    testCode: `
      await page.goto('https://example.com/login');
      await page.fill('#email', 'user@example.com');
      await page.fill('#password', 'password123');
      await page.click('#submit-button');  // ← Fails here
    `,
    pageHtml: `
      <html>
        <body>
          <form id="login-form">
            <input id="email" type="email">
            <input id="password" type="password">
            <button id="login-btn" disabled>Loading...</button>
          </form>
        </body>
      </html>
    `,
    previousFailures: [
      { testName: 'test_user_registration', error: 'TimeoutError: #create-account' },
      { testName: 'test_password_reset', error: 'TimeoutError: #reset-button' }
    ]
  };

  console.log('Analyzing failure...\n');

  const analysis = await client.analyzeRootCause(failureInfo);

  console.log('Root Cause Analysis:');
  console.log('===================');
  console.log(`\nSymptom: ${analysis.symptom}`);
  console.log(`Root Cause: ${analysis.rootCause}`);
  console.log(`Category: ${analysis.category}`);
  console.log(`Confidence: ${(analysis.confidence * 100).toFixed(0)}%`);
  console.log(`Impact: ${analysis.impact}`);

  console.log('\nEvidence:');
  analysis.evidence.forEach((e, i) => console.log(`  ${i + 1}. ${e}`));

  console.log('\nSuggested Fix:');
  console.log(analysis.suggestedFix.code);
  console.log(`\nExplanation: ${analysis.suggestedFix.explanation}`);

  if (analysis.suggestedFix.alternativeFixes.length > 0) {
    console.log('\nAlternative Fixes:');
    analysis.suggestedFix.alternativeFixes.forEach((fix, i) => {
      console.log(`\n  Option ${i + 1}:`);
      console.log(`  ${fix.code}`);
      console.log(`  Pros: ${fix.pros.join(', ')}`);
      console.log(`  Cons: ${fix.cons.join(', ')}`);
    });
  }

  console.log('\n✅ AI identified the root cause and suggested executable fixes!');
}

// ============================================================================
// Example 5: Failure Clustering - Group Related Failures
// ============================================================================

async function exampleFailureClustering() {
  console.log('\n📊 Example 5: Failure Clustering\n');

  const client = new AnthropicClient();

  // Simulate multiple test failures
  const failures = [
    {
      testName: 'test_login',
      errorMessage: 'TimeoutError: #submit-button',
      stackTrace: 'at Page.click'
    },
    {
      testName: 'test_signup',
      errorMessage: 'TimeoutError: #register-button',
      stackTrace: 'at Page.click'
    },
    {
      testName: 'test_checkout',
      errorMessage: 'TimeoutError: #pay-now-button',
      stackTrace: 'at Page.click'
    },
    {
      testName: 'test_profile_update',
      errorMessage: 'AssertionError: expected "John" to equal "Jane"',
      stackTrace: 'at expect'
    },
    {
      testName: 'test_settings_save',
      errorMessage: 'AssertionError: expected "dark" to equal "light"',
      stackTrace: 'at expect'
    },
    {
      testName: 'test_password_reset',
      errorMessage: 'NetworkError: Failed to fetch',
      stackTrace: 'at fetch'
    },
    {
      testName: 'test_email_verification',
      errorMessage: 'NetworkError: Connection refused',
      stackTrace: 'at request'
    }
  ];

  console.log(`Analyzing ${failures.length} test failures...\n`);

  const clustering = await client.clusterFailures(failures);

  console.log('Failure Clustering Results:');
  console.log('===========================');
  console.log(`Total Failures: ${clustering.totalFailures}`);
  console.log(`Unique Root Causes: ${clustering.uniqueRootCauses}`);
  console.log(`\nClusters:\n`);

  clustering.clusters.forEach((cluster, i) => {
    console.log(`Cluster ${i + 1}: ${cluster.rootCause}`);
    console.log(`  Failed Tests (${cluster.count}):`);
    cluster.failedTests.forEach(test => console.log(`    - ${test}`));
    console.log(`  Similarity: ${(cluster.similarity * 100).toFixed(0)}%`);
    console.log(`  Suggested Fix: ${cluster.suggestedFix}`);
    console.log('');
  });

  console.log('✅ AI grouped 7 failures into clusters by root cause!');
  console.log('💡 Fix one root cause → resolve multiple test failures');
}

// ============================================================================
// Run all examples
// ============================================================================

async function runAllExamples() {
  try {
    console.log('╔════════════════════════════════════════════════════════════╗');
    console.log('║   AI Playwright Framework - Advanced Features Demo        ║');
    console.log('╚════════════════════════════════════════════════════════════╝');

    await examplePromptCaching();
    await exampleStreaming();
    await exampleFunctionCalling();
    await exampleRootCauseAnalysis();
    await exampleFailureClustering();

    console.log('\n╔════════════════════════════════════════════════════════════╗');
    console.log('║   All examples completed successfully! ✅                  ║');
    console.log('╚════════════════════════════════════════════════════════════╝\n');

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
  examplePromptCaching,
  exampleStreaming,
  exampleFunctionCalling,
  exampleRootCauseAnalysis,
  exampleFailureClustering
};
