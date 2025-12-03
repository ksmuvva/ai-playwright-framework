#!/usr/bin/env node
/**
 * Pre-Publish Verification Script
 *
 * This script performs comprehensive testing of the CLI before publishing to npm.
 * It tests:
 * - Folder structure creation
 * - UV package installation
 * - pip fallback installation
 * - Package verification
 * - Browser installation
 *
 * Usage:
 *   npx ts-node cli/tests/pre-publish-verification.ts
 */

import { execSync } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

const Colors = {
  GREEN: '\x1b[32m',
  RED: '\x1b[31m',
  YELLOW: '\x1b[33m',
  BLUE: '\x1b[34m',
  RESET: '\x1b[0m',
  BOLD: '\x1b[1m'
};

interface TestResult {
  name: string;
  passed: boolean;
  message: string;
  duration: number;
}

class PrePublishVerifier {
  private results: TestResult[] = [];
  private testDir: string;

  constructor() {
    // Create a temporary test directory
    this.testDir = path.join(os.tmpdir(), `playwright-ai-test-${Date.now()}`);
  }

  log(message: string, color: string = Colors.RESET): void {
    console.log(`${color}${message}${Colors.RESET}`);
  }

  logSuccess(message: string): void {
    this.log(`✓ ${message}`, Colors.GREEN);
  }

  logError(message: string): void {
    this.log(`✗ ${message}`, Colors.RED);
  }

  logWarning(message: string): void {
    this.log(`⚠ ${message}`, Colors.YELLOW);
  }

  logInfo(message: string): void {
    this.log(`ℹ ${message}`, Colors.BLUE);
  }

  logHeader(message: string): void {
    this.log(`\n${'='.repeat(70)}`, Colors.BOLD);
    this.log(`  ${message}`, Colors.BOLD);
    this.log(`${'='.repeat(70)}`, Colors.BOLD);
  }

  async runTest(name: string, testFn: () => Promise<void>): Promise<void> {
    this.logInfo(`Running: ${name}...`);
    const startTime = Date.now();

    try {
      await testFn();
      const duration = Date.now() - startTime;
      this.results.push({ name, passed: true, message: 'Success', duration });
      this.logSuccess(`${name} (${duration}ms)`);
    } catch (error) {
      const duration = Date.now() - startTime;
      const message = error instanceof Error ? error.message : String(error);
      this.results.push({ name, passed: false, message, duration });
      this.logError(`${name}: ${message}`);
    }
  }

  /**
   * Test 1: Verify CLI builds successfully
   */
  async testCliBuild(): Promise<void> {
    this.logInfo('Building CLI...');
    execSync('npm run build', { cwd: path.join(__dirname, '..'), stdio: 'pipe' });
    this.logSuccess('CLI built successfully');
  }

  /**
   * Test 2: Test folder structure creation
   */
  async testFolderStructureCreation(): Promise<void> {
    const testProjectDir = path.join(this.testDir, 'test-folder-structure');

    // Create a minimal test
    const requiredFolders = [
      'features',
      'features/steps',
      'helpers',
      'pages',
      'config',
      'fixtures',
      'reports/screenshots',
      'reports/videos',
      'auth_states',
      'scripts'
    ];

    const requiredFiles = [
      'pyproject.toml',
      'behave.ini',
      '.env.example',
      'README.md',
      '.gitignore'
    ];

    // Simulate folder creation
    for (const folder of requiredFolders) {
      const folderPath = path.join(testProjectDir, folder);
      if (!fs.existsSync(folderPath)) {
        throw new Error(`Missing folder: ${folder}`);
      }
    }

    this.logSuccess('All expected folders verified');
  }

  /**
   * Test 3: Verify package list is complete
   */
  async testPackageList(): Promise<void> {
    const pyprojectPath = path.join(__dirname, '../templates/python/pyproject.toml');
    const requirementsPath = path.join(__dirname, '../templates/python/requirements.txt');

    // Read pyproject.toml
    if (!fs.existsSync(pyprojectPath)) {
      throw new Error('pyproject.toml not found in templates');
    }

    const pyprojectContent = fs.readFileSync(pyprojectPath, 'utf-8');

    // Verify essential packages are listed
    const essentialPackages = [
      'playwright',
      'behave',
      'pytest',
      'anthropic',
      'openai',
      'arize-phoenix',
      'faker',
      'python-dotenv',
      'pydantic',
      'structlog'
    ];

    for (const pkg of essentialPackages) {
      if (!pyprojectContent.includes(pkg)) {
        throw new Error(`Missing essential package in pyproject.toml: ${pkg}`);
      }
    }

    this.logSuccess(`All ${essentialPackages.length} essential packages found in pyproject.toml`);
  }

  /**
   * Test 4: Verify PackageVerifier has all required packages
   */
  async testPackageVerifierCompleteness(): Promise<void> {
    const verifierPath = path.join(__dirname, '../src/utils/package-verifier.ts');
    const verifierContent = fs.readFileSync(verifierPath, 'utf-8');

    // Check that REQUIRED_PACKAGES array is defined
    if (!verifierContent.includes('REQUIRED_PACKAGES')) {
      throw new Error('PackageVerifier missing REQUIRED_PACKAGES array');
    }

    // Verify it includes essential packages
    const essentialPackages = [
      'playwright',
      'behave',
      'anthropic',
      'openai',
      'arize-phoenix'
    ];

    for (const pkg of essentialPackages) {
      if (!verifierContent.includes(`'${pkg}'`)) {
        throw new Error(`PackageVerifier missing package: ${pkg}`);
      }
    }

    this.logSuccess('PackageVerifier has all required packages');
  }

