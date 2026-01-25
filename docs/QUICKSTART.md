# Quick Start Guide

Get up and running with AI Playwright Framework in 5 minutes.

## Prerequisites

- Python 3.10 or higher
- Node.js 16 or higher
- Git

## Installation

```bash
# Clone the repository
git clone https://github.com/ksmuvva/ai-playwright-framework.git
cd ai-playwright-framework

# Install Python dependencies
pip install -e .

# Install Playwright browsers
playwright install
```

## Your First Test in 3 Steps

### Step 1: Record Your Test

```bash
# Start Playwright codegen
playwright codegen https://demo.playwright.dev --target=python
```

Perform these actions in the browser:
1. Click on "Get Started"
2. Fill in a search term
3. Click search

Save the recording as `recordings/demo.spec.js`

### Step 2: Convert to BDD

```bash
# Import the recording
cpa ingest recordings/demo.spec.js

# Convert to Gherkin scenarios
cpa run convert
```

### Step 3: Run Your Test

```bash
# Run the BDD scenarios
behave features/
```

That's it! Your first AI-generated test is running.

## Next Steps

- Read [COMMANDS.md](COMMANDS.md) for all CLI commands
- Read [CONFIG.md](CONFIG.md) for configuration options
- Read [EXAMPLES.md](EXAMPLES.md) for more examples
