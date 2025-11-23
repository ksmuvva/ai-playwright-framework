import path from 'path';
import { FileUtils } from '../utils/file-utils';
import { TemplateEngine } from './template-engine';
import { Logger } from '../utils/logger';
import { InitOptions, TemplateContext } from '../types';

export class PythonGenerator {
  private templateEngine: TemplateEngine;
  private templateDir: string;

  constructor() {
    this.templateEngine = new TemplateEngine();
    this.templateDir = FileUtils.getTemplatePath('python');
  }

  /**
   * Generate complete Python framework
   */
  async generate(projectDir: string, options: InitOptions): Promise<void> {
    Logger.title('Generating Python Framework');

    // Create directory structure
    await this.createDirectoryStructure(projectDir);

    // Copy helper files
    await this.copyHelpers(projectDir);

    // Copy step files
    await this.copyStepFiles(projectDir);

    // Generate configuration files
    await this.generateConfigFiles(projectDir, options);

    // Generate requirements.txt
    await this.copyRequirements(projectDir);

    // Generate behave.ini
    await this.copyBehaveConfig(projectDir);

    // Generate .env.example
    await this.copyEnvExample(projectDir);

    // Generate README
    await this.generateReadme(projectDir, options);

    // Generate example feature
    await this.copyExampleFeature(projectDir);

    Logger.success('Python framework generated successfully!');
  }

  /**
   * Create directory structure
   */
  private async createDirectoryStructure(projectDir: string): Promise<void> {
    Logger.step('Creating directory structure...');

    const directories = [
      'features',
      'steps',
      'helpers',
      'pages',
      'fixtures',
      'reports/screenshots',
      'reports/videos',
      'auth_states',
      'config'
    ];

    for (const dir of directories) {
      await FileUtils.ensureDirectory(path.join(projectDir, dir));
    }

    Logger.success('Directory structure created');
  }

  /**
   * Copy helper files (PERF-001 fix - parallelized)
   */
  private async copyHelpers(projectDir: string): Promise<void> {
    Logger.step('Copying helper files...');

    const helpers = [
      'auth_helper.py',
      'healing_locator.py',
      'wait_manager.py',
      'data_generator.py',
      'screenshot_manager.py'
    ];

    // Parallelize file copy operations
    await Promise.all([
      ...helpers.map(helper =>
        FileUtils.copyFile(
          path.join(this.templateDir, 'helpers', helper),
          path.join(projectDir, 'helpers', helper)
        )
      ),
      // Create __init__.py for helpers package
      FileUtils.writeFile(
        path.join(projectDir, 'helpers', '__init__.py'),
        '# Helper utilities\n'
      )
    ]);

    Logger.success('Helper files copied');
  }

  /**
   * Copy step files (PERF-001 fix - parallelized)
   */
  private async copyStepFiles(projectDir: string): Promise<void> {
    Logger.step('Copying step definitions...');

    const stepFiles = ['environment.py', 'common_steps.py'];

    // Parallelize file copy operations
    await Promise.all([
      ...stepFiles.map(file =>
        FileUtils.copyFile(
          path.join(this.templateDir, 'steps', file),
          path.join(projectDir, 'steps', file)
        )
      ),
      // Create __init__.py for steps package
      FileUtils.writeFile(
        path.join(projectDir, 'steps', '__init__.py'),
        '# Step definitions\n'
      )
    ]);

    Logger.success('Step files copied');
  }

