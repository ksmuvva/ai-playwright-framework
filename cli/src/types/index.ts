/**
 * Type definitions for the AI Playwright Framework CLI
 */

export interface InitOptions {
  language: 'python' | 'typescript';
  projectName: string;
  bdd: boolean;
  powerApps: boolean;
  aiProvider: 'anthropic' | 'openai' | 'none';
  aiModel?: string;
  apiKey?: string;
  directory?: string;
}

export interface RecordOptions {
  url: string;
  scenarioName: string;
  browser?: string;
  convertToBdd: boolean;
  generateData: boolean;
}

export interface ConvertOptions {
  recordingFile: string;
  scenarioName?: string;
  outputDir?: string;
}

export interface PlaywrightAction {
  type: 'navigate' | 'click' | 'fill' | 'select' | 'check' | 'press' | 'wait';
  selector?: string;
  value?: string;
  url?: string;
  key?: string;
  timestamp?: number;
}

export interface BDDOutput {
  feature: string;        // Gherkin feature file content
  steps: string;          // Python/TypeScript step definitions
  locators: Record<string, string>;  // Locator mappings
  testData: Record<string, any>;     // Test data schema
  helpers: string[];      // Suggested helper functions
  pageObjects: Record<string, string>;  // Page object classes (page_name -> class code)
}

export interface DataSchema {
  [fieldName: string]: {
    type: string;
    required?: boolean;
    context?: string;
    example?: any;
  };
}

export interface LocatorContext {
  failedLocator: string;
  elementDescription: string;
  pageHtml: string;
  previousLocators?: string[];
}

export interface LocatorSuggestion {
  locator: string;
  confidence: number;
  alternatives: string[];
}

export interface TestData {
  [key: string]: any;
}

export interface WaitRecommendations {
  optimizations: Array<{
    locator: string;
    currentTimeout: number;
    recommendedTimeout: number;
    waitType: 'explicit' | 'implicit';
    reason: string;
  }>;
}

export interface PatternAnalysis {
  commonSteps: Array<{
    step: string;
    occurrences: number;
    suggestedHelper: string;
  }>;
  duplicateScenarios: Array<{
    scenarios: string[];
    similarity: number;
  }>;
  reusableLocators: Record<string, string[]>;
}

export interface FrameworkConfig {
  projectName: string;
  language: 'python' | 'typescript';
  features: {
    bdd: boolean;
    powerApps: boolean;
    healing: boolean;
    screenshots: boolean;
    video: boolean;
  };
  ai: {
    provider: 'anthropic' | 'openai' | 'none';
    model?: string;
  };
}

export interface AIClient {
  generateBDDScenario(recording: PlaywrightAction[], scenarioName: string): Promise<BDDOutput>;
  healLocator(context: LocatorContext): Promise<LocatorSuggestion>;
  generateTestData(schema: DataSchema): Promise<TestData>;
  optimizeWaits(testLog: any): Promise<WaitRecommendations>;
  analyzePatterns(scenarios: any[]): Promise<PatternAnalysis>;
}

export interface TemplateContext {
  projectName: string;
  language: 'python' | 'typescript';
  features: {
    bdd: boolean;
    powerApps: boolean;
    healing: boolean;
  };
  ai: {
    provider: string;
    enabled: boolean;
  };
  scenarios?: Array<{
    name: string;
    feature: string;
  }>;
}
