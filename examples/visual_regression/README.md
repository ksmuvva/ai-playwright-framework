# Visual Regression Example

Demonstrates visual regression testing capabilities using the AI Playwright Framework.

## What This Example Demonstrates

- ✅ Screenshot capture and comparison
- ✅ Visual diff generation
- ✅ Baseline management
- ✅ Ignore regions for dynamic content
- ✅ Multiple viewport testing
- ✅ Cross-browser visual testing

## Test Scenarios

### 1. Homepage Visual Regression
- Capture baseline screenshot
- Compare against current
- Generate diff report
- Accept/reject workflow

### 2. Component Visual Testing
- Test individual components
- Multiple states (hover, active, disabled)
- Responsive breakpoints

### 3. Cross-Browser Testing
- Chrome vs Firefox
- Desktop vs Mobile

## Quick Start

```bash
# Run visual regression tests
cpa run test examples/visual_regression/features/

# Update baselines
cpa run test --update-visual-baselines
```

## Example Feature File

```gherkin
Feature: Homepage Visual Regression
  Ensure homepage appearance is consistent

  Scenario: Homepage should match baseline
    Given I navigate to the homepage
    When I capture a screenshot
    Then it should match the baseline image
    And differences should be less than 0.1%

  Scenario: Homepage with ignored regions
    Given I navigate to the homepage
    And I ignore dynamic content regions:
      | #current-time |
      | .weather-widget |
    When I capture a screenshot
    Then it should match the baseline
```

## Visual Testing Page Object

```python
from pages.base_page import BasePage

class VisualRegressionPage(BasePage):
    """Visual regression testing utilities"""

    def capture_screenshot(self, name: str) -> str:
        """Capture screenshot with intelligent waits"""
        self.wait_for_page_load()
        screenshot_path = f"screenshots/{name}.png"
        self.page.screenshot(path=screenshot_path)
        return screenshot_path

    def compare_with_baseline(self, name: str, threshold: float = 0.1):
        """Compare with baseline screenshot"""
        from skills.builtins.e6_3_visual_regression import VisualRegression

        regression = VisualRegression(self.page)
        result = regression.compare(name)

        assert result.similarity >= (1.0 - threshold), \
            f"Visual diff: {result.diff_path}"
```

## What You'll Learn

- Screenshot comparison techniques
- Baseline management
- Ignore regions for dynamic content
- Multi-viewport testing
- Cross-browser visual testing
