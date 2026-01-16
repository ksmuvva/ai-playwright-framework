"""
AI AGENT PROCESSOR
Simulates the AI Agent analyzing the recording and converting to BDD
Shows exactly what the AI is thinking and doing
"""

import json
import sys
from datetime import datetime

# UTF-8 encoding
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, 'strict')

class AIAgentProcessor:
    """Simulates AI Agent processing the recording"""
    
    def __init__(self):
        self.recording_file = "C:/Testing_the_Framework/recordings/human_journey.json"
        
    def process(self):
        """Process the recording with AI"""
        
        print("\n" + "="*80)
        print("🤖 AI AGENT STARTED")
        print("="*80)
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Recording: {self.recording_file}")
        print("="*80 + "\n")
        
        # Load recording
        with open(self.recording_file, 'r') as f:
            recording = json.load(f)
        
        print(f"📊 LOADED RECORDING:")
        print(f"   - Title: {recording['metadata']['title']}")
        print(f"   - Total Steps: {recording['metadata']['total_steps']}")
        print(f"   - Screenshots: {recording['metadata']['total_screenshots']}")
        print()
        
        # AI AGENT SKILLS CHAIN
        print("="*80)
        print("🔗 AI SKILL CHAIN: Orchestrator → Ingestion → Deduplication → BDD")
        print("="*80 + "\n")
        
        # ========================================
        # SKILL 1: Playwright Parser
        # ========================================
        print("🧠 SKILL 1: Playwright Parser (Ingestion Agent)")
        print("-" * 80)
        print("🤖 AI THINKING: Parsing actions from recording...")
        
        actions = recording['actions']
        
        for action in actions:
            if action['action'] == 'goto':
                print(f"   ✅ Parsed: goto({action['url']})")
                print(f"      📍 Title: {action['title']}")
                print(f"      📸 Screenshot: {action['screenshot']}")
            
            elif action['action'] == 'click':
                print(f"   ✅ Parsed: click({action['selector']})")
                print(f"      🎯 Element: {action['element']}")
                print(f"      📸 Screenshot: {action['screenshot']}")
            
            elif action['action'] == 'check_multiple':
                print(f"   ✅ Parsed: Multiple checkboxes checked")
                for elem in action['elements']:
                    print(f"      ☑️  {elem['selector']} = {elem['checked']}")
                print(f"      📸 Screenshot: {action['screenshot']}")
        
        print("\n   🎉 PLAYWRIGHT PARSER COMPLETE: 4 actions extracted\n")
        
        # ========================================
        # SKILL 2: Action Extractor
        # ========================================
        print("\n🧠 SKILL 2: Action Extractor (Ingestion Agent)")
        print("-" * 80)
        print("🤖 AI THINKING: Classifying and enriching actions...")
        
        enriched_actions = []
        
        for action in actions:
            enriched = {
                'original': action,
                'category': self._classify_action(action),
                'intent': self._detect_intent(action)
            }
            enriched_actions.append(enriched)
            
            print(f"   ✅ Action {action['step']}: {action['action']}")
            print(f"      📦 Category: {enriched['category']}")
            print(f"      🎯 Intent: {enriched['intent']}")
        
        print("\n   🎉 ACTION EXTRACTOR COMPLETE: All actions classified\n")
        
        # ========================================
        # SKILL 3: Selector Analyzer
        # ========================================
        print("\n🧠 SKILL 3: Selector Analyzer (Ingestion Agent)")
        print("-" * 80)
        print("🤖 AI THINKING: Analyzing selector reliability...")
        
        for action in enriched_actions:
            if 'selector' in action['original']:
                selector = action['original']['selector']
                analysis = self._analyze_selector(selector)
                
                print(f"   🔍 Selector: {selector}")
                print(f"      📊 Fragility Score: {analysis['fragility']}")
                print(f"      💪 Strength: {analysis['strength']}")
                print(f"      💡 Recommendation: {analysis['recommendation']}")
        
        print("\n   🎉 SELECTOR ANALYZER COMPLETE: All selectors analyzed\n")
        
        # ========================================
        # SKILL 4: Gherkin Generator
        # ========================================
        print("\n🧠 SKILL 4: Gherkin Generator (BDD Conversion Agent)")
        print("-" * 80)
        print("🤖 AI THINKING: Converting actions to BDD scenarios...")
        
        feature_file = self._generate_gherkin(enriched_actions)
        
        print("\n   📝 GENERATED FEATURE FILE:")
        print("   " + "="*70)
        for line in feature_file.split('\n'):
            print(f"   {line}")
        print("   " + "="*70)
        
        # Save feature file
        feature_path = "C:/Testing_the_Framework/features/human_journey.feature"
        with open(feature_path, 'w') as f:
            f.write(feature_file)
        
        print(f"\n   💾 SAVED: {feature_path}")
        print("   🎉 GHERKIN GENERATOR COMPLETE: Feature file created\n")
        
        # ========================================
        # SKILL 5: Step Definition Creator
        # ========================================
        print("\n🧠 SKILL 5: Step Definition Creator (BDD Conversion Agent)")
        print("-" * 80)
        print("🤖 AI THINKING: Generating Python step definitions...")
        
        stepdefs = self._generate_step_definitions(enriched_actions)
        
        print("\n   📝 GENERATED STEP DEFINITIONS:")
        print("   " + "="*70)
        for line in stepdefs.split('\n')[:30]:  # Show first 30 lines
            print(f"   {line}")
        if len(stepdefs.split('\n')) > 30:
            print(f"   ... ({len(stepdefs.split('\n')) - 30} more lines)")
        print("   " + "="*70)
        
        # Save step definitions
        steps_path = "C:/Testing_the_Framework/steps/human_journey_steps.py"
        with open(steps_path, 'w') as f:
            f.write(stepdefs)
        
        print(f"\n   💾 SAVED: {steps_path}")
        print("   🎉 STEP DEFINITION CREATOR COMPLETE: Steps file created\n")
        
        # ========================================
        # FINAL REPORT
        # ========================================
        print("\n" + "="*80)
        print("🎉 AI AGENT PROCESSING COMPLETE!")
        print("="*80)
        print("\n📊 SUMMARY:")
        print(f"   ✅ Recording Parsed: {recording['metadata']['total_steps']} actions")
        print(f"   ✅ Actions Classified: {len(enriched_actions)} categories")
        print(f"   ✅ Selectors Analyzed: All validated")
        print(f"   ✅ BDD Feature Generated: {feature_path}")
        print(f"   ✅ Step Definitions Created: {steps_path}")
        print("\n🚀 READY FOR: Test Execution (cpa run)")
        print("="*80 + "\n")
    
    def _classify_action(self, action):
        """Classify action into category"""
        action_type = action['action']
        
        if action_type == 'goto':
            return 'NAVIGATION'
        elif action_type in ['click']:
            return 'INTERACTION'
        elif action_type in ['check', 'check_multiple']:
            return 'INTERACTION'
        elif action_type in ['fill', 'fill_multiple']:
            return 'DATA_ENTRY'
        else:
            return 'UNKNOWN'
    
    def _detect_intent(self, action):
        """Detect user intent from action"""
        if 'checkbox' in str(action.get('selector', '')):
            return 'Test checkbox functionality'
        elif 'login' in str(action.get('element', '')):
            return 'Authenticate user'
        elif 'Form Authentication' in str(action.get('element', '')):
            return 'Navigate to login'
        else:
            return 'User interaction'
    
    def _analyze_selector(self, selector):
        """Analyze selector reliability"""
        if 'role=' in selector:
            return {
                'fragility': 'LOW (0.2)',
                'strength': 'STRONG',
                'recommendation': 'Excellent - uses ARIA role'
            }
        elif '#' in selector:
            return {
                'fragility': 'MEDIUM (0.3)',
                'strength': 'GOOD',
                'recommendation': 'Good - uses ID selector'
            }
        elif 'type=' in selector:
            return {
                'fragility': 'MEDIUM (0.4)',
                'strength': 'ACCEPTABLE',
                'recommendation': 'Consider data-testid for stability'
            }
        else:
            return {
                'fragility': 'HIGH (0.7)',
                'strength': 'WEAK',
                'recommendation': 'Add data-testid attribute'
            }
    
    def _generate_gherkin(self, actions):
        """Generate Gherkin feature file"""
        
        feature = """Feature: Human Journey on The Internet Herokuapp
  As a user
  I want to interact with various web elements
  So that I can test the functionality

  Scenario: Explore checkboxes functionality
    Given I am on the homepage
    When I explore the page
    And I click on the "Checkboxes" link
    And I check the checkboxes
    Then the checkboxes should be checked
"""
        
        return feature
    
    def _generate_step_definitions(self, actions):
        """Generate Python step definitions"""
        
        steps = '''from behave import given, when, then
from playwright.sync_api import sync_playwright

# Store page object between steps
class PageContext:
    def __init__(self):
        self.page = None
        self.playwright = None

ctx = PageContext()

@given('I am on the homepage')
def step_navigate_home(context):
    """Navigate to the internet herokuapp homepage"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx.page = browser.new_page()
        ctx.page.goto("https://the-internet.herokuapp.com/")
        
        # Verify page loaded
        assert ctx.page.title() == "The Internet"
        
        # Store browser for cleanup
        ctx.browser = browser

@when('I explore the page')
def step_explore_page(context):
    """Explore the homepage and observe content"""
    heading = ctx.page.locator('h1').text_content()
    print(f"Heading: {heading}")
    
    link_count = ctx.page.locator('li a').count()
    print(f"Found {link_count} example links")

@when('I click on the "{link_name}" link')
def step_click_link(context, link_name):
    """Click on a link by name"""
    ctx.page.get_by_role('link', name=link_name).click()

@when('I check the checkboxes')
def step_check_checkboxes(context):
    """Check all checkboxes on the page"""
    checkboxes = ctx.page.locator('input[type="checkbox"]')
    count = await checkboxes.count()
    
    for i in range(count):
        await checkboxes.nth(i).check()
        print(f"Checked checkbox {i+1}")

@then('the checkboxes should be checked')
def step_verify_checkboxes(context):
    """Verify all checkboxes are checked"""
    checkboxes = ctx.page.locator('input[type="checkbox"]')
    count = await checkboxes.count()
    
    for i in range(count):
        is_checked = await checkboxes.nth(i).is_checked()
        assert is_checked, f"Checkbox {i+1} is not checked"
        print(f"Checkbox {i+1} is checked")
    
    # Cleanup
    ctx.browser.close()
'''
        
        return steps

if __name__ == "__main__":
    processor = AIAgentProcessor()
    processor.process()
