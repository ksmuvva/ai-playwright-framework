import { Command } from 'commander';
import inquirer from 'inquirer';
import ora from 'ora';
import chalk from 'chalk';
import path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs/promises';
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

    // Create/Update CLI .env file
    await createCliEnvFile(options);

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

  // Project name (BUG-009 fix - enhanced validation)
  if (!cmdOptions.projectName) {
    questions.push({
      type: 'input',
      name: 'projectName',
      message: 'Project name:',
      default: 'my-test-framework',
      validate: (input: string) => {
        // Check basic pattern
        if (!/^[a-z0-9-_]+$/i.test(input)) {
          return 'Project name can only contain letters, numbers, hyphens, and underscores';
        }

        // Check length
        if (input.length > 100) {
          return 'Project name too long (max 100 characters)';
        }

        if (input.length < 1) {
          return 'Project name cannot be empty';
        }

        // Check for reserved names
        const reservedNames = ['node_modules', '.git', 'dist', 'build', 'test', 'tests', 'src', 'lib'];
        if (reservedNames.includes(input.toLowerCase())) {
          return 'Project name is reserved. Please choose a different name.';
        }

        // Check for Windows reserved names
        const windowsReserved = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'];
        if (windowsReserved.includes(input.toUpperCase())) {
          return 'Project name is reserved on Windows. Please choose a different name.';
        }

        // Check for starting/ending with special characters
        if (input.startsWith('-') || input.startsWith('_') || input.endsWith('-') || input.endsWith('_')) {
          return 'Project name cannot start or end with hyphens or underscores';
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

  // Determine AI provider
  const aiProvider = (cmdOptions.aiProvider || answers.aiProvider) as 'anthropic' | 'openai' | 'none';

  // Prompt for model and API key if AI provider is selected
  let aiModel: string | undefined;
  let apiKey: string | undefined;

  if (aiProvider !== 'none') {
    const aiQuestions: any[] = [];

    // Model selection based on provider
    if (aiProvider === 'anthropic') {
      aiQuestions.push({
        type: 'list',
        name: 'aiModel',
        message: 'Select Claude model:',
        choices: [
          { name: 'Claude Sonnet 4.5 (Recommended - Fast & Intelligent)', value: 'claude-sonnet-4-5-20250929' },
          { name: 'Claude Opus 4 (Most Capable)', value: 'claude-opus-4-20250514' },
          { name: 'Claude Sonnet 3.5', value: 'claude-3-5-sonnet-20241022' },
          { name: 'Claude Haiku 3.5 (Fast & Economical)', value: 'claude-3-5-haiku-20241022' }
        ],
        default: 'claude-sonnet-4-5-20250929'
      });
    } else if (aiProvider === 'openai') {
      aiQuestions.push({
        type: 'list',
        name: 'aiModel',
        message: 'Select OpenAI model:',
        choices: [
          { name: 'GPT-4 Turbo (Recommended)', value: 'gpt-4-turbo-preview' },
          { name: 'GPT-4', value: 'gpt-4' },
          { name: 'GPT-3.5 Turbo (Fast & Economical)', value: 'gpt-3.5-turbo' }
        ],
        default: 'gpt-4-turbo-preview'
      });
    }

    // API Key input
    aiQuestions.push({
      type: 'password',
      name: 'apiKey',
      message: `Enter your ${aiProvider === 'anthropic' ? 'Anthropic' : 'OpenAI'} API key:`,
      validate: (input: string) => {
        if (!input || input.trim().length === 0) {
          return 'API key is required';
        }
        if (aiProvider === 'anthropic' && !input.startsWith('sk-ant-')) {
          return 'Anthropic API keys should start with "sk-ant-"';
        }
        if (aiProvider === 'openai' && !input.startsWith('sk-')) {
          return 'OpenAI API keys should start with "sk-"';
        }
        return true;
      }
    });

    const aiAnswers = await inquirer.prompt(aiQuestions);
    aiModel = aiAnswers.aiModel;
    apiKey = aiAnswers.apiKey;
  }

  return {
    projectName: cmdOptions.projectName || answers.projectName,
    language: (cmdOptions.language || answers.language) as 'python' | 'typescript',
    bdd: cmdOptions.bdd !== undefined ? cmdOptions.bdd : answers.bdd,
    powerApps: cmdOptions.powerApps || answers.powerApps || false,
    aiProvider: aiProvider,
    aiModel: aiModel,
    apiKey: apiKey,
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
      message: 'Install dependencies now (using UV - fast Python package manager)?',
      default: true
    }
  ]);

  if (!shouldInstall.install) {
    Logger.warning('Dependencies not installed. Run manually:');
    Logger.code('  uv sync  # Install all dependencies (creates venv automatically)');
    Logger.code('  uv run playwright install chromium  # Install browsers');
    Logger.newline();
    Logger.info('💡 UV is 10-100x faster than pip! Install it: https://docs.astral.sh/uv/');
    return;
  }

  const spinner = ora('Installing Python dependencies with UV...').start();

  try {
    if (options.language === 'python') {
      // Check if UV is installed
      spinner.text = 'Checking for UV installation...';
      try {
        await execAsync('uv --version', { cwd: projectDir });
        spinner.succeed(chalk.green('UV package manager detected'));
      } catch (uvCheckError) {
        spinner.warn(chalk.yellow('UV not found. Please install UV for 10-100x faster installs!'));
        Logger.newline();
        Logger.info('Install UV with one command:');
        Logger.code('  curl -LsSf https://astral.sh/uv/install.sh | sh  # Unix/macOS');
        Logger.code('  powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows');
        Logger.newline();
        Logger.info('Falling back to pip (slower)...');

        // Fallback to pip
        spinner.start('Creating virtual environment with venv...');
        await execAsync('python3 -m venv .venv || python -m venv .venv', { cwd: projectDir });

        spinner.text = 'Installing Python packages with pip...';
        const pipCommand = process.platform === 'win32'
          ? '.venv\\Scripts\\pip'
          : '.venv/bin/pip';

        await execAsync(`${pipCommand} install -e .`, {
          cwd: projectDir
        });

        spinner.text = 'Installing Playwright browsers...';
        const pythonCommand = process.platform === 'win32'
          ? '.venv\\Scripts\\python'
          : '.venv/bin/python';

        await execAsync(`${pythonCommand} -m playwright install chromium`, {
          cwd: projectDir
        });

        spinner.succeed(chalk.green('Dependencies installed successfully (with pip)'));
        return;
      }

      // UV is installed - use it!
      spinner.start('Installing dependencies with UV (10-100x faster than pip)...');

      // UV automatically creates venv and installs dependencies
      await execAsync('uv sync', { cwd: projectDir });

      // Install Playwright browsers using UV
      spinner.text = 'Installing Playwright browsers...';
      await execAsync('uv run playwright install chromium', {
        cwd: projectDir
      });

      spinner.succeed(chalk.green('✨ Dependencies installed successfully with UV!'));
    }

  } catch (error) {
    spinner.fail();
    Logger.error('Failed to install dependencies automatically.');
    Logger.newline();
    Logger.warning('Please install manually:');
    Logger.newline();
    Logger.info('Option 1 (Recommended - UV):');
    Logger.code('  # Install UV first: https://docs.astral.sh/uv/');
    Logger.code('  uv sync');
    Logger.code('  uv run playwright install chromium');
    Logger.newline();
    Logger.info('Option 2 (Traditional - pip):');
    Logger.code('  python3 -m venv .venv');
    Logger.code('  source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate');
    Logger.code('  pip install -e .');
    Logger.code('  playwright install chromium');
  }
}

async function createCliEnvFile(options: InitOptions): Promise<void> {
  if (options.aiProvider === 'none' || !options.apiKey) {
    return; // Skip if no AI provider or no API key
  }

  const spinner = ora('Creating CLI .env file...').start();

  try {
    // Get the CLI root directory (where package.json is)
    const cliRootDir = path.resolve(__dirname, '../..');
    const envFilePath = path.join(cliRootDir, '.env');

    // Check if .env file exists
    let envContent = '';
    try {
      envContent = await fs.readFile(envFilePath, 'utf-8');
    } catch (error) {
      // File doesn't exist, will create new one
    }

    // Parse existing env variables
    const envVars: Record<string, string> = {};
    if (envContent) {
      envContent.split('\n').forEach(line => {
        const trimmed = line.trim();
        if (trimmed && !trimmed.startsWith('#')) {
          const [key, ...valueParts] = trimmed.split('=');
          if (key && valueParts.length > 0) {
            envVars[key.trim()] = valueParts.join('=').trim();
          }
        }
      });
    }

    // Update AI configuration
    envVars['AI_PROVIDER'] = options.aiProvider;
    if (options.aiModel) {
      envVars['AI_MODEL'] = options.aiModel;
    }

    // Set the appropriate API key
    if (options.aiProvider === 'anthropic') {
      envVars['ANTHROPIC_API_KEY'] = options.apiKey!;
    } else if (options.aiProvider === 'openai') {
      envVars['OPENAI_API_KEY'] = options.apiKey!;
    }

    // Build new .env content
    const newEnvContent = `# AI Configuration (Generated by playwright-ai CLI)
# Last updated: ${new Date().toISOString()}

AI_PROVIDER=${envVars['AI_PROVIDER']}
${envVars['AI_MODEL'] ? `AI_MODEL=${envVars['AI_MODEL']}` : ''}

# API Keys
${envVars['ANTHROPIC_API_KEY'] ? `ANTHROPIC_API_KEY=${envVars['ANTHROPIC_API_KEY']}` : '# ANTHROPIC_API_KEY=sk-ant-your-key-here'}
${envVars['OPENAI_API_KEY'] ? `OPENAI_API_KEY=${envVars['OPENAI_API_KEY']}` : '# OPENAI_API_KEY=sk-your-key-here'}
`;

    // Write .env file with secure permissions (0o600 - owner read/write only)
    await fs.writeFile(envFilePath, newEnvContent.trim() + '\n', {
      encoding: 'utf-8',
      mode: 0o600 // SECURITY: Prevent other users from reading API keys
    });

    spinner.succeed(chalk.green('CLI .env file created/updated'));

  } catch (error) {
    spinner.fail();
    Logger.warning(`Failed to create CLI .env file: ${error}`);
    Logger.info('You can manually create it later.');
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
  Logger.step('Activate your environment and run tests:');
  Logger.code('  # With UV (recommended):');
  Logger.code('  uv run behave');
  Logger.code('  uv run behave --tags=@smoke');
  Logger.code('');
  Logger.code('  # Or activate venv manually:');
  Logger.code('  source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate');
  Logger.code('  behave');

  Logger.newline();
  Logger.step('Record a new scenario:');
  Logger.code('  playwright-ai record --url https://your-app.com');

  Logger.newline();
  Logger.info('💡 UV is 10-100x faster than pip! Already using it for dependencies.');
  Logger.newline();
  Logger.success('Happy testing! 🚀');
  Logger.newline();
}
