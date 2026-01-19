import { Command } from 'commander';
import { exec, spawn } from 'child_process';
import { promisify } from 'util';
import inquirer from 'inquirer';
import ora from 'ora';
import path from 'path';
import { RecordOptions } from '../types';
import { Logger } from '../utils/logger';
import { FileUtils } from '../utils/file-utils';
import { AnthropicClient } from '../ai/anthropic-client';
import { PythonParser } from '../parsers/python-parser';
import { PythonGenerator } from '../generators/python-generator';

const execAsync = promisify(exec);

export function createRecordCommand(): Command {
  return new Command('record')
    .description('Record a new test scenario using Playwright')
    .option('-u, --url <url>', 'Starting URL for recording')
    .option('-s, --scenario-name <name>', 'Name for the scenario')
    .option('-b, --browser <browser>', 'Browser to use (chromium, firefox, webkit)', 'chromium')
    .option('--convert-to-bdd', 'Auto-convert to BDD after recording', false)
    .option('--generate-data', 'Generate test data schema from recording', false)
    .option('--generate-page-objects', 'Generate page objects from recording', false)
    .option('--headless', 'Run recorder in headless mode', false)
    .action(async (options) => {
      await recordScenario(options);
    });
}

async function recordScenario(cmdOptions: any): Promise<void> {
  try {
    Logger.title('🎥 Playwright Scenario Recorder');

    // Prompt for missing options
    const options = await promptForRecordOptions(cmdOptions);

    // Check if we're in a valid project directory
    await validateProjectDirectory();

    // Create recordings directory
    await ensureRecordingsDirectory();

    // Launch Playwright recorder
    Logger.info('Launching Playwright recorder...');
    const recordingFile = await launchRecorder(options);

    Logger.success(`Recording saved to: ${recordingFile}`);

    // Auto-convert if requested
    if (options.convertToBdd) {
      await autoConvertToBDD(recordingFile, options, cmdOptions);
    } else {
      Logger.newline();
      Logger.info('To convert this recording to BDD, run:');
      Logger.code(`  cpa ingest ${recordingFile}`);
      Logger.code(`  cpa run convert`);
    }

    // Generate page objects if requested
    if (options.generatePageObjects) {
      await generatePageObjects(recordingFile, options);
    }

    // Generate test data if requested
    if (options.generateData) {
      await generateTestData(recordingFile, options);
    }

    Logger.newline();
    Logger.success('✅ Recording workflow complete!');
    Logger.newline();
    Logger.info('Next steps:');
    Logger.step('1. Review the generated feature file in features/');
    Logger.step('2. Implement step definitions in steps/');
    Logger.step('3. Run: cpa run test');

  } catch (error) {
    Logger.error(`Recording failed: ${error}`);
    process.exit(1);
  }
}

async function autoConvertToBDD(
  recordingFile: string,
  options: RecordOptions,
  cmdOptions: any
): Promise<void> {
  const spinner = ora('Converting to BDD...').start();

  try {
    // Step 1: Parse the recording
    spinner.text = 'Parsing Playwright recording...';
    const parser = new PythonParser();
    const recording = await parser.parseFile(recordingFile);

    if (!recording || recording.actions.length === 0) {
      throw new Error('No actions found in recording');
    }

    // Step 2: Generate BDD with AI
    spinner.text = 'Generating BDD scenarios with AI...';
    const anthropicClient = new AnthropicClient();
    await anthropicClient.initialize();

    const scenarioName = options.scenarioName || path.basename(recordingFile, '.py');
    const bddResult = await anthropicClient.generateBDDFromRecording(
      recording.actions,
      scenarioName
    );

    if (!bddResult.success) {
      throw new Error(`AI conversion failed: ${bddResult.error}`);
    }

    // Step 3: Save feature file
    spinner.text = 'Saving feature file...';
    const featureFile = await saveBDDResult(bddResult, scenarioName);

    // Step 4: Generate step definitions
    spinner.text = 'Generating step definitions...';
    const stepFile = await generateStepDefinitions(bddResult, scenarioName);

    // Step 5: Generate page objects if requested
    if (options.generatePageObjects) {
      spinner.text = 'Generating page objects...';
      await generatePageObjectsFromAI(bddResult, scenarioName);
    }

    spinner.succeed('Auto-conversion complete!');

    Logger.newline();
    Logger.success('📄 Generated files:');
    Logger.step(`Feature: ${featureFile}`);
    Logger.step(`Steps: ${stepFile}`);

    await anthropicClient.cleanup();

  } catch (error) {
    spinner.fail();
    Logger.error(`Auto-conversion failed: ${error}`);
    Logger.newline();
    Logger.info('You can still convert manually:');
    Logger.code(`  cpa ingest ${recordingFile}`);
    Logger.code(`  cpa run convert`);
  }
}

