# Technical Architecture - AI Playwright Framework

## 🏛️ System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Tool (TypeScript)                    │
│  ┌────────────┬──────────────┬─────────────┬──────────────┐ │
│  │   Init     │   Record     │  Convert    │   Optimize   │ │
│  │  Command   │   Command    │  Command    │   Command    │ │
│  └────────────┴──────────────┴─────────────┴──────────────┘ │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │      Template Generator Engine        │
        │  ┌─────────────┬──────────────────┐  │
        │  │   Python    │   TypeScript     │  │
        │  │  Templates  │    Templates     │  │
        │  └─────────────┴──────────────────┘  │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │         AI Processing Layer           │
        │  ┌──────────────────────────────────┐ │
        │  │  Recording → BDD Converter       │ │
        │  │  Locator Healer                  │ │
        │  │  Test Data Generator             │ │
        │  │  Wait Strategy Optimizer         │ │
        │  │  Code Pattern Analyzer           │ │
        │  └──────────────────────────────────┘ │
        └───────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────┐
│              Generated Framework (Python/TS)                  │
│  ┌─────────┬────────────┬──────────┬────────────┬──────────┐ │
│  │   BDD   │   Pages    │ Helpers  │    AI      │  Config  │ │
│  │Features │  Objects   │  Utils   │  Modules   │  Files   │ │
│  └─────────┴────────────┴──────────┴────────────┴──────────┘ │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Playwright + Test Runner                   │ │
│  └─────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

---

## 📦 Component Details

### 1. CLI Tool (TypeScript)

#### 1.1 Project Structure
```
cli/
├── src/
│   ├── commands/
│   │   ├── init.ts           # Initialize framework
│   │   ├── record.ts         # Launch Playwright recorder
│   │   ├── convert.ts        # Convert recording to BDD
│   │   ├── optimize.ts       # Optimize existing tests
│   │   └── add-scenario.ts   # Add new scenario
│   ├── generators/
│   │   ├── python-generator.ts    # Python framework generator
│   │   ├── typescript-generator.ts # TS framework generator
│   │   └── template-engine.ts     # Template processing
│   ├── ai/
│   │   ├── ai-client.ts      # AI provider abstraction
│   │   ├── anthropic.ts      # Anthropic integration
│   │   ├── openai.ts         # OpenAI integration
│   │   └── prompts.ts        # System prompts
│   ├── parsers/
│   │   ├── recording-parser.ts    # Parse Playwright recordings
│   │   ├── scenario-analyzer.ts   # Analyze scenarios
│   │   └── locator-extractor.ts   # Extract locators
│   ├── templates/
│   │   ├── python/           # Python framework templates
│   │   └── typescript/       # TypeScript framework templates
│   ├── utils/
│   │   ├── file-utils.ts
│   │   ├── logger.ts
│   │   └── validation.ts
│   ├── types/
│   │   └── index.ts          # TypeScript types
│   └── index.ts              # CLI entry point
├── templates/                # EJS/Handlebars templates
├── package.json
├── tsconfig.json
└── README.md
```

#### 1.2 Key Modules

**init.ts - Framework Initialization**
```typescript
interface InitOptions {
  language: 'python' | 'typescript';
  projectName: string;
  bdd: boolean;
  powerApps: boolean;
  aiProvider: 'anthropic' | 'openai' | 'local';
  directory?: string;
}

async function initializeFramework(options: InitOptions) {
  // 1. Validate options
  // 2. Create directory structure
  // 3. Generate configuration files
  // 4. Install dependencies
  // 5. Generate templates
  // 6. Initialize git
  // 7. Create .env.example
  // 8. Display success message with next steps
}
```

**convert.ts - Recording to BDD Conversion**
```typescript
interface ConversionOptions {
  recordingFile: string;
  scenarioName?: string;
  outputDir?: string;
  generateData: boolean;
}

async function convertRecording(options: ConversionOptions) {
  // 1. Parse recording JSON
  // 2. Send to AI for analysis
  // 3. Generate feature file
  // 4. Generate step definitions
  // 5. Extract locators
  // 6. Generate test data schema
  // 7. Identify reusable patterns
  // 8. Update framework files
}
```

