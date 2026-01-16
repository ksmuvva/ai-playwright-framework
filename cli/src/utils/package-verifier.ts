import { exec } from 'child_process';
import { promisify } from 'util';
import { Logger } from './logger';
import chalk from 'chalk';

const execAsync = promisify(exec);

export interface PackageInfo {
  name: string;
  version: string;
  required: boolean;
}

export interface VerificationResult {
  success: boolean;
  installedPackages: PackageInfo[];
  missingPackages: string[];
  failedPackages: string[];
}

/**
 * PackageVerifier - Verifies Python package installation
 *
 * This utility provides comprehensive verification of Python packages
 * to ensure all dependencies are properly installed by UV or pip.
 */
export class PackageVerifier {
  /**
   * Expected packages from pyproject.toml
   */
  private static readonly REQUIRED_PACKAGES = [
    'playwright',
    'behave',
    'pytest',
    'anthropic',
    'openai',
    'arize-phoenix',
    'opentelemetry-api',
    'opentelemetry-sdk',
    'opentelemetry-exporter-otlp',
    'faker',
    'python-dotenv',
    'pydantic',
    'structlog',
    'colorama',
    'requests',
    'pyyaml',
    'jinja2',
    'allure-behave'
  ];

  /**
   * Verify all required packages are installed
   */
  static async verifyPackages(projectDir: string): Promise<VerificationResult> {
    const result: VerificationResult = {
      success: false,
      installedPackages: [],
      missingPackages: [],
      failedPackages: []
    };

    Logger.info('Verifying Python packages...');

    for (const packageName of this.REQUIRED_PACKAGES) {
      try {
        const installed = await this.isPackageInstalled(projectDir, packageName);

        if (installed.isInstalled) {
          result.installedPackages.push({
            name: packageName,
            version: installed.version || 'unknown',
            required: true
          });
          Logger.success(`  ✓ ${packageName} ${installed.version ? `(${installed.version})` : ''}`);
        } else {
          result.missingPackages.push(packageName);
          Logger.warning(`  ✗ ${packageName} - NOT INSTALLED`);
        }
      } catch (error) {
        result.failedPackages.push(packageName);
        Logger.warning(`  ? ${packageName} - VERIFICATION FAILED`);
      }
    }

    result.success = result.missingPackages.length === 0 && result.failedPackages.length === 0;

    Logger.newline();
    if (result.success) {
      Logger.success(`All ${result.installedPackages.length} packages verified successfully!`);
    } else {
      Logger.warning(`Package verification incomplete:`);
      Logger.keyValue('  Installed', result.installedPackages.length.toString());
      Logger.keyValue('  Missing', result.missingPackages.length.toString());
      Logger.keyValue('  Failed', result.failedPackages.length.toString());
    }

    return result;
  }

  /**
   * Check if a specific package is installed
   */
  private static async isPackageInstalled(
    projectDir: string,
    packageName: string
  ): Promise<{ isInstalled: boolean; version?: string }> {
    try {
      // Try using the venv's python
      const pythonCommand = process.platform === 'win32'
        ? '.venv\\Scripts\\python'
        : '.venv/bin/python';

      // Use pip show to check if package is installed
      const { stdout } = await execAsync(
        `${pythonCommand} -m pip show ${packageName}`,
        { cwd: projectDir, timeout: 5000 }
      );

      if (stdout && stdout.includes('Name:')) {
        // Extract version from pip show output
        const versionMatch = stdout.match(/Version:\s*(.+)/);
        const version = versionMatch ? versionMatch[1].trim() : undefined;
        return { isInstalled: true, version };
      }

      return { isInstalled: false };
    } catch (error) {
      // Try alternative method using python import
      try {
        const pythonCommand = process.platform === 'win32'
          ? '.venv\\Scripts\\python'
          : '.venv/bin/python';

        // Normalize package name for import (e.g., python-dotenv -> dotenv)
        const importName = this.getImportName(packageName);

        const { stdout } = await execAsync(
          `${pythonCommand} -c "import ${importName}; print(getattr(${importName}, '__version__', 'unknown'))"`,
          { cwd: projectDir, timeout: 5000 }
        );

        if (stdout && !stdout.includes('Error') && !stdout.includes('ModuleNotFoundError')) {
          return { isInstalled: true, version: stdout.trim() };
        }
      } catch (importError) {
        // Package not installed
      }

      return { isInstalled: false };
    }
  }

