# CLI Commands Reference

Complete reference for all `cpa` commands.

## Project Management

### `cpa init <project-name>`
Create a new test project.

```bash
cpa init my-tests
```

### `cpa status`
Show project status and test counts.

### `cpa info`
Display framework information.

## Recording & Import

### `cpa ingest <recording-file>`
Import a Playwright recording.

```bash
cpa ingest recordings/login.spec.js
```

### `cpa list recordings`
List all imported recordings.

## Generation

### `cpa generate page-objects`
Generate Page Objects from recordings.

```bash
cpa generate page-objects
```

### `cpa run convert`
Convert recordings to BDD scenarios.

```bash
cpa run convert
```

### `cpa deduplicate`
Find and deduplicate selectors.

## Test Execution

### `cpa run test`
Run all tests.

```bash
cpa run test
```

### `cpa run test --tags @smoke`
Run tests by tag.

```bash
cpa run test --tags @smoke
```

### `cpa run full`
Run complete pipeline (ingest → convert → test).

## Reporting

### `cpa report`
View the latest test report.

```bash
cpa report
```

### `cpa report --analyze`
View report with AI analysis.

## Configuration

### `cpa configure set <key> <value>`
Set a configuration value.

```bash
cpa configure set timeout 30000
```

### `cpa configure profile <name>`
Switch configuration profile.

```bash
cpa configure profile dev
```

## Help

### `cpa --help`
Show general help.

### `cpa <command> --help`
Show command-specific help.
