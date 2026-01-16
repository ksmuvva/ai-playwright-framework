# Quick Start Guide

Get up and running with the Claude Playwright Agent in **5 minutes**.

## Prerequisites

- **Python 3.10+** installed
- **API Key** for an LLM provider (GLM 4.7 recommended)
- **Git** (optional, for cloning)

---

## Step 1: Installation (1 minute)

### Option A: Install from PyPI (Recommended)

```bash
pip install claude-playwright-agent
```

### Option B: Install from Source

```bash
git clone https://github.com/anthropics/claude-playwright-agent.git
cd claude-playwright-agent
pip install -e .
```

### Verify Installation

```bash
cpa --version
# Output: Claude Playwright Agent v1.0.0
```

---

## Step 2: Initialize Project (30 seconds)

```bash
cpa init my-first-tests
cd my-first-tests
```

**This creates:**
```
my-first-tests/
├── config/
│   ├── default/
│   │   ├── config.yaml
│   │   ├── pytest.ini
│   │   └── behave.ini
│   └── profiles/
│       ├── dev.yaml
│       ├── test.yaml
│       ├── prod.yaml
│       └── ci.yaml
├── pages/
│   ├── base_page.py
│   └── examples/
├── recordings/
├── features/
├── steps/
└── .cpa/
    └── state.json
```

---

## Step 3: Configure API Key (30 seconds)

### Using GLM 4.7 (Recommended)

Edit `config/default/config.yaml`:

```yaml
ai:
  provider: glm
  model: glm-4-plus
  max_tokens: 8192
  temperature: 0.3
```

Set your API key as environment variable:

```bash
export GLM_API_KEY=your-glm-api-key-here
```

**Or create `.env` file:**

```bash
echo "GLM_API_KEY=your-glm-api-key-here" > .env
```

---

## Step 4: Record Your First Test (2 minutes)

### Option A: Using Playwright Codegen (Recommended)

```bash
# Start Playwright code generator
playwright codegen https://the-internet.herokuapp.com/login --target=python
```

**Perform these actions:**
1. Enter username: `tomsmith`
2. Enter password: `SuperSecretPassword!`
3. Click "Login" button
4. Verify you're logged in
5. Close the browser

**Save the recording to:** `recordings/login.spec.js`

### Option B: Manual Recording

Create `recordings/login.json`:

```json
{
  "actions": [
    {
      "type": "fill",
      "selector": "#username",
      "value": "tomsmith"
    },
    {
      "type": "fill",
      "selector": "#password",
      "value": "SuperSecretPassword!"
    },
    {
      "type": "click",
      "selector": "button[type='submit']"
    }
  ]
}
```

---

## Step 5: Generate BDD Tests (30 seconds)

```bash
# Ingest the recording
cpa ingest recordings/login.spec.js

# Generate page objects (optional but recommended)
cpa generate page-objects

# Convert to BDD scenarios
cpa run convert
```

**This creates:**
- `features/login.feature` - BDD scenario in Gherkin syntax
- `steps/login_steps.py` - Python step definitions
- `pages/login_page.py` - Login page object

---

## Step 6: Run Your Tests (30 seconds)

```bash
# Run all tests
cpa run test

# Or use behave directly
behave

# Or use pytest-bdd
pytest features/
```

**Expected Output:**

```
✅ Scenario: Successful login
   ✓ Given I am on the login page
   ✓ When I enter valid credentials
   ✓ And I click the login button
   ✓ Then I should be logged in

1 scenario passed (1 passed)
4 steps passed (4 passed)
```

---

## Step 7: View Results (30 seconds)

```bash
# Open HTML report
open reports/index.html

# Or view JUnit XML
cat reports/junit/results.xml
```

---

## Congratulations! 🎉

You've successfully:
- ✅ Installed the framework
- ✅ Created a test project
- ✅ Recorded user interactions
- ✅ Generated BDD scenarios
- ✅ Run your first test

---

## Next Steps

### Learn More

