# Real-World Integration Tests

## Overview

This test suite provides comprehensive end-to-end testing of the AI Playwright Framework with real-world scenarios. The tests validate all aspects of the framework including creation, recording, script injection with Page Object Model (POM), duplicate elimination, reusability enhancement, and execution with various challenges.

## Test Coverage

### 1. Framework Creation Tests (`real-world-scenarios.test.ts`)

Tests the complete framework generation process:

- ✅ **Complete Python BDD framework structure** - Verifies all directories and files are created
- ✅ **AI capabilities enabled** - Ensures Claude AI integration is properly configured
- ✅ **Helper files generation** - Validates auth, healing, wait manager, and other helpers
- ✅ **Configuration files** - Checks requirements.txt, .gitignore, config.py

**Expected Output:**
```
✓ Framework structure created successfully
✓ AI capabilities configured
```

### 2. Different Types of Script Recording

Tests various recording scenarios from simple to complex:

#### Simple Navigation & Clicks
- **Website:** https://the-internet.herokuapp.com
- **Actions:** Navigate, click links, wait for elements
- **Validates:** Basic BDD scenario generation

#### Form Interactions
- **Website:** https://the-internet.herokuapp.com/login
- **Actions:** Fill username, password, submit, verify success
- **Validates:**
  - Form field handling
  - Test data extraction
  - Locator generation

#### Multi-Step Workflows
- **Websites:** Checkboxes, Dropdowns
- **Actions:** Select checkboxes, choose dropdown options
- **Validates:**
  - Complex step sequences
  - Multiple page interactions
  - Step definition generation

#### E-Commerce Checkout Flow
- **Website:** https://www.saucedemo.com
- **Actions:** Login → Add to cart → Checkout → Fill shipping → Continue
- **Validates:**
  - Long scenario generation
  - Multiple form handling
  - Business workflow BDD

**Expected Output:**
```
✓ Simple navigation recorded and converted to BDD
✓ Form interactions recorded with test data extraction
✓ Complex multi-step workflow recorded
✓ E-commerce checkout flow recorded
```

### 3. Script Injection to Automation Framework with POM

Tests the intelligent Page Object Model injection system:

#### First Page Object Creation
- Creates new LoginPage with locators and methods
- Verifies page object file structure
- Validates registry tracking

#### Page Object Extension (Not Replacement)
- Extends existing LoginPage with new locators
- Merges without duplicating existing elements
- Preserves existing functionality

#### Duplicate Locator Elimination
- Detects duplicate locators across page objects
- Filters out duplicates during injection
- Keeps only unique new locators

#### Multiple Page Objects for Different Pages
- Creates separate page objects (LoginPage, DashboardPage)
- Manages page object registry
- Tracks relationships between pages

**Expected Output:**
```
✓ First Page Object created successfully
✓ Page Object extended with new locators
✓ Duplicate locators eliminated
✓ Multiple Page Objects created for different pages
```

### 4. Duplicate Elimination Tests

Tests the semantic reuse engine for step definitions:

#### Exact Duplicate Identification
- Uses embeddings to find identical steps
- 95%+ similarity score for exact matches
- Suggests direct reuse without adaptation

#### Similar Steps with Adaptations
- Finds semantically similar steps (75%+ similarity)
- Identifies required adaptations
- Suggests parameter changes needed

#### Reuse Metrics Tracking
- Tracks reuse attempts
- Calculates reuse rate
- Reports direct vs adapted reuse

**Expected Output:**
```
✓ Exact duplicate identified for reuse
✓ Similar step found with 87% similarity
=== Reuse Statistics ===
Total steps indexed: 3
Reuse attempts: 3
Reuse rate: 67%
```

### 5. Reusability Enhancement Tests

Tests pattern analysis across multiple scenarios:

#### Pattern Analysis
- Identifies common steps across features
- Finds reusable locators
- Detects duplicate scenarios

#### Step Extraction for Reusability
- Suggests extracting common patterns
- Creates reusable step libraries
- Optimizes test maintenance

**Expected Output:**
```
=== Pattern Analysis Results ===
{
  "commonSteps": ["Given I am on the login page", ...],
  "reusableLocators": ["#username", "#password", ...],
  "duplicateScenarios": []
}
```

### 6. Running Scripts with Real-World Challenges

Tests execution with difficult scenarios:

#### Lazy Loading Elements
- **Website:** https://the-internet.herokuapp.com/dynamic_loading/2
- **Challenge:** Elements appear after delay
- **Solution:** Smart wait strategies, wait optimization

