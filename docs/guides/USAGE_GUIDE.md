# AI Playwright Framework - Complete Usage Guide

**Comprehensive guide for using the AI-powered Playwright test automation framework generator.**

---

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [CLI Commands](#cli-commands)
4. [Workflow Examples](#workflow-examples)
5. [Configuration](#configuration)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## 🚀 Installation

### Prerequisites

- Node.js 16+
- Python 3.8+
- npm or yarn

### From Source (Current Method)

```bash
# Clone the repository
git clone https://github.com/ksmuvva/ai-playwright-framework.git
cd ai-playwright-framework/cli

# Install dependencies
npm install

# Build the CLI
npm run build

# Link globally
npm link

# Verify installation
playwright-ai --version
```

### From npm (When Published)

```bash
npm install -g playwright-ai-framework
```

---

## ⚡ Quick Start

### 1. Initialize Framework

```bash
playwright-ai init
```

**Interactive prompts will ask:**
- Project name
- Language (Python/TypeScript)
- Enable BDD? (Yes/No)
- Optimize for Power Apps? (Yes/No)
- AI Provider (Anthropic/OpenAI/None)

**Or use flags:**

```bash
playwright-ai init \
  --project-name my-tests \
  --language python \
  --bdd \
  --power-apps \
  --ai-provider anthropic
```

### 2. Configure Environment

```bash
cd my-tests
nano .env  # or use your favorite editor
```

**Required configuration:**
```bash
APP_URL=https://your-app.com
TEST_USER=test@example.com
TEST_PASSWORD=your-password
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 3. Run Tests

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run all tests
behave

# Run with tags
behave --tags=@smoke
```

---

## 🎯 CLI Commands Reference

### `playwright-ai init`

Initialize a new test automation framework.

**Options:**
```
-l, --language <type>       Framework language (python|typescript)
-n, --project-name <name>   Project name
--bdd                       Enable BDD framework (default: true)
--power-apps                Add Power Apps helpers
--ai-provider <provider>    AI provider (anthropic|openai|none)
-d, --directory <path>      Output directory
```

**Examples:**

```bash
# Basic initialization (interactive)
playwright-ai init

# With all options
playwright-ai init \
  --language python \
  --project-name my-automation \
  --bdd \
  --power-apps \
  --ai-provider anthropic

# Skip AI features
playwright-ai init --ai-provider none
```

**What it creates:**
```
my-automation/
├── features/              # BDD feature files
│   ├── environment.py    # Behave hooks
│   └── steps/           # Step definitions
├── helpers/              # Helper utilities
│   ├── auth_helper.py
│   ├── healing_locator.py
│   ├── wait_manager.py
│   ├── data_generator.py
│   └── screenshot_manager.py
├── pages/               # Page objects
├── fixtures/            # Test data
├── config/             # Configuration
├── .env                # Environment variables
├── requirements.txt    # Python dependencies
└── README.md
```

---

### `playwright-ai record`

Record a new test scenario using Playwright's codegen.

**Options:**
```
-u, --url <url>              Starting URL for recording
-s, --scenario-name <name>   Name for the scenario
--convert-to-bdd            Auto-convert to BDD after recording
--generate-data             Generate test data schema
```

**Examples:**

```bash
# Basic recording (interactive)
playwright-ai record

# With options
playwright-ai record \
  --url https://your-app.com/login \
  --scenario-name user_login

# Record and auto-convert
playwright-ai record \
  --url https://your-app.com \
  --scenario-name create_contact \
  --convert-to-bdd
```

**How it works:**

1. Playwright browser opens to specified URL
2. You perform actions in the browser
3. Actions are recorded automatically
4. Close browser when done
5. Recording saved to `recordings/` directory

**Tips:**
- Use clear, deliberate actions
- Avoid unnecessary clicks/navigation
- Focus on the happy path first
- Use data-testid attributes for reliability

---

### `playwright-ai convert`

Convert Playwright recording to BDD scenario.

**Arguments:**
```
<recording-file>           Path to recording file (required)
```

**Options:**
```
-s, --scenario-name <name>  Override scenario name
-o, --output-dir <dir>      Output directory (default: .)
```

**Examples:**

```bash
# Basic conversion
playwright-ai convert recordings/user_login_2024-01-15.py

# With custom name
playwright-ai convert recordings/recording.py --scenario-name login_flow

# Custom output directory
playwright-ai convert recordings/test.py --output-dir ./my-tests
```

**What it generates:**

```
features/scenario_name.feature          # Gherkin feature file
features/steps/scenario_name_steps.py   # Python step definitions
config/scenario_name_locators.json      # Locator mappings
fixtures/scenario_name_data.json        # Test data
```

**AI Features:**
- Converts actions to human-readable Given/When/Then steps
- Extracts reusable locators
- Identifies test data to parameterize
- Suggests helper functions

**Fallback:**
- If AI not configured, uses template-based conversion
- Still creates valid BDD scenarios
- Requires manual refinement

---

## 📚 Workflow Examples

### Example 1: Complete New Feature Test

```bash
# 1. Initialize framework
playwright-ai init --project-name ecommerce-tests

cd ecommerce-tests

# 2. Configure
vi .env
# Add: APP_URL, TEST_USER, TEST_PASSWORD, API_KEY

# 3. Record login flow
playwright-ai record --url https://shop.com --scenario-name login

# 4. Convert to BDD
playwright-ai convert recordings/login*.py

# 5. Record checkout flow
playwright-ai record --url https://shop.com --scenario-name checkout

# 6. Convert
playwright-ai convert recordings/checkout*.py

# 7. Run tests
source venv/bin/activate
behave
```

---

### Example 2: Power Apps Testing

```bash
# 1. Initialize with Power Apps optimization
playwright-ai init \
  --project-name powerapp-tests \
  --power-apps \
  --ai-provider anthropic

cd powerapp-tests

# 2. Configure Power Apps URL
echo "APP_URL=https://your-org.powerapps.com" >> .env
echo "ANTHROPIC_API_KEY=sk-ant-xxx" >> .env

# 3. Record creating a contact
playwright-ai record \
  --url https://your-org.powerapps.com \
  --scenario-name create_contact \
  --convert-to-bdd

# 4. Run
behave features/create_contact.feature
```

**Power Apps Benefits:**
- Smart waits for Power Apps loading
- Handles dynamic elements
- Self-healing locators for Power Apps controls

---

### Example 3: Team Standardization

```bash
# Lead creates framework template
playwright-ai init --project-name team-automation

# Customize common helpers
cd team-automation
# Edit helpers/auth_helper.py for company SSO
# Add company-specific page objects

# Commit to git
git add .
git commit -m "Initial framework setup"
git push origin main

# Team members clone
git clone <repo-url>
cd team-automation
pip install -r requirements.txt
playwright install chromium

# Each tester records their scenarios
playwright-ai record --url https://app.com --scenario-name their_test
```

---

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Application Configuration
APP_URL=https://your-app.com
ENVIRONMENT=dev

# Authentication
TEST_USER=test@example.com
TEST_PASSWORD=SecurePassword123

# Browser Settings
BROWSER=chromium              # chromium, firefox, or webkit
HEADLESS=false               # true for CI/CD
VIEWPORT_WIDTH=1920
VIEWPORT_HEIGHT=1080

# Timeouts (milliseconds)
DEFAULT_TIMEOUT=10000
NAVIGATION_TIMEOUT=30000

# AI Provider
AI_PROVIDER=anthropic        # anthropic, openai, or none
ANTHROPIC_API_KEY=sk-ant-xxx
# OPENAI_API_KEY=sk-xxx

# Features
ENABLE_HEALING=true          # Self-healing locators
ENABLE_SCREENSHOTS=true      # Auto-screenshots
ENABLE_VIDEO=false           # Video recording (slower)

# Power Apps (if applicable)
POWER_APPS_TENANT_ID=your-tenant-id
POWER_APPS_CLIENT_ID=your-client-id
```

### Behave Configuration (behave.ini)

```ini
[behave]
show_skipped = true
show_timings = true
color = true
default_format = pretty
summary = true

# Run only smoke tests
# default_tags = @smoke

# Stop on first failure (debugging)
# stop = true
```

---

## 🎓 Best Practices

### 1. Use Descriptive Scenario Names
- ✅ `user_login_with_valid_credentials`
- ❌ `test1`

### 2. Configure AI for Best Results
- Self-healing reduces maintenance
- Test data generation improves coverage

### 3. Run Tests Frequently
- Smart waits improve over time
- Healing learns from failures

### 4. Commit Generated Files
- Feature files
- Locator configs
- But not credentials or logs

### 5. Review AI-Generated Code
- AI is helpful but not perfect
- Verify step definitions
- Adjust as needed

---

## 🐛 Troubleshooting

### Issue: "AI API key not configured"

**Solution:**
```bash
# Check .env file
cat .env | grep API_KEY

# Add API key
echo "ANTHROPIC_API_KEY=sk-ant-your-key" >> .env

# Verify
source .env
echo $ANTHROPIC_API_KEY
```

---

### Issue: "Locator failed to find element"

**Solutions:**

1. **Enable self-healing:**
   ```bash
   ENABLE_HEALING=true
   ```

2. **Check healing log:**
   ```bash
   cat locator_healing_log.json
   ```

3. **Use data-testid attributes in your app:**
   ```html
   <button data-testid="submit-button">Submit</button>
   ```

4. **Update locator in config:**
   ```json
   {
     "submit_button": "button[data-testid='submit-button']"
   }
   ```

---

### Issue: "Tests running slow"

**Solutions:**

1. **Check wait times:**
   ```bash
   cat wait_performance_log.json
   ```

2. **Reduce unnecessary waits:**
   - Smart waits learn over time
   - After multiple runs, waits auto-optimize

3. **Use headless mode for speed:**
   ```bash
   HEADLESS=true
   ```

4. **Disable screenshots in CI:**
   ```bash
   ENABLE_SCREENSHOTS=false
   ```

---

### Issue: "Python dependencies conflict"

**Solution:**
```bash
# Use virtual environment
python3 -m venv venv
source venv/bin/activate

# Clean install
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Issue: "Playwright browser not found"

**Solution:**
```bash
# Install browsers
playwright install chromium

# Or all browsers
playwright install
```

---

## 📞 Getting Help

### Documentation
- Main README: [README.md](../../README.md)
- Requirements: [REQUIREMENTS.md](../../REQUIREMENTS.md)
- Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
- Feature Guides: [docs/features/](../features/)

### Community
- GitHub Issues: Report bugs
- Discussions: Ask questions
- Examples: See example projects

### Debugging

**Enable verbose output:**
```bash
DEBUG=playwright-ai:* playwright-ai init
```

**Pause execution:**
```gherkin
When I click "Submit"
And I pause  # Browser will pause here
```

**Check screenshots:**
```bash
ls reports/screenshots/
```

---

**Happy Testing! 🚀**