  /**
   * Get Python import name from package name
   */
  private static getImportName(packageName: string): string {
    const importMap: Record<string, string> = {
      'python-dotenv': 'dotenv',
      'arize-phoenix': 'phoenix',
      'opentelemetry-api': 'opentelemetry.trace',
      'opentelemetry-sdk': 'opentelemetry.sdk',
      'opentelemetry-exporter-otlp': 'opentelemetry.exporter.otlp',
      'allure-behave': 'allure_behave',
      'pyyaml': 'yaml'
    };

    return importMap[packageName] || packageName;
  }

  /**
   * Install missing packages using pip
   */
  static async installMissingPackages(
    projectDir: string,
    packages: string[]
  ): Promise<{ success: boolean; errors: string[] }> {
    const errors: string[] = [];

    Logger.info(`Installing ${packages.length} missing packages with pip...`);

    const pipCommand = process.platform === 'win32'
      ? '.venv\\Scripts\\pip'
      : '.venv/bin/pip';

    for (const packageName of packages) {
      try {
        Logger.info(`  Installing ${packageName}...`);

        // Install with specific versions from pyproject.toml
        const versionMap = this.getPackageVersions();
        const packageSpec = versionMap[packageName] || packageName;

        await execAsync(
          `${pipCommand} install "${packageSpec}"`,
          { cwd: projectDir, timeout: 120000 } // 2 minute timeout per package
        );

        Logger.success(`  ✓ ${packageName} installed`);
      } catch (error) {
        const errorMsg = `Failed to install ${packageName}: ${error}`;
        errors.push(errorMsg);
        Logger.error(`  ✗ ${packageName} - FAILED`);
      }
    }

    return {
      success: errors.length === 0,
      errors
    };
  }

  /**
   * Get package versions from pyproject.toml
   */
  private static getPackageVersions(): Record<string, string> {
    return {
      'playwright': 'playwright>=1.40.0',
      'behave': 'behave>=1.2.6',
      'pytest': 'pytest>=7.4.3',
      'anthropic': 'anthropic>=0.30.0',
      'openai': 'openai>=1.6.1',
      'arize-phoenix': 'arize-phoenix>=12.16.0',
      'opentelemetry-api': 'opentelemetry-api>=1.38.0',
      'opentelemetry-sdk': 'opentelemetry-sdk>=1.38.0',
      'opentelemetry-exporter-otlp': 'opentelemetry-exporter-otlp>=1.38.0',
      'faker': 'faker>=20.1.0',
      'python-dotenv': 'python-dotenv>=1.0.0',
      'pydantic': 'pydantic>=2.5.3',
      'structlog': 'structlog>=24.1.0',
      'colorama': 'colorama>=0.4.6',
      'requests': 'requests>=2.31.0',
      'pyyaml': 'pyyaml>=6.0.0',
      'jinja2': 'jinja2>=3.1.0',
      'allure-behave': 'allure-behave>=2.13.2'
    };
  }

  /**
   * Verify Playwright browsers are installed
   */
  static async verifyPlaywrightBrowsers(projectDir: string): Promise<boolean> {
    try {
      const pythonCommand = process.platform === 'win32'
        ? '.venv\\Scripts\\python'
        : '.venv/bin/python';

      // Check if chromium is installed
      await execAsync(
        `${pythonCommand} -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.executable_path; p.stop()"`,
        { cwd: projectDir, timeout: 10000 }
      );

      Logger.success('Playwright browsers verified');
      return true;
    } catch (error) {
      Logger.warning('Playwright browsers not installed or not accessible');
      return false;
    }
  }

  /**
   * Generate detailed verification report
   */
  static generateReport(result: VerificationResult): string {
    let report = '\n' + '='.repeat(70) + '\n';
    report += '  PACKAGE VERIFICATION REPORT\n';
    report += '='.repeat(70) + '\n\n';

    report += `Status: ${result.success ? chalk.green('✓ SUCCESS') : chalk.red('✗ FAILED')}\n\n`;

    report += `Installed Packages (${result.installedPackages.length}):\n`;
    result.installedPackages.forEach(pkg => {
      report += `  ${chalk.green('✓')} ${pkg.name} (${pkg.version})\n`;
    });

    if (result.missingPackages.length > 0) {
      report += `\nMissing Packages (${result.missingPackages.length}):\n`;
      result.missingPackages.forEach(pkg => {
        report += `  ${chalk.red('✗')} ${pkg}\n`;
      });
    }

    if (result.failedPackages.length > 0) {
      report += `\nFailed Verification (${result.failedPackages.length}):\n`;
      result.failedPackages.forEach(pkg => {
        report += `  ${chalk.yellow('?')} ${pkg}\n`;
      });
    }

    report += '\n' + '='.repeat(70) + '\n';

    return report;
  }
}