async function saveBDDResult(bddResult: any, scenarioName: string): Promise<string> {
  const featuresDir = 'features';
  await FileUtils.ensureDirectory(featuresDir);

  const featureName = scenarioName.replace(/[^a-zA-Z0-9_]/g, '_').toLowerCase();
  const featureFile = path.join(featuresDir, `${featureName}.feature`);

  let featureContent = bddResult.feature || '';
  if (!featureContent && bddResult.scenarios) {
    featureContent = generateFeatureFromScenarios(scenarioName, bddResult.scenarios);
  }

  await FileUtils.writeFile(featureFile, featureContent);
  return featureFile;
}

function generateFeatureFromScenarios(featureName: string, scenarios: any[]): string {
  let content = `Feature: ${featureName}\n`;
  content += `  As a user\n`;
  content += `  I want to perform actions\n`;
  content += `  So that I can achieve my goals\n\n`;

  for (const scenario of scenarios) {
    content += `  Scenario: ${scenario.name}\n`;
    for (const step of scenario.steps || []) {
      content += `    ${step.keyword} ${step.text}\n`;
    }
    content += '\n';
  }

  return content;
}

async function generateStepDefinitions(bddResult: any, scenarioName: string): Promise<string> {
  const stepsDir = 'steps';
  await FileUtils.ensureDirectory(stepsDir);

  const stepName = scenarioName.replace(/[^a-zA-Z0-9_]/g, '_').toLowerCase();
  const stepFile = path.join(stepsDir, `${stepName}_steps.py`);

  const generator = new PythonGenerator();
  const stepContent = generator.generateStepDefinitions(bddResult);

  await FileUtils.writeFile(stepFile, stepContent);
  return stepFile;
}

async function generatePageObjects(recordingFile: string, options: RecordOptions): Promise<void> {
  try {
    const parser = new PythonParser();
    const recording = await parser.parseFile(recordingFile);

    const spinner = ora('Generating page objects...').start();

    const generator = new PythonGenerator();
    const pageObjects = generator.generatePageObjects(recording);

    const pagesDir = 'pages';
    await FileUtils.ensureDirectory(pagesDir);

    for (const po of pageObjects) {
      const poFile = path.join(pagesDir, `${po.name.toLowerCase()}_page.py`);
      await FileUtils.writeFile(poFile, po.content);
      Logger.step(`Generated: ${poFile}`);
    }

    spinner.succeed(`Generated ${pageObjects.length} page objects`);

  } catch (error) {
    Logger.error(`Failed to generate page objects: ${error}`);
  }
}

async function generatePageObjectsFromAI(bddResult: any, scenarioName: string): Promise<void> {
  try {
    const spinner = ora('Generating page objects from BDD...').start();

    const generator = new PythonGenerator();
    const pageObjects = generator.generatePageObjectsFromBDD(bddResult);

    const pagesDir = 'pages';
    await FileUtils.ensureDirectory(pagesDir);

    for (const po of pageObjects) {
      const poFile = path.join(pagesDir, `${po.name.toLowerCase()}_page.py`);
      await FileUtils.writeFile(poFile, po.content);
      Logger.step(`Generated: ${poFile}`);
    }

    spinner.succeed(`Generated ${pageObjects.length} page objects`);

  } catch (error) {
    Logger.error(`Failed to generate page objects: ${error}`);
  }
}

