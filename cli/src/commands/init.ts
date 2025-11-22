import { Command } from 'commander';
import inquirer from 'inquirer';
import ora from 'ora';
import chalk from 'chalk';
import path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';
import { InitOptions } from '../types';
import { PythonGenerator } from '../generators/python-generator';
import { FileUtils } from '../utils/file-utils';
import { Logger } from '../utils/logger';

const execAsync = promisify(exec);

export function createInitCommand(): Command {
  return new Command('init')
    .description('Initialize a new test automation framework')
    .option('-l, --language <type>', 'Framework language (python|typescript)', 'python')
    .option('-n, --project-name <name>', 'Project name')
    .option('--bdd', 'Enable BDD framework (default: true)', true)
    .option('--power-apps', 'Add Power Apps helpers', false)
    .option('--ai-provider <provider>', 'AI provider (anthropic|openai|none)', 'anthropic')
    .option('-d, --directory <path>', 'Output directory')
    .action(async (options) => {
      await initializeFramework(options);
    });
}

async function initializeFramework(cmdOptions: any): Promise<void> {
  try {
    Logger.title('🤖 AI-Powered Playwright Framework Generator');

    // Prompt for missing options
    const options = await promptForOptions(cmdOptions);

    // Validate options
    validateOptions(options);

    // Create project directory
    const projectDir = await createProjectDirectory(options);

    // Generate framework
    await generateFramework(projectDir, options);

    // Initialize git
    await initializeGit(projectDir);

    // Install dependencies
    await installDependencies(projectDir, options);

    // Display success message and next steps
    displaySuccessMessage(options);

  } catch (error) {
    Logger.error(`Failed to initialize framework: ${error}`);
    process.exit(1);
  }
}

async function promptForOptions(cmdOptions: any): Promise<InitOptions> {
  const questions: any[] = [];

  // Project name
  if (!cmdOptions.projectName) {
    questions.push({
      type: 'input',
      name: 'projectName',
      message: 'Project name:',
      default: 'my-test-framework',
      validate: (input: string) => {
        if (!/^[a-z0-9-_]+$/i.test(input)) {
          return 'Project name can only contain letters, numbers, hyphens, and underscores';
        }
        return true;
      }
    });
  }

  // Language
  if (!cmdOptions.language) {
    questions.push({
      type: 'list',
      name: 'language',
      message: 'Select framework language:',
      choices: [
        { name: 'Python (Recommended)', value: 'python' },
        { name: 'TypeScript (Coming soon)', value: 'typescript', disabled: true }
      ],
      default: 'python'
    });
  }

  // BDD
  if (cmdOptions.bdd === undefined) {
    questions.push({
      type: 'confirm',
      name: 'bdd',
      message: 'Enable BDD (Behave)?',
      default: true
    });
  }

  // Power Apps
  if (!cmdOptions.powerApps) {
    questions.push({
      type: 'confirm',
      name: 'powerApps',
      message: 'Optimize for Power Apps?',
      default: false
    });
  }

  // AI Provider
  if (!cmdOptions.aiProvider) {
    questions.push({
      type: 'list',
      name: 'aiProvider',
      message: 'Select AI provider (for self-healing & data generation):',
      choices: [
        { name: 'Anthropic (Claude) - Recommended', value: 'anthropic' },
        { name: 'OpenAI (GPT-4)', value: 'openai' },
        { name: 'None (Disable AI features)', value: 'none' }
      ],
      default: 'anthropic'
    });
  }

  const answers = await inquirer.prompt(questions);

  return {
    projectName: cmdOptions.projectName || answers.projectName,
    language: (cmdOptions.language || answers.language) as 'python' | 'typescript',
    bdd: cmdOptions.bdd !== undefined ? cmdOptions.bdd : answers.bdd,
    powerApps: cmdOptions.powerApps || answers.powerApps || false,
    aiProvider: (cmdOptions.aiProvider || answers.aiProvider) as 'anthropic' | 'openai' | 'none',
    directory: cmdOptions.directory
  };
}

function validateOptions(options: InitOptions): void {
  if (options.language === 'typescript') {
    throw new Error('TypeScript framework is not yet supported. Please use Python.');
  }

  if (!['anthropic', 'openai', 'none'].includes(options.aiProvider)) {
    throw new Error('Invalid AI provider. Choose: anthropic, openai, or none');
  }
}

async function createProjectDirectory(options: InitOptions): Promise<string> {
  const spinner = ora('Creating project directory...').start();

  try {
    const projectDir = options.directory
      ? path.resolve(options.directory)
      : path.resolve(process.cwd(), options.projectName);

    // Check if directory already exists
    const exists = await FileUtils.directoryExists(projectDir);

    if (exists) {
      spinner.fail();
      throw new Error(`Directory ${projectDir} already exists. Please choose a different name or location.`);
    }

    // Create directory
    await FileUtils.ensureDirectory(projectDir);

    spinner.succeed(chalk.green(`Project directory created: ${projectDir}`));

    return projectDir;

  } catch (error) {
    spinner.fail();
    throw error;
  }
}

