/**
 * End-to-End Integration Tests for CLI Workflows
 * Tests complete user workflows from initialization to test execution
 */

import * as fs from 'fs-extra';
import * as path from 'path';
import * as os from 'os';
import { PythonGenerator } from '../../src/generators/python-generator';
import { FileUtils } from '../../src/utils/file-utils';
import { AnthropicClient } from '../../src/ai/anthropic-client';
import { PlaywrightAction } from '../../src/types';
import * as dotenv from 'dotenv';

dotenv.config({ path: path.resolve(__dirname, '../../.env') });

describe('CLI Workflow Integration Tests', () => {
  let tempDir: string;
  let projectDir: string;

  beforeEach(async () => {
    tempDir = path.join(os.tmpdir(), `cli-test-${Date.now()}`);
    projectDir = path.join(tempDir, 'test-project');
    await fs.ensureDir(tempDir);
  });

  afterEach(async () => {
    if (await fs.pathExists(tempDir)) {
      await fs.remove(tempDir);
    }
  });

  describe('Complete Framework Generation Workflow', () => {
    it('should generate complete Python framework', async () => {
      const generator = new PythonGenerator();

      const options = {
        projectName: 'test-framework',
        language: 'python' as const,
        bdd: true,
        powerApps: false,
        aiProvider: 'anthropic' as const,
        aiModel: 'claude-sonnet-4-5-20250929',
        apiKey: process.env.ANTHROPIC_API_KEY
      };

      await generator.generate(projectDir, options);

      // Verify directory structure
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
        const exists = await fs.pathExists(dirPath);
        expect(exists).toBe(true);
      }

      // Verify helper files
      const expectedHelpers = [
        'helpers/__init__.py',
        'helpers/auth_helper.py',
        'helpers/healing_locator.py',
        'helpers/wait_manager.py',
        'helpers/data_generator.py',
        'helpers/screenshot_manager.py'
      ];

      for (const helper of expectedHelpers) {
        const helperPath = path.join(projectDir, helper);
        const exists = await fs.pathExists(helperPath);
        expect(exists).toBe(true);
      }

      // Verify config files
      const configPath = path.join(projectDir, 'config', 'config.py');
      const configExists = await fs.pathExists(configPath);
      expect(configExists).toBe(true);

      const configContent = await fs.readFile(configPath, 'utf-8');
      expect(configContent).toContain('class Config');
      expect(configContent).toContain('AI_PROVIDER');
      expect(configContent).toContain(options.aiProvider);

      console.log('\n=== Framework Structure Verified ===');
      console.log('All directories created successfully');
      console.log('All helper files in place');
      console.log('Configuration generated correctly');
    });

    it('should generate .gitignore file', async () => {
      const generator = new PythonGenerator();

      await generator.generate(projectDir, {
        projectName: 'test',
        language: 'python',
        bdd: true,
        powerApps: false,
        aiProvider: 'none'
      });

      await generator.generateGitignore(projectDir);

      const gitignorePath = path.join(projectDir, '.gitignore');
      const exists = await fs.pathExists(gitignorePath);
      expect(exists).toBe(true);

      const content = await fs.readFile(gitignorePath, 'utf-8');
      expect(content).toContain('__pycache__');
      expect(content).toContain('.env');
      expect(content).toContain('venv/');
      expect(content).toContain('reports/');
    });

    it('should generate requirements.txt', async () => {
      const generator = new PythonGenerator();

      await generator.generate(projectDir, {
        projectName: 'test',
        language: 'python',
        bdd: true,
        powerApps: false,
        aiProvider: 'anthropic'
      });

      const requirementsPath = path.join(projectDir, 'requirements.txt');
      const exists = await fs.pathExists(requirementsPath);
      expect(exists).toBe(true);

      const content = await fs.readFile(requirementsPath, 'utf-8');
      expect(content).toContain('playwright');
      expect(content).toContain('behave');
      expect(content).toContain('anthropic');
    });

    it('should generate example feature file', async () => {
      const generator = new PythonGenerator();

      await generator.generate(projectDir, {
        projectName: 'test',
        language: 'python',
        bdd: true,
        powerApps: false,
        aiProvider: 'none'
      });

      const featurePath = path.join(projectDir, 'features', 'example.feature');
      const exists = await fs.pathExists(featurePath);
      expect(exists).toBe(true);

      const content = await fs.readFile(featurePath, 'utf-8');
      expect(content).toContain('Feature:');
      expect(content).toContain('Scenario:');
    });
  });

  describe('Recording to BDD Conversion Workflow', () => {
    let aiClient: AnthropicClient;

    beforeAll(() => {
      const apiKey = process.env.ANTHROPIC_API_KEY;
      if (!apiKey) {
        throw new Error('ANTHROPIC_API_KEY required for integration tests');
      }
      aiClient = new AnthropicClient(apiKey);
    });

    it('should convert simple recording to complete BDD artifacts', async () => {
      // Simulate a recording
      const recording: PlaywrightAction[] = [
        { type: 'navigate', url: 'https://example.com/login' },
        { type: 'fill', selector: '#username', value: 'testuser' },
        { type: 'fill', selector: '#password', value: 'password123' },
        { type: 'click', selector: 'button[type=submit]' },
        { type: 'wait', selector: 'text=Welcome' }
      ];

      // Convert to BDD
      const bddOutput = await aiClient.generateBDDScenario(
        recording,
        'user_login',
        true // Use reasoning
      );

      // Write BDD artifacts to project
      const generator = new PythonGenerator();
      await generator.generate(projectDir, {
        projectName: 'login-test',
        language: 'python',
        bdd: true,
        powerApps: false,
        aiProvider: 'anthropic'
      });

      // Write feature file
      const featurePath = path.join(projectDir, 'features', 'user_login.feature');
      await FileUtils.writeFile(featurePath, bddOutput.feature);

      // Write locators
      if (Object.keys(bddOutput.locators).length > 0) {
        const locatorsPath = path.join(projectDir, 'config', 'user_login_locators.json');
        await FileUtils.writeFile(
          locatorsPath,
          JSON.stringify(bddOutput.locators, null, 2)
        );
      }

      // Write test data
      if (Object.keys(bddOutput.testData).length > 0) {
        const dataPath = path.join(projectDir, 'fixtures', 'user_login_data.json');
        await FileUtils.writeFile(
          dataPath,
          JSON.stringify(bddOutput.testData, null, 2)
        );
      }

      // Write step definitions
      if (bddOutput.steps) {
        const stepsPath = path.join(projectDir, 'steps', 'user_login_steps.py');
        await FileUtils.writeFile(stepsPath, bddOutput.steps);
      }

      // Verify all files created
      expect(await fs.pathExists(featurePath)).toBe(true);

      const featureContent = await fs.readFile(featurePath, 'utf-8');
      expect(featureContent).toContain('Feature:');

      console.log('\n=== Generated BDD Artifacts ===');
      console.log('Feature file:', featurePath);
      console.log('\nFeature content:');
      console.log(featureContent);

      if (await fs.pathExists(path.join(projectDir, 'config', 'user_login_locators.json'))) {
        const locators = JSON.parse(
          await fs.readFile(path.join(projectDir, 'config', 'user_login_locators.json'), 'utf-8')
        );
        console.log('\nLocators:', JSON.stringify(locators, null, 2));
      }
    }, 60000);

    it('should handle complex multi-step recording', async () => {
      const recording: PlaywrightAction[] = [
        { type: 'navigate', url: 'https://example.com' },
        { type: 'click', selector: 'text=Products' },
        { type: 'click', selector: '.product-card:first-child' },
        { type: 'click', selector: 'text=Add to Cart' },
        { type: 'click', selector: '.cart-icon' },
        { type: 'click', selector: 'text=Checkout' },
        { type: 'fill', selector: '#shipping-name', value: 'John Doe' },
        { type: 'fill', selector: '#shipping-address', value: '123 Main St' },
        { type: 'fill', selector: '#shipping-city', value: 'New York' },
        { type: 'select', selector: '#shipping-state', value: 'NY' },
        { type: 'fill', selector: '#shipping-zip', value: '10001' },
        { type: 'click', selector: 'text=Continue to Payment' },
        { type: 'fill', selector: '#card-number', value: '4111111111111111' },
        { type: 'fill', selector: '#card-expiry', value: '12/25' },
        { type: 'fill', selector: '#card-cvv', value: '123' },
        { type: 'click', selector: 'button:has-text("Place Order")' }
      ];

      const bddOutput = await aiClient.generateBDDScenario(
        recording,
        'complete_checkout',
        true
      );

      expect(bddOutput.feature).toBeTruthy();
      expect(bddOutput.feature.length).toBeGreaterThan(100);

      console.log('\n=== Complex Workflow BDD ===');
      console.log(bddOutput.feature.substring(0, 500) + '...');
    }, 90000);
  });

  describe('AI Feature Integration', () => {
    let aiClient: AnthropicClient;

    beforeAll(() => {
      const apiKey = process.env.ANTHROPIC_API_KEY;
      if (!apiKey) {
        throw new Error('ANTHROPIC_API_KEY required');
      }
      aiClient = new AnthropicClient(apiKey);
    });

    it('should demonstrate self-healing workflow', async () => {
      const failedLocator = 'button#old-id-that-changed';
      const pageHtml = `
        <html>
          <body>
            <form id="login-form">
              <button type="submit" class="btn-primary" data-testid="login-submit" aria-label="Login">
                Sign In
              </button>
            </form>
          </body>
        </html>
      `;

      const healedLocator = await aiClient.healLocator({
        failedLocator,
        elementDescription: 'Login submit button',
        pageHtml
      });

      expect(healedLocator.locator).toBeTruthy();
      expect(healedLocator.confidence).toBeGreaterThan(0);
      expect(healedLocator.alternatives.length).toBeGreaterThan(0);

      console.log('\n=== Self-Healing Demonstration ===');
      console.log('Original locator failed:', failedLocator);
      console.log('AI suggested:', healedLocator.locator);
      console.log('Confidence:', healedLocator.confidence);
      console.log('Alternative options:', healedLocator.alternatives);
    }, 30000);

    it('should generate realistic test data', async () => {
      const schema = {
        user_profile: {
          type: 'object',
          context: 'User registration form',
          example: {
            firstName: 'string',
            lastName: 'string',
            email: 'email',
            phone: 'phone',
            dateOfBirth: 'date',
            address: {
              street: 'string',
              city: 'string',
              state: 'string',
              zipCode: 'string'
            }
          }
        }
      };

      const testData = await aiClient.generateTestData(schema);

      expect(testData).toBeTruthy();

      console.log('\n=== Generated Test Data ===');
      console.log(JSON.stringify(testData, null, 2));
    }, 30000);

    it('should provide wait optimization recommendations', async () => {
      const testLog = {
        scenario: 'page_load_performance',
        totalDuration: 45000,
        steps: [
          {
            name: 'Navigate to home',
            locator: 'text=Home',
            actualTime: 1200,
            timeoutUsed: 5000,
            success: true
          },
          {
            name: 'Wait for product grid',
            locator: '.product-grid',
            actualTime: 3500,
            timeoutUsed: 10000,
            success: true
          },
          {
            name: 'Wait for recommendations',
            locator: '#recommendations',
            actualTime: 12000,
            timeoutUsed: 15000,
            success: true
          },
          {
            name: 'Wait for footer',
            locator: 'footer',
            actualTime: 500,
            timeoutUsed: 5000,
            success: true
          }
        ]
      };

      const optimizations = await aiClient.optimizeWaits(testLog);

      expect(optimizations.optimizations).toBeDefined();
      expect(Array.isArray(optimizations.optimizations)).toBe(true);

      console.log('\n=== Wait Optimization Recommendations ===');
      console.log(JSON.stringify(optimizations, null, 2));
    }, 30000);

    it('should analyze test patterns and suggest improvements', async () => {
      const scenarios = [
        {
          name: 'login_as_admin',
          feature: 'Admin Login',
          steps: [
            'Given I am on the login page',
            'When I enter admin credentials',
            'And I click the login button',
            'Then I should see the admin dashboard'
          ],
          locators: ['#email', '#password', 'button[type=submit]', '.admin-dashboard']
        },
        {
          name: 'login_as_user',
          feature: 'User Login',
          steps: [
            'Given I am on the login page',
            'When I enter user credentials',
            'And I click the login button',
            'Then I should see the user dashboard'
          ],
          locators: ['#email', '#password', 'button[type=submit]', '.user-dashboard']
        },
        {
          name: 'password_reset',
          feature: 'Password Reset',
          steps: [
            'Given I am on the login page',
            'When I click forgot password',
            'And I enter my email',
            'And I click the submit button',
            'Then I should see a confirmation message'
          ],
          locators: ['#email', 'a.forgot-password', 'button[type=submit]']
        }
      ];

      const analysis = await aiClient.analyzePatterns(scenarios);

      expect(analysis).toHaveProperty('commonSteps');
      expect(analysis).toHaveProperty('duplicateScenarios');
      expect(analysis).toHaveProperty('reusableLocators');

      console.log('\n=== Pattern Analysis ===');
      console.log(JSON.stringify(analysis, null, 2));
    }, 30000);
  });

  describe('File Operations Integration', () => {
    it('should handle complete file workflow', async () => {
      // Create project structure
      await FileUtils.ensureDirectory(path.join(projectDir, 'features'));
      await FileUtils.ensureDirectory(path.join(projectDir, 'steps'));
      await FileUtils.ensureDirectory(path.join(projectDir, 'config'));

      // Write feature file
      const featureContent = `
Feature: Sample Feature
  Scenario: Sample Test
    Given I am on the page
    When I perform an action
    Then I should see a result
      `.trim();

      await FileUtils.writeFile(
        path.join(projectDir, 'features', 'sample.feature'),
        featureContent
      );

      // Write config file
      const configContent = JSON.stringify({
        locators: {
          submit_button: 'button[type=submit]',
          email_field: '#email'
        }
      }, null, 2);

      await FileUtils.writeFile(
        path.join(projectDir, 'config', 'sample_locators.json'),
        configContent
      );

      // Verify files exist
      const featureExists = await FileUtils.fileExists(
        path.join(projectDir, 'features', 'sample.feature')
      );
      expect(featureExists).toBe(true);

      const configExists = await FileUtils.fileExists(
        path.join(projectDir, 'config', 'sample_locators.json')
      );
      expect(configExists).toBe(true);

      // Read files back
      const readFeature = await FileUtils.readFile(
        path.join(projectDir, 'features', 'sample.feature')
      );
      expect(readFeature).toContain('Feature: Sample Feature');

      const readConfig = await FileUtils.readFile(
        path.join(projectDir, 'config', 'sample_locators.json')
      );
      const parsedConfig = JSON.parse(readConfig);
      expect(parsedConfig.locators.submit_button).toBe('button[type=submit]');

      console.log('\n=== File Operations Completed ===');
      console.log('Files created and verified successfully');
    });
  });

  describe('Error Handling and Recovery', () => {
    it('should handle missing directories gracefully', async () => {
      const nonExistentPath = path.join(projectDir, 'does-not-exist', 'file.txt');

      // Should create parent directories
      await expect(
        FileUtils.writeFile(nonExistentPath, 'content')
      ).resolves.not.toThrow();

      const exists = await FileUtils.fileExists(nonExistentPath);
      expect(exists).toBe(true);
    });

    it('should handle file overwrites', async () => {
      const filePath = path.join(projectDir, 'test.txt');

      await FileUtils.writeFile(filePath, 'Original content');
      await FileUtils.writeFile(filePath, 'Updated content');

      const content = await FileUtils.readFile(filePath);
      expect(content).toBe('Updated content');
    });
  });

  describe('Performance and Scalability', () => {
    it('should handle large directory structures', async () => {
      const startTime = Date.now();

      // Create deep directory structure
      const deepPath = path.join(
        projectDir,
        'level1',
        'level2',
        'level3',
        'level4',
        'level5'
      );

      await FileUtils.ensureDirectory(deepPath);

      // Create multiple files at different levels
      const files = [];
      for (let i = 1; i <= 20; i++) {
        files.push(
          FileUtils.writeFile(
            path.join(projectDir, 'level1', `file${i}.txt`),
            `Content ${i}`
          )
        );
      }

      await Promise.all(files);

      const duration = Date.now() - startTime;

      console.log(`\nCreated deep structure with 20 files in ${duration}ms`);
      expect(duration).toBeLessThan(5000);
    });

    it('should handle concurrent file operations', async () => {
      const operations = [];

      for (let i = 0; i < 10; i++) {
        operations.push(
          FileUtils.writeFile(
            path.join(projectDir, `concurrent_${i}.txt`),
            `Content ${i}`
          )
        );
      }

      await expect(Promise.all(operations)).resolves.not.toThrow();

      // Verify all files created
      for (let i = 0; i < 10; i++) {
        const exists = await FileUtils.fileExists(
          path.join(projectDir, `concurrent_${i}.txt`)
        );
        expect(exists).toBe(true);
      }
    });
  });
});