async function generateTestData(recordingFile: string, options: RecordOptions): Promise<void> {
  try {
    const spinner = ora('Generating test data schema...').start();

    const parser = new PythonParser();
    const recording = await parser.parseFile(recordingFile);

    const dataSchema = extractDataSchema(recording);
    const dataFile = 'fixtures/test_data.json';

    await FileUtils.writeFile(dataFile, JSON.stringify(dataSchema, null, 2));

    spinner.succeed('Test data schema generated');
    Logger.step(`Generated: ${dataFile}`);

  } catch (error) {
    Logger.error(`Failed to generate test data: ${error}`);
  }
}

function extractDataSchema(recording: any): object {
  const schema: any = {
    description: 'Auto-generated test data schema from recording',
    generated: new Date().toISOString(),
    entities: {},
  };

  const forms: string[] = [];
  const inputs: string[] = [];

  for (const action of recording.actions || []) {
    if (action.type === 'fill' || action.type === 'check') {
      const selector = action.selector || '';
      const value = action.value || '';

      // Detect field type
      let fieldType = 'string';
      let fieldName = selector;

      if (selector.includes('email') || value.includes('@')) {
        fieldType = 'email';
      } else if (selector.includes('password')) {
        fieldType = 'password';
      } else if (selector.includes('phone')) {
        fieldType = 'phone';
      } else if (/^\d+$/.test(value)) {
        fieldType = 'integer';
      } else if (/^\d+\.\d+$/.test(value)) {
        fieldType = 'number';
      }

      // Clean field name
      fieldName = fieldName.replace(/[#.\[\]"']/g, ' ').trim();
      fieldName = fieldName.split(/\s+/).slice(-1)[0] || `field_${inputs.length}`;

      inputs.push({
        name: fieldName,
        type: fieldType,
        example: value,
      });
    }
  }

  if (inputs.length > 0) {
    schema.entities.form_data = {
      fields: inputs,
    };
  }

  return schema;
}

async function promptForRecordOptions(cmdOptions: any): Promise<RecordOptions> {
  const questions: any[] = [];

  if (!cmdOptions.url) {
    questions.push({
      type: 'input',
      name: 'url',
      message: 'Enter the starting URL:',
      default: 'https://example.com',
      validate: (input: string) => {
        if (!input) return 'URL is required';
        if (!input.startsWith('http')) {
          return 'URL must start with http:// or https://';
        }
        return true;
      }
    });
  }

  if (!cmdOptions.scenarioName) {
    questions.push({
      type: 'input',
      name: 'scenarioName',
      message: 'Enter scenario name:',
      default: 'my_scenario',
      validate: (input: string) => {
        if (!input) return 'Scenario name is required';
        if (!/^[a-z0-9_-]+$/i.test(input)) {
          return 'Scenario name can only contain letters, numbers, hyphens, and underscores';
        }
        return true;
      }
    });
  }

  // Ask about auto-conversion if not specified
  if (cmdOptions.convertToBdd === undefined || cmdOptions.convertToBdd === null) {
    questions.push({
      type: 'confirm',
      name: 'convertToBdd',
      message: 'Auto-convert to BDD after recording?',
      default: true,
    });
  }

  // Ask about page objects if converting to BDD
  if ((cmdOptions.convertToBdd || questions.find(q => q.name === 'convertToBdd')?.default) &&
      cmdOptions.generatePageObjects === undefined) {
    questions.push({
      type: 'confirm',
      name: 'generatePageObjects',
      message: 'Generate page objects?',
      default: true,
    });
  }

  // Ask about test data if not specified
  if (cmdOptions.generateData === undefined) {
    questions.push({
      type: 'confirm',
      name: 'generateData',
      message: 'Generate test data schema?',
      default: false,
    });
  }

  const answers = await inquirer.prompt(questions);

  // Validate browser option (BUG-017 fix)
  const browser = cmdOptions.browser || 'chromium';
  const validBrowsers = ['chromium', 'firefox', 'webkit'];
  if (!validBrowsers.includes(browser)) {
    throw new Error(`Invalid browser: ${browser}. Must be one of: ${validBrowsers.join(', ')}`);
  }

  return {
    url: cmdOptions.url || answers.url,
    scenarioName: cmdOptions.scenarioName || answers.scenarioName,
    browser: browser,
    convertToBdd: cmdOptions.convertToBdd ?? answers.convertToBdd ?? false,
    generateData: cmdOptions.generateData ?? answers.generateData ?? false,
    generatePageObjects: cmdOptions.generatePageObjects ?? answers.generatePageObjects ?? false,
  };
}

async function validateProjectDirectory(): Promise<void> {
  // Check if we're in a valid project directory
  const hasFeatures = await FileUtils.directoryExists('features');
  const hasSteps = await FileUtils.directoryExists('steps');

  if (!hasFeatures && !hasSteps) {
    const cwd = process.cwd();
    Logger.error('❌ Not in a test framework directory!');
    Logger.newline();
    Logger.error('Current directory: ' + cwd);
    Logger.error('Required directories not found: features/ and steps/');
    Logger.newline();
    Logger.info('📍 You need to be in the project ROOT directory (where features/ and steps/ exist)');
    Logger.newline();
    Logger.title('How to fix:');
    Logger.newline();
    Logger.step('Option 1: Navigate to your existing project root');
    Logger.code('  cd path/to/your/test-project  # Where features/ and steps/ are located');
    Logger.code('  playwright-ai record --url https://your-app.com');
    Logger.newline();
    Logger.step('Option 2: Initialize a new test framework first');
    Logger.code('  playwright-ai init  # Creates a new framework with proper structure');
    Logger.code('  cd your-project-name');
    Logger.code('  playwright-ai record --url https://your-app.com');
    Logger.newline();
    Logger.info('💡 Tip: Look for the directory containing features/, steps/, pages/, helpers/');
    throw new Error('Invalid project directory - not in framework root');
  }
}

async function ensureRecordingsDirectory(): Promise<void> {
  await FileUtils.ensureDirectory('recordings');
}

async function launchRecorder(options: RecordOptions): Promise<string> {
  const spinner = ora('Preparing Playwright recorder...').start();

  try {
    // Generate output file path
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
    const scenarioName = options.scenarioName || 'recording';
    const outputFile = path.join(
      'recordings',
      `${scenarioName}_${timestamp}.py`
    );

    spinner.text = 'Recorder is now open. Perform your test actions in the browser.';
    spinner.text += '\nClose the browser when done.';

    // Build Playwright codegen arguments
    const args = [
      'codegen',
      options.url,
      '--browser',
      options.browser || 'chromium',
      '--target',
      'python',
      '--output',
      outputFile
    ];

    // Add timeout option (10 minutes default)
    const timeoutMs = 10 * 60 * 1000; // 10 minutes

    // Launch Playwright codegen using spawn to prevent command injection (SEC-002 fix)
    await new Promise<void>((resolve, reject) => {
      const childProcess = spawn('playwright', args, {
        stdio: 'inherit',
        shell: false, // Critical: disable shell to prevent command injection
        timeout: timeoutMs,
      });

      let resolved = false;

      const resolveOnce = () => {
        if (!resolved) {
          resolved = true;
          resolve();
        }
      };

      const rejectOnce = (error: Error) => {
        if (!resolved) {
          resolved = true;
          reject(error);
        }
      };

      childProcess.on('error', (error) => {
        rejectOnce(new Error(`Failed to launch Playwright: ${error.message}`));
      });

      childProcess.on('close', (code) => {
        if (code === 0) {
          resolveOnce();
        } else if (code === null) {
          rejectOnce(new Error('Playwright recorder timed out'));
        } else {
          rejectOnce(new Error(`Playwright exited with code ${code}`));
        }
      });

      // Handle timeout
      setTimeout(() => {
        if (!resolved) {
          childProcess.kill('SIGTERM');
          rejectOnce(new Error('Recording timeout: Please complete your actions within 10 minutes'));
        }
      }, timeoutMs);
    });

    spinner.succeed('Recording completed successfully');

    // Verify file was created
    if (!require('fs').existsSync(outputFile)) {
      throw new Error('Recording file was not created');
    }

    return outputFile;

  } catch (error) {
    spinner.fail();
    throw new Error(`Failed to launch recorder: ${error}`);
  }
}
