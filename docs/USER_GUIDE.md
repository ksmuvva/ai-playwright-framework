# AI Playwright Framework - User Guide

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Core Concepts](#core-concepts)
4. [Common Workflows](#common-workflows)
5. [Advanced Features](#advanced-features)
6. [CI/CD Integration](#cicd-integration)
7. [Troubleshooting](#troubleshooting)

---

## Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git

### Install from Source

```bash
# Clone the repository
git clone https://github.com/ksmuvva/ai-playwright-framework.git
cd ai-playwright-framework

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
npx playwright install
```

### Docker Installation

```bash
# Build Docker image
docker build -t ai-playwright-framework .

# Run with Docker Compose
docker-compose up -d
```

---

## Quick Start

### 1. Record a Test

```bash
# Launch Playwright codegen
npx playwright codegen https://example.com

# Perform your test flow manually
# Save the recording to recordings/test.spec.js
```

### 2. Convert to BDD

```bash
# Ingest the recording
cpa ingest recordings/test.spec.js

# Convert to BDD
cpa bdd-convert

# Generate step definitions
cpa generate-steps features/test.feature
```

### 3. Run Tests

```bash
# Discover tests
cpa test discover

# Run all tests
cpa test run features/

# Run with specific tags
cpa test run features/ --tags smoke

# Run in parallel
cpa test run features/ --parallel --workers 4
```

### 4. View Results

```bash
# Generate HTML report
python -c "
from reports.generator import ReportGenerator
from pathlib import Path

generator = ReportGenerator()
generator.generate_report(
    test_results=[],
    metadata={'project': 'My Project'},
    report_path=Path('reports/report.html')
)
"

# Open in browser
open reports/report.html  # macOS
xdg-open reports/report.html  # Linux
start reports/report.html  # Windows
```

---

## Core Concepts

### Agents

The framework uses a multi-agent architecture:

- **IngestionAgent**: Parses Playwright recordings
- **DeduplicationAgent**: Removes duplicate test cases
- **BDDConversionAgent**: Converts to BDD scenarios
- **ExecutionAgent**: Runs tests
- **AnalysisAgent**: Analyzes results

### Memory System

Agents have 5 types of memory:

1. **Short-term**: Temporary session data
2. **Long-term**: Persistent knowledge
3. **Semantic**: Concepts and patterns
4. **Episodic**: Test execution events
5. **Working**: Current task context

### Self-Healing

The framework automatically heals broken selectors using 9 strategies:

1. Fallback selectors
2. ARIA attributes
3. Data-testid attributes
4. Text content matching
5. Role-based selectors
6. Parent-relative navigation
7. Sibling-relative navigation
8. Partial matching
9. Regex patterns

**Memory Integration**: The framework learns from past healing attempts and applies successful strategies automatically.

---

## Common Workflows

### Workflow 1: Create BDD Tests from Recordings

```bash
# Step 1: Record test
npx playwright codegen https://example.com/login

# Step 2: Ingest recording
cpa ingest recordings/login.spec.js

# Step 3: Deduplicate
cpa dedupe

# Step 4: Convert to BDD
cpa bdd-convert

# Step 5: Generate steps
cpa generate-steps features/login.feature

# Step 6: Run tests
cpa test run features/login.feature
```

### Workflow 2: Memory-Powered Testing

```bash
# Step 1: Run tests and learn
cpa test run features/

# Step 2: Query memory for patterns
cpa memory query "failed" --limit 10

# Step 3: Check statistics
cpa memory stats

# Step 4: Export memory for backup
cpa memory export backup.json

# Step 5: Consolidate short-term to long-term
cpa memory consolidate
```

### Workflow 3: Flaky Test Detection

```bash
# Step 1: Run tests multiple times
for i in {1..5}; do
    cpa test run features/
done

# Step 2: Analyze trends
cpa memory query "selector_healing"

# Step 3: Check healing analytics
python -c "
from src.claude_playwright_agent.self_healing import HealingAnalytics
analytics = HealingAnalytics()
stats = analytics.get_overall_stats()
print('Flaky selectors:', stats['failing_selectors'][:10])
"
```

---

## Advanced Features

### Custom Page Objects

```python
# pages/login_page.py
from pages.base_page import BasePage

class LoginPage(BasePage):
    def __init__(self, page, base_url, state_manager=None):
        super().__init__(page, base_url, state_manager)
        self.username_input = "#username"
        self.password_input = "#password"
        self.login_button = "button[type='submit']"

    def navigate(self):
        self.page.goto(f"{self.base_url}/login")

    def enter_username(self, username):
        self.fill(self.username_input, username)

    def enter_password(self, password):
        self.fill(self.password_input, password)

    def click_login(self):
        self.click(self.login_button)
```

### Custom Agents

```python
from src.claude_playwright_agent.agents.base import BaseAgent

class MyCustomAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            system_prompt="You are a custom test agent.",
            enable_memory=True,
        )

    async def process(self, input_data):
        # Remember input
        await self.remember(
            key="input",
            value=input_data,
            memory_type="working",
        )

        # Process data
        result = {"status": "processed"}

        # Remember result
        await self.remember(
            key="result",
            value=result,
            memory_type="episodic",
            tags=["processed"],
        )

        return result
```

### Multi-Agent Workflows

```python
from src.claude_playwright_agent.agents.orchestrator import OrchestratorAgent

orchestrator = OrchestratorAgent()
await orchestrator.initialize()

# Run BDD conversion workflow
result = await orchestrator.run_workflow(
    workflow_type="bdd_conversion",
    input_data={
        "recording_file": "test.spec.js",
        "output_dir": "features/",
    },
)

print(result)
```

---

## CI/CD Integration

### GitHub Actions

The framework includes a pre-configured GitHub Actions workflow:

```yaml
# .github/workflows/test.yml
on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          cpa test run features/ --parallel --workers 4
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any

    stages {
        stage('Test') {
            steps {
                sh 'cpa test run features/ --parallel'
            }
        }
        stage('Report') {
            steps {
                sh 'cpa memory stats'
                archiveArtifacts artifacts: 'reports/**'
            }
        }
    }
}
```

### Docker Integration

```bash
# Build image
docker build -t my-tests .

# Run tests
docker run --rm -v $(pwd)/reports:/app/reports my-tests

# Compose
docker-compose up
```

---

## Troubleshooting

### Issue: Tests fail with "Selector not found"

**Solution**: Enable self-healing

```python
from pages.base_page import BasePage

page = BasePage(
    page=browser_page,
    base_url="https://example.com",
    enable_self_healing=True,  # Enable this!
)
```

### Issue: Tests are slow

**Solution**: Enable parallel execution

```bash
cpa test run features/ --parallel --workers 4
```

### Issue: Memory database errors

**Solution**: Check directory permissions

```bash
mkdir -p .cpa
chmod 755 .cpa
cpa memory stats
```

### Issue: Agents not communicating

**Solution**: Check agent lifecycle

```python
from src.claude_playwright_agent.agents.lifecycle import AgentLifecycleManager

lifecycle = AgentLifecycleManager()

# Ensure agents are properly spawned
agent = await lifecycle.spawn_agent("ingestion", {})

# Check status
status = lifecycle.get_agent_status(agent.agent_id)
print(f"Agent status: {status}")

# Cleanup when done
await lifecycle.stop_agent(agent.agent_id)
```

### Enable Debug Logging

```bash
# Set environment variable
export CPA_LOG_LEVEL=DEBUG

# Run with debug output
cpa --verbose test run features/

# Check logs
tail -f logs/claude-playwright.log
```

---

## Best Practices

### 1. Test Organization

```
project/
├── features/           # BDD feature files
├── steps/              # Step definitions
├── pages/              # Page objects
├── recordings/         # Playwright recordings
├── reports/            # Test reports
└── tests/              # Unit tests
```

### 2. Memory Management

```bash
# Regularly consolidate memory
cpa memory consolidate

# Export memory periodically
cpa memory export "backup-$(date +%Y%m%d).json"

# Clear expired memories
cpa memory clear
```

### 3. Self-Healing Configuration

```python
# pages/base_page.py
from src.claude_playwright_agent.self_healing import HealingConfig

config = HealingConfig(
    enabled=True,
    max_attempts=3,
    auto_apply_threshold=0.8,
)

page = BasePage(
    page=browser_page,
    base_url="https://example.com",
    healing_config=config,
)
```

### 4. Parallel Execution

```bash
# Determine optimal worker count
WORKERS=$(python -c "import os; print(os.cpu_count())")

# Run with optimal workers
cpa test run features/ --parallel --workers $WORKERS
```

### 5. Test Tags

```gherkin
@smoke @happy-path
Feature: Login

  @smoke
  Scenario: Successful login
    Given I am on the login page
    When I enter valid credentials
    Then I should be logged in

  @regression @negative
  Scenario: Invalid login
    Given I am on the login page
    When I enter invalid credentials
    Then I should see an error
```

```bash
# Run only smoke tests
cpa test run features/ --tags smoke

# Exclude slow tests
cpa test run features/ --tags "~slow"
```

---

## Additional Resources

- [Architecture Documentation](ARCHITECTURE.md)
- [API Reference](API.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [GitHub Repository](https://github.com/ksmuvva/ai-playwright-framework)

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/ksmuvva/ai-playwright-framework/issues
- Documentation: https://github.com/ksmuvva/ai-playwright-framework/wiki
- Email: support@example.com
