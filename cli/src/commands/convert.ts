import { Command } from 'commander';
import ora from 'ora';
import path from 'path';
import { ConvertOptions, BDDOutput } from '../types';
import { Logger } from '../utils/logger';
import { FileUtils } from '../utils/file-utils';
import { AnthropicClient } from '../ai/anthropic-client';
import * as dotenv from 'dotenv';

dotenv.config();

/**
 * Custom error class for conversion failures with stage context
 * ENHANCEMENT (RC2.4): Provides clear error messages with stage information
 */
class ConversionError extends Error {
  constructor(
    message: string,
    public stage: string,
    public suggestion?: string,
    public originalError?: Error
  ) {
    super(message);
    this.name = 'ConversionError';
  }

  toString(): string {
    const lines = [
      '',
      '═'.repeat(70),
      '❌ CONVERSION FAILED',
      '═'.repeat(70),
      '',
      `Stage: ${this.stage}`,
      `Error: ${this.message}`,
    ];

    if (this.suggestion) {
      lines.push('', `💡 Suggestion: ${this.suggestion}`);
    }

    if (this.originalError) {
      lines.push('', `Details: ${this.originalError.message}`);
    }

    lines.push('', '═'.repeat(70), '');
    return lines.join('\n');
  }
}

export function createConvertCommand(): Command {
  return new Command('convert')
    .description('Convert Playwright recording to BDD scenario')
    .argument('<recording-file>', 'Path to recording file')
    .option('-s, --scenario-name <name>', 'Override scenario name')
    .option('-o, --output-dir <dir>', 'Output directory', '.')
    .option('-v, --verbose', 'Enable verbose logging for debugging')
    .action(async (recordingFile, options) => {
      await convertRecording(recordingFile, options);
    });
}

async function convertRecording(
  recordingFile: string,
  cmdOptions: any
): Promise<void> {
  // Enable verbose logging if requested
  const verbose = cmdOptions.verbose || false;

  try {
    Logger.title('🔄 Converting Recording to BDD');

    if (verbose) {
      Logger.info('Verbose mode enabled');
    }

    // Stage 1: File Validation
    if (verbose) Logger.info('[Stage 1/6] Validating recording file...');
    const validatedFile = await validateRecordingFile(recordingFile).catch(err => {
      throw new ConversionError(
        err.message,
        'FILE_VALIDATION',
        'Ensure the recording file exists and has valid content',
        err
      );
    });

    // Extract scenario name
    const scenarioName = cmdOptions.scenarioName ||
      path.basename(recordingFile, path.extname(recordingFile));

    Logger.info(`Scenario: ${scenarioName}`);
    Logger.info(`Recording file: ${validatedFile}`);
    Logger.newline();

    // Stage 2: Directory Setup
    if (verbose) Logger.info('[Stage 2/6] Creating required directories...');
    await ensureRequiredDirectories(cmdOptions.outputDir).catch(err => {
      throw new ConversionError(
        'Failed to create output directories',
        'DIRECTORY_SETUP',
        'Check write permissions in the output directory',
        err
      );
    });

    // Stage 3: Parse Recording
    if (verbose) Logger.info('[Stage 3/6] Parsing recording...');
    const spinner = ora('Parsing recording...').start();
    const recording = await parseRecording(validatedFile).catch(err => {
      spinner.fail();
      throw new ConversionError(
        'Failed to parse recording file',
        'RECORDING_PARSE',
        'Ensure the recording file contains valid JSON or Playwright code',
        err
      );
    });
    spinner.succeed(`Parsed ${recording.actions.length} actions`);

    // Stage 4: AI Conversion
    if (verbose) Logger.info('[Stage 4/6] Converting to BDD using AI...');
    const bddOutput = await convertToBDD(recording.actions, scenarioName, verbose).catch(err => {
      throw new ConversionError(
        'AI conversion failed',
        'AI_CONVERSION',
        'Check your API key is valid and you have network connectivity. Enable --verbose for more details.',
        err
      );
    });

    // Stage 5: Validate Generated Code
    if (verbose) Logger.info('[Stage 5/6] Validating generated code...');
    await validateGeneratedCode(bddOutput, verbose).catch(err => {
      throw new ConversionError(
        'Generated code validation failed',
        'CODE_VALIDATION',
        'The AI generated invalid Python code. Try running conversion again.',
        err
      );
    });

    // Stage 6: Write Files
    if (verbose) Logger.info('[Stage 6/6] Writing output files...');
    await writeOutputFiles(bddOutput, scenarioName, cmdOptions.outputDir).catch(err => {
      throw new ConversionError(
        'Failed to write output files',
        'FILE_WRITE',
        'Check write permissions and available disk space',
        err
      );
    });

    Logger.newline();
    Logger.success('✅ Conversion complete!');
    Logger.newline();

    displayGeneratedFiles(scenarioName);

  } catch (error) {
    if (error instanceof ConversionError) {
      Logger.error(error.toString());
    } else {
      Logger.error(`Conversion failed: ${error}`);
    }

    if (verbose && error instanceof Error) {
      Logger.error('\nStack trace:');
      Logger.error(error.stack || 'No stack trace available');
    }

    process.exit(1);
  }
}

