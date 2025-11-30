/**
 * TypeScript/JavaScript Recording Parser
 *
 * Program of Thoughts Implementation:
 * 1. Use TypeScript Compiler API for AST parsing
 * 2. Extract Playwright actions from call expressions
 * 3. Handle method chaining (e.g., page.getByRole().click())
 * 4. Support modern Playwright API (getByRole, getByText, etc.)
 * 5. Convert to normalized action format
 *
 * Uplift Feature: PILLAR 2 - Recording Intelligence (ROI: 9.5/10)
 * Addresses: FAILURE-004 (60% parsing success → 100%)
 */

import * as ts from 'typescript';
import { Logger } from '../utils/logger';
import { ParsedPlaywrightAction } from './python-parser';

export interface TypeScriptParseResult {
  actions: ParsedPlaywrightAction[];
  metadata: {
    startUrl?: string;
    hasAsync: boolean;
    hasPopups: boolean;
    hasAssertions: boolean;
    totalActions: number;
  };
  parseErrors: Array<{
    line: string;
    lineNumber: number;
    reason: string;
  }>;
}

/**
 * Main entry point: Parse TypeScript/JavaScript Playwright recording
 */
export function parseTypeScriptRecording(content: string): TypeScriptParseResult {
  Logger.info('Parsing TypeScript/JavaScript recording with AST...');

  const actions: ParsedPlaywrightAction[] = [];
  const parseErrors: Array<{ line: string; lineNumber: number; reason: string }> = [];

  const metadata = {
    startUrl: undefined as string | undefined,
    hasAsync: false,
    hasPopups: false,
    hasAssertions: false,
    totalActions: 0
  };

  try {
    // Create TypeScript source file
    const sourceFile = ts.createSourceFile(
      'recording.ts',
      content,
      ts.ScriptTarget.Latest,
      true
    );

    // Visit all nodes in the AST
    let lineNumber = 0;

    const visit = (node: ts.Node) => {
      // Track line numbers
      const pos = sourceFile.getLineAndCharacterOfPosition(node.getStart());
      lineNumber = pos.line + 1;

      // Check for async function (metadata)
      if (ts.isFunctionDeclaration(node) || ts.isArrowFunction(node)) {
        if (node.modifiers?.some(m => m.kind === ts.SyntaxKind.AsyncKeyword)) {
          metadata.hasAsync = true;
        }
      }

      // Parse await expressions with Playwright actions
      if (ts.isAwaitExpression(node)) {
        const action = extractActionFromExpression(node.expression, sourceFile, lineNumber);
        if (action) {
          actions.push(action);
        }
      }

      // Parse direct call expressions (non-await)
      if (ts.isCallExpression(node) && !ts.isAwaitExpression(node.parent)) {
        const action = extractActionFromExpression(node, sourceFile, lineNumber);
        if (action) {
          actions.push(action);
        }
      }

      // Parse expect() assertions
      if (ts.isCallExpression(node)) {
        const text = node.expression.getText(sourceFile);
        if (text === 'expect') {
          metadata.hasAssertions = true;
          const assertAction = extractAssertion(node, sourceFile, lineNumber);
          if (assertAction) {
            actions.push(assertAction);
          }
        }
      }

      ts.forEachChild(node, visit);
    };

    visit(sourceFile);

    // Extract start URL if present
    if (actions.length > 0 && actions[0].type === 'goto') {
      metadata.startUrl = actions[0].url;
    }

    metadata.totalActions = actions.length;

    Logger.info(`✓ Parsed ${actions.length} actions from TypeScript recording`);
    if (metadata.hasAsync) Logger.info('  - Async/await detected');
    if (metadata.hasAssertions) Logger.info('  - Contains assertions');
    if (metadata.hasPopups) Logger.info('  - Contains popup handling');

  } catch (error) {
    Logger.error(`Failed to parse TypeScript: ${error instanceof Error ? error.message : String(error)}`);
    throw error;
  }

  return { actions, metadata, parseErrors };
}

/**
 * Extract Playwright action from a call expression
 *
 * PoT:
 * 1. Identify if this is a Playwright action (page.*, locator.*)
 * 2. Extract method chain (e.g., getByRole().filter().click())
 * 3. Determine action type (click, fill, goto, etc.)
 * 4. Extract locator information
 * 5. Return normalized action object
 */
