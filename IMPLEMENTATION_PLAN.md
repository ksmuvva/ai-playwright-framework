# Implementation Plan - AI Playwright Framework

## 🎯 Project Goal

Build a production-ready CLI tool that generates AI-powered test automation frameworks for testers with no coding experience.

---

## 📅 Timeline & Phases

### **Phase 1: Foundation (Days 1-3)**
Setup project structure and basic CLI framework

### **Phase 2: Template System (Days 4-6)**
Create Python framework templates

### **Phase 3: AI Integration (Days 7-10)**
Implement AI-powered features

### **Phase 4: CLI Commands (Days 11-13)**
Complete all CLI commands

### **Phase 5: Testing & Polish (Days 14-15)**
End-to-end testing and documentation

---

## 📋 Detailed Implementation Steps

### Phase 1: Foundation (Days 1-3)

#### Day 1: CLI Project Setup

**Tasks:**
1. ✅ Initialize TypeScript project
   ```bash
   mkdir cli
   cd cli
   npm init -y
   npm install typescript @types/node --save-dev
   npx tsc --init
   ```

2. ✅ Install dependencies
   ```bash
   npm install \
     commander \
     inquirer \
     chalk \
     ora \
     fs-extra \
     ejs \
     dotenv
   ```

3. ✅ Setup project structure
   ```
   cli/
   ├── src/
   │   ├── index.ts
   │   ├── commands/
   │   ├── generators/
   │   ├── ai/
   │   ├── parsers/
   │   ├── templates/
   │   └── utils/
   ├── package.json
   ├── tsconfig.json
   └── README.md
   ```

4. ✅ Create basic CLI entry point
   ```typescript
   // src/index.ts
   #!/usr/bin/env node
   import { Command } from 'commander';

   const program = new Command();

   program
     .name('playwright-ai')
     .description('AI-powered Playwright framework generator')
     .version('1.0.0');

   program.parse();
   ```

5. ✅ Setup build and publish scripts
   ```json
   {
     "bin": {
       "playwright-ai": "./dist/index.js"
     },
     "scripts": {
       "build": "tsc",
       "dev": "ts-node src/index.ts",
       "test": "jest"
     }
   }
   ```

**Deliverables:**
- ✅ Working CLI skeleton
- ✅ TypeScript compilation
- ✅ Basic command structure

---

#### Day 2: Template Engine & File Structure

**Tasks:**
1. ✅ Create template directory structure
   ```
   templates/
   ├── python/
   │   ├── features/
   │   │   └── example.feature.ejs
   │   ├── steps/
   │   │   ├── common_steps.py.ejs
   │   │   └── environment.py.ejs
   │   ├── helpers/
   │   │   ├── auth_helper.py
   │   │   ├── healing_locator.py
   │   │   ├── wait_manager.py
   │   │   ├── data_generator.py
   │   │   └── screenshot_manager.py
   │   ├── pages/
   │   │   └── base_page.py
   │   ├── config/
   │   │   └── config.py.ejs
   │   ├── .env.example
   │   ├── requirements.txt
   │   ├── pytest.ini
   │   ├── behave.ini
   │   └── README.md.ejs
   ```

2. ✅ Build template engine
   ```typescript
   // src/generators/template-engine.ts
   import ejs from 'ejs';
   import fs from 'fs-extra';
   import path from 'path';

   export class TemplateEngine {
     async render(templatePath: string, data: any): Promise<string> {
       const template = await fs.readFile(templatePath, 'utf-8');
       return ejs.render(template, data);
     }

     async renderToFile(
       templatePath: string,
       outputPath: string,
       data: any
     ): Promise<void> {
       const content = await this.render(templatePath, data);
       await fs.ensureDir(path.dirname(outputPath));
       await fs.writeFile(outputPath, content);
     }
   }
   ```

3. ✅ Create file copier utility
   ```typescript
   // src/utils/file-utils.ts
   export class FileUtils {
     static async copyDirectory(src: string, dest: string) {
       await fs.copy(src, dest);
     }

     static async createDirectory(path: string) {
       await fs.ensureDir(path);
     }
   }
   ```

