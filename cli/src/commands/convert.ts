import { Command } from 'commander';
import ora from 'ora';
import path from 'path';
import { ConvertOptions, BDDOutput } from '../types';
import { Logger } from '../utils/logger';
import { FileUtils } from '../utils/file-utils';
import { AnthropicClient } from '../ai/anthropic-client';
import * as dotenv from 'dotenv';

dotenv.config();

export function createConvertCommand(): Command {
  return new Command('convert')
    .description('Convert Playwright recording to BDD scenario')
    .argument('<recording-file>', 'Path to recording file')
    .option('-s, --scenario-name <name>', 'Override scenario name')
    .option('-o, --output-dir <dir>', 'Output directory', '.')
    .action(async (recordingFile, options) => {
      await convertRecording(recordingFile, options);
    });
}

async function convertRecording(
  recordingFile: string,
  cmdOptions: any
): Promise<void> {
  try {
    Logger.title('🔄 Converting Recording to BDD');

    // Validate file exists
    const exists = await FileUtils.fileExists(recordingFile);
    if (!exists) {
      throw new Error(`Recording file not found: ${recordingFile}`);
    }

    // Extract scenario name
    const scenarioName = cmdOptions.scenarioName ||
      path.basename(recordingFile, path.extname(recordingFile));

    Logger.info(`Scenario: ${scenarioName}`);
    Logger.info(`Recording file: ${recordingFile}`);
    Logger.newline();

    // Parse recording
    const spinner = ora('Parsing recording...').start();
    const recording = await parseRecording(recordingFile);
    spinner.succeed(`Parsed ${recording.actions.length} actions`);

    // Convert to BDD using AI
    const bddOutput = await convertToBDD(recording.actions, scenarioName);

    // Write output files
    await writeOutputFiles(bddOutput, scenarioName, cmdOptions.outputDir);

    Logger.newline();
    Logger.success('✅ Conversion complete!');
    Logger.newline();

    displayGeneratedFiles(scenarioName);

  } catch (error) {
    Logger.error(`Conversion failed: ${error}`);
    process.exit(1);
  }
}

async function parseRecording(filePath: string): Promise<any> {
  // Read the recording file
  const content = await FileUtils.readFile(filePath);

  // Parse Playwright Python code to extract actions
  // This is a simplified parser - in production, you'd use proper AST parsing

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

    // Add more parsers for other Playwright actions as needed
  }

  return { actions };
}

async function convertToBDD(
  actions: any[],
  scenarioName: string
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

    // Use AI to convert
    const aiClient = new AnthropicClient(apiKey);
    const bddOutput = await aiClient.generateBDDScenario(actions, scenarioName);

    spinner.succeed('Conversion complete');

    return bddOutput;

  } catch (error) {
    spinner.fail();
    Logger.warning('AI conversion failed. Using template-based conversion.');
    return generateSimpleBDD(actions, scenarioName);
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
    helpers: []
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
    `steps/${scenarioName}_steps.py (if needed)`
  ]);

  Logger.newline();
  Logger.info('To run this scenario:');
  Logger.code(`  behave features/${scenarioName}.feature`);
}
