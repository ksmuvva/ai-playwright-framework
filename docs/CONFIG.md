# Configuration Guide

Configure the AI Playwright Framework for your needs.

## Configuration File

Configuration is stored in `config/default/config.yaml`:

```yaml
framework:
  bdd_framework: behave      # or pytest-bdd
  default_timeout: 30000     # milliseconds

browser:
  browser: chromium          # chromium, firefox, webkit
  headless: true
  viewport:
    width: 1280
    height: 720

ai:
  provider: glm              # anthropic, openai, glm
  model: glm-4.7
  max_tokens: 8192

execution:
  parallel_workers: 1
  retry_failed: 0
  self_healing: true

page_objects:
  output_dir: pages
  base_class: BasePage
  use_async: true
```

## Profiles

Pre-configured profiles for different environments:

### `dev` - Development
- headless: false
- devtools: true
- logging: DEBUG

### `test` - Test Environment
- parallel_workers: 4
- retry_failed: 2

### `prod` - Production
- parallel_workers: 8
- minimal logging

### `ci` - CI/CD Pipeline
- JUnit reports
- pipeline optimized

## Switching Profiles

```bash
cpa configure profile dev
cpa configure profile test
cpa configure profile prod
cpa configure profile ci
```

## Environment Variables

Set via environment or `.env` file:

```bash
# AI Provider
export CPA_AI__PROVIDER=glm
export GLM_API_KEY=your-key-here

# Browser
export CPA_BROWSER__HEADLESS=false

# Execution
export CPA_EXECUTION__PARALLEL_WORKERS=4
```

## Custom Profiles

Create custom profiles in `config/profiles/`:

```yaml
# config/profiles/custom.yaml
browser:
  headless: false
  viewport:
    width: 1920
    height: 1080

execution:
  parallel_workers: 2
  timeout: 60000
```

Use it:
```bash
cpa configure profile custom
```