#### Dynamic/Flaky Elements
- **Website:** https://the-internet.herokuapp.com/dynamic_controls
- **Challenge:** Elements that change or disappear
- **Solution:** Self-healing locators, alternative selectors

#### Different Wait Strategies
- Explicit waits for visibility
- Network idle waits
- Timeout-based waits
- Validates multiple approaches

#### Infinite Scroll
- **Website:** https://the-internet.herokuapp.com/infinite_scroll
- **Challenge:** Content loads dynamically on scroll
- **Solution:** Scroll simulation, dynamic element waiting

#### Disappearing Elements
- **Website:** https://the-internet.herokuapp.com/disappearing_elements
- **Challenge:** Elements randomly appear/disappear
- **Solution:** Conditional logic, retry mechanisms

**Expected Output:**
```
✓ Lazy loading handled with wait optimization
✓ Dynamic elements handled with self-healing
  Original: button#old-remove-button
  Healed: button (92% confidence)
✓ Multiple wait strategies tested
✓ Infinite scroll handled
✓ Disappearing elements handled with conditional logic
```

### 7. End-to-End Integration Tests

Complete workflow tests:

#### Full Workflow
1. Create framework
2. Record test scenario (login flow)
3. Inject into framework with POM
4. Verify all artifacts generated
5. Validate test structure

#### Multiple Scenarios with Cross-Page Reuse
- Tests multiple features (login, checkboxes)
- Validates separate feature files
- Checks for step reuse across features

**Expected Output:**
```
=== Starting Full E2E Workflow ===
Step 1: Creating framework...
✓ Framework created
Step 2: Recording test scenario...
✓ Scenario recorded and converted to BDD
Step 3: Injecting into framework...
✓ Scripts injected with Page Object Model
Step 4: Verifying framework integrity...
✓ All files verified
Step 5: Validating test structure...
✓ Test structure validated
=== Full E2E Workflow Completed Successfully ===
```

### 8. Advanced Real-World Scenarios

#### Complex Form Test Data Generation
- Generates realistic test data for complex forms
- Creates nested data structures
- Handles multiple data types (email, phone, address, etc.)

#### Wait Optimization Across Multiple Runs
- Analyzes wait times from multiple test runs
- Suggests optimal timeout values
- Reduces test execution time

## Real-World Test Websites

The tests use actual public websites to ensure real-world validity:

### Simple Sites
- `example.com` - Basic static content
- `httpbin.org/forms/post` - Simple HTTP testing

### Moderate Complexity
- `the-internet.herokuapp.com` - Various test scenarios
  - `/login` - Authentication testing
  - `/checkboxes` - Checkbox interactions
  - `/dropdown` - Dropdown selections

### Forms
- `demoqa.com` - Complex forms and widgets
  - `/automation-practice-form` - Multi-field forms
  - `/text-box` - Text input validation

### E-Commerce
- `automationexercise.com` - Full e-commerce site
- `saucedemo.com` - Login-protected shopping

### Lazy Loading
- `the-internet.herokuapp.com/infinite_scroll` - Infinite scroll
- `the-internet.herokuapp.com/dynamic_loading/2` - Dynamic content

### Flaky/Dynamic Elements
- `the-internet.herokuapp.com/dynamic_controls` - Dynamic controls
- `the-internet.herokuapp.com/dynamic_loading/1` - Hidden elements
- `the-internet.herokuapp.com/disappearing_elements` - Random elements

## Running the Tests

### Prerequisites

```bash
# Install dependencies
npm install

# Install Playwright browsers
npx playwright install chromium

# Set API key in .env file
echo "ANTHROPIC_API_KEY=your-key-here" > cli/.env
```

### Run All Tests

```bash
npm test
```

### Run Specific Test Suites

```bash
# Run only real-world scenarios
npm run test:real-world

# Run all integration tests
npm run test:integration

# Run with watch mode
npm run test:watch
```

### Run Individual Test Suites

```bash
# Framework creation tests only
npm test -- --testNamePattern="Framework Creation Tests"

# Recording tests only
npm test -- --testNamePattern="Different Types of Script Recording"

# POM injection tests only
npm test -- --testNamePattern="Script Injection to Automation Framework"

# Duplicate elimination tests only
npm test -- --testNamePattern="Duplicate Elimination Tests"

# Reusability tests only
npm test -- --testNamePattern="Reusability Enhancement Tests"

# Real-world challenges only
npm test -- --testNamePattern="Running Scripts with Real-World Challenges"

# E2E tests only
npm test -- --testNamePattern="End-to-End Integration Tests"
```

