import chalk from 'chalk';

/**
 * Log levels (BUG-011 fix)
 */
export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
  SILENT = 4
}

export class Logger {
  private static level: LogLevel = LogLevel.INFO;

  /**
   * Set the logging level
   */
  static setLevel(level: LogLevel): void {
    this.level = level;
  }

  /**
   * Get the current logging level
   */
  static getLevel(): LogLevel {
    return this.level;
  }

  /**
   * Debug level logging
   */
  static debug(message: string): void {
    if (this.level <= LogLevel.DEBUG) {
      console.log(chalk.gray('🔍'), chalk.gray(message));
    }
  }

  static info(message: string): void {
    if (this.level <= LogLevel.INFO) {
      console.log(chalk.blue('ℹ'), message);
    }
  }

  static success(message: string): void {
    if (this.level <= LogLevel.INFO) {
      console.log(chalk.green('✓'), message);
    }
  }

  static error(message: string): void {
    if (this.level <= LogLevel.ERROR) {
      console.log(chalk.red('✗'), message);
    }
  }

  static warning(message: string): void {
    if (this.level <= LogLevel.WARN) {
      console.log(chalk.yellow('⚠'), message);
    }
  }

  static warn(message: string): void {
    this.warning(message);
  }

  static step(message: string): void {
    if (this.level <= LogLevel.INFO) {
      console.log(chalk.cyan('→'), message);
    }
  }

  static title(message: string): void {
    if (this.level <= LogLevel.INFO) {
      console.log('\n' + chalk.bold.magenta(message) + '\n');
    }
  }

  static newline(): void {
    if (this.level <= LogLevel.INFO) {
      console.log();
    }
  }

  static list(items: string[]): void {
    if (this.level <= LogLevel.INFO) {
      items.forEach(item => {
        console.log(chalk.gray('  •'), item);
      });
    }
  }

  static code(code: string): void {
    if (this.level <= LogLevel.INFO) {
      console.log(chalk.gray(code));
    }
  }

  static keyValue(key: string, value: string): void {
    if (this.level <= LogLevel.INFO) {
      console.log(chalk.cyan(`  ${key}:`), chalk.white(value));
    }
  }
}
