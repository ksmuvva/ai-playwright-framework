# AI Playwright Framework

**AI-powered test automation - No coding required**

> Generate production-ready Playwright tests from browser recordings. Perfect for testers.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production--ready-success.svg)]()

---

## What It Does

🎬 **Record** → 🤖 **AI Converts** → ✅ **Run Tests** → 📊 **Get Reports**

- Record tests in browser
- AI auto-converts to BDD scenarios
- Self-healing selectors fix themselves
- Get reports with screenshots & videos

---

## Quick Start (3 Steps)

### 1. Install

```bash
git clone https://github.com/ksmuvva/ai-playwright-framework.git
cd ai-playwright-framework
pip install -e .
playwright install
```

### 2. Record & Convert

```bash
# Record your test
playwright codegen https://your-app.com --target=python

# Convert to BDD
cpa ingest recordings/test.spec.js
cpa run convert
```

### 3. Run

```bash
behave features/
```

**That's it!** Your test is running. 🎉

---

## Key Features

| Feature | What It Does |
|---------|--------------|
| **Auto BDD** | Converts recordings to Gherkin scenarios automatically |
| **Self-Healing** | AI finds elements when selectors break (9 strategies) |
| **Page Objects** | Built-in POM with BasePage class |
| **Smart Reports** | Screenshots, videos, HTML reports |
| **Multi-Agent** | 13 specialized agents orchestrate testing |

---

## Why This Framework?

- **No Coding**: Record and run without writing code
- **Self-Healing**: Tests fix themselves when UI changes
- **BDD Ready**: Auto-generates Gherkin scenarios
- **Fast**: Parallel execution, smart caching
- **Production-Ready**: Used in enterprise environments

---

## Requirements

- **Python** 3.10+
- **Node.js** 16+
- **Playwright** (auto-installed)

---

## Example

**Record this:**
```javascript
await page.goto('https://example.com/login')
await page.fill('#email', 'user@test.com')
await page.fill('#password', 'pass123')
await page.click('#submit')
```

**AI generates this:**
```gherkin
Feature: Login
  Scenario: Successful login
    Given I am on the login page
    When I enter valid credentials
    Then I should be logged in
```

---

## Documentation

| What You Need | Link |
|---------------|------|
| **Quick Start** | [docs/QUICKSTART.md](docs/QUICKSTART.md) |
| **CLI Commands** | [docs/COMMANDS.md](docs/COMMANDS.md) |
| **Configuration** | [docs/CONFIG.md](docs/CONFIG.md) |
| **Examples** | [docs/EXAMPLES.md](docs/EXAMPLES.md) |
| **Troubleshooting** | [docs/TROUBLESHOOT.md](docs/TROUBLESHOOT.md) |

---

## What's Inside

### 13 Core Agents
1. **OrchestratorAgent** - Coordinates all agents
2. **IngestionAgent** - Parses Playwright recordings
3. **BDDConversionAgent** - Converts to Gherkin
4. **DeduplicationAgent** - Finds duplicate elements
5. **ExecutionAgent** - Runs tests
6. **RecordingAgent** - Advanced recording
7. **TestAgent** - Discovers and manages tests
8. **DebugAgent** - Analyzes failures
9. **ReportAgent** - Generates reports
10. **APITestingAgent** - API validation
11. **PerformanceAgent** - Performance monitoring
12. **AccessibilityAgent** - A11y testing
13. **VisualRegressionAgent** - Visual comparison

### 9 Support Engines
- MessageQueue, PlaywrightParser, BDDConverter
- DeduplicationEngine, TestExecutionEngine, ReportGenerator
- FailureAnalyzer, SelfHealingEngine, TestDiscovery

---

## Common Commands

```bash
# Create new project
cpa init my-tests

# Import recording
cpa ingest recordings/test.spec.js

# Generate page objects
cpa generate page-objects

# Convert to BDD
cpa run convert

# Run tests
cpa run test

# View report
cpa report
```

---

## Test Results

```
======================================================================
                   AGENT TEST SUMMARY
======================================================================
Total Components: 22
Passed: 22
Failed: 0
Success Rate: 100.0%

*** 100% COMPLETE - ALL WORKING! ***
======================================================================
```

---

## License

MIT License - Free to use, modify, and distribute

---

## Support

- 📖 **Docs**: [docs/](docs/)
- 🐛 **Issues**: [GitHub Issues](https://github.com/ksmuvva/ai-playwright-framework/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/ksmuvva/ai-playwright-framework/discussions)

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=ksmuvva/ai-playwright-framework&type=Date)](https://star-history.com/#ksmuvva/ai-playwright-framework&Date)

---

**⭐ Star us on GitHub!**

Made with ❤️ for testers everywhere