**ai-client.ts - AI Abstraction Layer**
```typescript
interface AIClient {
  generateBDDScenario(recording: PlaywrightRecording): Promise<BDDOutput>;
  healLocator(context: LocatorContext): Promise<LocatorSuggestion>;
  generateTestData(schema: DataSchema): Promise<TestData>;
  optimizeWaits(testLog: TestLog): Promise<WaitRecommendations>;
  analyzePatterns(scenarios: Scenario[]): Promise<PatternAnalysis>;
}

class AnthropicClient implements AIClient { /* ... */ }
class OpenAIClient implements AIClient { /* ... */ }
```

#### 1.3 Template Engine

Uses EJS for dynamic template generation:

```typescript
interface TemplateContext {
  projectName: string;
  language: 'python' | 'typescript';
  features: {
    bdd: boolean;
    powerApps: boolean;
    healing: boolean;
  };
  scenarios: Scenario[];
  helpers: HelperFunction[];
}

function renderTemplate(templateName: string, context: TemplateContext): string {
  const template = ejs.compile(readTemplate(templateName));
  return template(context);
}
```

---

### 2. Python Framework Templates

#### 2.1 Core Files

**helpers/auth_helper.py**
```python
from typing import Optional, Dict
from playwright.sync_api import Page, BrowserContext
import os
from .screenshot_manager import capture_screenshot

class AuthHelper:
    """Reusable authentication helper - executes once per session"""

    _authenticated_context: Optional[BrowserContext] = None

    @staticmethod
    def authenticate(page: Page, username: str, password: str) -> bool:
        """Authenticate user and store session"""
        try:
            # Navigate to login
            page.goto(os.getenv('APP_URL') + '/login')

            # Fill credentials
            page.fill('[data-testid="username"]', username)
            page.fill('[data-testid="password"]', password)

            # Click login
            page.click('[data-testid="login-button"]')

            # Wait for successful login
            page.wait_for_url('**/home', timeout=10000)

            capture_screenshot(page, 'login_success')
            return True

        except Exception as e:
            capture_screenshot(page, 'login_failed')
            raise Exception(f"Authentication failed: {e}")

    @staticmethod
    def is_authenticated(page: Page) -> bool:
        """Check if user is already authenticated"""
        # Check for auth token, session cookie, or UI element
        pass

    @staticmethod
    def get_or_create_authenticated_context(browser, username: str, password: str):
        """Get existing authenticated context or create new one"""
        # Implementation
        pass
```

**helpers/healing_locator.py**
```python
from typing import List, Optional, Dict
from playwright.sync_api import Page, Locator
from anthropic import Anthropic
import json

class HealingLocator:
    """AI-powered self-healing locator finder"""

    def __init__(self, ai_client: Anthropic):
        self.ai_client = ai_client
        self.locator_history: Dict[str, List[str]] = {}

    def find_element(
        self,
        page: Page,
        locator: str,
        description: str = "",
        timeout: int = 5000
    ) -> Optional[Locator]:
        """
        Try to find element with healing capability

        Args:
            page: Playwright page
            locator: Original locator string
            description: Human-readable element description
            timeout: Wait timeout

        Returns:
            Locator if found, None otherwise
        """
        try:
            # Try original locator first
            element = page.locator(locator)
            element.wait_for(timeout=timeout)
            return element

        except Exception as original_error:
            print(f"⚠️  Original locator failed: {locator}")

            # Attempt healing
            healed_locator = self._heal_locator(page, locator, description)

            if healed_locator:
                try:
                    element = page.locator(healed_locator)
                    element.wait_for(timeout=timeout)

                    # Log successful healing
                    self._log_healing(locator, healed_locator)
                    print(f"✅ Healed locator: {healed_locator}")

                    return element
                except:
                    pass

            # If healing failed, raise original error
            raise original_error

    def _heal_locator(self, page: Page, failed_locator: str, description: str) -> Optional[str]:
        """Use AI to find alternative locator"""

        # Get page content
        page_html = page.content()

        # Prepare AI prompt
        prompt = f"""
        The following locator failed to find an element:
        Locator: {failed_locator}
        Description: {description}

        Page HTML (truncated):
        {page_html[:5000]}

        Please suggest alternative locators for this element.
        Return as JSON array of locator strings, ordered by reliability.
        """

        # Call AI
        response = self.ai_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        suggestions = json.loads(response.content[0].text)

        return suggestions[0] if suggestions else None

    def _log_healing(self, original: str, healed: str):
        """Log healing event for later analysis"""
        if original not in self.locator_history:
            self.locator_history[original] = []
        self.locator_history[original].append(healed)

        # Optionally write to file for framework optimization
        with open('locator_healing_log.json', 'w') as f:
            json.dump(self.locator_history, f, indent=2)
```

