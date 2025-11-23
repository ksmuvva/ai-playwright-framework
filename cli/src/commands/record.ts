import { Command } from 'commander';
import { exec, spawn } from 'child_process';
import { promisify } from 'util';
import inquirer from 'inquirer';
import ora from 'ora';
import path from 'path';
import { RecordOptions } from '../types';
import { Logger } from '../utils/logger';
import { FileUtils } from '../utils/file-utils';

const execAsync = promisify(exec);

export function createRecordCommand(): Command {
  return new Command('record')
    .description('Record a new test scenario using Playwright')
    .option('-u, --url <url>', 'Starting URL for recording')
    .option('-s, --scenario-name <name>', 'Name for the scenario')
    .option('-b, --browser <browser>', 'Browser to use (chromium, firefox, webkit)', 'chromium')
    .option('--convert-to-bdd', 'Auto-convert to BDD after recording', false)
    .option('--generate-data', 'Generate test data schema from recording', false)
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
    const recordingFile = await launchRecorder(options);

    Logger.success(`Recording saved to: ${recordingFile}`);

    // Auto-convert if requested
    if (options.convertToBdd) {
      Logger.info('Auto-converting to BDD...');
      // TODO: Call convert command
      Logger.info('Run: playwright-ai convert ' + recordingFile);
    } else {
      Logger.newline();
      Logger.info('To convert this recording to BDD, run:');
      Logger.code(`  playwright-ai convert ${recordingFile}`);
    }

  } catch (error) {
    Logger.error(`Recording failed: ${error}`);
    process.exit(1);
  }
}

async function promptForRecordOptions(cmdOptions: any): Promise<RecordOptions> {
  const questions: any[] = [];

  if (!cmdOptions.url) {
    questions.push({
      type: 'input',
      name: 'url',
      message: 'Enter the starting URL:',
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
    convertToBdd: cmdOptions.convertToBdd || false,
    generateData: cmdOptions.generateData || false
  };
}

async function validateProjectDirectory(): Promise<void> {
  // Check if we're in a valid project directory
  const hasFeatures = await FileUtils.directoryExists('features');
  const hasSteps = await FileUtils.directoryExists('steps');

  if (!hasFeatures && !hasSteps) {
    Logger.warning('Not in a test framework directory.');
    Logger.info('Make sure you\'re in the project root directory, or initialize a new framework:');
    Logger.code('  playwright-ai init');
    throw new Error('Invalid project directory');
  }
}

async function ensureRecordingsDirectory(): Promise<void> {
  await FileUtils.ensureDirectory('recordings');
}

async function launchRecorder(options: RecordOptions): Promise<string> {
  const spinner = ora('Launching Playwright recorder...').start();

  try {
    // Generate output file path
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
    const outputFile = path.join(
      'recordings',
      `${options.scenarioName}_${timestamp}.py`
    );

    spinner.text = 'Recorder is now open. Perform your test actions in the browser.';
    spinner.text += '\nClose the browser when done.';

    // Launch Playwright codegen using spawn to prevent command injection (SEC-002 fix)
    await new Promise<void>((resolve, reject) => {
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

      const childProcess = spawn('playwright', args, {
        stdio: 'inherit',
        shell: false // Critical: disable shell to prevent command injection
      });

      childProcess.on('error', (error) => {
        reject(new Error(`Failed to launch Playwright: ${error.message}`));
      });

      childProcess.on('close', (code) => {
        if (code === 0) {
          resolve();
        } else {
          reject(new Error(`Playwright exited with code ${code}`));
        }
      });
    });

    spinner.succeed('Recording completed');

    return outputFile;

  } catch (error) {
    spinner.fail();
    throw new Error(`Failed to launch recorder: ${error}`);
  }
}
