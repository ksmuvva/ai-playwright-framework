# API Design Document

## CLI API Design

### Main CLI Structure

```bash
# Main entry point
claude-playwright [COMMAND] [OPTIONS]

# Or shorter
cpa [COMMAND] [OPTIONS]
```

---

### Global Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--config` | `-c` | Path to config file | `~/.cpa/config.yaml` |
| `--verbose` | `-v` | Enable verbose output | `false` |
| `--quiet` | `-q` | Suppress non-error output | `false` |
| `--no-color` | | Disable colored output | `false` |
| `--version` | `-V` | Show version and exit | - |
| `--help` | `-h` | Show help and exit | - |

---

## Commands

### 1. `init` - Initialize Project

```bash
claude-playwright init [PROJECT_NAME] [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--template` | Template to use (`basic`, `ecommerce`, `saas`) |
| `--framework` | BDD framework (`behave`, `pytest-bdd`) |
| `--browser` | Default browser (`chromium`, `firefox`, `webkit`) |
| `--power-apps` | Enable Power Apps support |

**Example:**
```bash
cpa init my-tests --template ecommerce --framework behave
```

**Creates:**
```
my-tests/
├── .cpa/
│   └── config.yaml
├── features/
│   └── .gitkeep
├── steps/
│   └── .gitkeep
├── page_objects/
│   └── .gitkeep
├── test_data/
│   └── .gitkeep
├── reports/
│   └── .gitkeep
└── README.md
```

---

### 2. `record` - Record Test Actions

```bash
claude-playwright record [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--name` | Recording name |
| `--browser` | Browser to use |
| `--headless` | Run in headless mode |
| `--url` | Starting URL |
| `--save` | Save location |

**Example:**
```bash
cpa record --name login-flow --url https://example.com/login
```

**Interactive Mode:**
- Opens browser with CDP (Chrome DevTools Protocol)
- Records all user actions
- Auto-generates BDD scenarios on completion

---

### 3. `generate` - Generate Tests from Recording

```bash
claude-playwright generate [RECORDING] [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--output` | Output directory |
| `--format` | Output format (`bdd`, `python`) |
| `--include-screenshots` | Include screenshots in steps |
| `--smart-waits` | Add AI-generated wait strategies |

**Example:**
```bash
cpa generate recordings/login-flow.json --output features/
```

---

### 4. `run` - Execute Tests

```bash
claude-playwright run [OPTIONS] [FILTERS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--tags` | Run scenarios by tag (`@smoke`, `@regression`) |
| `--feature` | Run specific feature file |
| `--browser` | Browser to use |
| `--headless` | Run in headless mode |
| `--parallel` | Parallel execution count |
| `--self-heal` | Enable self-healing locators |
| `--report` | Report format (`html`, `json`, `junit`) |

**Examples:**
```bash
# Run all tests
cpa run

# Run only smoke tests
cpa run --tags @smoke

# Run specific feature with self-healing
cpa run --features features/login.feature --self-heal

# Run in parallel
cpa run --parallel 4
```

---

### 5. `debug` - Debug Test Failures

```bash
claude-playwright debug [TEST] [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--interactive` | Interactive debug mode |
| `--ai-analysis` | Enable AI root cause analysis |
| `--fix` | Auto-fix if possible |

**Example:**
```bash
cpa debug features/login.feature:15 --ai-analysis --fix
```

**Interactive Mode:**
```
[CPA Debug] Test failed: "Element not found"
? What would you like to do?
  1) View AI analysis
  2) Replay with screenshots
  3) Try self-healed locator
  4) Edit test
  5) Apply suggested fix
  6) Skip
> 1
```

---

### 6. `report` - Generate Reports

```bash
claude-playwright report [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--source` | Test results JSON |
| `--output` | Report output path |
| `--format` | Report format |
| `--include-ai` | Include AI insights |
| `--compare` | Compare with previous run |

**Example:**
```bash
cpa report --source results/test-run.json --format html --include-ai
```

---

### 7. `license` - License Management

```bash
claude-playwright license <SUBCOMMAND> [OPTIONS]
```

**Subcommands:**
- `activate <KEY>` - Activate license
- `deactivate` - Deactivate license
- `status` - Show license status
- `refresh` - Refresh license from server
- `info` - Show license details

**Examples:**
```bash
cpa license activate ABCD-1234-EFGH-5678
cpa license status
cpa license info
```

---

### 8. `config` - Configuration Management

```bash
claude-playwright config <SUBCOMMAND> [OPTIONS]
```

**Subcommands:**
- `set <KEY> <VALUE>` - Set config value
- `get <KEY>` - Get config value
- `list` - List all config
- `edit` - Open config in editor

**Examples:**
```bash
cpa config set default.browser firefox
cpa config get default.browser
cpa config edit
```

---

## Agent API Design

### TestAgent Class