**helpers/wait_manager.py**
```python
from typing import Callable, Optional, Literal
from playwright.sync_api import Page
import time

WaitState = Literal['visible', 'hidden', 'attached', 'detached']

class WaitManager:
    """AI-optimized wait management"""

    # Learning data structure for wait times
    wait_patterns: Dict[str, Dict] = {}

    @staticmethod
    def smart_wait(
        page: Page,
        locator: str,
        state: WaitState = 'visible',
        timeout: Optional[int] = None
    ):
        """
        Intelligent wait that adapts based on historical data

        Args:
            page: Playwright page
            locator: Element locator
            state: Expected state
            timeout: Max timeout (auto-calculated if None)
        """

        # Calculate optimal timeout based on history
        if timeout is None:
            timeout = WaitManager._calculate_optimal_timeout(locator)

        start_time = time.time()

        try:
            page.locator(locator).wait_for(state=state, timeout=timeout)
            elapsed = time.time() - start_time

            # Record successful wait
            WaitManager._record_wait(locator, elapsed, success=True)

        except Exception as e:
            elapsed = time.time() - start_time
            WaitManager._record_wait(locator, elapsed, success=False)
            raise e

    @staticmethod
    def wait_for_power_apps_load(page: Page):
        """Wait for Power Apps specific loading indicators"""

        # Wait for Power Apps spinner to disappear
        try:
            page.wait_for_selector(
                '.pa-loading-spinner',
                state='hidden',
                timeout=30000
            )
        except:
            pass  # Spinner might not appear

        # Wait for network idle
        page.wait_for_load_state('networkidle')

        # Additional Power Apps specific waits
        page.wait_for_function(
            "() => document.readyState === 'complete'"
        )

    @staticmethod
    def _calculate_optimal_timeout(locator: str) -> int:
        """Calculate timeout based on historical performance"""

        if locator in WaitManager.wait_patterns:
            pattern = WaitManager.wait_patterns[locator]
            avg_time = pattern['avg_time']
            # Add 50% buffer
            return int(avg_time * 1.5 * 1000)  # Convert to ms

        # Default timeout
        return 10000

    @staticmethod
    def _record_wait(locator: str, elapsed: float, success: bool):
        """Record wait performance for optimization"""

        if locator not in WaitManager.wait_patterns:
            WaitManager.wait_patterns[locator] = {
                'times': [],
                'successes': 0,
                'failures': 0,
                'avg_time': 0
            }

        pattern = WaitManager.wait_patterns[locator]
        pattern['times'].append(elapsed)

        if success:
            pattern['successes'] += 1
        else:
            pattern['failures'] += 1

        # Calculate average
        pattern['avg_time'] = sum(pattern['times']) / len(pattern['times'])
```