**Deliverables:**
- ✅ Template engine working
- ✅ All Python framework templates
- ✅ File utility functions

---

#### Day 3: Init Command Implementation

**Tasks:**
1. ✅ Create init command
   ```typescript
   // src/commands/init.ts
   import { Command } from 'commander';
   import inquirer from 'inquirer';
   import chalk from 'chalk';
   import ora from 'ora';

   interface InitOptions {
     language: 'python' | 'typescript';
     projectName: string;
     bdd: boolean;
     powerApps: boolean;
     aiProvider: 'anthropic' | 'openai';
     directory?: string;
   }

   export function createInitCommand(): Command {
     return new Command('init')
       .description('Initialize a new test framework')
       .option('-l, --language <type>', 'Framework language')
       .option('-n, --project-name <name>', 'Project name')
       .option('--bdd', 'Enable BDD framework')
       .option('--power-apps', 'Add Power Apps helpers')
       .option('--ai-provider <provider>', 'AI provider')
       .action(async (options) => {
         await initializeFramework(options);
       });
   }

   async function initializeFramework(options: InitOptions) {
     const spinner = ora('Initializing framework...').start();

     // 1. Prompt for missing options
     const answers = await promptForOptions(options);

     // 2. Create project directory
     const projectDir = await createProjectDirectory(answers.projectName);

     // 3. Generate framework files
     await generateFramework(projectDir, answers);

     // 4. Install dependencies
     await installDependencies(projectDir, answers.language);

     spinner.succeed(chalk.green('Framework initialized successfully!'));

     // 5. Display next steps
     displayNextSteps(answers.projectName);
   }
   ```

2. ✅ Implement framework generator
   ```typescript
   // src/generators/python-generator.ts
   export class PythonGenerator {
     async generate(projectDir: string, options: InitOptions) {
       const templateEngine = new TemplateEngine();

       // Copy helper files (no templating needed)
       await this.copyHelpers(projectDir);

       // Generate config files (with templating)
       await this.generateConfig(projectDir, options);

       // Generate requirements.txt
       await this.generateRequirements(projectDir, options);

       // Generate example feature
       await this.generateExampleFeature(projectDir);

       // Generate README
       await this.generateReadme(projectDir, options);

       // Create directory structure
       await this.createDirectories(projectDir);
     }

     private async copyHelpers(projectDir: string) {
       const helpers = [
         'auth_helper.py',
         'healing_locator.py',
         'wait_manager.py',
         'data_generator.py',
         'screenshot_manager.py'
       ];

       for (const helper of helpers) {
         await fs.copy(
           path.join(TEMPLATES_DIR, 'python', 'helpers', helper),
           path.join(projectDir, 'helpers', helper)
         );
       }
     }
   }
   ```

3. ✅ Add dependency installation
   ```typescript
   async function installDependencies(
     projectDir: string,
     language: string
   ) {
     if (language === 'python') {
       execSync('pip install -r requirements.txt', {
         cwd: projectDir,
         stdio: 'inherit'
       });

       execSync('playwright install chromium', {
         cwd: projectDir,
         stdio: 'inherit'
       });
     }
   }
   ```

**Deliverables:**
- ✅ Working `playwright-ai init` command
- ✅ Complete Python framework generation
- ✅ Automatic dependency installation

---

### Phase 2: Template System (Days 4-6)

#### Day 4: Python Helper Functions

**Tasks:**
1. ✅ Implement `auth_helper.py`
2. ✅ Implement `screenshot_manager.py`
3. ✅ Implement `wait_manager.py`
4. ✅ Create `base_page.py`
5. ✅ Create `config.py` template
6. ✅ Create `environment.py` (Behave hooks)

**Details in ARCHITECTURE.md - Use code from there**

**Deliverables:**
- ✅ All helper functions complete
- ✅ Working BDD integration
- ✅ Configuration management

---

#### Day 5: AI-Powered Helpers (Part 1)

