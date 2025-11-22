import chalk from 'chalk';

export class Logger {
  static info(message: string): void {
    console.log(chalk.blue('ℹ'), message);
  }

  static success(message: string): void {
    console.log(chalk.green('✓'), message);
  }

  static error(message: string): void {
    console.log(chalk.red('✗'), message);
  }

  static warning(message: string): void {
    console.log(chalk.yellow('⚠'), message);
  }

  static step(message: string): void {
    console.log(chalk.cyan('→'), message);
  }

  static title(message: string): void {
    console.log('\n' + chalk.bold.magenta(message) + '\n');
  }

  static newline(): void {
    console.log();
  }

  static list(items: string[]): void {
    items.forEach(item => {
      console.log(chalk.gray('  •'), item);
    });
  }

  static code(code: string): void {
    console.log(chalk.gray(code));
  }

  static keyValue(key: string, value: string): void {
    console.log(chalk.cyan(`  ${key}:`), chalk.white(value));
  }
}