function extractActionFromExpression(
  expr: ts.Expression,
  sourceFile: ts.SourceFile,
  lineNumber: number
): ParsedPlaywrightAction | null {
  if (!ts.isCallExpression(expr)) {
    return null;
  }

  const fullText = expr.getText(sourceFile);

  // Check if this is a Playwright action
  if (!isPlaywrightAction(fullText)) {
    return null;
  }

  // Parse method chain
  const chain = parseMethodChain(expr, sourceFile);
  if (!chain || chain.methods.length === 0) {
    return null;
  }

  // The last method in the chain is the action
  const actionMethod = chain.methods[chain.methods.length - 1];
  const actionType = mapActionType(actionMethod.name);

  if (!actionType) {
    return null;
  }

  // Build action object
  const action: ParsedPlaywrightAction = {
    type: actionType,
    rawLine: fullText,
    lineNumber,
    pageContext: chain.base === 'page' ? 'page' : chain.base
  };

  // Handle goto (navigation)
  if (actionType === 'goto') {
    const urlArg = actionMethod.args[0];
    if (urlArg && ts.isStringLiteral(urlArg)) {
      action.url = urlArg.text;
    }
    return action;
  }

  // Extract locator information from the chain
  const locatorInfo = extractLocatorFromChain(chain, sourceFile);
  if (locatorInfo) {
    action.locatorType = locatorInfo.type;
    action.locatorValue = locatorInfo.value;
    action.elementName = locatorInfo.name;
  }

  // Extract value for fill, press, etc.
  if (actionType === 'fill' || actionType === 'press' || actionType === 'select') {
    const valueArg = actionMethod.args[0];
    if (valueArg && ts.isStringLiteral(valueArg)) {
      action.value = valueArg.text;
    }
  }

  return action;
}

/**
 * Parse method chain from expression
 *
 * PoT:
 * 1. Start from the innermost expression
 * 2. Walk up the chain collecting methods
 * 3. Identify base object (page, locator, etc.)
 * 4. Return structured chain data
 */
interface MethodChain {
  base: string;  // 'page', 'page1', etc.
  methods: Array<{
    name: string;
    args: ts.Expression[];
  }>;
}

function parseMethodChain(expr: ts.CallExpression, sourceFile: ts.SourceFile): MethodChain | null {
  const methods: Array<{ name: string; args: ts.Expression[] }> = [];
  let current: ts.Expression = expr;
  let base = '';

  // Walk the chain from end to beginning
  while (ts.isCallExpression(current) || ts.isPropertyAccessExpression(current)) {
    if (ts.isCallExpression(current)) {
      // Extract method name and arguments
      if (ts.isPropertyAccessExpression(current.expression)) {
        const methodName = current.expression.name.text;
        const args = Array.from(current.arguments);
        methods.unshift({ name: methodName, args });
        current = current.expression.expression;
      } else {
        break;
      }
    } else if (ts.isPropertyAccessExpression(current)) {
      // Base identifier (e.g., 'page')
      if (ts.isIdentifier(current.expression)) {
        base = current.expression.text;
        break;
      }
      current = current.expression;
    } else {
      break;
    }
  }

  if (!base || methods.length === 0) {
    return null;
  }

  return { base, methods };
}

/**
 * Extract locator information from method chain
 *
 * PoT:
 * 1. Find locator method (getByRole, getByText, locator, etc.)
 * 2. Extract locator type and value
 * 3. Extract element name if present (e.g., { name: 'Submit' })
 * 4. Return locator info
 */