**Tasks:**
1. ✅ Setup AI client abstraction
   ```typescript
   // src/ai/ai-client.ts
   export interface AIClient {
     generateBDDScenario(recording: any): Promise<BDDOutput>;
     healLocator(context: any): Promise<string>;
     generateTestData(schema: any): Promise<any>;
   }
   ```

2. ✅ Implement Anthropic client
   ```typescript
   // src/ai/anthropic.ts
   import Anthropic from '@anthropic-ai/sdk';

   export class AnthropicClient implements AIClient {
     private client: Anthropic;

     constructor(apiKey: string) {
       this.client = new Anthropic({ apiKey });
     }

     async generateBDDScenario(recording: any): Promise<BDDOutput> {
       const response = await this.client.messages.create({
         model: 'claude-sonnet-4-5-20250929',
         max_tokens: 4000,
         messages: [{
           role: 'user',
           content: this.buildConversionPrompt(recording)
         }]
       });

       return JSON.parse(response.content[0].text);
     }
   }
   ```

3. ✅ Create system prompts
   ```typescript
   // src/ai/prompts.ts
   export const PROMPTS = {
     BDD_CONVERSION: `You are an expert test automation engineer...`,
     LOCATOR_HEALING: `You are an expert in DOM analysis...`,
     DATA_GENERATION: `Generate realistic test data...`
   };
   ```

**Deliverables:**
- ✅ AI client abstraction
- ✅ Anthropic integration
- ✅ System prompts defined

---

#### Day 6: AI-Powered Helpers (Part 2)

**Tasks:**
1. ✅ Implement `healing_locator.py` (full version)
2. ✅ Implement `data_generator.py` (full version)
3. ✅ Add AI client to Python templates
   ```python
   # templates/python/ai/ai_client.py
   from anthropic import Anthropic
   import os

   class AIClient:
       def __init__(self):
           self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
   ```

**Deliverables:**
- ✅ Self-healing locators working
- ✅ AI test data generation
- ✅ Python AI client integration

---

### Phase 3: AI Integration (Days 7-10)

#### Day 7: Recording Parser

**Tasks:**
1. ✅ Create recording parser
   ```typescript
   // src/parsers/recording-parser.ts
   export interface PlaywrightAction {
     type: string;
     selector?: string;
     value?: string;
     url?: string;
   }

   export class RecordingParser {
     parse(recordingFile: string): PlaywrightAction[] {
       const content = fs.readFileSync(recordingFile, 'utf-8');
       // Parse Playwright recording JSON/code
       return this.extractActions(content);
     }

     extractActions(content: string): PlaywrightAction[] {
       // Extract actions from recording
     }
   }
   ```

2. ✅ Create scenario analyzer
   ```typescript
   // src/parsers/scenario-analyzer.ts
   export class ScenarioAnalyzer {
     analyzeActions(actions: PlaywrightAction[]) {
       // Group related actions
       // Identify patterns
       // Extract test data
     }
   }
   ```

**Deliverables:**
- ✅ Recording parser working
- ✅ Action extraction
- ✅ Pattern identification

---

#### Day 8: BDD Converter

**Tasks:**
1. ✅ Implement conversion logic
   ```typescript
   // src/ai/bdd-converter.ts
   export class BDDConverter {
     async convert(
       recording: PlaywrightAction[],
       scenarioName: string
     ): Promise<BDDOutput> {
       // 1. Analyze actions
       const analysis = this.analyzer.analyze(recording);

       // 2. Send to AI
       const bddOutput = await this.aiClient.generateBDDScenario({
         actions: recording,
         scenarioName,
         analysis
       });

       // 3. Format output
       return this.formatOutput(bddOutput);
     }
   }
   ```

2. ✅ Create output formatter
   ```typescript
   formatOutput(bddOutput: any): BDDOutput {
     return {
       feature: this.formatFeatureFile(bddOutput),
       steps: this.formatStepDefinitions(bddOutput),
       locators: this.extractLocators(bddOutput),
       testData: this.extractTestData(bddOutput)
     };
   }
   ```

