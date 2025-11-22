# CLI Usability Guide - Real-World Usage Flows

**Document:** Complete CLI Interaction Guide
**Date:** 2025-11-22
**Purpose:** Document real-world usage scenarios, command sequences, and user interactions

---

## Table of Contents
1. [Initial Setup Flow](#initial-setup-flow)
2. [Creating First Test Flow](#creating-first-test-flow)
3. [Converting Recordings Flow](#converting-recordings-flow)
4. [Running Tests Flow](#running-tests-flow)
5. [AI-Powered Features Flow](#ai-powered-features-flow)
6. [Common Workflows](#common-workflows)
7. [Troubleshooting Flows](#troubleshooting-flows)
8. [Advanced Usage](#advanced-usage)

---

## Initial Setup Flow

### Scenario 1: First-Time User - Python Framework with AI

**User Goal:** Create a new test automation framework for a web application

**Step-by-Step Interaction:**

```bash
# Step 1: User starts CLI for the first time
$ playwright-ai

╔═══════════════════════════════════════════════════════════════╗
║                                                                ║
║   🤖  AI-Powered Playwright Framework Generator               ║
║                                                                ║
║   Generate complete test automation frameworks                ║
║   with self-healing, smart waits, and AI-powered features    ║
║                                                                ║
╚═══════════════════════════════════════════════════════════════╝

Usage: playwright-ai [options] [command]

🤖 AI-powered Playwright test automation framework generator

Options:
  -V, --version           output the version number
  -h, --help              display help for command

Commands:
  init [options]          Initialize a new test automation framework
  record [options]        Record a new test scenario using Playwright
  convert <recording-file> Convert Playwright recording to BDD scenario
  help [command]          display help for command


# Step 2: User initializes new framework
$ playwright-ai init

🤖 AI-Powered Playwright Framework Generator

? Project name: my-webapp-tests
? Select framework language: (Use arrow keys)
❯ Python (Recommended)
  TypeScript (Coming soon) (disabled)

# User selects Python and presses Enter
✔ Select framework language: Python (Recommended)

? Enable BDD (Behave)? (Y/n) y
✔ Enable BDD (Behave)? yes

? Optimize for Power Apps? (y/N) n
✔ Optimize for Power Apps? no

? Select AI provider (for self-healing & data generation): (Use arrow keys)
❯ Anthropic (Claude) - Recommended
  OpenAI (GPT-4)
  None (Disable AI features)

# User selects Anthropic
✔ Select AI provider: Anthropic (Claude) - Recommended

? Select Claude model: (Use arrow keys)
❯ Claude Sonnet 4.5 (Recommended - Fast & Intelligent)
  Claude Opus 4 (Most Capable)
  Claude Sonnet 3.5
  Claude Haiku 3.5 (Fast & Economical)

# User selects Sonnet 4.5
✔ Select Claude model: Claude Sonnet 4.5 (Recommended - Fast & Intelligent)

? Enter your Anthropic API key: [hidden input]
✔ Enter your Anthropic API key: sk-ant-api03...

# System starts generating framework
ℹ AnthropicClient initialized with model: claude-sonnet-4-5-20250929

⠹ Creating project directory...
✔ Project directory created: /Users/john/my-webapp-tests

⠸ Generating framework files...
  Generating Python Framework
  ⠴ Creating directory structure...
  ✔ Directory structure created
  ⠦ Copying helper files...
  ✔ Helper files copied
  ⠧ Copying step definitions...
  ✔ Step files copied
  ⠹ Generating configuration files...
  ✔ Configuration files generated
  ⠸ Copying requirements.txt...
  ✔ requirements.txt copied
  ⠼ Copying behave.ini...
  ✔ behave.ini copied
  ⠴ Copying .env.example...
  ✔ .env files created
  ⠦ Generating README...
  ✔ README generated
  ⠧ Copying example feature file...
  ✔ Example feature copied
  ✔ .gitignore created
✔ Framework files generated

⠹ Creating CLI .env file...
✔ CLI .env file created/updated

⠸ Initializing git repository...
✔ Git repository initialized

? Install dependencies now? (Y/n) y
✔ Install dependencies now? yes

⠹ Creating virtual environment...
⠸ Installing Python packages...
⠼ Installing Playwright browsers...
✔ Dependencies installed successfully


✅ Framework Initialized Successfully!

ℹ Project Details:
  Name: my-webapp-tests
  Language: python
  BDD: Enabled (Behave)
  Power Apps: Disabled
  AI Provider: anthropic


📋 Next Steps:

  ⠿ cd my-webapp-tests
  ⠿ Edit .env file and add your AI API key
    ANTHROPIC_API_KEY=sk-ant-your-key-here
    ℹ Get your API key at: https://console.anthropic.com/

  ⠿ Configure your application URL and credentials in .env:
    APP_URL=https://your-app.com
    TEST_USER=test@example.com
    TEST_PASSWORD=your-password

  ⠿ Run your tests:
    behave
    behave --tags=@smoke

  ⠿ Record a new scenario:
    playwright-ai record --url https://your-app.com

  ✅ Happy testing! 🚀
```

**What Happens Behind the Scenes:**
1. CLI displays welcome banner
2. Prompts user for project configuration
3. Validates user inputs (project name, API key format)
4. Creates project directory structure
5. Copies template files from `cli/templates/python/`
6. Generates config files with user settings
7. Creates/updates CLI .env file with API key
8. Initializes git repository
9. Creates Python virtual environment
10. Installs dependencies from requirements.txt
11. Installs Playwright browsers
12. Displays success message with next steps

**Files Created:**
```
my-webapp-tests/
├── .env                    # Configuration with secrets
├── .env.example            # Example configuration
├── .gitignore              # Git ignore rules
├── behave.ini              # Behave configuration
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
├── features/
│   └── example.feature     # Example BDD scenario
├── steps/
│   ├── __init__.py
│   ├── environment.py      # Test hooks
│   └── common_steps.py     # Reusable steps
├── helpers/
│   ├── __init__.py
│   ├── auth_helper.py      # Authentication
│   ├── healing_locator.py  # Self-healing
│   ├── wait_manager.py     # Smart waits
│   ├── data_generator.py   # Test data
│   └── screenshot_manager.py
├── pages/                  # Page objects
├── fixtures/               # Test data
├── config/
│   ├── __init__.py
│   └── config.py           # Configuration class
├── reports/
│   ├── screenshots/
│   └── videos/
└── auth_states/            # Saved auth states
```

**User State After Step:**
- Project initialized
- Dependencies installed
- Ready to configure application details
- Ready to write/record first test

---

## Creating First Test Flow

### Scenario 2: Recording a Login Test

**User Goal:** Record a login test for their web application

**Prerequisites:**
- Framework initialized (from Scenario 1)
- User is in project directory

**Step-by-Step Interaction:**

```bash
# Step 1: User navigates to project directory
$ cd my-webapp-tests

# Step 2: User configures application URL in .env
$ nano .env
# User edits:
APP_URL=https://myapp.example.com
TEST_USER=test@example.com
TEST_PASSWORD=SecurePass123!

# Step 3: User starts recording
$ playwright-ai record

🎥 Playwright Scenario Recorder

? Enter the starting URL: https://myapp.example.com
✔ Enter the starting URL: https://myapp.example.com

? Enter scenario name: user_login
✔ Enter scenario name: user_login

⠸ Launching Playwright recorder...
⠼ Recorder is now open. Perform your test actions in the browser.
  Close the browser when done.

# Browser window opens with Playwright Inspector
# User performs these actions in browser:
# 1. Navigate to https://myapp.example.com
# 2. Click on "Sign In" button
# 3. Fill email field with "test@example.com"
# 4. Fill password field with "SecurePass123!"
# 5. Click "Login" button
# 6. Wait for dashboard to load
# 7. Verify "Welcome" text appears
# 8. Close browser

✔ Recording completed

✅ Recording saved to: recordings/user_login_2025-11-22.py

ℹ To convert this recording to BDD, run:
  playwright-ai convert recordings/user_login_2025-11-22.py


# Step 4: User views the recording
$ cat recordings/user_login_2025-11-22.py

from playwright.sync_api import Playwright, sync_playwright

def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    page.goto("https://myapp.example.com")
    page.click("text=Sign In")
    page.fill("#email", "test@example.com")
    page.fill("#password", "SecurePass123!")
    page.click("button[type='submit']")
    page.wait_for_selector("text=Welcome")

    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
```

**What Happens:**
1. CLI prompts for URL and scenario name
2. Validates URL format (must start with http/https)
3. Validates scenario name (alphanumeric, hyphens, underscores)
4. Validates user is in project directory (checks for features/, steps/)
5. Creates recordings/ directory if not exists
6. Launches Playwright codegen with specified URL
7. User performs actions in browser
8. Playwright records all interactions
9. Saves recording as Python file
10. Displays path to saved recording

**User State After:**
- Has recorded test in `recordings/` directory
- Ready to convert to BDD format
- Raw Playwright code available for reference

---

## Converting Recordings Flow

### Scenario 3: Converting Recording to BDD with AI

**User Goal:** Convert recorded test to maintainable BDD scenario

**Prerequisites:**
- Recording exists (from Scenario 2)
- AI configured with API key

**Step-by-Step Interaction:**

```bash
# Step 1: User converts recording to BDD
$ playwright-ai convert recordings/user_login_2025-11-22.py

🔄 Converting Recording to BDD

ℹ Scenario: user_login
ℹ Recording file: recordings/user_login_2025-11-22.py

⠸ Parsing recording...
✔ Parsed 6 actions

⠸ Converting to BDD using AI...
ℹ Using Chain of Thought reasoning for BDD generation...

  # AI processes the recording through reasoning steps:
  # Step 1: Analyzing page structure and user intent
  # Step 2: Identifying reusable components
  # Step 3: Mapping to BDD Given/When/Then format
  # Step 4: Extracting locators and test data
  # Step 5: Generating helper suggestions

✔ Conversion complete

⠸ Writing output files...
  Created: features/user_login.feature
  Created: config/user_login_locators.json
  Created: fixtures/user_login_data.json
  Created: steps/user_login_steps.py (if needed)
✔ All files created


✅ Conversion complete!

ℹ Generated files:
  • features/user_login.feature
  • config/user_login_locators.json
  • fixtures/user_login_data.json
  • steps/user_login_steps.py (if needed)

ℹ To run this scenario:
  behave features/user_login.feature


# Step 2: User views generated feature file
$ cat features/user_login.feature

Feature: User Authentication
  As a registered user
  I want to log in to the application
  So that I can access my dashboard

  Background:
    Given the application is running
    And I am on the login page

  @smoke @authentication
  Scenario: Successful login with valid credentials
    Given I am not logged in
    When I click on "Sign In" link
    And I enter "test@example.com" in the email field
    And I enter my password in the password field
    And I click the "Login" button
    Then I should see the dashboard
    And I should see "Welcome" message


# Step 3: User views generated locators
$ cat config/user_login_locators.json

{
  "sign_in_link": "text=Sign In",
  "email_field": "#email",
  "password_field": "#password",
  "login_button": "button[type='submit']",
  "welcome_message": "text=Welcome",
  "dashboard_container": "[data-testid='dashboard']"
}


# Step 4: User views generated test data
$ cat fixtures/user_login_data.json

{
  "valid_user": {
    "email": "test@example.com",
    "password": "SecurePass123!",
    "expected_welcome": "Welcome"
  },
  "invalid_user": {
    "email": "invalid@example.com",
    "password": "WrongPassword",
    "expected_error": "Invalid credentials"
  }
}


# Step 5: User views generated steps (if custom steps needed)
$ cat steps/user_login_steps.py

from behave import given, when, then
from config.user_login_locators import locators
from fixtures.user_login_data import test_data

@given('I am on the login page')
def navigate_to_login(context):
    context.page.goto(context.config.APP_URL)

@when('I click on "{link_name}" link')
def click_sign_in(context, link_name):
    locator = locators.get(f"{link_name.lower().replace(' ', '_')}_link")
    context.page.click(locator)

@when('I enter "{email}" in the email field')
def enter_email(context, email):
    context.page.fill(locators['email_field'], email)

@when('I enter my password in the password field')
def enter_password(context):
    password = test_data['valid_user']['password']
    context.page.fill(locators['password_field'], password)

@when('I click the "{button_name}" button')
def click_login(context, button_name):
    context.page.click(locators['login_button'])

@then('I should see the dashboard')
def verify_dashboard(context):
    context.page.wait_for_selector(locators['dashboard_container'])
    assert context.page.is_visible(locators['dashboard_container'])

@then('I should see "{message}" message')
def verify_welcome(context, message):
    assert context.page.is_visible(locators['welcome_message'])
```

**What Happens:**
1. CLI validates recording file exists
2. Parses Playwright Python code using regex
3. Extracts actions: goto, click, fill, select
4. Sends actions to AI (Anthropic Claude) with Chain of Thought reasoning
5. AI analyzes actions and generates:
   - Feature file with Gherkin syntax
   - Step definitions in Python
   - Locator mappings
   - Test data fixtures
   - Helper function suggestions
6. Writes all files to appropriate directories
7. Displays file paths and next steps

**AI Reasoning Process:**
```json
{
  "steps": [
    {
      "step": 1,
      "thought": "Analyzing the recording, I see a standard login flow: navigate to site, click sign in, fill credentials, submit, verify success",
      "action": "Identify user intent: Authenticate user",
      "confidence": 0.95
    },
    {
      "step": 2,
      "thought": "The flow follows a common pattern. I'll structure it with Background for setup, Scenario for the test",
      "action": "Design BDD structure with Background and Scenario",
      "confidence": 0.92
    },
    {
      "step": 3,
      "thought": "Locators should be extracted to config for maintainability. Email and password fields are clear candidates",
      "action": "Extract locators: email_field, password_field, login_button, etc.",
      "confidence": 0.90
    },
    {
      "step": 4,
      "thought": "Test data should include both valid and invalid cases. I'll generate both scenarios",
      "action": "Create test data fixtures with valid and invalid users",
      "confidence": 0.88
    },
    {
      "step": 5,
      "thought": "Steps are generic enough to use common_steps.py, but custom validation may need specific steps",
      "action": "Generate custom steps for dashboard verification",
      "confidence": 0.85
    }
  ],
  "finalAnswer": "Generated complete BDD scenario with feature file, locators, test data, and step definitions",
  "reasoning": "The recording shows a standard authentication flow that benefits from BDD structure for maintainability and readability"
}
```

**User State After:**
- Has complete BDD test ready to run
- Locators organized in config
- Test data in fixtures
- Can run test immediately or customize

---

## Running Tests Flow

### Scenario 4: Running BDD Tests

**User Goal:** Execute the generated BDD tests

**Prerequisites:**
- BDD scenarios created (from Scenario 3)
- Dependencies installed

**Step-by-Step Interaction:**

```bash
# Step 1: User activates virtual environment
$ source venv/bin/activate
(venv) $

# Step 2: User runs all tests
(venv) $ behave

Feature: User Authentication # features/user_login.feature:1
  As a registered user
  I want to log in to the application
  So that I can access my dashboard

  Background:   # features/user_login.feature:6

  @smoke @authentication
  Scenario: Successful login with valid credentials  # features/user_login.feature:10
    Given the application is running                  # steps/common_steps.py:15 0.025s
    And I am on the login page                        # steps/user_login_steps.py:8 1.234s
    Given I am not logged in                          # steps/common_steps.py:22 0.018s
    When I click on "Sign In" link                    # steps/user_login_steps.py:12 0.145s
    And I enter "test@example.com" in the email field # steps/user_login_steps.py:17 0.098s
    And I enter my password in the password field     # steps/user_login_steps.py:21 0.076s
    And I click the "Login" button                    # steps/user_login_steps.py:26 0.321s
    Then I should see the dashboard                   # steps/user_login_steps.py:30 0.542s
    And I should see "Welcome" message                # steps/user_login_steps.py:35 0.067s

1 feature passed, 0 failed, 0 skipped
1 scenario passed, 0 failed, 0 skipped
9 steps passed, 0 failed, 0 skipped, 0 undefined
Took 0m2.526s


# Step 3: User runs tests with specific tags
(venv) $ behave --tags=@smoke

# Same output as above (only smoke-tagged scenarios run)


# Step 4: User runs tests with reporting
(venv) $ behave -f allure_behave.formatter:AllureFormatter -o reports/allure

Feature: User Authentication
  Scenario: Successful login with valid credentials
    ✓ Given the application is running
    ✓ And I am on the login page
    ✓ Given I am not logged in
    ✓ When I click on "Sign In" link
    ✓ And I enter "test@example.com" in the email field
    ✓ And I enter my password in the password field
    ✓ And I click the "Login" button
    ✓ Then I should see the dashboard
    ✓ And I should see "Welcome" message

1 feature passed, 0 failed, 0 skipped
1 scenario passed, 0 failed, 0 skipped
9 steps passed, 0 failed, 0 skipped, 0 undefined

Reports generated in: reports/allure/


# Step 5: User views Allure report
(venv) $ allure serve reports/allure

Generating report to temp directory...
Report successfully generated to /tmp/allure-report-xyz
Starting web server...
Server started at http://localhost:12345
Press Ctrl+C to exit

# Browser opens with interactive HTML report showing:
# - Test execution timeline
# - Pass/fail statistics
# - Screenshots (if enabled)
# - Step-by-step execution details
# - Failure analysis
# - Historical trends


# Step 6: Test fails - self-healing activates
(venv) $ behave features/user_login.feature

Feature: User Authentication
  Scenario: Successful login with valid credentials
    ✓ Given the application is running
    ✓ And I am on the login page
    ✓ Given I am not logged in
    ! When I click on "Sign In" link

    ⚠ Locator failed: text=Sign In
    ℹ Activating self-healing locator...
    ⠸ Using AI to find alternative locator...

    # AI analyzes page HTML and suggests alternatives:
    {
      "locator": "button:has-text('Sign In')",
      "confidence": 0.95,
      "alternatives": [
        "[data-testid='signin-button']",
        "//button[contains(text(), 'Sign In')]",
        ".auth-button.signin"
      ]
    }

    ✔ Healed locator found: button:has-text('Sign In')
    ℹ Logging healing event for future optimization

    ✓ When I click on "Sign In" link (healed)
    ✓ And I enter "test@example.com" in the email field
    ✓ And I enter my password in the password field
    ✓ And I click the "Login" button
    ✓ Then I should see the dashboard
    ✓ And I should see "Welcome" message

1 feature passed, 0 failed, 0 skipped
1 scenario passed, 0 failed, 0 skipped (1 healed)
9 steps passed, 0 failed, 0 skipped, 0 undefined

⚠ Recommendations:
  • Update locator in config/user_login_locators.json:
    "sign_in_link": "button:has-text('Sign In')"
```

**What Happens:**
1. Behave reads feature files from `features/` directory
2. Loads step definitions from `steps/` directory
3. Executes `environment.py` hooks:
   - `before_all()`: Set up global config
   - `before_scenario()`: Launch browser, initialize helpers
   - `before_step()`: Capture screenshots if enabled
   - `after_step()`: Log step results
   - `after_scenario()`: Close browser, save videos
   - `after_all()`: Generate summary report
4. For each scenario:
   - Executes Background steps first
   - Then executes scenario steps in order
   - Uses healing_locator.py if locator fails
   - Uses wait_manager.py for intelligent waits
5. Generates reports in specified format
6. Displays summary with timing and statistics

**Helper Activations During Execution:**

**Self-Healing Locator (`healing_locator.py`):**
```python
# When original locator fails:
try:
    page.click("text=Sign In")  # Original locator fails
except Exception:
    # Healing activates
    healer = HealingLocator(ai_client)

    # Capture page context
    html = page.content()

    # AI suggests alternative
    suggestion = healer.heal(
        failed_locator="text=Sign In",
        element_description="Sign in button",
        page_html=html
    )

    # Try suggested locator
    page.click(suggestion.locator)

    # Log healing event
    healer.log_healing(original, suggestion)
```

**Smart Wait Manager (`wait_manager.py`):**
```python
# Learns from execution history
wait_manager = WaitManager()

# First run: uses default timeout
wait_manager.wait_for_element(page, "#dashboard", timeout=10000)
# Actual time: 2.3s

# Logs performance
wait_manager.log_performance("#dashboard", 2.3)

# Second run: optimizes timeout
wait_manager.wait_for_element(page, "#dashboard")  # Uses learned 3s timeout
```

**Screenshot Manager (`screenshot_manager.py`):**
```python
# After each step:
if config.ENABLE_SCREENSHOTS:
    screenshot_manager.capture_step(
        page=page,
        scenario_name="user_login",
        step_name="click_sign_in",
        timestamp=time.time()
    )
    # Saves to: reports/screenshots/user_login/step_3_click_sign_in_20251122_143022.png
```

**User State After:**
- Tests executed
- Reports generated
- Self-healing activated if needed
- Performance data collected
- Ready to iterate or add more tests

---

## AI-Powered Features Flow

### Scenario 5: Using Advanced AI Reasoning

**User Goal:** Use Tree of Thought reasoning for complex test scenario generation

**Prerequisites:**
- Framework with AI enabled
- Complex application workflow to test

**Step-by-Step Interaction:**

```bash
# Step 1: User has a complex recording
$ cat recordings/complex_workflow_2025-11-22.py

# Recording shows:
# 1. Login
# 2. Navigate to Projects
# 3. Create new project
# 4. Add team members (multiple)
# 5. Assign tasks
# 6. Set deadlines
# 7. Configure permissions
# 8. Publish project
# 9. Verify notifications sent
# 10. Verify project appears in dashboard

# Step 2: User converts with explicit AI reasoning request
$ playwright-ai convert recordings/complex_workflow_2025-11-22.py \
  --use-reasoning tree-of-thought

🔄 Converting Recording to BDD

ℹ Scenario: complex_workflow
ℹ Recording file: recordings/complex_workflow_2025-11-22.py
ℹ Reasoning mode: Tree of Thought

⠸ Parsing recording...
✔ Parsed 47 actions

⠸ Converting to BDD using AI with Tree of Thought reasoning...

ℹ Exploring multiple reasoning paths...

  🌱 Initial: Analyzing complex workflow with multiple phases

  🌿 Branch 1: Linear scenario approach
     Evaluation: 0.65 - Simple but may miss optimization opportunities

  🌿 Branch 2: Feature decomposition approach
     Evaluation: 0.88 - Breaks into reusable features
     🍃 Sub-branch 2a: By domain (Projects, Tasks, Permissions)
        Evaluation: 0.92 - Clear separation of concerns
     🍃 Sub-branch 2b: By user role (Admin, Member, Viewer)
        Evaluation: 0.75 - Less applicable here

  🌿 Branch 3: Scenario outline with examples
     Evaluation: 0.82 - Good for data variation

  🎯 Selected Best Path: Feature decomposition by domain (Branch 2a, Eval: 0.92)

  ℹ Reasoning:
     • Complex workflow benefits from modular features
     • Domain separation enables parallel development
     • Reusable steps across features
     • Better maintenance and readability

✔ Conversion complete with Tree of Thought reasoning

⠸ Writing output files...
  Created: features/project_management.feature
  Created: features/team_collaboration.feature
  Created: features/permissions_setup.feature
  Created: config/project_locators.json
  Created: config/team_locators.json
  Created: config/permissions_locators.json
  Created: fixtures/project_data.json
  Created: fixtures/team_data.json
  Created: steps/project_steps.py
  Created: steps/team_steps.py
  Created: steps/permissions_steps.py
  Created: helpers/project_helper.py
✔ All files created


# Step 3: User views decomposed features
$ cat features/project_management.feature

Feature: Project Management
  As a project manager
  I want to create and configure projects
  So that I can organize work

  Background:
    Given I am logged in as project manager
    And I am on the projects page

  @project @smoke
  Scenario: Create new project with basic details
    When I click "New Project" button
    And I enter project name "Q4 Marketing Campaign"
    And I enter project description
    And I set project start date
    And I set project deadline
    And I click "Create" button
    Then I should see "Project created successfully"
    And the project should appear in my projects list


$ cat features/team_collaboration.feature

Feature: Team Collaboration
  As a project manager
  I want to add team members to projects
  So that we can collaborate effectively

  Background:
    Given I am logged in as project manager
    And I have a project "Q4 Marketing Campaign"

  @team @collaboration
  Scenario Outline: Add team member with role
    When I open project "Q4 Marketing Campaign"
    And I click "Add Member" button
    And I search for user "<email>"
    And I select role "<role>"
    And I click "Add" button
    Then I should see "<email>" in team members
    And "<email>" should have role "<role>"

    Examples:
      | email              | role        |
      | john@example.com   | Developer   |
      | jane@example.com   | Designer    |
      | bob@example.com    | QA Engineer |


# Step 4: User runs decomposed feature suite
$ behave

Feature: Project Management
  Scenario: Create new project with basic details
    ✓ All steps passed

Feature: Team Collaboration
  Scenario Outline: Add team member with role -- @1.1
    ✓ All steps passed
  Scenario Outline: Add team member with role -- @1.2
    ✓ All steps passed
  Scenario Outline: Add team member with role -- @1.3
    ✓ All steps passed

Feature: Permissions Setup
  Scenario: Configure project permissions
    ✓ All steps passed

3 features passed, 0 failed, 0 skipped
5 scenarios passed, 0 failed, 0 skipped
42 steps passed, 0 failed, 0 skipped, 0 undefined
Took 0m15.432s
```

**What Happens with Tree of Thought:**
1. AI generates multiple alternative approaches (branches)
2. Each branch is evaluated for quality and appropriateness
3. Best branches are expanded further (sub-branches)
4. All paths are scored and compared
5. Best path selected based on evaluation criteria
6. Final output synthesized from best path

**Reasoning Tree Structure:**
```
Root: Analyze complex workflow
├── Branch 1: Linear scenario (0.65)
├── Branch 2: Feature decomposition (0.88) ← Selected
│   ├── 2a: By domain (0.92) ← Best path
│   └── 2b: By role (0.75)
└── Branch 3: Scenario outline (0.82)
```

**Benefits Observed:**
- Better organized test suite
- Reusable components
- Parallel execution possible
- Easier maintenance
- Clear separation of concerns

**User State After:**
- Has modular, well-organized test suite
- Can run features independently
- Can extend easily
- Better test maintainability

---

## Common Workflows

### Workflow 1: Daily Development Cycle

```bash
# Morning: Pull latest changes
$ cd my-webapp-tests
$ git pull origin main

# Update dependencies if needed
$ source venv/bin/activate
$ pip install -r requirements.txt --upgrade

# Run smoke tests to verify environment
$ behave --tags=@smoke --format progress

# Development work happens...
# Developer changes application code

# Record new test for new feature
$ playwright-ai record --url https://localhost:3000 --scenario-name new_feature

# Convert recording
$ playwright-ai convert recordings/new_feature_*.py

# Run new test
$ behave features/new_feature.feature

# Run full regression
$ behave --tags=@regression

# Commit changes
$ git add features/ config/ fixtures/
$ git commit -m "Add tests for new feature"
$ git push origin feature-branch
```

### Workflow 2: CI/CD Pipeline

```yaml
# .github/workflows/tests.yml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium

      - name: Run smoke tests
        run: behave --tags=@smoke
        env:
          APP_URL: ${{ secrets.STAGING_URL }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_KEY }}

      - name: Run regression tests
        run: behave --tags=@regression
        if: github.event_name == 'push'

      - name: Upload reports
        uses: actions/upload-artifact@v2
        if: always()
        with:
          name: test-reports
          path: reports/
```

### Workflow 3: Data-Driven Testing

```bash
# Generate test data with AI
$ python
>>> from helpers.data_generator import DataGenerator
>>> gen = DataGenerator(ai_client)
>>>
>>> schema = {
...     "users": {
...         "count": 10,
...         "fields": {
...             "name": "full_name",
...             "email": "email",
...             "role": ["admin", "user", "guest"]
...         }
...     }
... }
>>>
>>> data = gen.generate(schema)
>>> gen.save_to_file(data, 'fixtures/users_dataset.json')

# Use generated data in scenario
$ cat features/user_management.feature

Scenario Outline: User operations with different roles
  Given I am logged in as "<role>"
  When I perform "<action>"
  Then I should see "<result>"

  Examples: fixtures/users_dataset.json
```

---

## Troubleshooting Flows

### Issue 1: Locator Failure

```bash
# Test fails with locator error
$ behave features/login.feature

Scenario: Login
  ✗ When I click the login button
    playwright._impl._api_types.TimeoutError:
    Timeout 30000ms exceeded waiting for selector "button#login"

# Enable debug mode
$ behave features/login.feature --no-capture --format plain

# Or use self-healing
$ cat config/config.py
# Change:
ENABLE_HEALING = True

$ behave features/login.feature
⚠ Locator failed: button#login
ℹ Activating self-healing...
✔ Found alternative: button:has-text("Login")
✓ Test passed with healed locator

# Update config with healed locator
$ nano config/login_locators.json
# Update "login_button": "button:has-text('Login')"
```

### Issue 2: AI API Failure

```bash
# AI call fails
$ playwright-ai convert recording.py

ERROR: Failed to convert recording
CAUSE: Anthropic API error: Rate limit exceeded
ACTION: Wait 60 seconds and retry, or use fallback mode

# Use fallback template-based conversion
$ playwright-ai convert recording.py --no-ai

⚠ AI not available. Using template-based conversion.
✔ Conversion complete (template mode)

ℹ Note: Template conversion is simpler than AI conversion.
  You may need to customize the generated files.
```

### Issue 3: Dependency Issues

```bash
# Dependencies broken
$ behave
ModuleNotFoundError: No module named 'anthropic'

# Reinstall dependencies
$ source venv/bin/activate
$ pip install -r requirements.txt

# If virtual env corrupted
$ rm -rf venv
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ playwright install chromium
```

---

## Advanced Usage

### Custom Helper Functions

```bash
# Create custom helper
$ cat helpers/custom_helper.py

from helpers.healing_locator import HealingLocator

class CustomHelper:
    def __init__(self, page, ai_client):
        self.page = page
        self.healer = HealingLocator(ai_client)

    def smart_click(self, locator, description):
        """Click with automatic healing"""
        try:
            self.page.click(locator)
        except Exception:
            healed = self.healer.heal(locator, description, self.page.content())
            self.page.click(healed.locator)

# Use in steps
$ cat steps/custom_steps.py

from helpers.custom_helper import CustomHelper

@when('I smartly click "{element}"')
def smart_click(context, element):
    helper = CustomHelper(context.page, context.ai_client)
    helper.smart_click(f"text={element}", element)
```

### Performance Optimization

```bash
# Run with performance profiling
$ behave --define profile=true

# View wait optimization suggestions
$ cat reports/wait_optimization.json

{
  "optimizations": [
    {
      "locator": "#dashboard",
      "currentTimeout": 10000,
      "recommendedTimeout": 3000,
      "reason": "Element consistently loads in <2s"
    }
  ]
}

# Apply optimizations
$ python scripts/apply_wait_optimizations.py
✔ Updated wait times in wait_manager.py
```

---

## Summary

**Key Interaction Patterns:**

1. **Interactive Prompts:** CLI guides users through configuration
2. **Spinners & Progress:** Visual feedback for long operations
3. **Color Coding:** Success (green), errors (red), warnings (yellow), info (cyan)
4. **Clear Next Steps:** Always tell user what to do next
5. **Graceful Failures:** Fallbacks and helpful error messages
6. **AI Transparency:** Show when AI is working and what it's doing
7. **Self-Healing:** Automatic recovery from common failures
8. **Comprehensive Logs:** Detailed logs for debugging

**User Experience Principles:**

- **Guided:** Prompts for missing information
- **Transparent:** Shows what's happening
- **Forgiving:** Handles errors gracefully
- **Intelligent:** Uses AI to assist
- **Fast:** Optimizes performance
- **Professional:** Clean output and reports

**Command Sequence for Complete Workflow:**

```bash
# 1. Setup
playwright-ai init
cd my-project
nano .env

# 2. Create tests
playwright-ai record --url https://app.com --scenario-name test1
playwright-ai convert recordings/test1_*.py

# 3. Run tests
source venv/bin/activate
behave --tags=@smoke

# 4. Iterate
playwright-ai record --scenario-name test2
playwright-ai convert recordings/test2_*.py
behave

# 5. Deploy
git add .
git commit -m "Add E2E tests"
git push
```

---

**Document Status:** Complete
**Last Updated:** 2025-11-22
