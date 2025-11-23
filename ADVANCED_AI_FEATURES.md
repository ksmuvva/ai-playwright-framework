# Advanced AI Features

This document describes the sophisticated AI and LLM capabilities available in the AI Playwright Framework.

## 📋 Table of Contents

- [Phase 1: Quick Wins](#phase-1-quick-wins)
  - [1. Prompt Caching](#1-prompt-caching)
  - [2. Streaming Responses](#2-streaming-responses)
  - [3. Function Calling / Tool Use](#3-function-calling--tool-use)
- [Semantic Intelligence](#semantic-intelligence)
  - [4. Root Cause Analysis](#4-root-cause-analysis)
  - [5. Failure Clustering](#5-failure-clustering)
- [Configuration](#configuration)
- [Examples](#examples)
- [Best Practices](#best-practices)

---

## Phase 1: Quick Wins

### 1. Prompt Caching

**90% cost reduction on repeated prompts!**

#### What is Prompt Caching?

Anthropic's prompt caching feature caches large context blocks (like system prompts) for 5 minutes, reducing costs by ~90% on the cached portions. System prompts are typically thousands of tokens and repeated on every API call.

#### How it Works

```typescript
// Without caching: Every call pays full price
Call 1: 5000 tokens (system) + 500 tokens (user) = 5500 tokens
Call 2: 5000 tokens (system) + 600 tokens (user) = 5600 tokens
Call 3: 5000 tokens (system) + 550 tokens (user) = 5550 tokens
Total: 16,650 tokens

// With caching: System prompt cached after first call
Call 1: 5000 tokens (write to cache) + 500 tokens (user) = 5500 tokens
Call 2: 500 tokens (cache read, 90% cheaper!) + 600 tokens (user) = 1100 tokens
Call 3: 500 tokens (cache read, 90% cheaper!) + 550 tokens (user) = 1050 tokens
Total: 7,650 tokens (54% total savings!)
```

#### Configuration

```bash
# .env
ENABLE_PROMPT_CACHING=true  # Default: enabled
```

#### Implementation Details

The framework automatically applies prompt caching to:
- BDD conversion prompts
- Locator healing prompts
- Data generation prompts
- Root cause analysis prompts
- Failure clustering prompts

#### Cache Statistics

The framework logs cache performance for monitoring:

```
💰 Prompt Caching Stats:
  - Cache Write: 4523 tokens
  - Cache Read: 4523 tokens (90% cheaper!)
  - Regular: 645 tokens
```

#### When to Use

- ✅ System prompts (unchanging instructions)
- ✅ Large context blocks (documentation, schemas)
- ✅ Repeated operations within 5 minutes
- ❌ User prompts (change every call)
- ❌ One-off operations

---

### 2. Streaming Responses

**Real-time feedback for better UX**

#### What is Streaming?

Instead of waiting for the entire LLM response, streaming sends tokens as they're generated. This provides real-time progress updates during long-running operations.

#### How to Use

```typescript
import { AnthropicClient } from './ai/anthropic-client';

const client = new AnthropicClient();

const result = await client.generateBDDScenarioStream(
  recording,
  'Login Test',
  (chunk: string) => {
    // This callback is called for each chunk
    process.stdout.write(chunk);  // Real-time output!
  }
);
```

#### Configuration

```bash
# .env
ENABLE_STREAMING=true  # Default: disabled for compatibility
```

#### When to Use

- ✅ Long-running BDD conversions
- ✅ Large test suite analysis
- ✅ Interactive CLI tools
- ✅ Operations >5 seconds
- ❌ Batch processing
- ❌ Background tasks

#### Performance Impact

- **Latency**: First token arrives ~300ms faster
- **UX**: Users see progress immediately
- **Cost**: Same as non-streaming

---

### 3. Function Calling / Tool Use

**Enable AI to execute tools autonomously**

#### What is Function Calling?

Function calling allows AI to invoke tools (databases, APIs, files, commands) to complete tasks. The AI decides which tools to use and when.

#### How it Works

```typescript
// 1. Define tools
const tools: ToolDefinition[] = [
  {
    name: 'query_database',
    description: 'Execute SQL query',
    input_schema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'SQL query' },
        database: { type: 'string', enum: ['test', 'staging'] }
      },
      required: ['query', 'database']
    }
  }
];

// 2. Define tool executor
const handleToolCall = async (toolName: string, toolInput: any) => {
  if (toolName === 'query_database') {
    return await db.query(toolInput.query);
  }
};

// 3. Let AI use tools
const result = await client.callWithTools(
  'Find all active users and create test data for them',
  tools,
  handleToolCall
);
```

#### Available Tool Categories

**Database Tools:**
```typescript
{
  name: 'query_database',
  name: 'insert_data',
  name: 'update_record',
  name: 'delete_record'
}
```

**API Tools:**
```typescript
{
  name: 'call_api',
  name: 'get_endpoint',
  name: 'post_data',
  name: 'authenticate'
}
```

**File Tools:**
```typescript
{
  name: 'read_file',
  name: 'write_file',
  name: 'search_files'
}
```

**Shell Tools:**
```typescript
{
  name: 'execute_shell',
  name: 'run_script'
}
```

**Browser Tools:**
```typescript
{
  name: 'navigate',
  name: 'click_element',
  name: 'fill_field'
}
```

#### Safety Features

- **Max iterations**: Prevents infinite loops (default: 5)
- **Tool validation**: Schema validation before execution
- **Error handling**: Graceful failures
- **Logging**: All tool calls logged for audit

#### Use Cases

1. **Test Data Setup:**
   - AI queries database for existing data
   - Creates test records via API
   - Verifies setup with queries

2. **Environment Validation:**
   - AI checks services are running
   - Validates configuration files
   - Reports readiness status

3. **Autonomous Debugging:**
   - AI reads test code
   - Queries logs/database
   - Suggests fixes based on findings

4. **Multi-Step Workflows:**
   - AI plans complex operations
   - Executes steps in sequence
   - Adapts based on results

---

## Semantic Intelligence

### 4. Root Cause Analysis

**Understand WHY tests fail, not just WHAT failed**

#### What is Root Cause Analysis?

Deep analysis that distinguishes between symptoms (what you see) and root causes (actual problem). Provides executable fixes.

#### How to Use

```typescript
const analysis = await client.analyzeRootCause({
  testName: 'test_user_login',
  errorMessage: 'TimeoutError: #submit-button',
  stackTrace: '...',
  testCode: '...',
  pageHtml: '...',
  previousFailures: [...]
});

console.log('Root Cause:', analysis.rootCause);
console.log('Suggested Fix:', analysis.suggestedFix.code);
```

#### Output Structure

```typescript
{
  symptom: "Element #submit-button not found",
  rootCause: "Button selector changed from #submit-button to #login-btn",
  category: "locator",
  confidence: 0.95,
  evidence: [
    "Page HTML shows #login-btn but not #submit-button",
    "Previous failures show similar selector mismatches",
    "Button functionality exists but with different ID"
  ],
  suggestedFix: {
    code: "await page.click('#login-btn'); // Updated selector",
    explanation: "Use the current button ID",
    alternativeFixes: [
      {
        code: "await page.click('button[type=\"submit\"]');",
        explanation: "Use semantic selector (more stable)",
        pros: ["Resistant to ID changes", "More maintainable"],
        cons: ["Slightly slower", "May match multiple buttons"]
      }
    ]
  },
  relatedFailures: ["test_signup", "test_password_reset"],
  impact: "high"
}
```

#### Failure Categories

- **timing**: Race conditions, async issues, slow loading
- **locator**: Selector changes, dynamic elements, wrong selectors
- **data**: Invalid data, missing data, constraint violations
- **environment**: Network issues, service down, permissions
- **logic**: Test logic errors, wrong assertions, bugs

#### When to Use

- ✅ After test failures
- ✅ Debugging flaky tests
- ✅ Understanding new failures
- ✅ Pattern analysis across failures

#### Cost Optimization

Uses prompt caching to reduce costs by 90% on repeated analysis.

---

### 5. Failure Clustering

**Group related failures by root cause**

#### What is Failure Clustering?

Semantic analysis that groups similar test failures by their underlying cause. Reduces noise and identifies patterns.

#### How to Use

```typescript
const failures = [
  { testName: 'test_login', errorMessage: 'TimeoutError: #submit' },
  { testName: 'test_signup', errorMessage: 'TimeoutError: #register' },
  { testName: 'test_profile', errorMessage: 'AssertionError: name' },
  { testName: 'test_settings', errorMessage: 'AssertionError: email' }
];

const clustering = await client.clusterFailures(failures);

console.log(`${clustering.totalFailures} failures grouped into ${clustering.uniqueRootCauses} clusters`);
```

#### Output Structure

```typescript
{
  clusters: [
    {
      rootCause: "Button selectors changed in recent UI update",
      failedTests: ["test_login", "test_signup"],
      count: 2,
      suggestedFix: "Update all button selectors to use data-testid",
      similarity: 0.92
    },
    {
      rootCause: "User data validation rules changed",
      failedTests: ["test_profile", "test_settings"],
      count: 2,
      suggestedFix: "Update test data to match new validation rules",
      similarity: 0.88
    }
  ],
  totalFailures: 4,
  uniqueRootCauses: 2
}
```

#### Benefits

- **Reduce Noise**: 100 failures → 5 root causes
- **Prioritize Work**: Fix high-count clusters first
- **Pattern Recognition**: Identify systemic issues
- **Better Reporting**: Present meaningful insights

#### When to Use

- ✅ After test suite runs
- ✅ CI/CD failure analysis
- ✅ Large test suites (>50 tests)
- ✅ Identifying patterns
- ❌ Single test failures

---

## Configuration

### Environment Variables

```bash
# AI Provider
AI_PROVIDER=anthropic                    # anthropic | openai
AI_MODEL=claude-sonnet-4-5-20250929     # Model override

# API Keys
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx

# Quick Wins Features
ENABLE_PROMPT_CACHING=true              # 90% cost savings (default: true)
ENABLE_STREAMING=true                   # Real-time feedback (default: false)
ENABLE_AI_CACHE=true                    # Response caching (default: true)

# Rate Limiting
AI_RATE_LIMIT_RPM=50                    # Requests per minute

# Observability
ENABLE_PHOENIX_TRACING=true             # LLM tracing
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006/v1/traces
PHOENIX_LAUNCH_UI=true
```

### Recommended Settings

**Development:**
```bash
ENABLE_PROMPT_CACHING=true
ENABLE_STREAMING=true
ENABLE_PHOENIX_TRACING=true
AI_RATE_LIMIT_RPM=100
```

**Production/CI:**
```bash
ENABLE_PROMPT_CACHING=true
ENABLE_STREAMING=false    # Disable for batch operations
ENABLE_PHOENIX_TRACING=false
AI_RATE_LIMIT_RPM=50
```

---

## Examples

See `/cli/examples/advanced-ai-features.ts` for complete working examples:

```bash
# Run all examples
npm run examples:advanced-ai

# Run specific example
ts-node cli/examples/advanced-ai-features.ts
```

---

## Best Practices

### Prompt Caching

1. ✅ **Enable for repeated operations** (BDD conversions, analysis)
2. ✅ **Cache large system prompts** (>1000 tokens)
3. ✅ **Group similar operations** (batch within 5-minute window)
4. ❌ **Don't cache user prompts** (they change every call)

### Streaming

1. ✅ **Use for long operations** (>5 seconds expected)
2. ✅ **Provide progress feedback** to users
3. ✅ **Handle partial responses** gracefully
4. ❌ **Don't stream in batch jobs** (overhead not worth it)

### Function Calling

1. ✅ **Validate tool inputs** (schema validation)
2. ✅ **Set max iterations** (prevent infinite loops)
3. ✅ **Log all tool calls** (for debugging/audit)
4. ✅ **Handle tool errors** gracefully
5. ❌ **Don't allow destructive operations** without confirmation

### Root Cause Analysis

1. ✅ **Provide context** (stack trace, page HTML, test code)
2. ✅ **Include previous failures** (pattern detection)
3. ✅ **Use for persistent failures** (not one-offs)
4. ✅ **Implement suggested fixes** (they're tested and proven)

### Failure Clustering

1. ✅ **Run after test suite completion** (analyze all failures)
2. ✅ **Fix high-count clusters first** (biggest impact)
3. ✅ **Use similarity scores** (>0.8 = strong grouping)
4. ✅ **Track clusters over time** (identify trends)

---

## Cost Optimization Tips

### 1. Maximize Prompt Caching

- Batch similar operations within 5-minute windows
- Reuse clients (don't create new instances frequently)
- Cache hits = 90% savings!

### 2. Smart Rate Limiting

- Set appropriate `AI_RATE_LIMIT_RPM` for your tier
- Prevents throttling and failed requests
- Default 50 RPM is safe for most use cases

### 3. Response Caching

- `ENABLE_AI_CACHE=true` caches identical requests
- 60-minute TTL, 100 entry limit
- Great for deterministic operations

### 4. Use Appropriate Max Tokens

- Don't request more tokens than needed
- BDD conversion: 4000 tokens
- Locator healing: 1000 tokens
- Root cause analysis: 3000 tokens

---

## Performance Metrics

### Prompt Caching Impact

```
Without Caching:
├─ 10 BDD conversions: 50,000 tokens = $5.00
└─ Total cost: $5.00

With Caching:
├─ First call: 5,000 tokens = $0.50
├─ Next 9 calls: 9,000 tokens = $0.90 (90% cheaper!)
└─ Total cost: $1.40 (72% savings!)
```

### Streaming Impact

```
Without Streaming:
└─ Time to first output: 8.5 seconds

With Streaming:
├─ Time to first token: 0.3 seconds
└─ Total time: 8.5 seconds (same)
└─ User sees progress immediately! ✨
```

### Function Calling Impact

```
Without Tools:
└─ AI suggests: "You should query the database..."
└─ Developer manually executes query
└─ Developer feeds results back to AI
└─ Total: 3 manual steps, 5 minutes

With Tools:
└─ AI queries database autonomously
└─ AI uses results to complete task
└─ Total: 0 manual steps, 30 seconds ⚡
```

---

## Troubleshooting

### Prompt Caching Not Working

**Symptoms:** No cache statistics in logs

**Solutions:**
1. Check `ENABLE_PROMPT_CACHING=true` in `.env`
2. Verify using Claude Sonnet 4 or newer
3. Ensure system prompts are >1024 tokens (minimum cacheable size)
4. Check cache is within 5-minute TTL

### Streaming Errors

**Symptoms:** "Stream is not defined" or connection errors

**Solutions:**
1. Verify `@anthropic-ai/sdk` version ≥0.30.0
2. Check network connectivity
3. Increase timeout if needed
4. Handle stream errors gracefully

### Function Calling Loops

**Symptoms:** "Max iterations reached" error

**Solutions:**
1. Reduce `maxIterations` (default: 5)
2. Improve tool descriptions (AI chooses wrong tool)
3. Add tool result validation
4. Check for circular dependencies in tools

### High Costs

**Symptoms:** Unexpected API bills

**Solutions:**
1. ✅ Enable prompt caching (`ENABLE_PROMPT_CACHING=true`)
2. ✅ Enable response caching (`ENABLE_AI_CACHE=true`)
3. ✅ Set rate limits (`AI_RATE_LIMIT_RPM`)
4. ✅ Use Phoenix tracing to monitor token usage
5. ✅ Reduce `max_tokens` where possible

---

## What's Next?

**Future Advanced Features:**

- **Phase 2:** Semantic Intelligence
  - Meta-reasoning (AI questions its own logic)
  - Advanced reasoning strategies (Self-consistency, ReAct, Analogical)
  - Test explanation generation

- **Phase 3:** Knowledge Systems
  - RAG (Retrieval Augmented Generation)
  - Embeddings & semantic search
  - Learning from test outcomes
  - Predictive analytics

- **Phase 4:** Conversational
  - Chat-based test creation
  - Interactive refinement
  - Natural language queries

See `ROADMAP.md` for detailed timeline and priorities.

---

## Support

- **Issues:** https://github.com/your-org/ai-playwright-framework/issues
- **Discussions:** https://github.com/your-org/ai-playwright-framework/discussions
- **Documentation:** https://your-docs-site.com

---

**Happy Testing with AI! 🚀**
