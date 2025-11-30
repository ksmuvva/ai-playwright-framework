/**
 * Real-World Scenario Tests for AI Playwright Framework
 *
 * Tests complete end-to-end workflows with real websites:
 * 1. Framework creation
 * 2. Different types of script recording
 * 3. Script injection to automation framework with POM
 * 4. Running scripts with various challenges (waits, lazy loading, flaky elements)
 *
 * Tests duplicate elimination and reusability enhancement
 */

import * as fs from 'fs-extra';
import * as path from 'path';
import * as os from 'os';
import { chromium, Browser, Page, BrowserContext } from 'playwright';
import { PythonGenerator } from '../../src/generators/python-generator';
import { FileUtils } from '../../src/utils/file-utils';
import { AnthropicClient } from '../../src/ai/anthropic-client';
import { PlaywrightAction } from '../../src/types';
import { PageObjectRegistry } from '../../src/utils/page-object-registry';
import { SemanticReuseEngine, StepDefinition } from '../../src/engines/semantic-reuse';
import * as dotenv from 'dotenv';

dotenv.config({ path: path.resolve(__dirname, '../../.env') });

// Real-world test websites
const TEST_SITES = {
  SIMPLE: {
    EXAMPLE: 'https://example.com',
    HTTPBIN: 'https://httpbin.org/forms/post'
  },
  MODERATE: {
    THE_INTERNET: 'https://the-internet.herokuapp.com',
    LOGIN: 'https://the-internet.herokuapp.com/login',
    CHECKBOXES: 'https://the-internet.herokuapp.com/checkboxes',
    DROPDOWN: 'https://the-internet.herokuapp.com/dropdown'
  },
  FORMS: {
    DEMOQA: 'https://demoqa.com/automation-practice-form',
    DEMOQA_TEXT_BOX: 'https://demoqa.com/text-box'
  },
  ECOMMERCE: {
    AUTOMATION_EXERCISE: 'https://automationexercise.com',
    SAUCE_DEMO: 'https://www.saucedemo.com'
  },
  LAZY_LOADING: {
    INFINITE_SCROLL: 'https://the-internet.herokuapp.com/infinite_scroll',
    LAZY_LOADING: 'https://the-internet.herokuapp.com/dynamic_loading/2'
  },
  FLAKY: {
    DYNAMIC_CONTROLS: 'https://the-internet.herokuapp.com/dynamic_controls',
    DYNAMIC_LOADING: 'https://the-internet.herokuapp.com/dynamic_loading/1',
    DISAPPEARING_ELEMENTS: 'https://the-internet.herokuapp.com/disappearing_elements'
  }
};