async function generateFramework(projectDir: string, options: InitOptions): Promise<void> {
  const spinner = ora('Generating framework files...').start();

  try {
    if (options.language === 'python') {
      const generator = new PythonGenerator();
      await generator.generate(projectDir, options);
      await generator.generateGitignore(projectDir);
    }

    spinner.succeed(chalk.green('Framework files generated'));

  } catch (error) {
    spinner.fail();
    throw error;
  }
}

async function initializeGit(projectDir: string): Promise<void> {
  const spinner = ora('Initializing git repository...').start();

  try {
    await execAsync('git init', { cwd: projectDir });
    spinner.succeed(chalk.green('Git repository initialized'));
  } catch (error) {
    spinner.warn(chalk.yellow('Git initialization skipped (git not installed or error occurred)'));
  }
}

async function installDependencies(projectDir: string, options: InitOptions): Promise<void> {
  Logger.newline();

  const shouldInstall = await inquirer.prompt([
    {
      type: 'confirm',
      name: 'install',
      message: 'Install dependencies now?',
      default: true
    }
  ]);

  if (!shouldInstall.install) {
    Logger.warning('Dependencies not installed. Run manually:');
    Logger.code('  pip install -r requirements.txt');
    Logger.code('  playwright install chromium');
    return;
  }

  const spinner = ora('Installing Python dependencies...').start();

  try {
    if (options.language === 'python') {
      // Create virtual environment
      spinner.text = 'Creating virtual environment...';
      await execAsync('python3 -m venv venv || python -m venv venv', { cwd: projectDir });

      // Install requirements
      spinner.text = 'Installing Python packages...';
      const pipCommand = process.platform === 'win32'
        ? 'venv\\Scripts\\pip'
        : 'venv/bin/pip';

      await execAsync(`${pipCommand} install -r requirements.txt`, {
        cwd: projectDir
      });

      // Install Playwright browsers
      spinner.text = 'Installing Playwright browsers...';
      const pythonCommand = process.platform === 'win32'
        ? 'venv\\Scripts\\python'
        : 'venv/bin/python';

      await execAsync(`${pythonCommand} -m playwright install chromium`, {
        cwd: projectDir
      });

      spinner.succeed(chalk.green('Dependencies installed successfully'));
    }

  } catch (error) {
    spinner.fail();
    Logger.error('Failed to install dependencies automatically.');
    Logger.warning('Please install manually:');
    Logger.code('  python3 -m venv venv');
    Logger.code('  source venv/bin/activate  # On Windows: venv\\Scripts\\activate');
    Logger.code('  pip install -r requirements.txt');
    Logger.code('  playwright install chromium');
  }
}

function displaySuccessMessage(options: InitOptions): void {
  Logger.newline();
  Logger.title('✅ Framework Initialized Successfully!');

  Logger.newline();
  Logger.info('Project Details:');
  Logger.keyValue('  Name', options.projectName);
  Logger.keyValue('  Language', options.language);
  Logger.keyValue('  BDD', options.bdd ? 'Enabled (Behave)' : 'Disabled');
  Logger.keyValue('  Power Apps', options.powerApps ? 'Enabled' : 'Disabled');
  Logger.keyValue('  AI Provider', options.aiProvider);

  Logger.newline();
  Logger.title('📋 Next Steps:');

  Logger.step(`cd ${options.projectName}`);

  if (options.aiProvider !== 'none') {
    Logger.step('Edit .env file and add your AI API key');

    if (options.aiProvider === 'anthropic') {
      Logger.code('  ANTHROPIC_API_KEY=sk-ant-your-key-here');
      Logger.info('  Get your API key at: https://console.anthropic.com/');
    } else if (options.aiProvider === 'openai') {
      Logger.code('  OPENAI_API_KEY=sk-your-key-here');
      Logger.info('  Get your API key at: https://platform.openai.com/');
    }

    Logger.newline();
  }

  Logger.step('Configure your application URL and credentials in .env:');
  Logger.code('  APP_URL=https://your-app.com');
  Logger.code('  TEST_USER=test@example.com');
  Logger.code('  TEST_PASSWORD=your-password');

  Logger.newline();
  Logger.step('Run your tests:');
  Logger.code('  behave');
  Logger.code('  behave --tags=@smoke');

  Logger.newline();
  Logger.step('Record a new scenario:');
  Logger.code('  playwright-ai record --url https://your-app.com');

  Logger.newline();
  Logger.success('Happy testing! 🚀');
  Logger.newline();
}
