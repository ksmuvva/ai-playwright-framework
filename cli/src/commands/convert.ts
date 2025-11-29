import { Command } from 'commander';
import ora from 'ora';
import path from 'path';
import { ConvertOptions, BDDOutput } from '../types';
import { Logger } from '../utils/logger';
import { FileUtils } from '../utils/file-utils';
import { AnthropicClient } from '../ai/anthropic-client';
import { StepRegistry } from '../utils/step-registry';
import { PageObjectRegistry } from '../utils/page-object-registry';
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
    .option('-f, --scenario-folder <folder>', 'Organize scenario into a folder (e.g., authentication, checkout)')
    .option('--no-registry', 'Disable step/page registry (create standalone files)')
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
    await ensureRequiredDirectories(cmdOptions.outputDir, cmdOptions.scenarioFolder).catch(err => {
      throw new ConversionError(
        'Failed to create output directories',
        'DIRECTORY_SETUP',
        'Check write permissions in the output directory',
        err
      );
    });

    // Stage 2.5: Initialize Registries (P1 Feature)
    let stepRegistry: StepRegistry | null = null;
    let pageRegistry: PageObjectRegistry | null = null;

    if (cmdOptions.registry !== false) {  // Registry enabled by default
      if (verbose) Logger.info('[Stage 2.5/6] Initializing framework registries...');
      try {
        stepRegistry = new StepRegistry(cmdOptions.outputDir);
        await stepRegistry.initialize();

        pageRegistry = new PageObjectRegistry(cmdOptions.outputDir);
        await pageRegistry.initialize();

        if (verbose) {
          Logger.info('Registry statistics:');
          const stepStats = stepRegistry.getReuseStats();
          Logger.info(`  - Existing steps: ${stepStats.totalSteps}`);
          Logger.info(`  - Existing pages: ${pageRegistry.getAllPages().length}`);
        }
      } catch (error) {
        Logger.warning('Registry initialization failed, continuing without registry...');
        stepRegistry = null;
        pageRegistry = null;
      }
    } else {
      Logger.info('Registry disabled - creating standalone files');
    }

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

    // Stage 6: Write Files with Registry Integration
    if (verbose) Logger.info('[Stage 6/6] Writing output files...');
    await writeOutputFiles(
      bddOutput,
      scenarioName,
      cmdOptions.outputDir,
      stepRegistry,
      pageRegistry,
      cmdOptions.scenarioFolder
    ).catch(err => {
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
 * FIX P2-2: Support scenario folders for better organization
 */
async function ensureRequiredDirectories(outputDir: string, scenarioFolder?: string): Promise<void> {
  const fs = require('fs').promises;
  const requiredDirs = [
    'features',
    path.join('features', 'steps'),  // FIX: Behave expects steps inside features/
    'fixtures',
    'recordings',
    'pages',
    'helpers',
    'config',
    'reports',
    path.join('reports', 'screenshots'),
  ];

  // Add scenario folder if specified (P2-2)
  if (scenarioFolder) {
    requiredDirs.push(path.join('scenarios', scenarioFolder));
    Logger.info(`📁 Using scenario folder: ${scenarioFolder}`);
  }

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

/**
 * Detect recording format based on content and file extension
 * ROOT CAUSE FIX (RC4): Proper format detection with helpful error messages
 */
function detectRecordingFormat(content: string, filePath: string): 'python' | 'json' | 'typescript' | 'unknown' {
  const ext = path.extname(filePath).toLowerCase();

  // Check by extension first (most reliable)
  if (ext === '.py') return 'python';
  if (ext === '.json') return 'json';
  if (ext === '.ts' || ext === '.js') return 'typescript';

  // Fallback: detect by content
  const trimmed = content.trim();

  // JSON detection
  if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
    try {
      JSON.parse(trimmed);
      return 'json';
    } catch {
      // Not valid JSON
    }
  }

  // Python detection
  if (
    content.includes('from playwright') ||
    content.includes('import playwright') ||
    content.includes('def run(playwright') ||
    content.includes('page.get_by_')
  ) {
    return 'python';
  }

  // TypeScript/JavaScript detection
  if (
    content.includes("import { ") ||
    content.includes("from 'playwright") ||
    content.includes("from '@playwright")
  ) {
    return 'typescript';
  }

  return 'unknown';
}

async function parseRecording(filePath: string): Promise<any> {
  // Read the recording file
  const content = await FileUtils.readFile(filePath);

  // UPLIFT: Use Universal Parser for multi-format support
  // Supports: Python, TypeScript/JavaScript, HAR, JSON
  const { parseRecording: universalParse } = require('../parsers/universal-parser');

  const result = universalParse(content);

  // Check for parsing errors
  if (result.parseErrors.length > 0) {
    const errorDetails = result.parseErrors
      .slice(0, 3)
      .map(e => `  - ${e.reason}${e.lineNumber ? ` (line ${e.lineNumber})` : ''}`)
      .join('\n');

    throw new ConversionError(
      `Failed to parse recording (format: ${result.format})`,
      'RECORDING_PARSE',
      `Parsing errors:\n${errorDetails}\n\n` +
      `File: ${filePath}\n` +
      'Supported formats: Python (.py), TypeScript/JavaScript (.ts/.js), HAR (.har/.json)'
    );
  }

  // Show warnings if any
  if (result.warnings.length > 0) {
    result.warnings.forEach(warning => {
      Logger.warning(`⚠️  ${warning}`);
    });
  }

  // Return parsed actions in legacy format for compatibility
  return {
    actions: result.actions,
    metadata: result.metadata
  };
}

/**
 * Parse Python Playwright recording
 * ROOT CAUSE FIX (RC1, RC2): Comprehensive Python parser for modern Playwright API
 */
function parsePythonRecording(content: string): any {
  // Import and use the comprehensive Python parser
  const { parsePythonScript, convertToLegacyFormat } = require('../parsers/python-parser');

  Logger.info('Using comprehensive Python parser for modern Playwright API...');

  const parsed = parsePythonScript(content);

  if (parsed.actions.length === 0) {
    throw new Error('No actions found in Python recording');
  }

  if (parsed.parseErrors.length > 0) {
    Logger.warning(`⚠️  ${parsed.parseErrors.length} lines could not be parsed`);
  }

  // Return in format expected by downstream code
  return {
    actions: parsed.actions,  // Use rich parsed actions
    metadata: parsed.metadata,
    parseErrors: parsed.parseErrors
  };
}

/**
 * Parse JSON recording
 */
function parseJsonRecording(content: string): any {
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

  } catch (error) {
    throw new ConversionError(
      'Invalid JSON format',
      'JSON_PARSE',
      `Could not parse JSON recording: ${error}\n\n` +
      'Expected format:\n' +
      '{\n' +
      '  "actions": [\n' +
      '    { "type": "navigate", "url": "..." },\n' +
      '    { "type": "click", "selector": "..." }\n' +
      '  ]\n' +
      '}',
      error as Error
    );
  }
}

// OLD BASIC PARSER - REMOVED
// Now using comprehensive Python parser from ../parsers/python-parser.ts

async function convertToBDD(
  actions: any[],
  scenarioName: string,
  verbose: boolean = false
): Promise<BDDOutput> {
  const spinner = ora('Converting to BDD using AI...').start();

  try {
    // FAILURE-003 FIX: Better error handling for missing API keys
    const aiProvider = process.env.AI_PROVIDER || 'anthropic';
    const apiKey = process.env.ANTHROPIC_API_KEY || process.env.OPENAI_API_KEY;

    if (!apiKey) {
      spinner.fail('AI API key not configured');
      Logger.newline();
      Logger.error('❌ AI API KEY NOT CONFIGURED');
      Logger.newline();
      Logger.error('The AI-powered BDD conversion requires an API key.');
      Logger.newline();
      Logger.info('How to fix:');
      Logger.info('1. Get an API key from: https://console.anthropic.com/');
      Logger.info('2. Set it in your .env file:');
      Logger.code('   ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key');
      Logger.info('3. Or set as environment variable:');
      Logger.code('   export ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key');
      Logger.newline();
      Logger.info('To use template-based conversion instead (limited functionality):');
      Logger.code('   # Set environment variable to skip AI');
      Logger.code('   export SKIP_AI=true');
      Logger.newline();

      // Check if user wants to skip AI
      if (process.env.SKIP_AI === 'true') {
        Logger.warning('Using template-based conversion (limited functionality)...');
        return generateSimpleBDD(actions, scenarioName);
      }

      throw new ConversionError(
        'API key required for AI conversion',
        'CONFIGURATION',
        'Set ANTHROPIC_API_KEY environment variable or use SKIP_AI=true for template-based conversion'
      );
    }

    if (verbose) {
      Logger.info(`Using AI provider: ${aiProvider}`);
      Logger.info(`Actions to convert: ${actions.length}`);
    }

    // Use AI to convert with STRUCTURED OUTPUT (ROOT CAUSE FIX RC7)
    const aiClient = new AnthropicClient(apiKey);

    // Use the new structured output method for reliable parsing
    Logger.info('🎯 Using structured output for reliable BDD generation...');
    const bddOutput = await aiClient.generateBDDScenarioStructured(actions, scenarioName);

    spinner.succeed('Conversion complete with structured output');

    if (verbose) {
      Logger.info(`Generated feature file: ${bddOutput.feature.length} chars`);
      Logger.info(`Generated steps: ${bddOutput.steps.length} chars`);
      Logger.info(`Locators: ${Object.keys(bddOutput.locators).length}`);
      Logger.info(`Test data: ${Object.keys(bddOutput.testData).length}`);
      Logger.info(`Page objects: ${Object.keys(bddOutput.pageObjects).length}`);
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

    // Try fallback to old method
    try {
      Logger.warning('Structured output failed. Trying legacy method...');
      const aiClient = new AnthropicClient(process.env.ANTHROPIC_API_KEY);
      return await aiClient.generateBDDScenario(actions, scenarioName);
    } catch (fallbackError) {
      Logger.warning('AI conversion failed. Using template-based conversion.');
      return generateSimpleBDD(actions, scenarioName);
    }
  }
}

/**
 * Validate generated Python code syntax
 * ENHANCEMENT (RC2.6): Ensures AI-generated code is syntactically valid
 * STRICT VALIDATION (FAILURE-006): Multiple validation strategies, fails on errors
 */
async function validateGeneratedCode(bddOutput: BDDOutput, verbose: boolean = false): Promise<void> {
  const spawn = require('child_process').spawn;
  const validationErrors: string[] = [];

  // Validate step definitions
  if (bddOutput.steps && bddOutput.steps.trim()) {
    if (verbose) {
      Logger.info('Validating step definitions syntax...');
    }

    // Strategy 1: Python compilation check (if python3 available)
    const pythonAvailable = await new Promise<boolean>((resolve) => {
      const testProcess = spawn('python3', ['--version'], { stdio: 'ignore' });
      testProcess.on('close', (code: number) => resolve(code === 0));
      testProcess.on('error', () => resolve(false));
    });

    if (pythonAvailable) {
      await new Promise<void>((resolve) => {
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
            validationErrors.push(`Python compilation failed: ${stderrData}`);
          } else if (verbose) {
            Logger.info('✓ Step definitions syntax valid');
          }
          resolve();
        });

        process.on('error', () => resolve());
      });
    } else if (verbose) {
      Logger.warning('Python3 not available for syntax validation, using regex validation only');
    }

    // Strategy 2: Basic regex patterns for common syntax errors
    const regexErrors = validateWithRegex(bddOutput.steps);
    if (regexErrors.length > 0) {
      validationErrors.push(...regexErrors);
    }
  }

  // Validate page objects (if python3 is available)
  if (bddOutput.pageObjects && Object.keys(bddOutput.pageObjects).length > 0) {
    const pythonAvailable = await new Promise<boolean>((resolve) => {
      const testProcess = spawn('python3', ['--version'], { stdio: 'ignore' });
      testProcess.on('close', (code: number) => resolve(code === 0));
      testProcess.on('error', () => resolve(false));
    });

    if (pythonAvailable) {
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
              if (code !== 0) {
                validationErrors.push(`${pageName} compilation failed: ${stderrData}`);
              } else if (verbose) {
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
  }

  // If ANY validation found errors, FAIL
  if (validationErrors.length > 0) {
    Logger.error('❌ GENERATED CODE HAS SYNTAX ERRORS:');
    validationErrors.forEach((err, i) => {
      Logger.error(`   ${i + 1}. ${err}`);
    });
    Logger.newline();
    Logger.info('This is an AI generation issue. Please try running the conversion again.');

    throw new ConversionError(
      'Generated code contains syntax errors',
      'CODE_VALIDATION',
      'The AI generated invalid Python code. Try running the conversion again or use --verbose for more details.'
    );
  }

  if (verbose) {
    Logger.success('✓ Code syntax validation passed');
  }
}

/**
 * Validate Python code with regex patterns for common syntax errors
 */
function validateWithRegex(code: string): string[] {
  const errors: string[] = [];
  const lines = code.split('\n');

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const lineNum = i + 1;

    // Check for common Python syntax errors

    // 1. Missing colon after def/if/for/while/class
    if (/^\s*(def|if|elif|else|for|while|with|class|try|except|finally)\s+.*[^:]$/.test(line) &&
        !line.trim().endsWith('\\') &&
        line.trim().length > 0) {
      // Make sure it's not a continuation line
      const stripped = line.trim();
      if (stripped.startsWith('def ') || stripped.startsWith('class ') ||
          stripped.startsWith('if ') || stripped.startsWith('for ') ||
          stripped.startsWith('while ') || stripped.startsWith('with ')) {
        errors.push(`Line ${lineNum}: Missing colon after statement`);
      }
    }

    // 2. Unmatched quotes
    const singleQuotes = (line.match(/'/g) || []).length;
    const doubleQuotes = (line.match(/"/g) || []).length;
    if (singleQuotes % 2 !== 0 || doubleQuotes % 2 !== 0) {
      // Could be multi-line string, but flag as potential error
      if (!line.includes('"""') && !line.includes("'''")) {
        errors.push(`Line ${lineNum}: Unmatched quotes detected`);
      }
    }

    // 3. Invalid indentation (mixing tabs and spaces - very basic check)
    if (line.startsWith('\t') && line.includes('    ')) {
      errors.push(`Line ${lineNum}: Mixed tabs and spaces in indentation`);
    }

    // 4. Missing parentheses in function calls
    if (/\b(print|len|str|int|float|list|dict|set|tuple)\s+[^(]/.test(line)) {
      errors.push(`Line ${lineNum}: Function call missing parentheses`);
    }
  }

  return errors;
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
  outputDir: string,
  stepRegistry: StepRegistry | null = null,
  pageRegistry: PageObjectRegistry | null = null,
  scenarioFolder?: string
): Promise<void> {
  const spinner = ora('Writing output files...').start();

  try {
    // Determine feature file location (P2-2: Scenario folder support)
    let featureFile: string;
    if (scenarioFolder) {
      // Use scenarios/{folder}/*.feature structure
      featureFile = path.join(outputDir, 'scenarios', scenarioFolder, `${scenarioName}.feature`);
      spinner.text = `Using scenario folder: ${scenarioFolder}`;
    } else {
      // Use standard features/*.feature structure
      featureFile = path.join(outputDir, 'features', `${scenarioName}.feature`);
    }

    // Write feature file
    await FileUtils.writeFile(featureFile, bddOutput.feature);
    spinner.text = `Created: ${featureFile}`;

    // FIX P0-2: Ensure environment.py exists in features/ directory
    const envFile = path.join(outputDir, 'features', 'environment.py');
    try {
      await FileUtils.readFile(envFile);
      // File exists, don't overwrite
    } catch {
      // File doesn't exist, copy from template
      const templatePath = FileUtils.getTemplatePath('python');
      const envTemplatePath = path.join(templatePath, 'features', 'environment.py');
      try {
        await FileUtils.copyFile(envTemplatePath, envFile);
        spinner.text = `Created: ${envFile}`;
      } catch (error) {
        Logger.warning('Could not copy environment.py template. Please create it manually.');
      }
    }

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

    // Write step definitions with framework injection (P1 Feature)
    if (bddOutput.steps) {
      const stepsFile = path.join(outputDir, 'features', 'steps', `${scenarioName}_steps.py`);

      // P1: Use registry for step reuse analysis
      if (stepRegistry) {
        Logger.info('🔍 Analyzing step reusability...');

        // Parse step patterns from generated steps
        const stepPatterns = extractStepPatterns(bddOutput.steps);

        if (stepPatterns.length > 0) {
          const analysis = stepRegistry.analyzeSteps(stepPatterns);

          Logger.info(
            `📊 Step Analysis:\n` +
            `  Total steps: ${analysis.totalSteps}\n` +
            `  Reusable: ${analysis.reusableSteps.length} (${Math.round(analysis.reusableSteps.length / analysis.totalSteps * 100)}%)\n` +
            `  New: ${analysis.newStepsNeeded.length}`
          );

          if (analysis.reusableSteps.length > 0) {
            Logger.info(`♻️  Reusing ${analysis.reusableSteps.length} existing steps:`);
            analysis.reusableSteps.slice(0, 3).forEach(step => {
              Logger.info(`    - "${step}"`);
            });
            if (analysis.reusableSteps.length > 3) {
              Logger.info(`    ... and ${analysis.reusableSteps.length - 3} more`);
            }
          }

          // Only write new steps (P1-2: Step merging)
          if (analysis.newStepsNeeded.length > 0) {
            const newStepsCode = filterNewSteps(bddOutput.steps, analysis.newStepsNeeded);
            await FileUtils.writeFile(stepsFile, newStepsCode);
            spinner.text = `Created: ${stepsFile} (${analysis.newStepsNeeded.length} new steps)`;
          } else {
            Logger.info('✨ All steps already exist - no new steps needed!');
          }
        } else {
          // No patterns found, write all steps
          await FileUtils.writeFile(stepsFile, bddOutput.steps);
          spinner.text = `Created: ${stepsFile}`;
        }
      } else {
        // Registry disabled, write all steps (standalone mode)
        await FileUtils.writeFile(stepsFile, bddOutput.steps);
        spinner.text = `Created: ${stepsFile}`;
      }

      // FIX P0-3: Ensure __init__.py exists in features/steps/
      const stepsInitFile = path.join(outputDir, 'features', 'steps', '__init__.py');
      try {
        await FileUtils.readFile(stepsInitFile);
        // File exists, don't overwrite
      } catch {
        // File doesn't exist, create it
        await FileUtils.writeFile(stepsInitFile, '# Step definitions package\n');
        spinner.text = `Created: ${stepsInitFile}`;
      }
    }

    // Write page objects with framework injection (P2 Feature)
    if (bddOutput.pageObjects && Object.keys(bddOutput.pageObjects).length > 0) {
      // FIX P0-3: Ensure __init__.py exists in pages/
      const pagesInitFile = path.join(outputDir, 'pages', '__init__.py');
      try {
        await FileUtils.readFile(pagesInitFile);
        // File exists, don't overwrite
      } catch {
        // File doesn't exist, create it
        await FileUtils.writeFile(pagesInitFile, '# Page objects package\n');
        spinner.text = `Created: ${pagesInitFile}`;
      }

      for (const [pageName, pageCode] of Object.entries(bddOutput.pageObjects)) {
        const pageFile = path.join(outputDir, 'pages', `${pageName}.py`);

        // P2: Use registry for page merging
        if (pageRegistry && typeof pageCode === 'string') {
          // Extract class name from file name (e.g., 'login_page' -> 'LoginPage')
          const className = pageName
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join('');

          if (pageRegistry.pageExists(className)) {
            Logger.info(`🔄 Page ${className} exists - attempting merge...`);

            const mergeResult = await pageRegistry.mergePage(className, pageCode);

            if (mergeResult.shouldCreate) {
              // Create new page
              await FileUtils.writeFile(pageFile, pageCode);
              spinner.text = `Created: ${pageFile}`;
            } else if (mergeResult.mergedCode) {
              // Write merged page
              await FileUtils.writeFile(pageFile, mergeResult.mergedCode);
              spinner.text = `Updated: ${pageFile} (merged)`;
            } else {
              // No changes needed
              Logger.info(`  ✓ ${className} unchanged - all elements already exist`);
            }
          } else {
            // New page
            await FileUtils.writeFile(pageFile, pageCode);
            spinner.text = `Created: ${pageFile}`;
          }
        } else {
          // Registry disabled or invalid code, write directly
          await FileUtils.writeFile(pageFile, pageCode);
          spinner.text = `Created: ${pageFile}`;
        }
      }
    }

    spinner.succeed('All files created');

  } catch (error) {
    spinner.fail();
    throw error;
  }
}

/**
 * Extract step patterns from generated step code
 * Helper for step registry analysis
 */
function extractStepPatterns(stepsCode: string): string[] {
  const patterns: string[] = [];
  const lines = stepsCode.split('\n');

  for (const line of lines) {
    const match = line.trim().match(/^@(?:given|when|then)\(['"](.+?)['"]\)/);
    if (match) {
      patterns.push(match[1]);
    }
  }

  return patterns;
}

/**
 * Filter steps code to only include new steps
 * Helper for step merging
 */
function filterNewSteps(stepsCode: string, newStepPatterns: string[]): string {
  const lines = stepsCode.split('\n');
  const filteredLines: string[] = [];
  let inNewStep = false;
  let currentStepIndent = 0;

  // Keep imports and module-level code
  let i = 0;
  while (i < lines.length && !lines[i].trim().startsWith('@')) {
    filteredLines.push(lines[i]);
    i++;
  }

  // Process step definitions
  for (; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Check if this is a decorator for a new step
    const decoratorMatch = trimmed.match(/^@(?:given|when|then)\(['"](.+?)['"]\)/);
    if (decoratorMatch) {
      const pattern = decoratorMatch[1];
      inNewStep = newStepPatterns.includes(pattern);

      if (inNewStep) {
        filteredLines.push(line);
        currentStepIndent = line.search(/\S/);
      }
      continue;
    }

    // If we're in a new step, keep the line
    if (inNewStep) {
      const currentIndent = line.search(/\S/);

      // End of function (dedent)
      if (trimmed && currentIndent > 0 && currentIndent <= currentStepIndent) {
        inNewStep = false;
      } else {
        filteredLines.push(line);
      }
    }
  }

  return filteredLines.join('\n');
}

function displayGeneratedFiles(scenarioName: string): void {
  Logger.info('Generated files:');
  Logger.list([
    `features/${scenarioName}.feature`,
    `features/steps/${scenarioName}_steps.py`,  // FIX P0-1: Updated path
    `features/environment.py (if not exists)`,
    `config/${scenarioName}_locators.json`,
    `fixtures/${scenarioName}_data.json`,
    `pages/*_page.py (page objects if detected)`
  ]);

  Logger.newline();
  Logger.info('To run this scenario:');
  Logger.code(`  behave features/${scenarioName}.feature`);
  Logger.newline();
  Logger.info('💡 Tip: Make sure to run this from your project root directory');
}