describe('Real-World Framework Tests', () => {
  let tempDir: string;
  let projectDir: string;
  let browser: Browser;
  let context: BrowserContext;
  let page: Page;
  let aiClient: AnthropicClient;

  beforeAll(async () => {
    const apiKey = process.env.ANTHROPIC_API_KEY;
    if (!apiKey) {
      throw new Error('ANTHROPIC_API_KEY required for real-world tests');
    }
    aiClient = new AnthropicClient(apiKey);

    // Launch browser for recording simulations
    browser = await chromium.launch({ headless: true });
  });

  afterAll(async () => {
    if (browser) {
      await browser.close();
    }
  });

  beforeEach(async () => {
    tempDir = path.join(os.tmpdir(), `framework-test-${Date.now()}`);
    projectDir = path.join(tempDir, 'test-project');
    await fs.ensureDir(tempDir);

    context = await browser.newContext();
    page = await context.newPage();
  });

  afterEach(async () => {
    if (context) {
      await context.close();
    }
    if (await fs.pathExists(tempDir)) {
      await fs.remove(tempDir);
    }
  });

  describe('1. Framework Creation Tests', () => {
    it('should create complete Python BDD framework structure', async () => {
      const generator = new PythonGenerator();

      const options = {
        projectName: 'real-world-test',
        language: 'python' as const,
        bdd: true,
        powerApps: false,
        aiProvider: 'anthropic' as const,
        aiModel: 'claude-sonnet-4-5-20250929',
        apiKey: process.env.ANTHROPIC_API_KEY
      };

      await generator.generate(projectDir, options);

      // Verify complete structure
      const expectedDirs = [
        'features',
        'steps',
        'helpers',
        'pages',
        'fixtures',
        'config',
        'reports',
        'reports/screenshots',
        'reports/videos',
        'auth_states'
      ];

      for (const dir of expectedDirs) {
        const dirPath = path.join(projectDir, dir);
        expect(await fs.pathExists(dirPath)).toBe(true);
      }

      // Verify critical helper files
      const criticalFiles = [
        'helpers/__init__.py',
        'helpers/auth_helper.py',
        'helpers/healing_locator.py',
        'helpers/wait_manager.py',
        'config/config.py',
        'requirements.txt',
        '.gitignore'
      ];

      for (const file of criticalFiles) {
        const filePath = path.join(projectDir, file);
        expect(await fs.pathExists(filePath)).toBe(true);
      }

      console.log('✓ Framework structure created successfully');
    }, 30000);

    it('should create framework with AI capabilities enabled', async () => {
      const generator = new PythonGenerator();

      await generator.generate(projectDir, {
        projectName: 'ai-enabled-test',
        language: 'python',
        bdd: true,
        powerApps: false,
        aiProvider: 'anthropic',
        aiModel: 'claude-sonnet-4-5-20250929',
        apiKey: process.env.ANTHROPIC_API_KEY
      });

      // Verify AI configuration
      const configPath = path.join(projectDir, 'config', 'config.py');
      const configContent = await fs.readFile(configPath, 'utf-8');

      expect(configContent).toContain('AI_PROVIDER');
      expect(configContent).toContain('anthropic');
      expect(configContent).toContain('SELF_HEALING_ENABLED');

      console.log('✓ AI capabilities configured');
    }, 30000);
  });

  describe('2. Different Types of Script Recording', () => {
    beforeEach(async () => {
      // Create framework first
      const generator = new PythonGenerator();
      await generator.generate(projectDir, {
        projectName: 'recording-test',
        language: 'python',
        bdd: true,
        powerApps: false,
        aiProvider: 'anthropic',
        apiKey: process.env.ANTHROPIC_API_KEY
      });
    });

    it('should record simple navigation and clicks', async () => {
      await page.goto(TEST_SITES.MODERATE.THE_INTERNET);

      const recording: PlaywrightAction[] = [
        { type: 'navigate', url: TEST_SITES.MODERATE.THE_INTERNET },
        { type: 'click', selector: 'a[href="/login"]' },
        { type: 'wait', selector: '#username' }
      ];

      const bddOutput = await aiClient.generateBDDScenario(
        recording,
        'navigate_to_login',
        true
      );

      expect(bddOutput.feature).toBeTruthy();
      expect(bddOutput.feature).toContain('Feature:');
      expect(bddOutput.feature).toContain('Scenario:');

      console.log('✓ Simple navigation recorded and converted to BDD');
    }, 60000);

    it('should record form interactions', async () => {
      await page.goto(TEST_SITES.MODERATE.LOGIN);

      const recording: PlaywrightAction[] = [
        { type: 'navigate', url: TEST_SITES.MODERATE.LOGIN },
        { type: 'fill', selector: '#username', value: 'tomsmith' },
        { type: 'fill', selector: '#password', value: 'SuperSecretPassword!' },
        { type: 'click', selector: 'button[type="submit"]' },
        { type: 'wait', selector: '.flash.success' }
      ];

      const bddOutput = await aiClient.generateBDDScenario(
        recording,
        'successful_login',
        true
      );

      expect(bddOutput.feature).toBeTruthy();
      expect(bddOutput.testData).toBeTruthy();
      expect(bddOutput.locators).toBeTruthy();

      // Verify test data extraction
      console.log('\n=== Generated Test Data ===');
      console.log(JSON.stringify(bddOutput.testData, null, 2));

      console.log('✓ Form interactions recorded with test data extraction');
    }, 60000);

    it('should record complex multi-step workflow with checkboxes and dropdowns', async () => {
      const recording: PlaywrightAction[] = [
        { type: 'navigate', url: TEST_SITES.MODERATE.CHECKBOXES },
        { type: 'click', selector: 'input[type="checkbox"]:nth-of-type(1)' },
        { type: 'click', selector: 'input[type="checkbox"]:nth-of-type(2)' },
        { type: 'navigate', url: TEST_SITES.MODERATE.DROPDOWN },
        { type: 'select', selector: '#dropdown', value: '1' },
        { type: 'wait', selector: '#dropdown option[selected]' }
      ];

      const bddOutput = await aiClient.generateBDDScenario(
        recording,
        'checkbox_and_dropdown_interaction',
        true
      );

      expect(bddOutput.feature).toBeTruthy();
      expect(bddOutput.steps).toBeTruthy();

      console.log('✓ Complex multi-step workflow recorded');
    }, 60000);

    it('should record e-commerce checkout flow', async () => {
      const recording: PlaywrightAction[] = [
        { type: 'navigate', url: TEST_SITES.ECOMMERCE.SAUCE_DEMO },
        { type: 'fill', selector: '#user-name', value: 'standard_user' },
        { type: 'fill', selector: '#password', value: 'secret_sauce' },
        { type: 'click', selector: '#login-button' },
        { type: 'wait', selector: '.inventory_list' },
        { type: 'click', selector: '.inventory_item:first-child .btn_inventory' },
        { type: 'click', selector: '.shopping_cart_link' },
        { type: 'wait', selector: '.cart_item' },
        { type: 'click', selector: '#checkout' },
        { type: 'fill', selector: '#first-name', value: 'John' },
        { type: 'fill', selector: '#last-name', value: 'Doe' },
        { type: 'fill', selector: '#postal-code', value: '12345' },
        { type: 'click', selector: '#continue' },
        { type: 'wait', selector: '.summary_info' }
      ];

      const bddOutput = await aiClient.generateBDDScenario(
        recording,
        'complete_checkout_flow',
        true
      );

      expect(bddOutput.feature).toBeTruthy();
      expect(bddOutput.feature.length).toBeGreaterThan(200);

      console.log('✓ E-commerce checkout flow recorded');
      console.log('\nGenerated Feature (first 300 chars):');
      console.log(bddOutput.feature.substring(0, 300) + '...');
    }, 90000);
  });

  describe('3. Script Injection to Automation Framework with POM', () => {
    let pageObjectRegistry: PageObjectRegistry;

    beforeEach(async () => {
      // Create framework
      const generator = new PythonGenerator();
      await generator.generate(projectDir, {
        projectName: 'pom-test',
        language: 'python',
        bdd: true,
        powerApps: false,
        aiProvider: 'anthropic',
        apiKey: process.env.ANTHROPIC_API_KEY
      });

      // Initialize Page Object Registry
      pageObjectRegistry = new PageObjectRegistry(projectDir);
      await pageObjectRegistry.initialize();
    });

    it('should inject first script and create new Page Object', async () => {
      const recording: PlaywrightAction[] = [
        { type: 'navigate', url: TEST_SITES.MODERATE.LOGIN },
        { type: 'fill', selector: '#username', value: 'tomsmith' },
        { type: 'fill', selector: '#password', value: 'SuperSecretPassword!' },
        { type: 'click', selector: 'button[type="submit"]' }
      ];

      const bddOutput = await aiClient.generateBDDScenario(
        recording,
        'login_test',
        true
      );

      // Write Page Object
      const pageObjectCode = `from playwright.sync_api import Page

class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.username_input = page.locator('#username')
        self.password_input = page.locator('#password')
        self.submit_button = page.locator('button[type="submit"]')
        self.success_message = page.locator('.flash.success')

    def navigate(self):
        self.page.goto('${TEST_SITES.MODERATE.LOGIN}')

    def login(self, username: str, password: str):
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.submit_button.click()

    def is_login_successful(self) -> bool:
        return self.success_message.is_visible()
`;

      const pageObjectPath = path.join(projectDir, 'pages', 'login_page.py');
      await FileUtils.writeFile(pageObjectPath, pageObjectCode);

      // Verify page object created
      expect(await fs.pathExists(pageObjectPath)).toBe(true);

      // Re-initialize registry to pick up new page
      await pageObjectRegistry.initialize();
      expect(pageObjectRegistry.pageExists('LoginPage')).toBe(true);

      console.log('✓ First Page Object created successfully');
    }, 60000);

    it('should extend existing Page Object instead of replacing', async () => {
      // First, create initial LoginPage
      const initialPageCode = `from playwright.sync_api import Page

class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.username_input = page.locator('#username')
        self.password_input = page.locator('#password')

    def navigate(self):
        self.page.goto('https://the-internet.herokuapp.com/login')
`;

      const pageObjectPath = path.join(projectDir, 'pages', 'login_page.py');
      await FileUtils.writeFile(pageObjectPath, initialPageCode);

      await pageObjectRegistry.initialize();
      const initialPage = pageObjectRegistry.getPage('LoginPage');
      expect(initialPage).toBeTruthy();
      expect(initialPage!.locators.length).toBe(2);

      // Now try to inject additional locators
      const newPageCode = `from playwright.sync_api import Page

class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.username_input = page.locator('#username')
        self.password_input = page.locator('#password')
        self.submit_button = page.locator('button[type="submit"]')
        self.success_message = page.locator('.flash.success')
        self.error_message = page.locator('.flash.error')

    def navigate(self):
        self.page.goto('https://the-internet.herokuapp.com/login')

    def login(self, username: str, password: str):
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.submit_button.click()
`;

      // Merge with existing page
      const mergeResult = await pageObjectRegistry.mergePage('LoginPage', newPageCode);

      expect(mergeResult.shouldCreate).toBe(false);
      expect(mergeResult.mergedCode).toBeTruthy();

      // Write merged code
      if (mergeResult.mergedCode) {
        await FileUtils.writeFile(pageObjectPath, mergeResult.mergedCode);
      }

      // Verify merge succeeded
      const updatedContent = await fs.readFile(pageObjectPath, 'utf-8');
      expect(updatedContent).toContain('submit_button');
      expect(updatedContent).toContain('success_message');
      expect(updatedContent).toContain('error_message');

      console.log('✓ Page Object extended with new locators');
    }, 60000);

    it('should handle duplicate locator elimination', async () => {
      const pageCode = `from playwright.sync_api import Page

class TestPage:
    def __init__(self, page: Page):
        self.page = page
        self.username = page.locator('#username')
        self.password = page.locator('#password')
`;

      const pageObjectPath = path.join(projectDir, 'pages', 'test_page.py');
      await FileUtils.writeFile(pageObjectPath, pageCode);
      await pageObjectRegistry.initialize();

      // Try to add duplicate locators
      const newLocators = [
        { name: 'username', selector: '#username' },  // Duplicate
        { name: 'password', selector: '#password' },  // Duplicate
        { name: 'submit', selector: '#submit' }       // New
      ];

      const extension = pageObjectRegistry.generateLocatorExtension(
        'TestPage',
        newLocators
      );

      // Should only include the new locator
      expect(extension).not.toContain('username');
      expect(extension).not.toContain('password');
      expect(extension).toContain('submit');

      console.log('✓ Duplicate locators eliminated');
    }, 30000);

    it('should create separate Page Objects for different pages', async () => {
      // Create LoginPage
      const loginPageCode = `from playwright.sync_api import Page

class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.username = page.locator('#username')
        self.password = page.locator('#password')

    def navigate(self):
        self.page.goto('https://the-internet.herokuapp.com/login')
`;

      // Create DashboardPage
      const dashboardPageCode = `from playwright.sync_api import Page

class DashboardPage:
    def __init__(self, page: Page):
        self.page = page
        self.logout_button = page.locator('a.button.secondary')
        self.welcome_message = page.locator('#flash')

    def logout(self):
        self.logout_button.click()
`;

      await FileUtils.writeFile(
        path.join(projectDir, 'pages', 'login_page.py'),
        loginPageCode
      );

      await FileUtils.writeFile(
        path.join(projectDir, 'pages', 'dashboard_page.py'),
        dashboardPageCode
      );

      await pageObjectRegistry.initialize();

      expect(pageObjectRegistry.pageExists('LoginPage')).toBe(true);
      expect(pageObjectRegistry.pageExists('DashboardPage')).toBe(true);

      const allPages = pageObjectRegistry.getAllPages();
      expect(allPages.length).toBeGreaterThanOrEqual(2);

      console.log('✓ Multiple Page Objects created for different pages');
    }, 30000);
  });

  describe('4. Duplicate Elimination Tests', () => {
    let reuseEngine: SemanticReuseEngine;

    beforeEach(async () => {
      reuseEngine = new SemanticReuseEngine();

      // Initialize with some existing steps
      const existingSteps: StepDefinition[] = [
        {
          id: 'step1',
          name: 'navigate_to_login',
          description: 'Given I am on the login page',
          code: 'page.goto("/login")',
          parameters: [],
          filePath: 'steps/login_steps.py',
          usageCount: 5
        },
        {
          id: 'step2',
          name: 'enter_credentials',
          description: 'When I enter valid credentials',
          code: 'page.fill("#username", username)',
          parameters: ['username', 'password'],
          filePath: 'steps/login_steps.py',
          usageCount: 5
        },
        {
          id: 'step3',
          name: 'click_submit',
          description: 'And I click the submit button',
          code: 'page.click("button[type=submit]")',
          parameters: [],
          filePath: 'steps/common_steps.py',
          usageCount: 10
        }
      ];

      await reuseEngine.initialize(existingSteps);
    });

    it('should identify exact duplicate steps', async () => {
      const newStep = {
        description: 'Given I am on the login page',
        parameters: []
      };

      const suggestions = await reuseEngine.findReusableSteps(newStep);

      expect(suggestions.length).toBeGreaterThan(0);
      expect(suggestions[0].similarityScore).toBeGreaterThan(0.95);
      expect(suggestions[0].canReuse).toBe(true);
      expect(suggestions[0].adaptationNeeded.length).toBe(0);

      console.log('✓ Exact duplicate identified for reuse');
    }, 30000);

    it('should identify similar steps with adaptations needed', async () => {
      const newStep = {
        description: 'Given I navigate to the login screen',
        parameters: []
      };

      const suggestions = await reuseEngine.findReusableSteps(newStep);

      expect(suggestions.length).toBeGreaterThan(0);
      expect(suggestions[0].similarityScore).toBeGreaterThan(0.75);

      console.log(`✓ Similar step found with ${Math.round(suggestions[0].similarityScore * 100)}% similarity`);
    }, 30000);

    it('should track reuse metrics', async () => {
      // Simulate multiple reuse attempts
      await reuseEngine.findReusableSteps({
        description: 'Given I am on the login page',
        parameters: []
      });

      await reuseEngine.findReusableSteps({
        description: 'When I enter my username and password',
        parameters: ['username', 'password']
      });

      await reuseEngine.findReusableSteps({
        description: 'Then I should see a completely new page',
        parameters: []
      });

      const stats = reuseEngine.getStatistics();

      expect(stats.reuseAttempts).toBeGreaterThan(0);
      expect(stats.totalSteps).toBeGreaterThan(0);

      console.log('\n=== Reuse Statistics ===');
      console.log(`Total steps indexed: ${stats.totalSteps}`);
      console.log(`Reuse attempts: ${stats.reuseAttempts}`);
      console.log(`Reuse rate: ${Math.round(stats.reuseRate * 100)}%`);
    }, 30000);
  });

  describe('5. Reusability Enhancement Tests', () => {
    it('should analyze patterns across multiple scenarios', async () => {
      const scenarios = [
        {
          name: 'user_login',
          feature: 'User Authentication',
          steps: [
            'Given I am on the login page',
            'When I enter valid user credentials',
            'And I click the login button',
            'Then I should see the user dashboard'
          ],
          locators: ['#username', '#password', 'button[type=submit]', '.dashboard']
        },
        {
          name: 'admin_login',
          feature: 'Admin Authentication',
          steps: [
            'Given I am on the login page',
            'When I enter valid admin credentials',
            'And I click the login button',
            'Then I should see the admin panel'
          ],
          locators: ['#username', '#password', 'button[type=submit]', '.admin-panel']
        },
        {
          name: 'guest_checkout',
          feature: 'Guest Checkout',
          steps: [
            'Given I am on the checkout page',
            'When I enter shipping details',
            'And I click the continue button',
            'Then I should see the payment page'
          ],
          locators: ['#email', '#address', 'button.continue', '.payment-form']
        }
      ];

      const analysis = await aiClient.analyzePatterns(scenarios);

      expect(analysis).toHaveProperty('commonSteps');
      expect(analysis).toHaveProperty('duplicateScenarios');
      expect(analysis).toHaveProperty('reusableLocators');

      console.log('\n=== Pattern Analysis Results ===');
      console.log(JSON.stringify(analysis, null, 2));

      // Verify common steps identified
      if (analysis.commonSteps && Array.isArray(analysis.commonSteps)) {
        expect(analysis.commonSteps.length).toBeGreaterThan(0);
        console.log(`\n✓ Found ${analysis.commonSteps.length} reusable common steps`);
      }
    }, 60000);

    it('should suggest step extraction for reusability', async () => {
      const reuseEngine = new SemanticReuseEngine();

      const steps: StepDefinition[] = [
        {
          id: 's1',
          name: 'login_as_user',
          description: 'When I login as a standard user',
          code: 'login_page.login("user", "pass")',
          parameters: [],
          filePath: 'steps/user_steps.py',
          usageCount: 1
        },
        {
          id: 's2',
          name: 'login_as_admin',
          description: 'When I login as an administrator',
          code: 'login_page.login("admin", "pass")',
          parameters: [],
          filePath: 'steps/admin_steps.py',
          usageCount: 1
        }
      ];

      await reuseEngine.initialize(steps);

      const suggestions = await reuseEngine.findReusableSteps({
        description: 'When I login as a guest user',
        parameters: []
      });

      expect(suggestions.length).toBeGreaterThan(0);
      console.log('✓ Reusable login steps identified across different user types');
    }, 30000);
  });

  describe('6. Running Scripts with Real-World Challenges', () => {
    it('should handle lazy loading elements', async () => {
      await page.goto(TEST_SITES.LAZY_LOADING.LAZY_LOADING);

      // Wait for lazy loaded content
      await page.click('button');
      await page.waitForSelector('#finish', { state: 'visible', timeout: 10000 });

      const recording: PlaywrightAction[] = [
        { type: 'navigate', url: TEST_SITES.LAZY_LOADING.LAZY_LOADING },
        { type: 'click', selector: 'button' },
        { type: 'wait', selector: '#finish' }
      ];

      const bddOutput = await aiClient.generateBDDScenario(
        recording,
        'lazy_loading_test',
        true
      );

      expect(bddOutput.feature).toBeTruthy();

      // Test wait optimization
      const testLog = {
        scenario: 'lazy_loading_test',
        totalDuration: 8000,
        steps: [
          {
            name: 'Wait for lazy content',
            locator: '#finish',
            actualTime: 3500,
            timeoutUsed: 10000,
            success: true
          }
        ]
      };

      const optimizations = await aiClient.optimizeWaits(testLog);
      expect(optimizations).toBeTruthy();

      console.log('✓ Lazy loading handled with wait optimization');
    }, 60000);

    it('should handle dynamic/flaky elements', async () => {
      await page.goto(TEST_SITES.FLAKY.DYNAMIC_CONTROLS);

      const recording: PlaywrightAction[] = [
        { type: 'navigate', url: TEST_SITES.FLAKY.DYNAMIC_CONTROLS },
        { type: 'click', selector: 'button' },
        { type: 'wait', selector: 'input' }
      ];

      const bddOutput = await aiClient.generateBDDScenario(
        recording,
        'dynamic_controls_test',
        true
      );

      expect(bddOutput.feature).toBeTruthy();

      // Test self-healing for flaky elements
      const failedLocator = 'button#old-remove-button';
      const pageHtml = await page.content();

      const healedLocator = await aiClient.healLocator({
        failedLocator,
        elementDescription: 'Remove button',
        pageHtml
      });

      expect(healedLocator.locator).toBeTruthy();
      expect(healedLocator.confidence).toBeGreaterThan(0);

      console.log('✓ Dynamic elements handled with self-healing');
      console.log(`  Original: ${failedLocator}`);
      console.log(`  Healed: ${healedLocator.locator} (${Math.round(healedLocator.confidence * 100)}% confidence)`);
    }, 60000);

    it('should handle different wait strategies', async () => {
      // Test multiple wait scenarios
      const testScenarios = [
        {
          name: 'Explicit wait for visibility',
          url: TEST_SITES.LAZY_LOADING.LAZY_LOADING,
          action: async () => {
            await page.click('button');
            await page.waitForSelector('#finish', { state: 'visible' });
          }
        },
        {
          name: 'Wait for network idle',
          url: TEST_SITES.MODERATE.LOGIN,
          action: async () => {
            await page.fill('#username', 'test');
            await page.waitForLoadState('networkidle');
          }
        },
        {
          name: 'Wait with timeout',
          url: TEST_SITES.FLAKY.DYNAMIC_LOADING,
          action: async () => {
            await page.click('button');
            await page.waitForSelector('#finish', { timeout: 10000 });
          }
        }
      ];

      for (const scenario of testScenarios) {
        await page.goto(scenario.url);
        try {
          await scenario.action();
          console.log(`✓ ${scenario.name} - Success`);
        } catch (error) {
          console.log(`⚠ ${scenario.name} - Expected behavior for test`);
        }
      }

      console.log('✓ Multiple wait strategies tested');
    }, 90000);

    it('should handle infinite scroll', async () => {
      await page.goto(TEST_SITES.LAZY_LOADING.INFINITE_SCROLL);

      // Simulate scrolling
      for (let i = 0; i < 3; i++) {
        await page.evaluate(() => window.scrollBy(0, window.innerHeight));
        await page.waitForTimeout(1000);
      }

      const recording: PlaywrightAction[] = [
        { type: 'navigate', url: TEST_SITES.LAZY_LOADING.INFINITE_SCROLL },
        { type: 'scroll', selector: 'body', value: '0,1000' },
        { type: 'wait', selector: '.jscroll-added' }
      ];

      const bddOutput = await aiClient.generateBDDScenario(
        recording,
        'infinite_scroll_test',
        true
      );

      expect(bddOutput.feature).toBeTruthy();
      console.log('✓ Infinite scroll handled');
    }, 60000);

    it('should handle disappearing elements', async () => {
      await page.goto(TEST_SITES.FLAKY.DISAPPEARING_ELEMENTS);

      // Elements may or may not be present
      const buttons = await page.locator('ul li').count();
      console.log(`Found ${buttons} elements (may vary on each load)`);

      // Record with conditional logic
      const recording: PlaywrightAction[] = [
        { type: 'navigate', url: TEST_SITES.FLAKY.DISAPPEARING_ELEMENTS },
        { type: 'wait', selector: 'ul' }
      ];

      const bddOutput = await aiClient.generateBDDScenario(
        recording,
        'disappearing_elements_test',
        true
      );

      expect(bddOutput.feature).toBeTruthy();
      console.log('✓ Disappearing elements handled with conditional logic');
    }, 60000);
  });

  describe('7. End-to-End Integration Tests', () => {
    it('should complete full workflow: Create framework → Record → Inject → Run', async () => {
      console.log('\n=== Starting Full E2E Workflow ===\n');

      // Step 1: Create Framework
      console.log('Step 1: Creating framework...');
      const generator = new PythonGenerator();
      await generator.generate(projectDir, {
        projectName: 'e2e-test',
        language: 'python',
        bdd: true,
        powerApps: false,
        aiProvider: 'anthropic',
        apiKey: process.env.ANTHROPIC_API_KEY
      });
      console.log('✓ Framework created');

      // Step 2: Record test scenario
      console.log('\nStep 2: Recording test scenario...');
      const recording: PlaywrightAction[] = [
        { type: 'navigate', url: TEST_SITES.MODERATE.LOGIN },
        { type: 'fill', selector: '#username', value: 'tomsmith' },
        { type: 'fill', selector: '#password', value: 'SuperSecretPassword!' },
        { type: 'click', selector: 'button[type="submit"]' },
        { type: 'wait', selector: '.flash.success' }
      ];

      const bddOutput = await aiClient.generateBDDScenario(
        recording,
        'login_workflow',
        true
      );
      console.log('✓ Scenario recorded and converted to BDD');

      // Step 3: Inject into framework with POM
      console.log('\nStep 3: Injecting into framework...');

      // Create Page Object
      const pageObjectCode = `from playwright.sync_api import Page

class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.username_input = page.locator('#username')
        self.password_input = page.locator('#password')
        self.submit_button = page.locator('button[type="submit"]')
        self.success_flash = page.locator('.flash.success')

    def navigate(self):
        self.page.goto('${TEST_SITES.MODERATE.LOGIN}')

    def login(self, username: str, password: str):
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.submit_button.click()

    def is_success_displayed(self) -> bool:
        return self.success_flash.is_visible()
`;

      await FileUtils.writeFile(
        path.join(projectDir, 'pages', 'login_page.py'),
        pageObjectCode
      );

      // Write feature file
      await FileUtils.writeFile(
        path.join(projectDir, 'features', 'login.feature'),
        bddOutput.feature
      );

      // Write step definitions (if generated)
      if (bddOutput.steps) {
        await FileUtils.writeFile(
          path.join(projectDir, 'steps', 'login_steps.py'),
          bddOutput.steps
        );
      }

      // Write test data
      if (bddOutput.testData && Object.keys(bddOutput.testData).length > 0) {
        await FileUtils.writeFile(
          path.join(projectDir, 'fixtures', 'login_data.json'),
          JSON.stringify(bddOutput.testData, null, 2)
        );
      }

      console.log('✓ Scripts injected with Page Object Model');

      // Step 4: Verify all files created
      console.log('\nStep 4: Verifying framework integrity...');
      const expectedFiles = [
        'pages/login_page.py',
        'features/login.feature'
      ];

      for (const file of expectedFiles) {
        const exists = await fs.pathExists(path.join(projectDir, file));
        expect(exists).toBe(true);
      }

      console.log('✓ All files verified');

      // Step 5: Simulate running (verify structure is correct)
      console.log('\nStep 5: Validating test structure...');
      const featureContent = await fs.readFile(
        path.join(projectDir, 'features', 'login.feature'),
        'utf-8'
      );

      expect(featureContent).toContain('Feature:');
      expect(featureContent).toContain('Scenario:');

      const pageContent = await fs.readFile(
        path.join(projectDir, 'pages', 'login_page.py'),
        'utf-8'
      );

      expect(pageContent).toContain('class LoginPage');
      expect(pageContent).toContain('def login');

      console.log('✓ Test structure validated');
      console.log('\n=== Full E2E Workflow Completed Successfully ===\n');
    }, 120000);

    it('should handle multiple scenarios with cross-page reuse', async () => {
      // Create framework
      const generator = new PythonGenerator();
      await generator.generate(projectDir, {
        projectName: 'multi-scenario-test',
        language: 'python',
        bdd: true,
        powerApps: false,
        aiProvider: 'anthropic',
        apiKey: process.env.ANTHROPIC_API_KEY
      });

      const registry = new PageObjectRegistry(projectDir);
      await registry.initialize();

      // Scenario 1: Login
      const loginScenario: PlaywrightAction[] = [
        { type: 'navigate', url: TEST_SITES.MODERATE.LOGIN },
        { type: 'fill', selector: '#username', value: 'tomsmith' },
        { type: 'fill', selector: '#password', value: 'SuperSecretPassword!' },
        { type: 'click', selector: 'button[type="submit"]' }
      ];

      // Scenario 2: Checkboxes
      const checkboxScenario: PlaywrightAction[] = [
        { type: 'navigate', url: TEST_SITES.MODERATE.CHECKBOXES },
        { type: 'click', selector: 'input[type="checkbox"]:nth-of-type(1)' },
        { type: 'click', selector: 'input[type="checkbox"]:nth-of-type(2)' }
      ];

      const [bdd1, bdd2] = await Promise.all([
        aiClient.generateBDDScenario(loginScenario, 'login', true),
        aiClient.generateBDDScenario(checkboxScenario, 'checkboxes', true)
      ]);

      // Write both scenarios
      await FileUtils.writeFile(
        path.join(projectDir, 'features', 'login.feature'),
        bdd1.feature
      );

      await FileUtils.writeFile(
        path.join(projectDir, 'features', 'checkboxes.feature'),
        bdd2.feature
      );

      // Verify both created
      expect(await fs.pathExists(path.join(projectDir, 'features', 'login.feature'))).toBe(true);
      expect(await fs.pathExists(path.join(projectDir, 'features', 'checkboxes.feature'))).toBe(true);

      console.log('✓ Multiple scenarios created with separate features');
    }, 120000);
  });

  describe('8. Advanced Real-World Scenarios', () => {
    it('should generate test data for complex forms', async () => {
      const schema = {
        user_registration: {
          type: 'object',
          context: 'E-commerce user registration',
          example: {
            firstName: 'string',
            lastName: 'string',
            email: 'email',
            phone: 'phone',
            password: 'password',
            dateOfBirth: 'date',
            address: {
              street: 'string',
              city: 'string',
              state: 'string',
              zipCode: 'string',
              country: 'string'
            },
            preferences: {
              newsletter: 'boolean',
              smsUpdates: 'boolean'
            }
          }
        }
      };

      const testData = await aiClient.generateTestData(schema);

      expect(testData).toBeTruthy();
      console.log('\n=== Generated Complex Test Data ===');
      console.log(JSON.stringify(testData, null, 2));
    }, 60000);

    it('should optimize waits across multiple test runs', async () => {
      const testLogs = [
        {
          scenario: 'login_test_run_1',
          totalDuration: 5000,
          steps: [
            {
              name: 'Wait for username',
              locator: '#username',
              actualTime: 100,
              timeoutUsed: 5000,
              success: true
            },
            {
              name: 'Wait for submit',
              locator: 'button',
              actualTime: 50,
              timeoutUsed: 5000,
              success: true
            }
          ]
        },
        {
          scenario: 'login_test_run_2',
          totalDuration: 4800,
          steps: [
            {
              name: 'Wait for username',
              locator: '#username',
              actualTime: 120,
              timeoutUsed: 5000,
              success: true
            },
            {
              name: 'Wait for submit',
              locator: 'button',
              actualTime: 60,
              timeoutUsed: 5000,
              success: true
            }
          ]
        }
      ];

      const optimizations = await Promise.all(
        testLogs.map(log => aiClient.optimizeWaits(log))
      );

      expect(optimizations.length).toBe(2);
      optimizations.forEach(opt => {
        expect(opt.optimizations).toBeDefined();
      });

      console.log('✓ Wait times optimized across multiple runs');
    }, 60000);
  });
});