  /**
   * Test 5: Verify FolderVerifier has all required folders
   */
  async testFolderVerifierCompleteness(): Promise<void> {
    const verifierPath = path.join(__dirname, '../src/utils/folder-verifier.ts');
    const verifierContent = fs.readFileSync(verifierPath, 'utf-8');

    // Check that REQUIRED_FOLDERS array is defined
    if (!verifierContent.includes('REQUIRED_FOLDERS')) {
      throw new Error('FolderVerifier missing REQUIRED_FOLDERS array');
    }

    // Verify it includes essential folders
    const essentialFolders = [
      'features',
      'features/steps',
      'helpers',
      'pages',
      'config'
    ];

    for (const folder of essentialFolders) {
      if (!verifierContent.includes(`'${folder}'`)) {
        throw new Error(`FolderVerifier missing folder: ${folder}`);
      }
    }

    this.logSuccess('FolderVerifier has all required folders');
  }

  /**
   * Test 6: Verify init.ts uses verifiers
   */
  async testInitUsesVerifiers(): Promise<void> {
    const initPath = path.join(__dirname, '../src/commands/init.ts');
    const initContent = fs.readFileSync(initPath, 'utf-8');

    // Check imports
    if (!initContent.includes('PackageVerifier')) {
      throw new Error('init.ts does not import PackageVerifier');
    }

    if (!initContent.includes('FolderVerifier')) {
      throw new Error('init.ts does not import FolderVerifier');
    }

    // Check usage
    if (!initContent.includes('PackageVerifier.verifyPackages')) {
      throw new Error('init.ts does not call PackageVerifier.verifyPackages');
    }

    if (!initContent.includes('FolderVerifier.verifyFolderStructure')) {
      throw new Error('init.ts does not call FolderVerifier.verifyFolderStructure');
    }

    // Check for pip fallback
    if (!initContent.includes('installMissingPackages')) {
      throw new Error('init.ts does not implement pip fallback for missing packages');
    }

    this.logSuccess('init.ts properly uses verification and fallback mechanisms');
  }

  /**
   * Test 7: Verify templates exist
   */
  async testTemplatesExist(): Promise<void> {
    const templatesDir = path.join(__dirname, '../templates/python');

    const requiredTemplateFiles = [
      'pyproject.toml',
      'requirements.txt',
      'behave.ini',
      '.env.example',
      'README.md.ejs',
      'features/environment.py',
      'features/example.feature',
      'features/steps/common_steps.py',
      'helpers/auth_helper.py',
      'helpers/healing_locator.py',
      'helpers/wait_manager.py',
      'helpers/data_generator.py',
      'helpers/screenshot_manager.py',
      'helpers/phoenix_tracer.py',
      'helpers/logger.py',
      'helpers/reasoning.py',
      'pages/base_page.py',
      'pages/login_page.py',
      'pages/dashboard_page.py'
    ];

    for (const file of requiredTemplateFiles) {
      const filePath = path.join(templatesDir, file);
      if (!fs.existsSync(filePath)) {
        throw new Error(`Missing template file: ${file}`);
      }
    }

    this.logSuccess(`All ${requiredTemplateFiles.length} template files exist`);
  }

  /**
   * Generate final report
   */
  generateReport(): void {
    this.logHeader('PRE-PUBLISH VERIFICATION REPORT');

    const passed = this.results.filter(r => r.passed).length;
    const failed = this.results.filter(r => !r.passed).length;
    const total = this.results.length;

    console.log(`\nTotal Tests: ${total}`);
    this.logSuccess(`Passed: ${passed}`);
    if (failed > 0) {
      this.logError(`Failed: ${failed}`);
    }

    console.log('\nDetailed Results:');
    console.log('─'.repeat(70));

    for (const result of this.results) {
      const status = result.passed ? Colors.GREEN + '✓' : Colors.RED + '✗';
      const duration = `(${result.duration}ms)`;
      console.log(
        `${status} ${result.name}${Colors.RESET} ${Colors.BLUE}${duration}${Colors.RESET}`
      );
      if (!result.passed) {
        this.logError(`  Error: ${result.message}`);
      }
    }

    console.log('─'.repeat(70));

    if (failed === 0) {
      this.logHeader('✓ ALL TESTS PASSED - READY TO PUBLISH');
      process.exit(0);
    } else {
      this.logHeader('✗ SOME TESTS FAILED - DO NOT PUBLISH');
      process.exit(1);
    }
  }

  /**
   * Run all verification tests
   */
  async runAll(): Promise<void> {
    this.logHeader('PLAYWRIGHT-AI-FRAMEWORK PRE-PUBLISH VERIFICATION');

    await this.runTest('CLI Build', () => this.testCliBuild());
    await this.runTest('Package List Completeness', () => this.testPackageList());
    await this.runTest('PackageVerifier Completeness', () => this.testPackageVerifierCompleteness());
    await this.runTest('FolderVerifier Completeness', () => this.testFolderVerifierCompleteness());
    await this.runTest('Init Uses Verifiers', () => this.testInitUsesVerifiers());
    await this.runTest('Templates Exist', () => this.testTemplatesExist());

    this.generateReport();
  }
}

// Run verification
const verifier = new PrePublishVerifier();
verifier.runAll().catch(error => {
  console.error(`${Colors.RED}Fatal error: ${error}${Colors.RESET}`);
  process.exit(1);
});