  /**
   * Generate configuration files
   */
  private async generateConfigFiles(
    projectDir: string,
    options: InitOptions
  ): Promise<void> {
    Logger.step('Generating configuration files...');

    const context: TemplateContext = {
      projectName: options.projectName,
      language: 'python',
      features: {
        bdd: options.bdd,
        powerApps: options.powerApps,
        healing: options.aiProvider !== 'none'
      },
      ai: {
        provider: options.aiProvider,
        enabled: options.aiProvider !== 'none'
      }
    };

    // For now, we'll create a simple config file
    // In future, you can make this a template
    const configContent = `"""
Configuration module
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""

    # Application
    APP_URL = os.getenv('APP_URL', 'http://localhost:3000')
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')

    # Browser
    BROWSER = os.getenv('BROWSER', 'chromium')
    HEADLESS = os.getenv('HEADLESS', 'false').lower() == 'true'
    VIEWPORT_WIDTH = int(os.getenv('VIEWPORT_WIDTH', '1920'))
    VIEWPORT_HEIGHT = int(os.getenv('VIEWPORT_HEIGHT', '1080'))

    # Timeouts
    DEFAULT_TIMEOUT = int(os.getenv('DEFAULT_TIMEOUT', '10000'))
    NAVIGATION_TIMEOUT = int(os.getenv('NAVIGATION_TIMEOUT', '30000'))

    # AI
    AI_PROVIDER = os.getenv('AI_PROVIDER', '${options.aiProvider}')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    # Features
    ENABLE_HEALING = os.getenv('ENABLE_HEALING', 'true').lower() == 'true'
    ENABLE_SCREENSHOTS = os.getenv('ENABLE_SCREENSHOTS', 'true').lower() == 'true'
    ENABLE_VIDEO = os.getenv('ENABLE_VIDEO', 'false').lower() == 'true'

    # Authentication
    TEST_USER = os.getenv('TEST_USER')
    TEST_PASSWORD = os.getenv('TEST_PASSWORD')

config = Config()
`;

    await FileUtils.writeFile(
      path.join(projectDir, 'config', 'config.py'),
      configContent
    );

    await FileUtils.writeFile(
      path.join(projectDir, 'config', '__init__.py'),
      'from .config import config\n'
    );

    Logger.success('Configuration files generated');
  }

  /**
   * Copy requirements.txt
   */
  private async copyRequirements(projectDir: string): Promise<void> {
    Logger.step('Copying requirements.txt...');

    const src = path.join(this.templateDir, 'requirements.txt');
    const dest = path.join(projectDir, 'requirements.txt');
    await FileUtils.copyFile(src, dest);

    Logger.success('requirements.txt copied');
  }

  /**
   * Copy behave.ini
   */
  private async copyBehaveConfig(projectDir: string): Promise<void> {
    Logger.step('Copying behave.ini...');

    const src = path.join(this.templateDir, 'behave.ini');
    const dest = path.join(projectDir, 'behave.ini');
    await FileUtils.copyFile(src, dest);

    Logger.success('behave.ini copied');
  }

  /**
   * Copy .env.example
   */
  private async copyEnvExample(projectDir: string): Promise<void> {
    Logger.step('Copying .env.example...');

    const src = path.join(this.templateDir, '.env.example');
    const dest = path.join(projectDir, '.env.example');
    await FileUtils.copyFile(src, dest);

    // Also create a basic .env file
    await FileUtils.copyFile(src, path.join(projectDir, '.env'));

    Logger.success('.env files created');
  }

  /**
   * Generate README
   */
  private async generateReadme(
    projectDir: string,
    options: InitOptions
  ): Promise<void> {
    Logger.step('Generating README...');

    const context: TemplateContext = {
      projectName: options.projectName,
      language: 'python',
      features: {
        bdd: options.bdd,
        powerApps: options.powerApps,
        healing: options.aiProvider !== 'none'
      },
      ai: {
        provider: options.aiProvider,
        enabled: options.aiProvider !== 'none'
      }
    };

    const templatePath = path.join(this.templateDir, 'README.md.ejs');
    const outputPath = path.join(projectDir, 'README.md');

    await this.templateEngine.renderToFile(templatePath, outputPath, context);

    Logger.success('README generated');
  }

  /**
   * Copy example feature
   */
  private async copyExampleFeature(projectDir: string): Promise<void> {
    Logger.step('Copying example feature file...');

    const src = path.join(this.templateDir, 'features', 'example.feature');
    const dest = path.join(projectDir, 'features', 'example.feature');
    await FileUtils.copyFile(src, dest);

    Logger.success('Example feature copied');
  }

  /**
   * Generate .gitignore
   */
  async generateGitignore(projectDir: string): Promise<void> {
    const gitignoreContent = `# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Playwright
playwright-report/
test-results/
traces/

# Reports
reports/
*.png
*.mp4
*.webm

# Environment
.env
.env.local

# Logs
*.log
wait_performance_log.json
locator_healing_log.json

# Authentication
auth_states/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
`;

    await FileUtils.writeFile(path.join(projectDir, '.gitignore'), gitignoreContent);
    Logger.success('.gitignore created');
  }
}
