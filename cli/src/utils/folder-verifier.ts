import * as fs from 'fs/promises';
import path from 'path';
import { Logger } from './logger';
import chalk from 'chalk';

export interface FolderVerificationResult {
  success: boolean;
  existingFolders: string[];
  missingFolders: string[];
  existingFiles: string[];
  missingFiles: string[];
}

/**
 * FolderVerifier - Verifies framework folder structure and files
 *
 * Ensures all expected directories and files are created during initialization
 */
export class FolderVerifier {
  /**
   * Expected directories from PythonGenerator
   */
  private static readonly REQUIRED_FOLDERS = [
    'features',
    'features/steps',
    'helpers',
    'pages',
    'fixtures',
    'reports',
    'reports/screenshots',
    'reports/videos',
    'auth_states',
    'config',
    'scripts'
  ];

  /**
   * Expected critical files
   */
  private static readonly REQUIRED_FILES = [
    'pyproject.toml',
    'behave.ini',
    '.env',
    '.env.example',
    'README.md',
    '.gitignore',
    'features/environment.py',
    'features/example.feature',
    'features/steps/common_steps.py',
    'features/steps/__init__.py',
    'config/config.py',
    'config/__init__.py',
    'helpers/__init__.py',
    'helpers/auth_helper.py',
    'helpers/healing_locator.py',
    'helpers/wait_manager.py',
    'helpers/data_generator.py',
    'helpers/screenshot_manager.py',
    'helpers/phoenix_tracer.py',
    'helpers/logger.py',
    'helpers/reasoning.py',
    'pages/__init__.py',
    'pages/base_page.py',
    'pages/login_page.py',
    'pages/dashboard_page.py'
  ];

  /**
   * Verify folder structure
   */
  static async verifyFolderStructure(projectDir: string): Promise<FolderVerificationResult> {
    const result: FolderVerificationResult = {
      success: false,
      existingFolders: [],
      missingFolders: [],
      existingFiles: [],
      missingFiles: []
    };

    Logger.info('Verifying folder structure...');

    // Check folders
    for (const folder of this.REQUIRED_FOLDERS) {
      const folderPath = path.join(projectDir, folder);
      try {
        const stats = await fs.stat(folderPath);
        if (stats.isDirectory()) {
          result.existingFolders.push(folder);
          Logger.success(`  ✓ ${folder}/`);
        } else {
          result.missingFolders.push(folder);
          Logger.error(`  ✗ ${folder}/ - NOT A DIRECTORY`);
        }
      } catch (error) {
        result.missingFolders.push(folder);
        Logger.error(`  ✗ ${folder}/ - MISSING`);
      }
    }

    Logger.newline();
    Logger.info('Verifying critical files...');

    // Check files
    for (const file of this.REQUIRED_FILES) {
      const filePath = path.join(projectDir, file);
      try {
        const stats = await fs.stat(filePath);
        if (stats.isFile()) {
          result.existingFiles.push(file);
          Logger.success(`  ✓ ${file}`);
        } else {
          result.missingFiles.push(file);
          Logger.error(`  ✗ ${file} - NOT A FILE`);
        }
      } catch (error) {
        result.missingFiles.push(file);
        Logger.error(`  ✗ ${file} - MISSING`);
      }
    }

    result.success = result.missingFolders.length === 0 && result.missingFiles.length === 0;

    Logger.newline();
    if (result.success) {
      Logger.success(`All ${result.existingFolders.length} folders and ${result.existingFiles.length} files verified!`);
    } else {
      Logger.warning('Folder structure verification incomplete:');
      Logger.keyValue('  Folders OK', result.existingFolders.length.toString());
      Logger.keyValue('  Folders Missing', result.missingFolders.length.toString());
      Logger.keyValue('  Files OK', result.existingFiles.length.toString());
      Logger.keyValue('  Files Missing', result.missingFiles.length.toString());
    }

    return result;
  }

  /**
   * Generate detailed verification report
   */
  static generateReport(result: FolderVerificationResult): string {
    let report = '\n' + '='.repeat(70) + '\n';
    report += '  FOLDER STRUCTURE VERIFICATION REPORT\n';
    report += '='.repeat(70) + '\n\n';

    report += `Status: ${result.success ? chalk.green('✓ SUCCESS') : chalk.red('✗ FAILED')}\n\n`;

    // Folders section
    report += `Folders (${result.existingFolders.length}/${this.REQUIRED_FOLDERS.length}):\n`;

    if (result.missingFolders.length > 0) {
      report += `\n${chalk.red('Missing Folders')} (${result.missingFolders.length}):\n`;
      result.missingFolders.forEach(folder => {
        report += `  ${chalk.red('✗')} ${folder}/\n`;
      });
    }

    // Files section
    report += `\nFiles (${result.existingFiles.length}/${this.REQUIRED_FILES.length}):\n`;

    if (result.missingFiles.length > 0) {
      report += `\n${chalk.red('Missing Files')} (${result.missingFiles.length}):\n`;
      result.missingFiles.forEach(file => {
        report += `  ${chalk.red('✗')} ${file}\n`;
      });
    }

    report += '\n' + '='.repeat(70) + '\n';

    return report;
  }

  /**
   * Quick check - just verify essential files exist
   */
  static async quickCheck(projectDir: string): Promise<boolean> {
    const essentialFiles = [
      'pyproject.toml',
      'features/environment.py',
      'config/config.py',
      'helpers/healing_locator.py'
    ];

    for (const file of essentialFiles) {
      try {
        await fs.access(path.join(projectDir, file));
      } catch (error) {
        return false;
      }
    }

    return true;
  }

  /**
   * Create missing folders (recovery mode)
   */
  static async createMissingFolders(projectDir: string, missingFolders: string[]): Promise<void> {
    Logger.info(`Creating ${missingFolders.length} missing folders...`);

    for (const folder of missingFolders) {
      try {
        const folderPath = path.join(projectDir, folder);
        await fs.mkdir(folderPath, { recursive: true });
        Logger.success(`  ✓ Created ${folder}/`);
      } catch (error) {
        Logger.error(`  ✗ Failed to create ${folder}/: ${error}`);
      }
    }
  }
}