1. **[User Guide](user_guide.md)** - Complete documentation
2. **[CLI Reference](cli_reference.md)** - All CLI commands
3. **[Page Objects Guide](page_objects.md)** - Create page objects
4. **[Configuration Guide](../config/README.md)** - Configure the framework

### Advanced Features

#### Use Different Profiles

```bash
# Development profile (headless=false, devtools=true)
cpa --profile dev run test

# CI profile (parallel execution, JUnit reports)
cpa --profile ci run test
```

#### Run Specific Tests

```bash
# Run by tag
cpa run test --tags @smoke

# Run specific feature
behave features/login.feature

# Run specific scenario
behave features/login.feature:10
```

#### Parallel Execution

```bash
# Run 4 tests in parallel
cpa --profile test run test
```

#### Debugging

```bash
# Run with debug output
cpa --profile dev run test

# Run with Playwright Inspector
PWDEBUG=1 behave features/login.feature
```

---

## Common Issues

### Issue: "cpa: command not found"

**Solution:** Make sure you installed the package:

```bash
pip install claude-playwright-agent
# Or if installed from source
export PATH="$PATH:$PWD/src"
```

### Issue: "API key not found"

**Solution:** Set your API key:

```bash
export GLM_API_KEY=your-key-here
# Or create .env file
echo "GLM_API_KEY=your-key-here" > .env
```

### Issue: "Recording not found"

**Solution:** Check recording file exists:

```bash
ls recordings/
# Should show login.spec.js or login.json
```

### Issue: "Tests failing with timeout"

**Solution:** Increase timeout in `config/default/config.yaml`:

```yaml
framework:
  default_timeout: 60000  # 60 seconds
```

---

## Quick Reference

### Essential Commands

| Command | Description |
|---------|-------------|
| `cpa init <name>` | Create new project |
| `cpa ingest <file>` | Import recording |
| `cpa run test` | Run tests |
| `cpa run convert` | Generate BDD scenarios |
| `cpa generate page-objects` | Generate page objects |
| `cpa --profile <name>` | Use specific profile |

### Common Workflows

```bash
# Full workflow (recommended)
cpa init my-project
cd my-project
cpa ingest recordings/test.spec.js
cpa generate page-objects
cpa run convert
cpa run test

# Quick workflow (skip page objects)
cpa init my-project
cd my-project
cpa ingest recordings/test.spec.js
cpa run convert
cpa run test

# Development workflow
cpa --profile dev run test
```

---

## Example Test Structure

**After completing the quick start, you'll have:**

```
my-first-tests/
├── config/
│   └── default/
│       └── config.yaml          # Framework configuration
├── features/
│   └── login.feature             # BDD scenarios
├── steps/
│   └── login_steps.py            # Step definitions
├── pages/
│   ├── base_page.py              # Base page class
│   └── login_page.py             # Login page object
├── recordings/
│   └── login.spec.js             # Original recording
├── reports/
│   └── index.html                # Test results
└── .env                          # API keys (optional)
```

---

## What's Next?

### Continue Learning

1. **Create More Tests** - Record additional user flows
2. **Page Objects** - Create reusable page objects
3. **Assertions** - Add verification to tests
4. **Data-Driven** - Test with multiple data sets
5. **CI/CD** - Integrate with your pipeline

### Explore Features

- **Self-Healing** - Automatic selector recovery
- **Component Extraction** - Reusable UI components
- **Parallel Execution** - Run tests faster
- **AI Analysis** - Smart failure analysis
- **Multiple Browsers** - Chrome, Firefox, Safari

### Join the Community

- 📖 [Documentation](../README.md)
- 💬 [Discussions](https://github.com/anthropics/claude-playwright-agent/discussions)
- 🐛 [Issues](https://github.com/anthropics/claude-playwright-agent/issues)
- ⭐ [GitHub](https://github.com/anthropics/claude-playwright-agent)

---

**Ready to dive deeper?** Check out the [User Guide](user_guide.md) for comprehensive documentation.