## Test Configuration

### Environment Variables

Create a `.env` file in the `cli` directory:

```env
ANTHROPIC_API_KEY=sk-ant-api03-...
NODE_ENV=test
ENABLE_PHOENIX_TRACING=false
```

### Timeouts

Tests have appropriate timeouts based on complexity:
- Simple tests: 30 seconds
- AI generation tests: 60 seconds
- Complex workflows: 90-120 seconds

Configure in `jest.config.js`:
```javascript
testTimeout: 30000  // Default 30s
```

## Key Features Tested

### 1. **Duplicate Elimination**
- ✅ Semantic similarity detection
- ✅ Exact match identification
- ✅ Adaptation suggestions
- ✅ Reuse metrics tracking

### 2. **Reusability Enhancement**
- ✅ Pattern analysis across scenarios
- ✅ Common step identification
- ✅ Reusable locator detection
- ✅ Step extraction suggestions

### 3. **Page Object Model**
- ✅ Intelligent page object creation
- ✅ Extension over replacement
- ✅ Duplicate locator prevention
- ✅ Multi-page management

### 4. **Self-Healing**
- ✅ Failed locator recovery
- ✅ Alternative selector suggestions
- ✅ Confidence scoring
- ✅ Element description matching

### 5. **Wait Optimization**
- ✅ Actual vs timeout analysis
- ✅ Wait strategy recommendations
- ✅ Performance optimization
- ✅ Multi-run analysis

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install
      - run: npx playwright install --with-deps chromium
      - run: npm test
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Troubleshooting

### Browser Download Issues

If Playwright browser download fails:

```bash
# Try manual installation
npx playwright install chromium --force

# Or use system browser
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
```

### API Rate Limiting

If hitting Claude API rate limits:

```bash
# Reduce concurrent tests
npm test -- --maxWorkers=1
```

### Timeout Errors

If tests timeout:

```bash
# Increase timeout in jest.config.js
testTimeout: 60000  // 60 seconds
```

## Test Results Example

```
Real-World Framework Tests
  ✓ Framework Creation Tests
    ✓ should create complete Python BDD framework structure (2543 ms)
    ✓ should create framework with AI capabilities enabled (1876 ms)
  ✓ Different Types of Script Recording
    ✓ should record simple navigation and clicks (5234 ms)
    ✓ should record form interactions (6127 ms)
    ✓ should record complex multi-step workflow (7891 ms)
    ✓ should record e-commerce checkout flow (9456 ms)
  ✓ Script Injection to Automation Framework with POM
    ✓ should inject first script and create new Page Object (4123 ms)
    ✓ should extend existing Page Object (3876 ms)
    ✓ should handle duplicate locator elimination (2341 ms)
    ✓ should create separate Page Objects (2987 ms)
  ✓ Duplicate Elimination Tests
    ✓ should identify exact duplicate steps (3124 ms)
    ✓ should identify similar steps with adaptations (3456 ms)
    ✓ should track reuse metrics (2789 ms)
  ✓ Reusability Enhancement Tests
    ✓ should analyze patterns across multiple scenarios (8234 ms)
    ✓ should suggest step extraction (3567 ms)
  ✓ Running Scripts with Real-World Challenges
    ✓ should handle lazy loading elements (7891 ms)
    ✓ should handle dynamic/flaky elements (6234 ms)
    ✓ should handle different wait strategies (11234 ms)
    ✓ should handle infinite scroll (5678 ms)
    ✓ should handle disappearing elements (4567 ms)
  ✓ End-to-End Integration Tests
    ✓ should complete full workflow (15234 ms)
    ✓ should handle multiple scenarios (12456 ms)
  ✓ Advanced Real-World Scenarios
    ✓ should generate test data for complex forms (6789 ms)
    ✓ should optimize waits across multiple runs (7234 ms)

Test Suites: 1 passed, 1 total
Tests:       25 passed, 25 total
Time:        152.456 s
```

## Contributing

When adding new tests:

1. Use real-world websites (no mocks)
2. Test actual framework capabilities
3. Include positive and negative scenarios
4. Document expected behaviors
5. Add appropriate timeouts
6. Group related tests in describe blocks

## License

MIT