**Deliverables:**
- ✅ BDD conversion working
- ✅ Feature file generation
- ✅ Step definition generation

---

#### Day 9: Locator Extraction & Management

**Tasks:**
1. ✅ Create locator extractor
   ```typescript
   // src/parsers/locator-extractor.ts
   export class LocatorExtractor {
     extract(actions: PlaywrightAction[]): Record<string, string> {
       const locators = {};

       for (const action of actions) {
         if (action.selector) {
           const name = this.generateLocatorName(action);
           locators[name] = action.selector;
         }
       }

       return locators;
     }
   }
   ```

2. ✅ Create locator mapping file generator
   ```typescript
   generateLocatorFile(
     locators: Record<string, string>,
     outputDir: string
   ) {
     const content = JSON.stringify(locators, null, 2);
     fs.writeFileSync(
       path.join(outputDir, 'config', 'locators.json'),
       content
     );
   }
   ```

**Deliverables:**
- ✅ Locator extraction
- ✅ Locator mapping files
- ✅ Locator naming conventions

---

#### Day 10: Test Data Extraction

**Tasks:**
1. ✅ Create data schema extractor
   ```typescript
   // src/parsers/data-extractor.ts
   export class DataExtractor {
     extractSchema(actions: PlaywrightAction[]): DataSchema {
       const schema = {};

       for (const action of actions) {
         if (action.type === 'fill') {
           schema[action.selector] = {
             type: this.inferType(action.value),
             example: action.value
           };
         }
       }

       return schema;
     }
   }
   ```

2. ✅ Generate test data files
   ```typescript
   async generateTestDataFile(
     schema: DataSchema,
     outputDir: string
   ) {
     // Use AI to generate sample data
     const testData = await this.aiClient.generateTestData(schema);

     fs.writeFileSync(
       path.join(outputDir, 'fixtures', 'test_data.json'),
       JSON.stringify(testData, null, 2)
     );
   }
   ```

**Deliverables:**
- ✅ Data schema extraction
- ✅ Test data generation
- ✅ Fixture file creation

---

### Phase 4: CLI Commands (Days 11-13)

#### Day 11: Record Command

**Tasks:**
1. ✅ Implement record command
   ```typescript
   // src/commands/record.ts
   export function createRecordCommand(): Command {
     return new Command('record')
       .description('Record a new test scenario')
       .option('-u, --url <url>', 'Starting URL')
       .option('-s, --scenario-name <name>', 'Scenario name')
       .option('--convert-to-bdd', 'Auto-convert after recording')
       .action(async (options) => {
         await recordScenario(options);
       });
   }

   async function recordScenario(options: any) {
     // 1. Launch Playwright codegen
     const recordingFile = await launchRecorder(options);

     // 2. Save recording
     await saveRecording(recordingFile, options.scenarioName);

     // 3. Auto-convert if requested
     if (options.convertToBdd) {
       await convertRecording(recordingFile);
     }
   }

   async function launchRecorder(options: any): Promise<string> {
     execSync(`npx playwright codegen ${options.url}`, {
       stdio: 'inherit'
     });

     // Recording saved by Playwright
     return path.join(process.cwd(), 'recordings', `${Date.now()}.json`);
   }
   ```

**Deliverables:**
- ✅ Recording command working
- ✅ Integration with Playwright codegen
- ✅ Auto-conversion option

---

#### Day 12: Convert Command

**Tasks:**
1. ✅ Implement convert command
   ```typescript
   // src/commands/convert.ts
   export function createConvertCommand(): Command {
     return new Command('convert')
       .description('Convert recording to BDD')
       .argument('<recording-file>', 'Path to recording')
       .option('-o, --output <dir>', 'Output directory')
       .option('--scenario-name <name>', 'Scenario name')
       .action(async (recordingFile, options) => {
         await convertRecording(recordingFile, options);
       });
   }

   async function convertRecording(
     recordingFile: string,
     options: any
   ) {
     const spinner = ora('Converting recording...').start();

     // 1. Parse recording
     const parser = new RecordingParser();
     const actions = parser.parse(recordingFile);

     // 2. Convert to BDD
     const converter = new BDDConverter(aiClient);
     const bddOutput = await converter.convert(
       actions,
       options.scenarioName
     );

     // 3. Write files
     await writeFeatureFile(bddOutput.feature);
     await writeStepDefinitions(bddOutput.steps);
     await writeLocators(bddOutput.locators);
     await writeTestData(bddOutput.testData);

     spinner.succeed('Conversion complete!');
   }
   ```

