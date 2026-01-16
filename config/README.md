# Configuration Guide

Complete guide to configuring the Claude Playwright Agent framework.

## Table of Contents

1. [Configuration Structure](#configuration-structure)
2. [Quick Start](#quick-start)
3. [Configuration Files](#configuration-files)
4. [Configuration Sections](#configuration-sections)
5. [Profiles](#profiles)
6. [Environment Variables](#environment-variables)
7. [Examples](#examples)

---

## Configuration Structure

The framework uses a hierarchical configuration system:

```
project-root/
├── config/
│   ├── default/
│   │   ├── config.yaml      # Main configuration file
│   │   ├── pytest.ini       # Pytest configuration
│   │   └── behave.ini       # Behave configuration
│   └── profiles/
│       ├── dev.yaml         # Development profile
│       ├── test.yaml        # Test profile
│       ├── prod.yaml        # Production profile
│       └── ci.yaml          # CI/CD profile
└── .cpa/
    └── state.json           # Runtime state
```

---

## Quick Start

### 1. Using Default Configuration

The framework works out of the box with default settings:

```bash
cpa init my-project
cd my-project
cpa run test
```

### 2. Using a Profile

```bash
# Use development profile (headless=false, devtools=true)
cpa --profile dev run test

# Use CI profile (parallel execution, JUnit reports)
cpa --profile ci run test
```

### 3. Custom Configuration

Create or edit `config/default/config.yaml`:

```yaml
browser:
  headless: false
  browser: firefox

execution:
  parallel_workers: 4

ai:
  provider: glm
  model: glm-4-plus
```

---

## Configuration Files

### config.yaml

Main configuration file located at `config/default/config.yaml`.

**Location Priority:**
1. Project-specific: `<project>/config/default/config.yaml`
2. User-specific: `~/.cpa/config.yaml`
3. Framework defaults

### pytest.ini

Pytest configuration for pytest-bdd framework.

**Key Settings:**
- Test discovery patterns
- BDD features location
- Coverage options
- Markers
- Logging configuration

### behave.ini

Behave framework configuration.

**Key Settings:**
- Feature files location
- Step definitions directory
- Output format
- JUnit reports
- Logging configuration

---

## Configuration Sections

### Framework

```yaml
framework:
  # BDD framework: behave, pytest-bdd
  bdd_framework: behave

  # Project template: basic, advanced, ecommerce
  template: basic

  # Default timeout for operations (milliseconds)
  default_timeout: 30000
```

### Browser

```yaml
browser:
  # Browser engine: chromium, firefox, webkit
  browser: chromium

  # Run browser in headless mode
  headless: true

  # Enable DevTools for debugging
  devtools: false

  # Slow down operations by specified milliseconds
  slow_mo: 0

  # Browser viewport size
  viewport:
    width: 1280
    height: 720
```

### Execution

```yaml
execution:
  # Number of parallel workers
  parallel_workers: 1

  # Number of times to retry failed tests
  retry_failed: 0

  # Stop execution on first failure
  fail_fast: false

  # Enable self-healing selector recovery
  self_healing: true
```

### AI Configuration

```yaml
ai:
  # LLM Provider: anthropic, openai, glm
  provider: glm

  # Model to use
  model: glm-4-plus

  # Maximum tokens for LLM responses
  max_tokens: 8192

  # Temperature for LLM (0.0 - 1.0)
  temperature: 0.3

  # Enable response caching
  enable_caching: true
```

**Supported Models:**

| Provider | Models |
|----------|--------|
| Anthropic | claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022 |
| OpenAI | gpt-4, gpt-4-turbo, gpt-3.5-turbo |
| GLM | glm-4-plus, glm-4, glm-3-turbo |

### Logging

```yaml
logging:
  # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
  level: INFO

  # Enable console output
  console: true

  # Log file path (relative to project root)
  file: logs/cpa.log

  # Use JSON format for logs
  json_format: false
```

### Recording & Ingestion

```yaml
recording:
  # Input directory for recordings
  input_dir: recordings

  # Automatically generate page objects after ingestion
  generate_page_objects: true

  # Run deduplication after ingestion
  deduplicate_elements: true

  # Minimum usage count for component extraction
  min_usage_for_component: 2
```

### Page Object Generation

```yaml
page_objects:
  # Output directory for generated page objects
  output_dir: pages

  # Base class name for generated page objects
  base_class: BasePage

  # Use async/await in generated code
  use_async: true

  # Include type hints in generated code
  include_type_hints: true

  # Generate separate component classes
  generate_components: true
```

### Self-Healing

```yaml
self_healing:
  # Enable self-healing
  enabled: true

  # Maximum number of healing attempts
  max_attempts: 3

  # Confidence threshold for accepting healed selector
  confidence_threshold: 0.7

  # Log healing attempts
  log_attempts: true
```

### Reporting

```yaml
reporting:
  # Report format: html, json, junit, all
  format: html

  # Output directory for reports
  output_dir: reports

  # Include screenshots in reports
  include_screenshots: true

  # Include AI-powered analysis in reports
  include_ai_analysis: true

  # Report retention (days)
  retention_days: 30
```

---

## Profiles

Profiles are pre-configured settings for different environments.

### Built-in Profiles

#### Default Profile

**Purpose:** General-purpose configuration

```yaml
browser:
  headless: true
execution:
  parallel_workers: 1
logging:
  level: INFO
```

#### Development Profile (`dev`)

**Purpose:** Local development with debugging

```yaml
browser:
  headless: false
  devtools: true
  slow_mo: 100
logging:
  level: DEBUG
execution:
  fail_fast: true
```

#### Test Profile (`test`)

**Purpose:** Test environment with parallel execution

```yaml
browser:
  headless: true
execution:
  parallel_workers: 4
  retry_failed: 2
logging:
  json_format: true
```

#### Production Profile (`prod`)

**Purpose:** Production runs with minimal overhead

```yaml
browser:
  headless: true
execution:
  parallel_workers: 8
logging:
  level: WARNING
  console: false
reporting:
  format: junit
```

#### CI/CD Profile (`ci`)

**Purpose:** Continuous integration pipelines

```yaml
browser:
  headless: true
execution:
  parallel_workers: 4
  retry_failed: 2
logging:
  json_format: true
reporting:
  format: junit
```

### Using Profiles

```bash
# Command line
cpa --profile dev run test
cpa --profile ci run test

# Environment variable
export CPA_PROFILE=ci
cpa run test
```

### Custom Profiles

Create custom profiles in `config/profiles/`:

```bash
# Create staging profile
cat > config/profiles/staging.yaml << EOF
browser:
  headless: true
execution:
  parallel_workers: 2
logging:
  level: INFO
EOF
```

Use custom profile:

```bash
cpa --profile staging run test
```

---

## Environment Variables

Environment variables override configuration file settings.

### Format

```bash
CPA_SECTION__KEY=value
```

### Examples

```bash
# Override browser settings
export CPA_BROWSER__HEADLESS=false
export CPA_BROWSER__BROWSER=firefox

# Override execution settings
export CPA_EXECUTION__PARALLEL_WORKERS=4
export CPA_EXECUTION__FAIL_FAST=false

# Override AI settings
export CPA_AI__PROVIDER=openai
export CPA_AI__MODEL=gpt-4

# Override logging
export CPA_LOGGING__LEVEL=DEBUG
```

### Complete Example

```bash
# Set environment variables
export CPA_BROWSER__HEADLESS=false
export CPA_EXECUTION__PARALLEL_WORKERS=4
export CPA_LOGGING__LEVEL=DEBUG

# Run tests with overrides
cpa run test
```

### Priority Order

Configuration is applied in this order (later overrides earlier):

1. Framework defaults
2. Profile configuration
3. `config/default/config.yaml`
4. Environment variables

---

## Examples

### Example 1: Development Setup

```yaml
# config/default/config.yaml
browser:
  headless: false
  devtools: true
  slow_mo: 100

logging:
  level: DEBUG
  console: true

execution:
  parallel_workers: 1
  fail_fast: true

self_healing:
  log_attempts: true
  max_attempts: 5
```

### Example 2: CI/CD Pipeline

```yaml
# config/profiles/ci.yaml
browser:
  headless: true

execution:
  parallel_workers: 4
  retry_failed: 2

logging:
  json_format: true

reporting:
  format: junit
  include_screenshots: true
```

```bash
# In CI pipeline
cpa --profile ci run test
```

### Example 3: Local Testing with GLM

```yaml
# config/default/config.yaml
ai:
  provider: glm
  model: glm-4-plus
  max_tokens: 8192
  temperature: 0.3

# Set API key in environment
export GLM_API_KEY=your-api-key
```

### Example 4: Performance Testing

```yaml
# config/default/config.yaml
execution:
  parallel_workers: 8

performance:
  enabled: true
  thresholds:
    page_load: 3000
    api_response: 1000

reporting:
  include_timeline: true
```

### Example 5: Debugging Failed Tests

```yaml
# config/default/config.yaml
browser:
  headless: false
  devtools: true

logging:
  level: DEBUG

self_healing:
  log_attempts: true

reporting:
  include_screenshots: true
  include_timeline: true
  include_ai_analysis: true
```

---

## Troubleshooting

### Configuration Not Loading

**Problem:** Changes to config.yaml not taking effect

**Solutions:**
1. Verify file path: `config/default/config.yaml`
2. Check YAML syntax
3. Clear cache: `rm .cpa/state.json`
4. Enable debug logging: `CPA_LOGGING__LEVEL=DEBUG`

### Profile Not Found

**Problem:** `Invalid profile: xxx`

**Solutions:**
1. Check built-in profiles: default, dev, test, prod, ci
2. Verify custom profile location: `config/profiles/xxx.yaml`
3. Check profile YAML syntax

### Environment Variables Not Working

**Problem:** Environment variables not overriding settings

**Solutions:**
1. Use correct format: `CPA_SECTION__KEY` (double underscore)
2. Check variable name case (uppercase)
3. Verify environment variable is set: `echo $CPA_BROWSER__HEADLESS`

### Configuration Validation Errors

**Problem:** `Configuration validation failed`

**Solutions:**
1. Check data types (string, int, bool)
2. Verify enum values (browser, framework, provider)
3. Check required fields are present
4. Review error message for specific field

---

## Best Practices

1. **Use Version Control:** Commit `config/` directory to git
2. **Environment-Specific:** Use profiles for different environments
3. **Secrets Management:** Use environment variables for API keys
4. **Documentation:** Comment complex configurations
5. **Validation:** Test configuration changes in development first
6. **Backup:** Keep default configurations as reference

---

## Additional Resources

- [Framework Architecture](../FRAMEWORK_ARCHITECTURE.md)
- [CLI Reference](../docs/cli_reference.md)
- [Page Objects Guide](../docs/page_objects.md)
- [Troubleshooting](../docs/troubleshooting.md)
