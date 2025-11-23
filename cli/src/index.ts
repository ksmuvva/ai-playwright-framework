#!/usr/bin/env node

import { Command } from 'commander';
import chalk from 'chalk';
import { createInitCommand } from './commands/init';
import { createRecordCommand } from './commands/record';
import { createConvertCommand } from './commands/convert';

const program = new Command();

program
  .name('playwright-ai')
  .description('🤖 AI-powered Playwright test automation framework generator')
  .version('1.0.1');

// Display banner
console.log(chalk.bold.cyan(`
╔═══════════════════════════════════════════════════════════════╗
║                                                                ║
║   🤖  AI-Powered Playwright Framework Generator               ║
║                                                                ║
║   Generate complete test automation frameworks                ║
║   with self-healing, smart waits, and AI-powered features    ║
║                                                                ║
╚═══════════════════════════════════════════════════════════════╝
`));

// Add commands
program.addCommand(createInitCommand());
program.addCommand(createRecordCommand());
program.addCommand(createConvertCommand());

// Add example usage
program.on('--help', () => {
  console.log('');
  console.log('Examples:');
  console.log('');
  console.log(chalk.gray('  # Initialize a new Python framework'));
  console.log('  $ playwright-ai init --language python --bdd --power-apps');
  console.log('');
  console.log(chalk.gray('  # Record a new scenario'));
  console.log('  $ playwright-ai record --url https://your-app.com --scenario-name login');
  console.log('');
  console.log(chalk.gray('  # Convert recording to BDD'));
  console.log('  $ playwright-ai convert recordings/login.py');
  console.log('');
  console.log('Documentation: https://github.com/your-org/playwright-ai-framework');
  console.log('');
});

// Parse command line arguments
program.parse(process.argv);

// Show help if no command provided
if (!process.argv.slice(2).length) {
  program.outputHelp();
}
