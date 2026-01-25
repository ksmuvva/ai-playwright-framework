# Troubleshooting Guide

Solutions to common issues.

## Installation Issues

### "pip install fails with Python version error"

**Problem:** Python version too old

**Solution:**
```bash
# Check Python version
python --version

# Must be 3.10 or higher
# Upgrade Python or use virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

### "playwright install fails"

**Problem:** Playwright browsers not downloading

**Solution:**
```bash
# Install system dependencies first
# Ubuntu/Debian:
sudo apt-get install libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups6 libdrm2 libdbus-1-3 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2

# Then install Playwright
playwright install --with-deps
```

## Recording Issues

### "cpa ingest fails with parsing error"

**Problem:** Recording format not supported

**Solution:**
```bash
# Ensure recording is from Playwright codegen
playwright codegen https://example.com --target=python

# Check file exists
ls -la recordings/

# Verify format
head -20 recordings/your-recording.spec.js
```

### "Actions not being detected"

**Problem:** Recording too fast or elements not visible

**Solution:**
```bash
# Add waits in recording
await page.waitForSelector('#element')
await page.click('#element')

# Or increase timeout
export CPA_DEFAULT_TIMEOUT=10000
```

## BDD Conversion Issues

### "Gherkin syntax errors"

**Problem:** Generated scenarios have syntax issues

**Solution:**
```bash
# Validate Gherkin
behave --features features/ --dry-run

# Fix common issues:
# - Remove special characters from scenario names
# - Ensure proper indentation (2 spaces)
# - Check quotes are balanced
```

### "Step definitions not found"

**Problem:** Behave can't find step implementations

**Solution:**
```bash
# Ensure steps directory exists
mkdir -p steps/

# Add steps/__init__.py
touch steps/__init__.py

# Regenerate steps
cpa run convert --force
```

## Execution Issues

### "Tests timeout"

**Problem:** Tests failing with timeout errors

**Solution:**
```yaml
# config/default/config.yaml
framework:
  default_timeout: 60000  # Increase to 60 seconds

# Or per test
@timeout(120)
Scenario: Slow scenario
  Given I am on page
```

### "Selector not found"

**Problem:** Elements can't be located

**Solution:**
```bash
# Enable self-healing
# config/default/config.yaml
execution:
  self_healing: true

# Or use more robust selectors
await page.click('button:has-text("Submit")')  # Text-based
await page.click('[data-testid="submit"]')     # Test ID
```

### "Parallel execution fails"

**Problem:** Tests fail when run in parallel

**Solution:**
```bash
# Reduce parallel workers
cpa run test --parallel 1

# Or fix race conditions
# - Use unique test data
# - Avoid shared state
# - Add proper cleanup
```

## API Key Issues

### "GLM API returns 401 Unauthorized"

**Problem:** Invalid or missing API key

**Solution:**
```bash
# Set API key
export GLM_API_KEY=your-key-here

# Or add to .env file
echo "GLM_API_KEY=your-key-here" > .env

# Verify key
curl -H "Authorization: Bearer $GLM_API_KEY" https://api.z.ai/api/paas/v4/models
```

### "OpenAI API quota exceeded"

**Problem:** API rate limit hit

**Solution:**
```bash
# Switch to GLM (more generous quota)
cpa configure set ai.provider glm
cpa configure set ai.model glm-4.7

# Or add caching
execution:
  cache_enabled: true
```

## Report Issues

### "Report files not generated"

**Problem:** No HTML report created

**Solution:**
```bash
# Ensure reports directory exists
mkdir -p reports/

# Check permissions
chmod 755 reports/

# Generate manually
cpa report --format html
```

## Performance Issues

### "Tests running slow"

**Problem:** Tests taking too long

**Solution:**
```yaml
# Enable parallel execution
execution:
  parallel_workers: 4

# Use headless mode
browser:
  headless: true

# Disable video recording (faster)
recording:
  video: false
  trace: false
```

### "Memory usage high"

**Problem:** Tests consuming too much memory

**Solution:**
```yaml
# Limit parallel workers
execution:
  parallel_workers: 2

# Enable context reuse
browser:
  reuse_context: true

# Clear cache between tests
execution:
  clear_cache: true
```

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `Timeout exceeded` | Element not found | Increase timeout or check selector |
| `Node not found` | Wrong selector | Use self-healing or better selector |
| `Test not found` | Wrong feature file path | Check `features/` directory |
| `Step not defined` | Missing step definition | Run `cpa run convert` again |
| `Import error` | Package not installed | Run `pip install -e .` |

## Getting Help

Still stuck?

1. Check [GitHub Issues](https://github.com/ksmuvva/ai-playwright-framework/issues)
2. Start a [Discussion](https://github.com/ksmuvva/ai-playwright-framework/discussions)
3. Enable debug logging:
   ```bash
   export CPA_LOG_LEVEL=DEBUG
   cpa run test
   ```
4. Check logs in `logs/` directory