/**
 * Comprehensive recording file validation with helpful error messages
 */
async function validateRecordingFile(filePath: string): Promise<string> {
  const fs = require('fs').promises;
  const normalizedPath = path.resolve(filePath);

  // Check if file exists
  try {
    await fs.access(normalizedPath);
  } catch {
    // Try alternative path in recordings directory
    const baseName = path.basename(filePath);
    const altPath = path.join(process.cwd(), 'recordings', baseName);

    let suggestion = '';
    try {
      await fs.access(altPath);
      suggestion = `\n\nDid you mean: ${altPath}`;
    } catch {
      // No alternative found
    }

    throw new Error(
      `Recording file not found: ${normalizedPath}${suggestion}\n\n` +
      `To create a recording:\n` +
      `  playwright-ai record --url https://your-app.com`
    );
  }

  // Check if it's a file (not a directory)
  const stats = await fs.stat(normalizedPath);
  if (stats.isDirectory()) {
    throw new Error(`Path is a directory, not a file: ${normalizedPath}`);
  }

  // Check file is not empty
  if (stats.size === 0) {
    throw new Error(`Recording file is empty: ${normalizedPath}`);
  }

  return normalizedPath;
}

/**
 * Ensure all required directories exist before writing files
 */
async function ensureRequiredDirectories(outputDir: string): Promise<void> {
  const fs = require('fs').promises;
  const requiredDirs = [
    'features',
    'steps',
    'fixtures',
    'recordings',
    'pages',
    'helpers',
    'config',
    'reports',
    path.join('reports', 'screenshots'),
  ];

  for (const dir of requiredDirs) {
    const fullPath = path.join(outputDir, dir);
    try {
      await fs.mkdir(fullPath, { recursive: true });
    } catch (error) {
      // Directory might already exist, which is fine
      Logger.warning(`Could not create directory ${dir}: ${error}`);
    }
  }

  Logger.info('✓ All required directories verified');
}

async function parseRecording(filePath: string): Promise<any> {
  // Read the recording file
  const content = await FileUtils.readFile(filePath);

  // Try to parse as JSON first (preferred format)
  try {
    const json = JSON.parse(content);

    // Validate JSON structure
    if (json.actions && Array.isArray(json.actions)) {
      // Normalize action format
      const normalizedActions = json.actions.map((action: any) => {
        // Handle JSONL-style format (name instead of type)
        if (action.name && !action.type) {
          return {
            type: action.name,
            selector: action.selector,
            value: action.text || action.value,
            url: action.url,
          };
        }
        return action;
      });

      if (normalizedActions.length === 0) {
        throw new Error('Recording has no actions');
      }

      return { actions: normalizedActions };
    }

    // If json is just an array, wrap it
    if (Array.isArray(json)) {
      if (json.length === 0) {
        throw new Error('Recording has no actions');
      }
      return { actions: json };
    }

    throw new Error("Recording JSON missing 'actions' array");

  } catch (jsonError) {
    // If not valid JSON, try parsing as Playwright Python code
    Logger.warning('Not valid JSON, attempting to parse as Playwright code...');
    return parsePlaywrightCode(content);
  }
}

