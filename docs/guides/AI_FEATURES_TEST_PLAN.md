# 🤖 AI Features Testing Plan

## Testing Plan for Bugs #4 & #8

This document outlines how to test the AI-powered features of the playwright-ai-framework to verify Bugs #4 and #8 are fixed.

---

## 🎯 What Needs Testing

### Bug #4: AI Conversion Not Working
**Severity:** 🔴 Critical - Core feature

**Feature:** `playwright-ai convert` command
- Converts Playwright recordings to BDD scenarios
- Generates feature files
- Creates step definitions
- Generates page objects

### Bug #8: AI Features Need Validation
**Severity:** 🟡 Medium - Quality assurance

**Features:**
- Self-healing locators
- Smart wait recommendations
- Test data generation
- Reasoning engine (Chain-of-Thought, Tree-of-Thought)
- Pattern analysis
- Meta-reasoning for flaky tests

---

## ✅ Prerequisites

### 1. API Keys Required

You need at least one of these:

**Anthropic (Recommended):**
```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

**OpenAI (Alternative):**
```bash
export OPENAI_API_KEY="sk-..."
```

### 2. Set Up Environment

```bash
cd /home/user/ai-playwright-framework/cli

# Create .env file
cp .env.example .env

# Edit .env with your API key
nano .env
```

**Add to `.env`:**
```env
# AI Provider Configuration
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
# OR
OPENAI_API_KEY=sk-your-key-here

# Model Configuration
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
```

### 3. Rebuild CLI with Environment

```bash
npm install
npm run build
npm link
```

---

## 🧪 Test Suite

### Test 1: Verify AI Client Initialization

**Command:**
```bash
# This should not error about missing API key
playwright-ai init --language python --project-name ai-test --bdd
```

**Expected:**
- ✅ Asks for AI provider selection
- ✅ No "API key missing" error
- ✅ Project generation completes

**Actual Result:** _[To be filled after testing]_

---

### Test 2: Test BDD Conversion (Bug #4)

**Prerequisite:** Create a test Playwright recording

**Step 1: Create Recording**
```bash
mkdir -p /tmp/ai-test-recordings
cd /tmp/ai-test-recordings

# Create sample Playwright recording
cat > test_login.py << 'EOF'
from playwright.sync_api import Playwright, sync_playwright

def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    # Navigate to login page
    page.goto("https://example.com/login")

    # Fill username
    page.fill('input[name="username"]', 'testuser')

    # Fill password
    page.fill('input[name="password"]', 'password123')

    # Click login button
    page.click('button[type="submit"]')

    # Wait for dashboard
    page.wait_for_url("**/dashboard")

    # Verify welcome message
    page.locator('text=Welcome').is_visible()

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
EOF
```

**Step 2: Convert Recording**
```bash
playwright-ai convert test_login.py
```

**Expected Output:**
```
🤖 Analyzing recording with AI...
✓ Identified 1 scenario
✓ Generated BDD feature file
✓ Created step definitions
✓ Generated page objects

Files created:
  ✓ features/test_login.feature
  ✓ steps/test_login_steps.py
  ✓ pages/login_page.py
```

**Expected Files:**

`features/test_login.feature`:
```gherkin
Feature: User Login
  As a user
  I want to log into the application
  So that I can access the dashboard

  Scenario: Successful user login
    Given I am on the login page
    When I enter username "testuser"
    And I enter password "password123"
    And I click the login button
    Then I should see the dashboard
    And I should see the welcome message
```

`steps/test_login_steps.py`:
```python
from behave import given, when, then
from pages.login_page import LoginPage

@given('I am on the login page')
def step_impl(context):
    context.page.goto("https://example.com/login")

@when('I enter username "{username}"')
def step_impl(context, username):
    login_page = LoginPage(context.page)
    login_page.fill_username(username)

# ... more steps
```

**Verification Checklist:**
- [ ] AI analyzed the recording
- [ ] Generated .feature file with proper Gherkin
- [ ] Created step definitions
- [ ] Generated page object
- [ ] Files have correct structure
- [ ] Code is syntactically valid

**Actual Result:** _[To be filled after testing]_

---

### Test 3: Test Self-Healing Locators

**Test Code:**
```python
# In a generated test
from helpers.healing_locator import HealingLocator

# Old locator: button#submit
# New locator (after UI change): button[data-testid="submit-button"]

locator = HealingLocator.find(
    page=page,
    primary_selector='button#submit',
    fallback_selectors=[
        'button[type="submit"]',
        'button[data-testid="submit-button"]',
        'button:has-text("Submit")'
    ],
    ai_healing=True
)
```

**Expected:**
- ✅ AI suggests best locator
- ✅ Falls back to alternatives
- ✅ Logs locator changes

**Actual Result:** _[To be filled after testing]_

---

### Test 4: Test Data Generation

**Command:**
```bash
# In a generated project
python -c "
from helpers.data_generator import TestDataGenerator

