# Troubleshooting Guide

Common issues and solutions for Claude Playwright Agent.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Configuration Issues](#configuration-issues)
3. [Recording Issues](#recording-issues)
4. [Execution Issues](#execution-issues)
5. [AI/LLM Issues](#aillm-issues)
6. [Browser Issues](#browser-issues)
7. [Performance Issues](#performance-issues)

---

## Installation Issues

### `cpa: command not found`

**Problem:** The `cpa` command is not recognized after installation.

**Solutions:**

1. **Verify installation:**
   ```bash
   pip show claude-playwright-agent
   ```

2. **Check pip install location:**
   ```bash
   pip install -e .
   export PATH="$PATH:$(python -m site.USER_BASE)/bin"
   ```

3. **Reinstall:**
   ```bash
   pip uninstall claude-playwright-agent
   pip install claude-playwright-agent
   ```

---

### Python version not supported

**Problem:** "Python version 3.x not supported. Requires Python 3.10+"

**Solution:**
```bash
# Check Python version
python --version

# Install Python 3.10+ from https://python.org
```

---

### Playwright browser not found

**Problem:** "Browser not found. Please run `playwright install`"

**Solution:**
```bash
# Install all browsers
playwright install --with-deps

# Install specific browser
playwright install chromium
playwright install firefox
playwright install webkit
```

---

## Configuration Issues

### API key not found

**Problem:** "API key not configured. Set GLM_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY"

**Solutions:**

1. **Set environment variable:**
   ```bash
   export GLM_API_KEY=your-api-key
   ```

2. **Create .env file:**
   ```bash
   echo "GLM_API_KEY=your-api-key" > .env
   ```

3. **Verify configuration:**
   ```bash
   cpa doctor
   ```

---

### Configuration file not valid

**Problem:** "Configuration validation failed"

**Solutions:**

1. **Check YAML syntax:**
   ```bash
   pip install pyyaml
   python -c "import yaml; yaml.safe_load(open('config/default/config.yaml'))"
   ```

2. **Use default config:**
   ```bash
   cpa init --force
   ```

3. **Validate config:**
   ```bash
   cpa config validate
   ```

---

## Recording Issues

### Recording file not found

**Problem:** "Recording file not found: path/to/recording.spec.js"

**Solutions:**

1. **Check file path:**
   ```bash
   ls -la recordings/
   ```

2. **Use absolute path:**
   ```bash
   cpa ingest /full/path/to/recording.spec.js
   ```

3. **Check file extension:**
   - Supported: `.spec.js`, `.spec.json`, `.json`

---

### Invalid recording format

**Problem:** "Invalid recording format. Expected Playwright codegen output"

**Solutions:**

1. **Use Playwright codegen:**
   ```bash
   playwright codegen https://example.com --target=python -o recordings/test.spec.js
   ```

2. **Check JSON structure:**
   ```bash
   cat recordings/test.json | python -m json.tool
   ```

3. **Use supported format:**
   ```json
   {
     "actions": [
       {"type": "goto", "url": "https://example.com"},
       {"type": "click", "selector": "#submit"},
       {"type": "fill", "selector": "#email", "value": "test@test.com"}
     ]
   }
   ```

---

## Execution Issues

### Tests failing with timeout

**Problem:** Tests fail with "Timeout exceeded" or "Element not found"

**Solutions:**

1. **Increase timeout:**
   ```yaml
   # config/default/config.yaml
   framework:
     default_timeout: 60000  # 60 seconds
   ```

2. **Use self-healing:**
   ```yaml
   execution:
     self_healing: true
   ```

3. **Debug with Playwright Inspector:**
   ```bash
   PWDEBUG=1 cpa run test
   ```

4. **Check element selectors:**
   ```bash
   # Use Playwright to find correct selector
   playwright codegen --inspector https://example.com
   ```

---

### No tests found

**Problem:** "No tests found in features/"

**Solutions:**

1. **Check feature file syntax:**
   ```gherkin
   Feature: Login
     Scenario: Successful login
       Given I am on the login page
   ```

2. **Verify file location:**
   ```bash
   ls features/
   ```

3. **Check behave installation:**
   ```bash
   behave --version
   ```

---

### Parallel execution not working

**Problem:** Tests run sequentially despite `--parallel` flag

**Solutions:**

1. **Install pytest-xdist:**
   ```bash
   pip install pytest-xdist
   ```

2. **Check test isolation:**
   - Ensure tests don't share state
   - Use unique test data

3. **Configure workers:**
   ```bash
   cpa run test --parallel 4
   ```

---

## AI/LLM Issues

### AI generation fails

**Problem:** "AI generation failed" or empty output

**Solutions:**

1. **Check API key:**
   ```bash
   cpa provider test
   ```

2. **Check API availability:**
   ```bash
   curl -H "Authorization: Bearer $GLM_API_KEY" https://api.openbigmodel.cn/api/paas/v4/models
   ```

3. **Reduce max_tokens:**
   ```yaml
   ai:
     max_tokens: 4096
   ```

4. **Check model availability:**
   ```yaml
   ai:
     model: glm-4  # Use stable model
   ```

---

### Poor AI suggestions

**Problem:** AI generates low-quality or incorrect selectors

**Solutions:**

1. **Provide more context:**
   ```bash
   cpa ingest recordings/test.spec.js --verbose
   ```

2. **Adjust temperature:**
   ```yaml
   ai:
     temperature: 0.1  # More deterministic
   ```

3. **Use specific selectors:**
   - Add `data-testid` attributes
   - Use semantic HTML

---

## Browser Issues

### Browser launch fails

**Problem:** "Failed to launch browser" or "Browser crashed"

**Solutions:**

1. **Install browser dependencies:**
   ```bash
   playwright install --with-deps
   ```

2. **Use headless mode:**
   ```yaml
   browser:
     headless: true
   ```

3. **Check system resources:**
   ```bash
   free -m  # Check memory
   ```

4. **Try different browser:**
   ```bash
   cpa run test --browser firefox
   ```

---

### Headless mode not working

**Problem:** Browser opens in headed mode instead of headless

**Solutions:**

1. **Check configuration:**
   ```yaml
   browser:
     headless: true
   ```

2. **Use CLI flag:**
   ```bash
   cpa run test --headless
   ```

3. **Check profile:**
   ```bash
   cpa configure profile test  # test profile uses headless
   ```

---

### Browser context issues

**Problem:** "Failed to create browser context" or cookies not persisting

**Solutions:**

1. **Clear browser data:**
   ```bash
   rm -rf ~/.cache/ms-playwright/
   ```

2. **Increase timeout:**
   ```yaml
   browser:
     launch_timeout: 60000
   ```

3. **Disable hardware acceleration:**
   ```yaml
   browser:
     args: ["--disable-gpu"]
   ```

---

## Performance Issues

### Tests running slowly

**Problem:** Test execution takes too long

**Solutions:**

1. **Use parallel execution:**
   ```bash
   cpa run test --parallel 4
   ```

2. **Reduce wait times:**
   ```yaml
   framework:
     default_timeout: 10000
   ```

3. **Use headed mode for debugging only:**
   ```bash
   cpa --profile dev run test
   ```

4. **Optimize selectors:**
   - Use ID selectors
   - Avoid nth-child
   - Use semantic selectors

---

### High memory usage

**Problem:** Tests consume too much memory

**Solutions:**

1. **Limit parallel workers:**
   ```bash
   cpa run test --parallel 2
   ```

2. **Clear screenshots:**
   ```bash
   cpa clean screenshots
   ```

3. **Disable video recording:**
   ```yaml
   browser:
     videos: false
   ```

---

### Report generation slow

**Problem:** HTML report takes too long to generate

**Solutions:**

1. **Limit report data:**
   ```bash
   cpa report --limit 100
   ```

2. **Use JSON format:**
   ```bash
   cpa report --format json > report.json
   ```

3. **Clear old reports:**
   ```bash
   cpa clean reports --keep 5
   ```

---

## Getting Help

### Debug Mode

Enable debug logging for detailed information:

```bash
CPA_LOGGING__LEVEL=DEBUG cpa run test
```

### Doctor Command

Run diagnostics to identify issues:

```bash
cpa doctor
```

### Verbose Output

Get detailed command output:

```bash
cpa --verbose run test
cpa ingest recordings/test.spec.js --verbose
```

### Get Support

- **Check logs:** `logs/` directory
- **GitHub Issues:** https://github.com/anthropics/claude-playwright-agent/issues
- **Documentation:** [docs/](docs/)
- **Discussions:** https://github.com/anthropics/claude-playwright-agent/discussions

---

## Common Error Messages

| Error Message | Solution |
|--------------|----------|
| "Element not found" | Use self-healing, check selectors |
| "Timeout exceeded" | Increase timeout, check page load |
| "API key not found" | Set GLM_API_KEY environment variable |
| "Browser not found" | Run `playwright install` |
| "Configuration invalid" | Validate YAML syntax |
| "No tests found" | Check feature file syntax |
| "Recording format invalid" | Use Playwright codegen output |
| "Parallel execution failed" | Install pytest-xdist |
| "AI generation failed" | Check API key and model |
| "Memory error" | Reduce parallel workers |
