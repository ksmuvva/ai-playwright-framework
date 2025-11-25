/**
 * Page Object Registry for Framework Injection
 *
 * ROOT CAUSE FIX (P2): Implements Page Object tracking and extension
 *
 * Purpose:
 * - Track existing Page Object classes
 * - Detect locators and methods in pages
 * - Enable page extension instead of replacement
 * - Support incremental page object development
 *
 * Features:
 * - Scans existing page object files
 * - Parses class definitions, locators, and methods
 * - Detects duplicate pages
 * - Supports page merging and extension
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import { Logger } from './logger';

export interface PageLocator {
  name: string;              // Locator variable name (e.g., 'username_input')
  selector: string;          // Playwright selector
  lineNumber: number;
}

export interface PageMethod {
  name: string;              // Method name (e.g., 'login')
  parameters: string[];      // Method parameters
  returnType: string;        // Return type (if specified)
  lineNumber: number;
  code: string;              // Full method code
}

export interface PageObjectDefinition {
  className: string;         // Class name (e.g., 'LoginPage')
  filePath: string;          // Source file
  baseClass: string;         // Base class name (e.g., 'BasePage')
  locators: PageLocator[];   // Locators defined in this page
  methods: PageMethod[];     // Methods defined in this page
  imports: string[];         // Import statements
}

export class PageObjectRegistry {
  private pages: Map<string, PageObjectDefinition>;
  private projectRoot: string;
  private pagesDirectory: string;

  constructor(projectRoot: string) {
    this.projectRoot = projectRoot;
    this.pagesDirectory = path.join(projectRoot, 'pages');
    this.pages = new Map();
  }

  /**
   * Initialize registry by scanning existing page object files
   */
  async initialize(): Promise<void> {
    Logger.info('Initializing Page Object Registry...');

    try {
      // Check if pages directory exists
      await fs.access(this.pagesDirectory);

      // Scan all Python files in pages directory
      const files = await this.findPageFiles();

      for (const file of files) {
        await this.parsePageFile(file);
      }

      Logger.info(`✓ Loaded ${this.pages.size} existing page objects from ${files.length} files`);
    } catch (error) {
      // Directory doesn't exist - this is a new project
      Logger.info('No existing page objects found - initializing new project');
    }
  }

  /**
   * Find all page object files
   */
  private async findPageFiles(): Promise<string[]> {
    const files: string[] = [];

    try {
      const entries = await fs.readdir(this.pagesDirectory);

      for (const entry of entries) {
        if (entry.endsWith('_page.py') || entry === 'base_page.py') {
          files.push(path.join(this.pagesDirectory, entry));
        }
      }
    } catch (error) {
      // Directory doesn't exist
    }

    return files;
  }

  /**
   * Parse a page object file
   */
  private async parsePageFile(filePath: string): Promise<void> {
    try {
      const content = await fs.readFile(filePath, 'utf-8');
      const lines = content.split('\n');

      let className: string | null = null;
      let baseClass: string = 'BasePage';
      const imports: string[] = [];
      const locators: PageLocator[] = [];
      const methods: PageMethod[] = [];

      let inClass = false;
      let inMethod = false;
      let currentMethod: Partial<PageMethod> | null = null;
      let methodCode: string[] = [];
      let classIndent = 0;

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trim();

        // Parse imports
        if (trimmed.startsWith('from ') || trimmed.startsWith('import ')) {
          imports.push(trimmed);
          continue;
        }

        // Parse class definition
        const classMatch = trimmed.match(/^class\s+(\w+)(?:\((\w+)\))?:/);
        if (classMatch) {
          className = classMatch[1];
          baseClass = classMatch[2] || 'object';
          inClass = true;
          classIndent = line.search(/\S/);
          continue;
        }

        if (!inClass || !className) continue;

        const currentIndent = line.search(/\S/);

        // End of class (dedent back to class level or less)
        if (trimmed && currentIndent <= classIndent) {
          break;
        }

        // Parse locators (self.xxx = page.locator(...))
        const locatorMatch = trimmed.match(/self\.(\w+)\s*=\s*page\.(?:locator|get_by_\w+)\(['"](.+?)['"]/);
        if (locatorMatch) {
          locators.push({
            name: locatorMatch[1],
            selector: locatorMatch[2],
            lineNumber: i + 1
          });
          continue;
        }

        // Parse method definition
        const methodMatch = trimmed.match(/^def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*(.+?))?:/);
        if (methodMatch) {
          // Save previous method if any
          if (inMethod && currentMethod && currentMethod.name) {
            methods.push({
              name: currentMethod.name,
              parameters: currentMethod.parameters || [],
              returnType: currentMethod.returnType || 'None',
              lineNumber: currentMethod.lineNumber || i + 1,
              code: methodCode.join('\n')
            });
          }

          // Start new method
          const params = methodMatch[2]
            .split(',')
            .map(p => p.trim())
            .filter(p => p && p !== 'self');

          currentMethod = {
            name: methodMatch[1],
            parameters: params,
            returnType: methodMatch[3]?.trim() || 'None',
            lineNumber: i + 1
          };
          methodCode = [line];
          inMethod = true;
          continue;
        }

        // Collect method body
        if (inMethod && currentMethod) {
          methodCode.push(line);
        }
      }

      // Save last method if any
      if (inMethod && currentMethod && currentMethod.name) {
        methods.push({
          name: currentMethod.name,
          parameters: currentMethod.parameters || [],
          returnType: currentMethod.returnType || 'None',
          lineNumber: currentMethod.lineNumber || 0,
          code: methodCode.join('\n')
        });
      }

      // Add page to registry
      if (className) {
        this.pages.set(className, {
          className,
          filePath,
          baseClass,
          locators,
          methods,
          imports
        });
      }

    } catch (error) {
      Logger.warning(`Could not parse page file ${filePath}: ${error}`);
    }
  }

  /**
   * Check if a page exists
   */
  pageExists(className: string): boolean {
    return this.pages.has(className);
  }

  /**
   * Get page definition
   */
  getPage(className: string): PageObjectDefinition | undefined {
    return this.pages.get(className);
  }

  /**
   * Get all pages
   */
  getAllPages(): PageObjectDefinition[] {
    return Array.from(this.pages.values());
  }

  /**
   * Check if a locator exists in a page
   */
  locatorExists(className: string, locatorName: string): boolean {
    const page = this.pages.get(className);
    if (!page) return false;

    return page.locators.some(loc => loc.name === locatorName);
  }

  /**
   * Check if a method exists in a page
   */
  methodExists(className: string, methodName: string): boolean {
    const page = this.pages.get(className);
    if (!page) return false;

    return page.methods.some(method => method.name === methodName);
  }

  /**
   * Generate code to extend an existing page with new locators
   */
  generateLocatorExtension(
    className: string,
    newLocators: Array<{ name: string; selector: string }>
  ): string {
    const page = this.pages.get(className);
    if (!page) {
      return '';
    }

    // Filter out locators that already exist
    const uniqueLocators = newLocators.filter(
      loc => !this.locatorExists(className, loc.name)
    );

    if (uniqueLocators.length === 0) {
      return '';
    }

    // Generate code to add to __init__ method
    const locatorCode = uniqueLocators.map(loc =>
      `        self.${loc.name} = page.locator('${loc.selector}')`
    ).join('\n');

    return locatorCode;
  }

  /**
   * Generate code to extend an existing page with new methods
   */
  generateMethodExtension(
    className: string,
    newMethods: Array<{ name: string; code: string }>
  ): string {
    const page = this.pages.get(className);
    if (!page) {
      return '';
    }

    // Filter out methods that already exist
    const uniqueMethods = newMethods.filter(
      method => !this.methodExists(className, method.name)
    );

    if (uniqueMethods.length === 0) {
      return '';
    }

    // Generate method code
    return uniqueMethods.map(method => method.code).join('\n\n');
  }

  /**
   * Merge new page object with existing one
   * Returns: { shouldCreate: boolean, mergedCode?: string }
   */
  async mergePage(
    className: string,
    newPageCode: string
  ): Promise<{ shouldCreate: boolean; mergedCode?: string }> {
    const existingPage = this.pages.get(className);

    if (!existingPage) {
      // Page doesn't exist, create new one
      return { shouldCreate: true };
    }

    // Page exists, merge locators and methods
    Logger.info(`Merging new elements into existing page: ${className}`);

    try {
      const existingContent = await fs.readFile(existingPage.filePath, 'utf-8');

      // Parse new page to extract locators and methods
      const newLocators = this.extractLocators(newPageCode);
      const newMethods = this.extractMethods(newPageCode);

      // Generate extension code
      const locatorExtension = this.generateLocatorExtension(className, newLocators);
      const methodExtension = this.generateMethodExtension(className, newMethods);

      if (!locatorExtension && !methodExtension) {
        Logger.info(`No new elements to add to ${className}`);
        return { shouldCreate: false };
      }

      // Insert new locators into __init__ method
      let mergedCode = existingContent;

      if (locatorExtension) {
        // Find __init__ method and insert locators
        const initMatch = mergedCode.match(/def __init__\(self[^)]*\):[\s\S]*?(?=\n    def |\n\nclass |\n\n$|$)/);
        if (initMatch) {
          const initEnd = initMatch.index! + initMatch[0].length;
          mergedCode = mergedCode.slice(0, initEnd) + '\n' + locatorExtension + mergedCode.slice(initEnd);
        }
      }

      if (methodExtension) {
        // Append new methods at the end of the class
        const classEnd = this.findClassEnd(mergedCode, className);
        if (classEnd > 0) {
          mergedCode = mergedCode.slice(0, classEnd) + '\n' + methodExtension + '\n' + mergedCode.slice(classEnd);
        }
      }

      return { shouldCreate: false, mergedCode };

    } catch (error) {
      Logger.error(`Error merging page ${className}: ${error}`);
      return { shouldCreate: true };  // Fallback to creating new page
    }
  }

  /**
   * Extract locators from page code
   */
  private extractLocators(code: string): Array<{ name: string; selector: string }> {
    const locators: Array<{ name: string; selector: string }> = [];
    const lines = code.split('\n');

    for (const line of lines) {
      const match = line.match(/self\.(\w+)\s*=\s*page\.(?:locator|get_by_\w+)\(['"](.+?)['"]/);
      if (match) {
        locators.push({ name: match[1], selector: match[2] });
      }
    }

    return locators;
  }

  /**
   * Extract methods from page code
   */
  private extractMethods(code: string): Array<{ name: string; code: string }> {
    const methods: Array<{ name: string; code: string }> = [];
    const lines = code.split('\n');

    let inMethod = false;
    let methodName = '';
    let methodLines: string[] = [];
    let methodIndent = 0;

    for (const line of lines) {
      const trimmed = line.trim();

      // Skip __init__ method (handled separately)
      if (trimmed.startsWith('def __init__')) {
        inMethod = true;
        methodIndent = line.search(/\S/);
        continue;
      }

      // Start of method
      const methodMatch = trimmed.match(/^def\s+(\w+)\s*\(/);
      if (methodMatch && !trimmed.startsWith('def __init__')) {
        // Save previous method
        if (inMethod && methodName && methodLines.length > 0) {
          methods.push({ name: methodName, code: methodLines.join('\n') });
        }

        methodName = methodMatch[1];
        methodLines = [line];
        inMethod = true;
        methodIndent = line.search(/\S/);
        continue;
      }

      // Method body
      if (inMethod) {
        const currentIndent = line.search(/\S/);

        // End of method (dedent)
        if (trimmed && currentIndent > 0 && currentIndent <= methodIndent) {
          // Save method
          if (methodName && methodLines.length > 0) {
            methods.push({ name: methodName, code: methodLines.join('\n') });
          }

          // Reset
          inMethod = false;
          methodName = '';
          methodLines = [];
        } else {
          methodLines.push(line);
        }
      }
    }

    // Save last method
    if (inMethod && methodName && methodLines.length > 0) {
      methods.push({ name: methodName, code: methodLines.join('\n') });
    }

    return methods;
  }

  /**
   * Find the end of a class definition
   */
  private findClassEnd(code: string, className: string): number {
    const lines = code.split('\n');
    let inClass = false;
    let classIndent = 0;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const trimmed = line.trim();

      if (trimmed.startsWith(`class ${className}`)) {
        inClass = true;
        classIndent = line.search(/\S/);
        continue;
      }

      if (inClass) {
        const currentIndent = line.search(/\S/);

        // End of class (dedent or new class)
        if ((trimmed && currentIndent <= classIndent) || trimmed.startsWith('class ')) {
          // Return position before this line
          return code.split('\n').slice(0, i).join('\n').length;
        }
      }
    }

    // End of file
    return code.length;
  }

  /**
   * Export registry to JSON for debugging
   */
  exportToJSON(): string {
    const pagesArray = Array.from(this.pages.entries()).map(([key, page]) => ({
      className: page.className,
      filePath: page.filePath,
      baseClass: page.baseClass,
      locatorCount: page.locators.length,
      methodCount: page.methods.length,
      locators: page.locators.map(l => l.name),
      methods: page.methods.map(m => m.name)
    }));

    return JSON.stringify(pagesArray, null, 2);
  }
}