gen = TestDataGenerator()
user_data = gen.generate_test_data({
    'name': 'full_name',
    'email': 'email',
    'age': 'number:18-65',
    'address': 'address'
}, use_ai=True)

print(user_data)
"
```

**Expected Output:**
```json
{
  "name": "John Smith",
  "email": "john.smith@example.com",
  "age": 42,
  "address": "123 Main St, Springfield, IL 62701"
}
```

**Verification:**
- [ ] Realistic data generated
- [ ] Follows schema constraints
- [ ] AI enhanced (contextual data)

**Actual Result:** _[To be filled after testing]_

---

### Test 5: Test Reasoning Engine

**Test Code:**
```python
from helpers.reasoning import create_reasoning_engine, ReasoningMode

# Test Chain-of-Thought
cot_engine = create_reasoning_engine(ReasoningMode.CHAIN_OF_THOUGHT)
result = cot_engine.analyze_test_failure(
    test_name="Login Test",
    error_message="Element not found: button#submit",
    stack_trace="...",
    screenshot_path="failure.png"
)

print(result.reasoning_steps)
print(result.root_cause)
print(result.suggested_fixes)
```

**Expected Output:**
```
Reasoning Steps:
1. Element selector changed or removed
2. Checking if button still exists with different selector
3. Analyzing screenshot for UI changes
4. Button moved to different location

Root Cause:
UI refactored - submit button ID changed from 'submit' to 'submit-btn'

Suggested Fixes:
1. Update locator to: button#submit-btn
2. Use data-testid attribute: button[data-testid="submit"]
3. Use text-based locator: button:has-text("Submit")
```

**Verification:**
- [ ] Reasoning steps are logical
- [ ] Root cause identified
- [ ] Fixes are actionable

**Actual Result:** _[To be filled after testing]_

---

### Test 6: Test Meta-Reasoning for Flaky Tests

**Test Scenario:**
```bash
# Run flaky test detection
playwright-ai analyze-flaky --test-results ./test-results/
```

**Expected:**
- ✅ Detects flaky patterns
- ✅ Clusters similar failures
- ✅ Suggests fixes
- ✅ Auto-generates fix PR

**Actual Result:** _[To be filled after testing]_

---

## 📊 Test Results Summary

| Test # | Feature | Status | Notes |
|--------|---------|--------|-------|
| 1 | AI Client Init | ⏳ Pending | Needs API key |
| 2 | BDD Conversion (Bug #4) | ⏳ Pending | Core feature |
| 3 | Self-Healing Locators | ⏳ Pending | Bug #8 |
| 4 | Data Generation | ⏳ Pending | Bug #8 |
| 5 | Reasoning Engine | ⏳ Pending | Bug #8 |
| 6 | Meta-Reasoning | ⏳ Pending | Bug #8 |

---

## 🐛 Bug Status After Testing

### If All Tests Pass ✅

**Bug #4: AI Conversion** - FIXED
- `playwright-ai convert` works
- Generates valid BDD files
- Creates proper step definitions

**Bug #8: AI Features Validated** - FIXED
- Self-healing works
- Data generation works
- Reasoning engine functional
- All AI features validated

### If Tests Fail ❌

Document specific failures and create fix plan.

---

## 🚀 How to Run Tests

### Full Test Suite

```bash
# Set API key
export ANTHROPIC_API_KEY="your-key-here"

# Navigate to CLI
cd /home/user/ai-playwright-framework/cli

# Rebuild
npm install
npm run build
npm link

# Test 1: Init
playwright-ai init --help

# Test 2: Conversion (create recording first)
playwright-ai convert path/to/recording.py

# Test 3-6: Run generated project tests
cd /tmp/generated-project
pip install -r requirements.txt
behave features/ -v
```

---

## 📝 Notes for Tester

**Important:**
- You MUST have a valid API key (Anthropic or OpenAI)
- API calls will incur costs (~$0.01-$0.10 per test)
- Some features require actual UI testing
- Recording must be valid Playwright Python code

**Recommended:**
- Start with Test 1 (simplest)
- Then Test 2 (core feature)
- Then Tests 3-6 (advanced features)

---

## ✅ Success Criteria

AI features are considered **working** when:

- [ ] API key is recognized
- [ ] No authentication errors
- [ ] `playwright-ai convert` generates valid BDD
- [ ] Self-healing locators suggest alternatives
- [ ] Data generation produces realistic data
- [ ] Reasoning engine provides useful insights
- [ ] Meta-reasoning detects flaky patterns

**Current Status:** Awaiting API key for testing

---

## 📞 Get API Keys

### Anthropic (Recommended)
1. Go to: https://console.anthropic.com/
2. Sign up / Log in
3. Navigate to API Keys
4. Create new key
5. Copy key starting with `sk-ant-api03-...`

### OpenAI (Alternative)
1. Go to: https://platform.openai.com/
2. Sign up / Log in
3. Navigate to API Keys
4. Create new key
5. Copy key starting with `sk-...`

---

**Estimated Testing Time:** 1-2 hours
**Required:** Valid API key
**Cost:** ~$0.50 for full test suite