**helpers/data_generator.py**
```python
from typing import Dict, Any, List
from anthropic import Anthropic
import json
import random
from faker import Faker

class TestDataGenerator:
    """AI-powered test data generation"""

    def __init__(self, ai_client: Anthropic):
        self.ai_client = ai_client
        self.faker = Faker()

    def generate_from_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate test data from field schema

        Args:
            schema: Field definitions with types and constraints

        Returns:
            Generated test data

        Example schema:
        {
            "email": {"type": "email", "required": true},
            "phone": {"type": "phone", "country": "US"},
            "company_name": {"type": "text", "context": "company"}
        }
        """

        data = {}

        for field_name, field_spec in schema.items():
            data[field_name] = self._generate_field_value(field_name, field_spec)

        return data

    def _generate_field_value(self, field_name: str, spec: Dict) -> Any:
        """Generate value for a single field"""

        field_type = spec.get('type', 'text')

        # Use Faker for common types
        generators = {
            'email': lambda: self.faker.email(),
            'phone': lambda: self.faker.phone_number(),
            'name': lambda: self.faker.name(),
            'address': lambda: self.faker.address(),
            'company': lambda: self.faker.company(),
            'url': lambda: self.faker.url(),
            'date': lambda: self.faker.date(),
            'number': lambda: random.randint(1, 1000),
        }

        if field_type in generators:
            return generators[field_type]()

        # Use AI for context-specific generation
        return self._ai_generate_field(field_name, spec)

    def _ai_generate_field(self, field_name: str, spec: Dict) -> str:
        """Use AI to generate contextual field value"""

        prompt = f"""
        Generate a realistic value for the following field:
        Field Name: {field_name}
        Type: {spec.get('type', 'text')}
        Context: {spec.get('context', 'general')}

        Return only the generated value, nothing else.
        """

        response = self.ai_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    def generate_power_apps_entity_data(self, entity_type: str) -> Dict[str, Any]:
        """Generate data specific to Power Apps entities"""

        # Common Power Apps entity schemas
        schemas = {
            'contact': {
                'firstname': {'type': 'name'},
                'lastname': {'type': 'name'},
                'emailaddress1': {'type': 'email'},
                'telephone1': {'type': 'phone'},
                'jobtitle': {'type': 'text', 'context': 'job_title'},
            },
            'account': {
                'name': {'type': 'company'},
                'emailaddress1': {'type': 'email'},
                'telephone1': {'type': 'phone'},
                'websiteurl': {'type': 'url'},
            },
            'lead': {
                'firstname': {'type': 'name'},
                'lastname': {'type': 'name'},
                'companyname': {'type': 'company'},
                'emailaddress1': {'type': 'email'},
            }
        }

        schema = schemas.get(entity_type.lower(), {})
        return self.generate_from_schema(schema)
```

**helpers/screenshot_manager.py**
```python
from playwright.sync_api import Page
from pathlib import Path
from datetime import datetime
import os

class ScreenshotManager:
    """Auto-capture screenshots for every step"""

    screenshot_dir = Path("reports/screenshots")
    step_counter = 0

    @classmethod
    def setup(cls):
        """Initialize screenshot directory"""
        cls.screenshot_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def capture_screenshot(
        cls,
        page: Page,
        name: str,
        full_page: bool = True
    ) -> str:
        """
        Capture screenshot with automatic naming

        Args:
            page: Playwright page
            name: Screenshot name/description
            full_page: Capture full page or viewport

        Returns:
            Path to saved screenshot
        """

        cls.step_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{cls.step_counter:03d}_{timestamp}_{name}.png"
        filepath = cls.screenshot_dir / filename

        page.screenshot(path=str(filepath), full_page=full_page)

        print(f"📸 Screenshot saved: {filepath}")
        return str(filepath)

    @classmethod
    def capture_on_failure(cls, page: Page, test_name: str):
        """Capture screenshot when test fails"""
        return cls.capture_screenshot(page, f"FAILURE_{test_name}")

    @classmethod
    def reset_counter(cls):
        """Reset step counter for new test"""
        cls.step_counter = 0
```

#### 2.2 BDD Integration (Behave)