```python
from claude_playwright_agent.agents import TestAgent
from claude_playwright_agent.config import AgentConfig

class TestAgent:
    """Main agent for test generation and execution"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.client = None
        self.mcp_servers = {}

    async def initialize(self):
        """Initialize Claude SDK client with tools"""
        pass

    async def generate_tests(
        self,
        source: str,
        source_type: Literal["recording", "requirements", "video"],
        output_format: Literal["bdd", "python"] = "bdd"
    ) -> TestGenerationResult:
        """Generate tests from source"""
        pass

    async def analyze_recording(self, recording_data: dict) -> RecordingAnalysis:
        """Analyze recording and suggest improvements"""
        pass

    async def heal_locator(
        self,
        failed_locator: str,
        page_state: dict
    ) -> HealedLocator:
        """Heal a failed locator"""
        pass
```

---

### DebugAgent Class

```python
class DebugAgent:
    """Agent for debugging test failures"""

    async def analyze_failure(
        self,
        test_name: str,
        error: Exception,
        context: dict
    ) -> FailureAnalysis:
        """Analyze a test failure"""
        pass

    async def suggest_fix(
        self,
        failure_analysis: FailureAnalysis
    ) -> FixSuggestion:
        """Suggest fix for failure"""
        pass

    async def apply_fix(
        self,
        test_file: str,
        fix: FixSuggestion
    ) -> bool:
        """Apply suggested fix"""
        pass
```

---

### ReportAgent Class

```python
class ReportAgent:
    """Agent for generating intelligent reports"""

    async def analyze_results(
        self,
        results_path: str
    ) -> ResultsAnalysis:
        """Analyze test results with AI"""
        pass

    async def generate_executive_summary(
        self,
        analysis: ResultsAnalysis,
        format: Literal["markdown", "html"] = "markdown"
    ) -> str:
        """Generate business-friendly summary"""
        pass

    async def cluster_failures(
        self,
        results: TestResults
    ) -> List[FailureCluster]:
        """Cluster similar failures"""
        pass
```

---

## Configuration API

### Config File Structure

```yaml
# ~/.cpa/config.yaml or project/.cpa/config.yaml

version: "1.0"

# License settings
license:
  key: "${CPA_LICENSE_KEY}"  # Environment variable
  server: "https://license.claudeplaywright.ai"
  offline_grace_period_days: 30

# Default settings
defaults:
  browser: chromium
  headless: true
  parallel: 4
  timeout: 30000

# BDD framework settings
framework:
  name: behave
  step_implementation: playwright
  page_objects: true

# AI settings
ai:
  model: claude-3-5-sonnet-20241022
  max_tokens: 4096
  temperature: 0.3
  enable_caching: true
  enable_streaming: true

# Self-healing settings
self_healing:
  enabled: true
  max_attempts: 3
  confidence_threshold: 0.8

# Reporting settings
reporting:
  formats: [html, json]
  include_screenshots: true
  include_videos: false
  include_ai_insights: true

# Power Apps settings
power_apps:
  enabled: false
  credentials_ref: null

# Telemetry
telemetry:
  enabled: true
  endpoint: "https://telemetry.claudeplaywright.ai"
```

---

## Python SDK API

For programmatic access:

```python
from claude_playwright_agent import CPA

# Initialize
agent = CPA(config_path="path/to/config.yaml")

# Generate tests
result = await agent.generate_tests(
    source="recording.json",
    source_type="recording"
)

# Run tests
results = await agent.run_tests(
    tags=["@smoke"],
    self_heal=True
)

# Debug failures
analysis = await agent.debug_failure(
    test="features/login.feature:15"
)

# Generate report
report = await agent.generate_report(
    results=results,
    format="html"
)
```

---

## REST API (Optional Enterprise Feature)

### Endpoints

```
POST   /api/v1/tests/generate     Generate tests
POST   /api/v1/tests/run          Run tests
POST   /api/v1/tests/debug        Debug test
GET    /api/v1/tests/{id}         Get test details
POST   /api/v1/reports/generate   Generate report
GET    /api/v1/license/status     License status
GET    /api/v1/health             Health check
```

### Authentication

```python
# API Key in header
Authorization: Bearer <api_key>

# Or JWT token
Authorization: JWT <token>
```

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| **[AGENT_ARCHITECTURE.md](AGENT_ARCHITECTURE.md)** | Complete Orchestrator + Specialist Agent architecture |
| **[SYSTEM_DESIGN.md](SYSTEM_DESIGN.md)** | System architecture and data flow |
| **[STATE_SCHEMA.md](STATE_SCHEMA.md)** | State management schema |
| **[SKILL_DEV_GUIDE.md](SKILL_DEV_GUIDE.md)** | Guide for developing custom skills |
| **[SDK_MAPPING.md](SDK_MAPPING.md)** | Claude Agent SDK Python implementation mapping |
| **[EXAMPLES.md](EXAMPLES.md)** | Development examples and workflows |

---

**Version:** 1.1
**Last Updated:** 2025-01-11