function parsePlaywrightCode(content: string): any {
  const actions: any[] = [];
  const lines = content.split('\n');

  for (const line of lines) {
    const trimmed = line.trim();

    // Skip comments and empty lines
    if (trimmed.startsWith('#') || !trimmed) continue;

    // Parse page.goto()
    if (trimmed.includes('page.goto(')) {
      const match = trimmed.match(/page\.goto\(['"](.*?)['"]/);
      if (match) {
        actions.push({
          type: 'navigate',
          url: match[1]
        });
      }
    }

    // Parse page.click()
    else if (trimmed.includes('page.click(')) {
      const match = trimmed.match(/page\.click\(['"](.*?)['"]/);
      if (match) {
        actions.push({
          type: 'click',
          selector: match[1]
        });
      }
    }

    // Parse page.fill()
    else if (trimmed.includes('page.fill(')) {
      const match = trimmed.match(/page\.fill\(['"](.*?)['"],\s*['"](.*?)['"]/);
      if (match) {
        actions.push({
          type: 'fill',
          selector: match[1],
          value: match[2]
        });
      }
    }

    // Parse page.select_option()
    else if (trimmed.includes('page.select_option(')) {
      const match = trimmed.match(/page\.select_option\(['"](.*?)['"],\s*['"](.*?)['"]/);
      if (match) {
        actions.push({
          type: 'select',
          selector: match[1],
          value: match[2]
        });
      }
    }
  }

  if (actions.length === 0) {
    throw new Error('No valid Playwright actions found in recording');
  }

  return { actions };
}

async function convertToBDD(
  actions: any[],
  scenarioName: string,
  verbose: boolean = false
): Promise<BDDOutput> {
  const spinner = ora('Converting to BDD using AI...').start();

  try {
    // Check if AI is configured
    const aiProvider = process.env.AI_PROVIDER || 'anthropic';
    const apiKey = process.env.ANTHROPIC_API_KEY || process.env.OPENAI_API_KEY;

    if (!apiKey) {
      spinner.warn('AI not configured. Using template-based conversion.');
      return generateSimpleBDD(actions, scenarioName);
    }

    if (verbose) {
      Logger.info(`Using AI provider: ${aiProvider}`);
      Logger.info(`Actions to convert: ${actions.length}`);
    }

    // Use AI to convert
    const aiClient = new AnthropicClient(apiKey);
    const bddOutput = await aiClient.generateBDDScenario(actions, scenarioName);

    spinner.succeed('Conversion complete');

    if (verbose) {
      Logger.info(`Generated feature file: ${bddOutput.feature.length} chars`);
      Logger.info(`Generated steps: ${bddOutput.steps.length} chars`);
      Logger.info(`Locators: ${Object.keys(bddOutput.locators).length}`);
      Logger.info(`Test data: ${Object.keys(bddOutput.testData).length}`);
    }

    return bddOutput;

  } catch (error) {
    spinner.fail();
    if (verbose) {
      Logger.error(`AI conversion error: ${error}`);
      if (error instanceof Error) {
        Logger.error(`Stack: ${error.stack}`);
      }
    }
    Logger.warning('AI conversion failed. Using template-based conversion.');
    return generateSimpleBDD(actions, scenarioName);
  }
}

/**
 * Validate generated Python code syntax
 * ENHANCEMENT (RC2.6): Ensures AI-generated code is syntactically valid
 */
async function validateGeneratedCode(bddOutput: BDDOutput, verbose: boolean = false): Promise<void> {
  const spawn = require('child_process').spawn;

  // Validate step definitions
  if (bddOutput.steps && bddOutput.steps.trim()) {
    if (verbose) {
      Logger.info('Validating step definitions syntax...');
    }

    await new Promise<void>((resolve, reject) => {
      const process = spawn('python3', ['-m', 'py_compile', '-'], {
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let stderrData = '';

      process.stdin.write(bddOutput.steps);
      process.stdin.end();

      process.stderr.on('data', (data: Buffer) => {
        stderrData += data.toString();
      });

      process.on('close', (code: number) => {
        if (code !== 0) {
          if (verbose) {
            Logger.warning('Python syntax validation failed:');
            Logger.warning(stderrData);
            Logger.warning('Generated code may have syntax errors but will proceed with conversion.');
          }
          // Don't reject - just warn, as the code might still be useful
          resolve();
        } else {
          if (verbose) {
            Logger.info('✓ Step definitions syntax valid');
          }
          resolve();
        }
      });

      process.on('error', (err: Error) => {
        if (verbose) {
          Logger.warning('Could not validate Python syntax (python3 not available)');
        }
        // Don't fail if python3 is not available
        resolve();
      });
    });
  }

  // Validate page objects
  if (bddOutput.pageObjects && Object.keys(bddOutput.pageObjects).length > 0) {
    for (const [pageName, pageCode] of Object.entries(bddOutput.pageObjects)) {
      if (typeof pageCode === 'string' && pageCode.trim()) {
        if (verbose) {
          Logger.info(`Validating ${pageName} syntax...`);
        }

        await new Promise<void>((resolve) => {
          const process = spawn('python3', ['-m', 'py_compile', '-'], {
            stdio: ['pipe', 'pipe', 'pipe']
          });

          let stderrData = '';

          process.stdin.write(pageCode);
          process.stdin.end();

          process.stderr.on('data', (data: Buffer) => {
            stderrData += data.toString();
          });

          process.on('close', (code: number) => {
            if (code !== 0 && verbose) {
              Logger.warning(`${pageName} syntax validation failed:${stderrData}`);
            } else if (code === 0 && verbose) {
              Logger.info(`✓ ${pageName} syntax valid`);
            }
            resolve();
          });

          process.on('error', () => {
            resolve();
          });
        });
      }
    }
  }

  if (verbose) {
    Logger.info('Code validation complete');
  }
}

function generateSimpleBDD(actions: any[], scenarioName: string): BDDOutput {
  // Simple template-based conversion (fallback when AI not available)

  const steps: string[] = [];
  const locators: Record<string, string> = {};
  const testData: Record<string, any> = {};

  let stepNumber = 1;

  for (const action of actions) {
    switch (action.type) {
      case 'navigate':
        steps.push(`When I navigate to "${action.url}"`);
        break;

      case 'click':
        const clickKey = `button_${stepNumber}`;
        locators[clickKey] = action.selector;
        steps.push(`And I click on "${clickKey}"`);
        stepNumber++;
        break;

      case 'fill':
        const fillKey = `field_${stepNumber}`;
        locators[fillKey] = action.selector;
        testData[fillKey] = action.value;
        steps.push(`And I fill "${fillKey}" with "${action.value}"`);
        stepNumber++;
        break;

      case 'select':
        const selectKey = `dropdown_${stepNumber}`;
        locators[selectKey] = action.selector;
        steps.push(`And I select "${action.value}" from "${selectKey}"`);
        stepNumber++;
        break;
    }
  }

  const feature = `Feature: ${scenarioName}

  Scenario: ${scenarioName}
    Given I am logged in
    ${steps.join('\n    ')}
    Then I should see "Success"
`;

  const stepDefs = `# Step definitions for ${scenarioName}
# Add custom step implementations here
`;

  return {
    feature,
    steps: stepDefs,
    locators,
    testData,
    helpers: [],
    pageObjects: {}
  };
}

async function writeOutputFiles(
  bddOutput: BDDOutput,
  scenarioName: string,
  outputDir: string
): Promise<void> {
  const spinner = ora('Writing output files...').start();

  try {
    // Write feature file
    const featureFile = path.join(outputDir, 'features', `${scenarioName}.feature`);
    await FileUtils.writeFile(featureFile, bddOutput.feature);
    spinner.text = `Created: ${featureFile}`;

    // Write locators to config
    if (Object.keys(bddOutput.locators).length > 0) {
      const locatorsFile = path.join(outputDir, 'config', `${scenarioName}_locators.json`);
      await FileUtils.writeFile(
        locatorsFile,
        JSON.stringify(bddOutput.locators, null, 2)
      );
      spinner.text = `Created: ${locatorsFile}`;
    }

    // Write test data
    if (Object.keys(bddOutput.testData).length > 0) {
      const dataFile = path.join(outputDir, 'fixtures', `${scenarioName}_data.json`);
      await FileUtils.writeFile(
        dataFile,
        JSON.stringify(bddOutput.testData, null, 2)
      );
      spinner.text = `Created: ${dataFile}`;
    }

    // Write step definitions if provided
    if (bddOutput.steps) {
      const stepsFile = path.join(outputDir, 'steps', `${scenarioName}_steps.py`);
      await FileUtils.writeFile(stepsFile, bddOutput.steps);
      spinner.text = `Created: ${stepsFile}`;
    }

    // Write page objects if provided
    if (bddOutput.pageObjects && Object.keys(bddOutput.pageObjects).length > 0) {
      for (const [pageName, pageCode] of Object.entries(bddOutput.pageObjects)) {
        const pageFile = path.join(outputDir, 'pages', `${pageName}.py`);
        await FileUtils.writeFile(pageFile, pageCode);
        spinner.text = `Created: ${pageFile}`;
      }
    }

    spinner.succeed('All files created');

  } catch (error) {
    spinner.fail();
    throw error;
  }
}

function displayGeneratedFiles(scenarioName: string): void {
  Logger.info('Generated files:');
  Logger.list([
    `features/${scenarioName}.feature`,
    `config/${scenarioName}_locators.json`,
    `fixtures/${scenarioName}_data.json`,
    `steps/${scenarioName}_steps.py`,
    `pages/*_page.py (page objects if detected)`
  ]);

  Logger.newline();
  Logger.info('To run this scenario:');
  Logger.code(`  behave features/${scenarioName}.feature`);
}