**features/environment.py** (Behave hooks)
```python
from playwright.sync_api import sync_playwright
from helpers.screenshot_manager import ScreenshotManager
from helpers.auth_helper import AuthHelper
from helpers.wait_manager import WaitManager
import os

def before_all(context):
    """Setup before all tests"""

    # Initialize Playwright
    context.playwright = sync_playwright().start()
    context.browser = context.playwright.chromium.launch(
        headless=os.getenv('HEADLESS', 'false') == 'true'
    )

    # Setup screenshot directory
    ScreenshotManager.setup()

    # Load configuration
    context.config = load_config()

def before_scenario(context, scenario):
    """Setup before each scenario"""

    # Create new page
    context.page = context.browser.new_page()

    # Reset screenshot counter
    ScreenshotManager.reset_counter()

    # Authenticate if needed (reuse session)
    if 'skip_auth' not in scenario.tags:
        AuthHelper.authenticate(
            context.page,
            os.getenv('TEST_USER'),
            os.getenv('TEST_PASSWORD')
        )

def after_step(context, step):
    """Capture screenshot after every step"""

    step_name = step.name.replace(' ', '_')[:50]
    ScreenshotManager.capture_screenshot(context.page, step_name)

def after_scenario(context, scenario):
    """Cleanup after scenario"""

    # Capture failure screenshot
    if scenario.status == 'failed':
        ScreenshotManager.capture_on_failure(context.page, scenario.name)

    # Close page
    context.page.close()

def after_all(context):
    """Cleanup after all tests"""

    context.browser.close()
    context.playwright.stop()
```

**steps/common_steps.py** (Reusable step definitions)
```python
from behave import given, when, then
from helpers.wait_manager import WaitManager
from helpers.healing_locator import HealingLocator
from helpers.screenshot_manager import ScreenshotManager

@given('I am on the "{page_name}" page')
def step_navigate_to_page(context, page_name):
    url = context.config['pages'][page_name]
    context.page.goto(url)
    WaitManager.wait_for_power_apps_load(context.page)

@when('I click on "{element_description}"')
def step_click_element(context, element_description):
    # Use healing locator
    locator = context.locators.get(element_description)
    healer = HealingLocator(context.ai_client)
    element = healer.find_element(context.page, locator, element_description)
    element.click()

@when('I fill "{field_name}" with "{value}"')
def step_fill_field(context, field_name, value):
    locator = context.locators.get(field_name)
    healer = HealingLocator(context.ai_client)
    element = healer.find_element(context.page, locator, field_name)
    element.fill(value)

@then('I should see "{text}"')
def step_verify_text(context, text):
    WaitManager.smart_wait(context.page, f'text={text}')
    assert context.page.locator(f'text={text}').is_visible()
```

---

### 3. AI Processing Layer

#### 3.1 Recording to BDD Converter

**Conversion Logic**:

```typescript
interface PlaywrightAction {
  type: 'navigate' | 'click' | 'fill' | 'select' | 'check' | 'press';
  selector?: string;
  value?: string;
  url?: string;
}

interface BDDOutput {
  feature: string;        // Gherkin feature file content
  steps: string;          // Python step definitions
  locators: Record<string, string>;  // Locator mappings
  testData: Record<string, any>;     // Test data schema
}

async function convertRecordingToBDD(
  recording: PlaywrightAction[],
  scenarioName: string,
  aiClient: AIClient
): Promise<BDDOutput> {

  const prompt = `
    Convert the following Playwright recording into a BDD scenario:

    Recording Actions:
    ${JSON.stringify(recording, null, 2)}

    Scenario Name: ${scenarioName}

    Generate:
    1. A Gherkin feature file with Given/When/Then steps
    2. Python step definitions (use Behave syntax)
    3. Extract all locators into a separate mapping
    4. Identify test data that should be parameterized

    Return as JSON with keys: feature, steps, locators, testData
  `;

  const result = await aiClient.complete(prompt);
  return JSON.parse(result);
}
```

#### 3.2 AI Prompts

**System Prompt for BDD Conversion**:
```
You are an expert test automation engineer specializing in BDD and Playwright.

Your task is to convert Playwright recordings into well-structured BDD scenarios.

Guidelines:
1. Use clear, business-readable Given/When/Then language
2. Group related actions into single steps
3. Identify reusable steps that might exist across scenarios
4. Extract dynamic data into test data files
5. Use descriptive element names instead of technical selectors
6. Follow Behave (Python BDD) syntax
7. Include proper imports and fixtures

Output Format: JSON with keys {feature, steps, locators, testData}
```