**Deliverables:**
- ✅ Convert command working
- ✅ Complete file generation
- ✅ Integration with BDD converter

---

#### Day 13: Optimize Command

**Tasks:**
1. ✅ Implement optimize command
   ```typescript
   // src/commands/optimize.ts
   export function createOptimizeCommand(): Command {
     return new Command('optimize')
       .description('Optimize existing tests')
       .action(async () => {
         await optimizeFramework();
       });
   }

   async function optimizeFramework() {
     const spinner = ora('Analyzing framework...').start();

     // 1. Analyze all feature files
     const features = await loadAllFeatures();

     // 2. Find patterns
     const patterns = await analyzePatterns(features);

     // 3. Generate suggestions
     const suggestions = await generateOptimizations(patterns);

     // 4. Display results
     displayOptimizations(suggestions);

     spinner.succeed('Analysis complete!');
   }
   ```

**Deliverables:**
- ✅ Optimize command working
- ✅ Pattern analysis
- ✅ Optimization suggestions

---

### Phase 5: Testing & Polish (Days 14-15)

#### Day 14: Integration Testing

**Tasks:**
1. ✅ Test complete workflow
   - Init framework
   - Record scenario
   - Convert to BDD
   - Run tests
   - Verify healing
   - Verify data generation

2. ✅ Test with real Power Apps
   - Create test Power Apps environment
   - Record real scenarios
   - Verify framework works

3. ✅ Fix bugs and issues

**Deliverables:**
- ✅ All features tested
- ✅ Bugs fixed
- ✅ Stable release

---

#### Day 15: Documentation & Publishing

**Tasks:**
1. ✅ Complete documentation
   - README.md
   - API documentation
   - Tutorial videos
   - Example projects

2. ✅ Publish to NPM
   ```bash
   npm login
   npm publish
   ```

3. ✅ Create GitHub releases
4. ✅ Marketing materials

**Deliverables:**
- ✅ Published to NPM
- ✅ Complete documentation
- ✅ Ready for users

---

## 📊 Success Metrics

- [ ] Framework generates in < 30 seconds
- [ ] BDD conversion accuracy > 90%
- [ ] Self-healing success rate > 75%
- [ ] Tests run without manual intervention
- [ ] Non-technical testers can use without help

---

## 🚀 Quick Start (For Developers)

```bash
# Clone repo
git clone <repo-url>

# Install CLI dependencies
cd cli
npm install

# Build CLI
npm run build

# Link for local testing
npm link

# Test CLI
playwright-ai init --language python --bdd

# Develop
npm run dev -- init --help
```

---

## 📝 Notes

- Use **chain-of-thought** prompting for AI tasks
- Cache AI responses to reduce costs
- Add telemetry for usage analytics (opt-in)
- Consider offline mode with cached responses
- Add update checker for CLI

---

## ✅ Completion Checklist

### Phase 1: Foundation
- [ ] CLI project setup
- [ ] Template engine
- [ ] Init command

### Phase 2: Templates
- [ ] Python helpers
- [ ] AI helpers (Part 1)
- [ ] AI helpers (Part 2)

### Phase 3: AI Integration
- [ ] Recording parser
- [ ] BDD converter
- [ ] Locator extraction
- [ ] Test data extraction

### Phase 4: CLI Commands
- [ ] Record command
- [ ] Convert command
- [ ] Optimize command

### Phase 5: Testing & Polish
- [ ] Integration testing
- [ ] Documentation
- [ ] NPM publishing

---

**Let's build this! 🚀**