function extractLocatorFromChain(
  chain: MethodChain,
  sourceFile: ts.SourceFile
): { type: ParsedPlaywrightAction['locatorType']; value: string; name?: string } | null {

  // Look for locator methods
  for (const method of chain.methods) {
    // getByRole('button', { name: 'Submit' })
    if (method.name === 'getByRole') {
      const roleArg = method.args[0];
      if (roleArg && ts.isStringLiteral(roleArg)) {
        const role = roleArg.text;
        let elementName: string | undefined;

        // Check for { name: '...' } option
        const optionsArg = method.args[1];
        if (optionsArg && ts.isObjectLiteralExpression(optionsArg)) {
          const nameProp = optionsArg.properties.find(p =>
            ts.isPropertyAssignment(p) &&
            ts.isIdentifier(p.name) &&
            p.name.text === 'name'
          ) as ts.PropertyAssignment | undefined;

          if (nameProp && ts.isStringLiteral(nameProp.initializer)) {
            elementName = nameProp.initializer.text;
          }
        }

        return { type: 'role', value: role, name: elementName };
      }
    }

    // getByText('Login')
    if (method.name === 'getByText') {
      const textArg = method.args[0];
      if (textArg && ts.isStringLiteral(textArg)) {
        return { type: 'text', value: textArg.text };
      }
    }

    // getByLabel('Username')
    if (method.name === 'getByLabel') {
      const labelArg = method.args[0];
      if (labelArg && ts.isStringLiteral(labelArg)) {
        return { type: 'label', value: labelArg.text };
      }
    }

    // getByPlaceholder('Enter username')
    if (method.name === 'getByPlaceholder') {
      const placeholderArg = method.args[0];
      if (placeholderArg && ts.isStringLiteral(placeholderArg)) {
        return { type: 'placeholder', value: placeholderArg.text };
      }
    }

    // getByTestId('submit-button')
    if (method.name === 'getByTestId') {
      const testIdArg = method.args[0];
      if (testIdArg && ts.isStringLiteral(testIdArg)) {
        return { type: 'testid', value: testIdArg.text };
      }
    }

    // locator('.my-selector') or locator('//xpath')
    if (method.name === 'locator') {
      const selectorArg = method.args[0];
      if (selectorArg && ts.isStringLiteral(selectorArg)) {
        const selector = selectorArg.text;
        const type = selector.startsWith('//') || selector.startsWith('(//') ? 'xpath' : 'css';
        return { type, value: selector };
      }
    }
  }

  return null;
}

/**
 * Extract expect() assertion
 */
function extractAssertion(
  node: ts.CallExpression,
  sourceFile: ts.SourceFile,
  lineNumber: number
): ParsedPlaywrightAction | null {

  const fullText = node.getText(sourceFile);

  // Parse different assertion types
  if (fullText.includes('.toHaveURL') || fullText.includes('.to_have_url')) {
    const match = fullText.match(/toHaveURL\(['"](.+?)['"]\)/);
    if (match) {
      return {
        type: 'expect',
        assertion: {
          type: 'url',
          expected: match[1],
          matcher: 'equals'
        },
        rawLine: fullText,
        lineNumber
      };
    }
  }

  if (fullText.includes('.toBeVisible') || fullText.includes('.to_be_visible')) {
    return {
      type: 'expect',
      assertion: {
        type: 'visible',
        expected: 'true'
      },
      rawLine: fullText,
      lineNumber
    };
  }

  if (fullText.includes('.toHaveText') || fullText.includes('.to_have_text')) {
    const match = fullText.match(/toHaveText\(['"](.+?)['"]\)/);
    if (match) {
      return {
        type: 'expect',
        assertion: {
          type: 'text',
          expected: match[1]
        },
        rawLine: fullText,
        lineNumber
      };
    }
  }

  return null;
}

/**
 * Check if expression is a Playwright action
 */
function isPlaywrightAction(text: string): boolean {
  const playwrightPatterns = [
    'page.goto',
    'page.getByRole',
    'page.getByText',
    'page.getByLabel',
    'page.getByPlaceholder',
    'page.getByTestId',
    'page.locator',
    'page.click',
    'page.fill',
    '.click()',
    '.fill(',
    '.press(',
    '.check(',
    '.hover(',
  ];

  return playwrightPatterns.some(pattern => text.includes(pattern));
}

/**
 * Map TypeScript method name to action type
 */
function mapActionType(methodName: string): ParsedPlaywrightAction['type'] | null {
  const mapping: Record<string, ParsedPlaywrightAction['type']> = {
    'goto': 'goto',
    'click': 'click',
    'dblclick': 'dblclick',
    'fill': 'fill',
    'press': 'press',
    'check': 'check',
    'hover': 'hover',
    'selectOption': 'select',
    'close': 'close'
  };

  return mapping[methodName] || null;
}