**System Prompt for Locator Healing**:
```
You are an expert in web page DOM analysis and element identification.

When a locator fails, analyze the page structure and suggest reliable alternatives.

Priority order:
1. data-testid or data-test attributes
2. Accessible roles and labels
3. Unique text content
4. CSS selectors (class + structure)
5. XPath as last resort

Return suggestions as JSON array, ordered by reliability.
```

---

### 4. Configuration Management

**config/config.py**
```python
from pydantic import BaseSettings, Field
from typing import Dict, Optional

class FrameworkConfig(BaseSettings):
    """Framework configuration using Pydantic"""

    # Application URLs
    app_url: str = Field(..., env='APP_URL')

    # Authentication
    test_user: str = Field(..., env='TEST_USER')
    test_password: str = Field(..., env='TEST_PASSWORD')

    # Playwright settings
    headless: bool = Field(False, env='HEADLESS')
    browser: str = Field('chromium', env='BROWSER')
    viewport_width: int = Field(1920, env='VIEWPORT_WIDTH')
    viewport_height: int = Field(1080, env='VIEWPORT_HEIGHT')

    # AI Configuration
    ai_provider: str = Field('anthropic', env='AI_PROVIDER')
    anthropic_api_key: Optional[str] = Field(None, env='ANTHROPIC_API_KEY')
    openai_api_key: Optional[str] = Field(None, env='OPENAI_API_KEY')

    # Feature flags
    enable_healing: bool = Field(True, env='ENABLE_HEALING')
    enable_screenshots: bool = Field(True, env='ENABLE_SCREENSHOTS')
    enable_video: bool = Field(False, env='ENABLE_VIDEO')

    # Timeouts
    default_timeout: int = Field(10000, env='DEFAULT_TIMEOUT')
    navigation_timeout: int = Field(30000, env='NAVIGATION_TIMEOUT')

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

# Global config instance
config = FrameworkConfig()
```

---

## 🚀 Implementation Phases

### Phase 1: CLI Foundation (Week 1)
- ✅ Setup TypeScript project
- ✅ Implement `init` command
- ✅ Create template engine
- ✅ Generate basic Python framework structure

### Phase 2: Python Framework Core (Week 2)
- ✅ Implement all helper functions
- ✅ Setup Behave integration
- ✅ Create base page objects
- ✅ Configuration management

### Phase 3: AI Integration (Week 3)
- ✅ Implement AI client abstraction
- ✅ Build recording converter
- ✅ Implement locator healing
- ✅ Create test data generator

### Phase 4: Advanced Features (Week 4)
- ✅ Smart wait optimization
- ✅ Power Apps specific helpers
- ✅ Screenshot automation
- ✅ Video recording

### Phase 5: CLI Commands (Week 5)
- ✅ `record` command
- ✅ `convert` command
- ✅ `optimize` command
- ✅ Integration testing

### Phase 6: Documentation & Publishing (Week 6)
- ✅ Complete documentation
- ✅ Example scenarios
- ✅ NPM package publishing
- ✅ Video tutorials

---

## 🧪 Testing Strategy

1. **CLI Testing**: Unit tests for all commands
2. **Template Testing**: Verify generated frameworks work
3. **AI Integration Testing**: Mock AI responses
4. **E2E Testing**: Test with real Power Apps applications
5. **Performance Testing**: Ensure fast generation times

---

## 📊 Success Metrics

1. **Generation Time**: < 30 seconds for full framework
2. **Conversion Accuracy**: > 90% for recording → BDD
3. **Healing Success Rate**: > 75% for failed locators
4. **Framework Reliability**: < 5% flaky tests
5. **User Adoption**: Target 100+ projects in first 3 months

---

## 🔄 Continuous Improvement

1. **Telemetry**: Collect anonymized usage data
2. **AI Model Updates**: Improve prompts based on feedback
3. **Template Updates**: Add new features to generated frameworks
4. **Community**: Open-source contributions

---

## Next: Start Building! 🎯
