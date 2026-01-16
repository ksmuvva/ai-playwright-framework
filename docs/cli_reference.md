# CLI Command Reference

Complete reference for all Claude Playwright Agent CLI commands.

## Table of Contents

1. [Global Options](#global-options)
2. [Project Commands](#project-commands)
3. [Recording Commands](#recording-commands)
4. [Generation Commands](#generation-commands)
5. [Test Execution Commands](#test-execution-commands)
6. [Reporting Commands](#reporting-commands)
7. [Configuration Commands](#configuration-commands)
8. [Utility Commands](#utility-commands)

---

## Global Options

These options can be used with any command:

```bash
cpa [GLOBAL-OPTIONS] COMMAND [COMMAND-OPTIONS]
```

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--profile <name>` | `-p` | Configuration profile to use | default |
| `--config <path>` | `-c` | Path to config file | config/default/config.yaml |
| `--verbose` | `-v` | Enable verbose output | false |
| `--quiet` | `-q` | Suppress output | false |
| `--help` | `-h` | Show help message | - |
| `--version` | `-V` | Show version | - |

**Examples:**

```bash
# Use development profile
cpa --profile dev run test

# Enable verbose output
cpa --verbose ingest recordings/test.spec.js

# Show version
cpa --version
```

---

## Project Commands

### `cpa init`

Initialize a new test project.

**Usage:**
```bash
cpa init <project-name> [options]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--template <name>` | `-t` | Project template (basic, advanced, ecommerce) | basic |
| `--framework <name>` | `-f` | BDD framework (behave, pytest-bdd) | behave |
| `--base-url <url>` | | Base URL for application | - |
| `--directory <path>` | `-d` | Parent directory | current directory |

**Examples:**

```bash
# Basic project
cpa init my-tests

# Advanced template with pytest-bdd
cpa init my-tests --template advanced --framework pytest-bdd

# With base URL
cpa init my-tests --base-url https://example.com

# In specific directory
cpa init my-tests --directory /path/to/projects
```

**What it creates:**

```
my-tests/
├── config/
├── pages/
├── recordings/
├── features/
├── steps/
└── .cpa/
```

---

### `cpa status`

Show project status and information.

**Usage:**
```bash
cpa status
```

**Output:**

```
Project: my-tests
Profile: default
Framework: behave

Recordings: 5
Features: 3
Page Objects: 2

Last Test Run: 2026-01-16 10:30:00
Status: PASSED (3/3 scenarios)
```

---

## Recording Commands

### `cpa ingest`

Ingest a recording file into the framework.

**Usage:**
```bash
cpa ingest <recording-file> [options]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--name <name>` | `-n` | Recording name | auto-generated |
| `--tags <tags>` | `-t` | Comma-separated tags | - |
| `--deduplicate` | `-d` | Run deduplication | true |
| `--generate-bdd` | `-g` | Generate BDD scenarios | true |

**Examples:**

```bash
# Ingest with defaults
cpa ingest recordings/login.spec.js

# With custom name and tags
cpa ingest recordings/login.spec.js --name "Login Flow" --tags @smoke,@auth

# Without BDD generation
cpa ingest recordings/test.spec.js --no-generate-bdd

# From Playwright codegen output
cpa ingest recordings/generated.spec.js
```

**Supported formats:**
- Playwright recordings (`.spec.js`, `.spec.json`)
- Chrome DevTools recordings (`.json`)
- Custom JSON format

---

### `cpa record`

Record user interactions using Playwright codegen.

**Usage:**
```bash
cpa record <url> [options]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--output <path>` | `-o` | Output file path | recordings/recording.spec.js |
| `--target` | `-t` | Target language (python, javascript) | python |
| `--device <name>` | | Device to emulate | desktop |
| `--save-trace` | | Save trace file | false |

**Examples:**

```bash
# Record with defaults
cpa record https://example.com/login

# Specify output file
cpa record https://example.com --output recordings/homepage.spec.js

# Emulate mobile device
cpa record https://example.com --device "iPhone 13"

# Save trace for debugging
cpa record https://example.com --save-trace
```

---

## Generation Commands

### `cpa generate`

Generate various artifacts from recordings and state.

**Usage:**
```bash
cpa generate <artifact-type> [options]
```

**Artifact Types:**

#### `page-objects`

Generate Page Object classes from deduplicated elements.

```bash
cpa generate page-objects [options]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--input-dir <path>` | `-i` | Input directory | recordings |
| `--output-dir <path>` | `-o` | Output directory | pages |
| `--base-class <name>` | `-b` | Base class name | BasePage |
| `--force` | `-f` | Overwrite existing | false |

**Examples:**

```bash
# Generate with defaults
cpa generate page-objects

# Custom output directory
cpa generate page-objects --output-dir src/pages

# Custom base class
cpa generate page-objects --base-class CustomBasePage

# Overwrite existing
cpa generate page-objects --force
```

#### `steps`

Generate step definitions for BDD scenarios.

```bash
cpa generate steps [options]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--features-dir <path>` | `-f` | Features directory | features |
| `--output-dir <path>` | `-o` | Output directory | steps |

#### `components`

Generate component classes from deduplicated components.

```bash
cpa generate components [options]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--output-dir <path>` | `-o` | Output directory | components |

---

### `cpa deduplicate`

Run element deduplication across recordings.

**Usage:**
```bash
cpa deduplicate [options]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--input-dir <path>` | `-i` | Input directory | recordings |
| `--min-usage <number>` | `-m` | Minimum usage count | 2 |
| `--output <path>` | `-o` | Output file | .cpa/deduplicated.json |

**Examples:**

```bash
# Run deduplication
cpa deduplicate

# Custom minimum usage
cpa deduplicate --min-usage 3

# Output to specific file
cpa deduplicate --output results/deduplication.json
```

---

## Test Execution Commands

### `cpa run`

Run tests or workflows.

**Usage:**
```bash
cpa run <workflow> [options]
```

**Workflows:**

#### `test`

Execute BDD scenarios.

```bash
cpa run test [options]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--tags <expression>` | `-t` | Tag expression | - |
| `--features <paths>` | `-f` | Feature files to run | features/ |
| `--parallel <number>` | `-p` | Number of parallel workers | 1 |
| `--retry <number>` | `-r` | Retry failed tests | 0 |
| `--fail-fast` | | Stop on first failure | false |
| `--verbose` | `-v` | Verbose output | false |

**Examples:**

```bash
# Run all tests
cpa run test

# Run by tag
cpa run test --tags @smoke
cpa run test --tags "@smoke and not @wip"

# Run specific feature
cpa run test --features features/login.feature

# Parallel execution
cpa run test --parallel 4

# Retry failed tests
cpa run test --retry 2

# Fail on first error
cpa run test --fail-fast
```

#### `convert`

Convert recordings to BDD scenarios.

```bash
cpa run convert [options]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--input-dir <path>` | `-i` | Input directory | recordings |
| `--output-dir <path>` | `-o` | Output directory | features |

#### `ingest`

Ingest all pending recordings.

```bash
cpa run ingest [options]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--input-dir <path>` | `-i` | Input directory | recordings |

#### `full`

Run complete pipeline (ingest → dedup → convert → test).

```bash
cpa run full [options]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--input-dir <path>` | `-i` | Input directory | recordings |
| `--parallel <number>` | `-p` | Parallel workers | 1 |

---

## Reporting Commands

### `cpa report`

View test reports.

**Usage:**
```bash
cpa report [test-run-id] [options]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--format <type>` | `-f` | Report format (html, json, junit) | html |
| `--output <path>` | `-o` | Output path | reports/ |
| `--open` | | Open report in browser | false |
| `--analyze` | `-a` | Include AI analysis | false |

**Examples:**

```bash
# View latest report
cpa report

# View specific test run
cpa report abc123

# JSON format
cpa report --format json

# Open in browser
cpa report --open

# With AI analysis
cpa report --analyze
```

---

### `cpa list`

List recordings, features, or test runs.

**Usage:**
```bash
cpa list <type> [options]
```

**Types:**

#### `recordings`

List all recordings.

```bash
cpa list recordings
```

#### `features`

List all BDD features.

```bash
cpa list features
```

#### `runs`

List test runs.

```bash
cpa list runs
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--limit <number>` | `-l` | Limit results | 20 |
| `--offset <number>` | | Offset for pagination | 0 |
| `--format <type>` | | Output format (table, json) | table |

---

## Configuration Commands

### `cpa configure`

Manage framework configuration.

**Usage:**
```bash
cpa configure <action> [options]
```

**Actions:**

#### `set`

Set a configuration value.

```bash
cpa configure set <key> <value>
```

**Examples:**

```bash
# Set browser
cpa configure set browser.browser firefox

# Set parallel workers
cpa configure set execution.parallel_workers 4

# Set headless mode
cpa configure set browser.headless false
```

#### `get`

Get a configuration value.

```bash
cpa configure get <key>
```

**Examples:**

```bash
# Get browser setting
cpa configure get browser.browser

# Get timeout
cpa configure get framework.default_timeout
```

#### `list`

List all configuration values.

```bash
cpa configure list
```

#### `profile`

Switch configuration profile.

```bash
cpa configure profile <profile-name>
```

**Examples:**

```bash
# Switch to development profile
cpa configure profile dev

# Switch to CI profile
cpa configure profile ci
```

---

### `cpa env`

Manage environment variables.

**Usage:**
```bash
cpa env <action> [options]
```

**Actions:**

#### `set`

Set environment variable.

```bash
cpa env set <key> <value>
```

**Examples:**

```bash
# Set API key
cpa env set GLM_API_KEY your-key-here

# Set base URL
cpa env set CPA_BASE_URL https://staging.example.com
```

#### `get`

Get environment variable.

```bash
cpa env get <key>
```

#### `list`

List all environment variables.

```bash
cpa env list
```

#### `unset`

Unset environment variable.

```bash
cpa env unset <key>
```

---

## Utility Commands

### `cpa clean`

Clean generated files and caches.

**Usage:**
```bash
cpa clean <target> [options]
```

**Targets:**

#### `all`

Clean all generated files.

```bash
cpa clean all
```

#### `cache`

Clean framework cache.

```bash
cpa clean cache
```

#### `reports`

Clean test reports.

```bash
cpa clean reports
```

#### `screenshots`

Clean screenshots.

```bash
cpa clean screenshots
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--keep <number>` | `-k` | Keep N most recent | 0 |
| `--yes` | `-y` | Skip confirmation | false |

---

### `cpa export`

Export project data.

**Usage:**
```bash
cpa export <format> [options]
```

**Formats:**

#### `json`

Export as JSON.

```bash
cpa export json --output project.json
```

#### `yaml`

Export as YAML.

```bash
cpa export yaml --output project.yaml
```

---

### `cpa doctor`

Check project health and dependencies.

**Usage:**
```bash
cpa doctor
```

**Output:**

```
✅ Python 3.11.0
✅ Playwright 1.40.0
✅ All dependencies installed
✅ Configuration valid
✅ API key configured
✅ Recordings found: 3
⚠️  No page objects generated
✅ Features found: 2
```

---

### `cpa info`

Show framework and project information.

**Usage:**
```bash
cpa info
```

**Output:**

```
Claude Playwright Agent
Version: 1.0.0
Python: 3.11.0

Project: my-tests
Profile: default
Framework: behave

Config: config/default/config.yaml
Pages: pages/
Recordings: recordings/
Features: features/
Steps: steps/
```

---

## Command Examples

### Common Workflows

#### New Test Project

```bash
cpa init my-project
cd my-project
cpa record https://example.com/login
cpa ingest recordings/login.spec.js
cpa generate page-objects
cpa run convert
cpa run test
```

#### Debugging Tests

```bash
# Use development profile
cpa --profile dev run test

# Verbose output
cpa run test --verbose

# Run specific scenario
behave features/login.feature:15

# With Playwright inspector
PWDEBUG=1 cpa run test
```

#### CI/CD Pipeline

```bash
# Use CI profile
cpa --profile ci run test

# Export JUnit for CI
cpa report --format junit --output reports/junit/

# Check health
cpa doctor
```

#### Parallel Execution

```bash
# Run 4 tests in parallel
cpa run test --parallel 4

# Or use test profile
cpa --profile test run test
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Test failures |
| 3 | Configuration error |
| 4 | File not found |
| 5 | Validation error |

**Example:**

```bash
cpa run test
if [ $? -eq 0 ]; then
  echo "Tests passed!"
else
  echo "Tests failed with code $?"
fi
```

---

## Environment Variables

The framework respects these environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `CPA_PROFILE` | Default profile | `dev` |
| `CPA_CONFIG` | Config file path | `/path/to/config.yaml` |
| `CPA_BASE_URL` | Base URL | `https://example.com` |
| `CPA_BROWSER__HEADLESS` | Headless mode | `false` |
| `CPA_EXECUTION__PARALLEL_WORKERS` | Parallel workers | `4` |
| `GLM_API_KEY` | GLM API key | `your-key` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `your-key` |
| `OPENAI_API_KEY` | OpenAI API key | `your-key` |

---

## Tips and Tricks

### 1. Aliases

Create bash aliases for common commands:

```bash
# Add to ~/.bashrc or ~/.zshrc
alias cpa-test='cpa run test'
alias cpa-dev='cpa --profile dev run test'
alias cpa-record='cpa record'
```

### 2. Shell Completion

Enable tab completion:

```bash
# For bash
echo 'eval "$(_CPA_COMPLETE=bash_source cpa)"' >> ~/.bashrc

# For zsh
echo 'eval "$(_CPA_COMPLETE=zsh_source cpa)"' >> ~/.zshrc
```

### 3. Pipe to Grep

Filter output:

```bash
cpa run test --verbose | grep "PASSED"
```

### 4. Save Output

Save command output to file:

```bash
cpa run test > test-output.log 2>&1
```

### 5. Run in Background

Run tests in background:

```bash
cpa run test &
```

---

## Getting Help

### Command Help

Get help for any command:

```bash
cpa --help
cpa init --help
cpa run test --help
```

### Version Info

Show version:

```bash
cpa --version
```

### Debug Mode

Enable debug logging:

```bash
CPA_LOGGING__LEVEL=DEBUG cpa run test
```

---

**For more information:**
- [Quick Start Guide](quick_start.md)
- [User Guide](user_guide.md)
- [Configuration Guide](../config/README.md)
