# Intelligent Waits Guide

Complete guide to using intelligent wait strategies in the Claude Playwright Agent.

## Table of Contents

1. [Introduction](#introduction)
2. [Why Intelligent Waits?](#why-intelligent-waits)
3. [Wait Strategies](#wait-strategies)
4. [Wait Conditions](#wait-conditions)
5. [Quick Start](#quick-start)
6. [Usage Examples](#usage-examples)
7. [Smart Wait Analysis](#smart-wait-analysis)
8. [Analytics & Optimization](#analytics--optimization)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Introduction

Intelligent waits eliminate flaky tests by using AI-powered wait strategies that adapt to page conditions. Instead of fixed delays, the framework analyzes context and selects the optimal wait strategy.

### Key Features

- ✅ **Four wait strategies**: explicit, implicit, smart, hybrid
- ✅ **Seven wait conditions**: visible, hidden, attached, detached, enabled, disabled, stable
- ✅ **Context-aware analysis**: Detects loading indicators, animations, network state
- ✅ **Multiple fallback strategies**: Tries different approaches automatically
- ✅ **Analytics & optimization**: Tracks wait patterns and suggests improvements
- ✅ **Self-optimizing**: Learns from historical wait times

---

## Why Intelligent Waits?

### The Problem: Flaky Tests

Flaky tests are caused by timing issues:

```python
# ❌ BAD: Fixed sleep (slow and unreliable)
page.click("#load-data")
await asyncio.sleep(5)  # Wait 5 seconds (too long or too short)
page.click("#process-button")
```

**Problems:**
- Too slow: Waits 5 seconds even if element is ready in 0.5s
- Too fast: Fails if element takes 6 seconds to load
- Wastes time: 5-second delay × 100 tests = 8+ minutes wasted

### The Solution: Intelligent Waits

```python
# ✅ GOOD: Smart wait (fast and reliable)
page.click("#load-data")
# Wait only as long as needed (0.5s to 30s, adapts automatically)
await wait_for_element_visible(page, "#process-button")
```

**Benefits:**
- Fast: Returns immediately when element is ready
- Reliable: Waits up to 30s if needed
- Smart: Detects loading indicators, animations, network state

---

## Wait Strategies

### 1. Explicit Wait

Wait for a specific condition on an element.

**Best for:** Known element states

```python
from skills.builtins.e6_6_intelligent_waits import IntelligentWaitsManager, WaitCondition

manager = IntelligentWaitsManager(page)

# Wait for element to be visible
result = await manager.explicit_wait(
    selector="#submit-button",
    condition=WaitCondition.VISIBLE,
    timeout=30000
)

if result.success:
    print(f"Element visible after {result.duration_ms}ms")
else:
    print(f"Timeout: {result.message}")
```

**Supported conditions:**
- `VISIBLE` - Element is visible in viewport
- `HIDDEN` - Element is not visible
- `ATTACHED` - Element is in DOM
- `DETACHED` - Element removed from DOM
- `ENABLED` - Element is enabled
- `DISABLED` - Element is disabled
- `STABLE` - Element position is stable (no animations)

### 2. Implicit Wait

Global wait for all element interactions.

**Best for:** General stability across all interactions

```python
# Set implicit wait globally
await page.set_default_timeout(5000)

# Now all interactions wait up to 5 seconds
await page.click("#slow-button")  # Waits up to 5s for button to be ready
await page.fill("#input", "text")  # Waits up to 5s for input to be ready
```

**Note:** Implicit wait is set once and applies to all subsequent operations.

### 3. Smart Wait (AI-Powered)

Analyzes page context and tries multiple strategies automatically.

**Best for:** Dynamic content, complex pages

```python
# AI analyzes page and selects optimal strategy
result = await manager.smart_wait(
    selector="#dynamic-content",
    condition=WaitCondition.VISIBLE,
    timeout=30000,
    retry_count=3
)

# Result includes which strategy succeeded
print(f"Strategy used: {result.optimizations}")
print(f"Attempts: {result.attempts}")
```

**How it works:**

1. **Analyzes page context:**
   - Page load state
   - Network idle status
   - Element existence and visibility
   - Loading indicators present
   - CSS animations active

2. **Determines optimal strategies:**
   - Direct locator wait (fastest)
   - Wait for loading indicators to disappear
   - Wait for network idle
   - Wait for animations to complete
   - Poll for element visibility
   - Wait for DOM to stabilize
   - Wait for data-loaded attribute

3. **Tries strategies in order:**
   - Executes each strategy with fallback
   - Stops when element is found
   - Returns which strategy succeeded

### 4. Hybrid Wait

Combines explicit and smart strategies for maximum reliability.

**Best for:** Critical elements, maximum reliability

```python
# Try explicit first, fall back to smart
result = await manager.hybrid_wait(
    selector="#critical-element",
    condition=WaitCondition.VISIBLE,
    timeout=30000,
    retry_count=3
)
```

**How it works:**
1. Tries explicit wait (fastest for simple cases)
2. If explicit fails, tries smart wait (adaptive for complex cases)
3. Returns result from whichever strategy succeeded

---

## Wait Conditions

### Visible

Wait for element to be visible in viewport:

```python
await manager.explicit_wait("#modal", WaitCondition.VISIBLE)
```

### Hidden

Wait for element to be hidden:

```python
await manager.explicit_wait("#spinner", WaitCondition.HIDDEN)
```

### Attached

Wait for element to be in DOM (may not be visible):

```python
await manager.explicit_wait("#dynamic-div", WaitCondition.ATTACHED)
```

### Detached

Wait for element to be removed from DOM:

```python
await manager.explicit_wait("#removed-element", WaitCondition.DETACHED)
```

### Enabled

Wait for element to be enabled:

```python
await manager.explicit_wait("#submit-button", WaitCondition.ENABLED)
```

### Disabled

Wait for element to be disabled:

```python
await manager.explicit_wait("#disabled-input", WaitCondition.DISABLED)
```

### Stable

Wait for element position to be stable (no animations):

```python
await manager.explicit_wait("#animated-element", WaitCondition.STABLE)
```

---

## Quick Start

### Installation

The intelligent waits skill is included with the framework. No additional installation needed.

### Basic Usage

**Step 1: Import the skill**

```python
from skills.builtins.e6_6_intelligent_waits import (
    wait_for_element_visible,
    wait_for_element_hidden,
    wait_for_page_load,
    IntelligentWaitsManager,
    WaitCondition
)
```

**Step 2: Use convenience functions**

```python
# Wait for element to be visible
await wait_for_element_visible(page, "#submit-button")

# Wait for page to load
await wait_for_page_load(page)

# Wait for element to be hidden
await wait_for_element_hidden(page, "#loading-spinner")
```

**Step 3: Or use the manager directly**

```python
manager = IntelligentWaitsManager(page)

# Smart wait with context analysis
result = await manager.smart_wait(
    selector="#dynamic-content",
    condition=WaitCondition.VISIBLE,
    timeout=30000
)

if result.success:
    print(f"Success! Waited {result.duration_ms}ms")
```

---

## Usage Examples

### Example 1: Wait for Modal Dialog

```python
async def test_modal_dialog(page):
    # Click button to open modal
    await page.click("#open-modal")

    # Wait for modal to appear
    await wait_for_element_visible(page, "#modal")

    # Verify modal content
    await page.click("#modal #close-button")

    # Wait for modal to disappear
    await wait_for_element_hidden(page, "#modal")
```

### Example 2: Wait for Dynamic Content

```python
async def test_dynamic_content(page):
    # Click button to load data
    await page.click("#load-data")

    # Smart wait detects loading indicators
    await wait_for_element_visible(page, "#data-table")

    # Verify data loaded
    rows = await page.locator("#data-table tbody tr").count()
    assert rows > 0
```

### Example 3: Wait for AJAX Request

```python
async def test_ajax_request(page):
    # Trigger AJAX request
    await page.click("#refresh-data")

    # Wait for network idle
    await wait_for_page_load(page)

    # Wait for new data to appear
    await wait_for_element_visible(page, "#updated-content")
```

### Example 4: Wait for Specific Text

```python
from skills.builtins.e6_6_intelligent_waits import wait_for_text

async def test_success_message(page):
    # Submit form
    await page.click("#submit-form")

    # Wait for success message to appear
    success = await wait_for_text(
        page,
        selector="#message",
        text="Success! Form submitted.",
        timeout=10000
    )

    assert success, "Success message not found"
```

### Example 5: Custom Timeout and Retry

```python
async def test_slow_element(page):
    manager = IntelligentWaitsManager(page)

    # Custom timeout and retry count
    result = await manager.smart_wait(
        selector="#slow-element",
        condition=WaitCondition.VISIBLE,
        timeout=60000,  # 60 seconds
        retry_count=5   # Try 5 times
    )

    assert result.success, f"Element not found: {result.message}"
```

### Example 6: Wait for Multiple Elements

```python
async def test_multiple_elements(page):
    # Wait for multiple elements in parallel
    import asyncio

    results = await asyncio.gather(
        wait_for_element_visible(page, "#header"),
        wait_for_element_visible(page, "#sidebar"),
        wait_for_element_visible(page, "#content")
    )

    # All waits completed successfully
    assert all(results)
```

### Example 7: Integration with Page Objects

```python
from pages.base_page import BasePage

class DashboardPage(BasePage):
    """Dashboard page with intelligent waits"""

    def __init__(self, page, base_url=""):
        super().__init__(page, base_url, "DashboardPage")

    def wait_for_chart_to_load(self):
        """Wait for chart to render"""
        # Uses intelligent wait from BasePage
        self.assert_visible("#chart canvas")

    def wait_for_data_update(self):
        """Wait for data to update"""
        # Wait for loading spinner to disappear
        self.wait_for_selector(".loading-spinner", state="hidden")
        # Then wait for data to appear
        self.assert_visible("#data-table")

# Usage
async def test_dashboard(page):
    dashboard = DashboardPage(page)
    dashboard.navigate()

    # Intelligent waits handle timing automatically
    dashboard.wait_for_chart_to_load()
    dashboard.wait_for_data_update()
```

---

## Smart Wait Analysis

The smart wait analyzes page context to determine the optimal strategy:

### Context Analysis Factors

1. **Page Load State**
   - Document ready state
   - DOM content loaded

2. **Network State**
   - Network idle (no pending requests)
   - Response times

3. **Element State**
   - Existence in DOM
   - Visibility status

4. **Loading Indicators**
   - `.loading`, `.spinner`, `[data-loading]`
   - Progress bars
   - Skeleton screens

5. **Animations**
   - CSS animations
   - Transitions in progress

6. **Network Speed**
   - Fast: < 2s page load time
   - Medium: 2-5s page load time
   - Slow: > 5s page load time

### Strategy Selection Logic

```python
# Simplified logic (actual implementation is more complex)

if loading_indicators_present:
    strategies.append("wait_for_loading_complete")

if not network_idle:
    strategies.append("wait_for_network_idle")

if animations_active:
    strategies.append("wait_for_animations")

if not element_visible:
    strategies.append("poll_visibility")

# Always include direct locator (fastest)
strategies.insert(0, "direct_locator")
```

---

## Analytics & Optimization

The intelligent waits skill tracks all wait operations and provides optimization suggestions.

### Analytics Summary

```python
manager = IntelligentWaitsManager(page)

# Perform some waits...
await manager.smart_wait("#element1", WaitCondition.VISIBLE)
await manager.smart_wait("#element2", WaitCondition.VISIBLE)

# Get analytics summary
analytics = manager.get_analytics_summary()

print(f"Total waits: {analytics['total_waits']}")
print(f"Success rate: {analytics['success_rate']:.1%}")
print(f"Average wait time: {analytics['average_wait_ms']:.0f}ms")
print(f"Recommended timeout: {analytics['recommended_timeout_ms']}ms")
```

**Example output:**
```
Total waits: 150
Successful waits: 142
Failed waits: 8
Success rate: 94.7%
Total wait time: 1,250,000ms
Average wait: 8,333ms
Recommended timeout: 15,000ms
```

### Optimization Suggestions

```python
suggestions = manager.get_optimization_suggestions()

for suggestion in suggestions:
    print(f"Suggestion: {suggestion}")
```

**Example suggestions:**
```
Suggestion: Average wait time (8333ms) is close to default timeout. Consider increasing default_timeout to 12500ms
Suggestion: Low success rate (75%). Consider using smart waits or adjusting selectors
Suggestion: Based on history, recommended timeout is 15000ms (current: 30000ms)
Suggestion: Consider reducing timeout to 15000ms for faster test failures
```

### Performance Tracking

The skill tracks:
- Total wait count
- Success/failure rates
- Average wait times
- P95/P99 wait times
- Recommended timeouts

This data helps optimize test suite performance over time.

---

## Best Practices

### 1. Use Smart Waits by Default

```python
# ✅ GOOD: Smart wait adapts to conditions
await wait_for_element_visible(page, "#element")

# ❌ BAD: Fixed sleep is slow and unreliable
await asyncio.sleep(5)
```

### 2. Choose the Right Condition

```python
# ✅ GOOD: Wait for specific condition
await wait_for_element_visible(page, "#modal")

# ❌ BAD: Wait for attached (might not be visible)
await manager.explicit_wait("#modal", WaitCondition.ATTACHED)
```

### 3. Set Appropriate Timeouts

```python
# ✅ GOOD: Timeout based on expected load time
await wait_for_element_visible(page, "#fast-element", timeout=5000)

# ✅ GOOD: Longer timeout for slow elements
await wait_for_element_visible(page, "#slow-element", timeout=60000)

# ❌ BAD: Same timeout for all elements
await wait_for_element_visible(page, "#element", timeout=30000)
```

### 4. Use Hybrid Wait for Critical Elements

```python
# ✅ GOOD: Hybrid wait for maximum reliability
result = await manager.hybrid_wait(
    "#submit-button",
    WaitCondition.ENABLED,
    timeout=30000
)

# ❌ BAD: Only one strategy might fail
result = await manager.explicit_wait(
    "#submit-button",
    WaitCondition.ENABLED,
    timeout=30000
)
```

### 5. Don't Wait Too Long

```python
# ✅ GOOD: Reasonable timeout
await wait_for_element_visible(page, "#element", timeout=30000)

# ❌ BAD: Excessive timeout wastes time
await wait_for_element_visible(page, "#element", timeout=300000)  # 5 minutes!
```

### 6. Handle Timeouts Gracefully

```python
result = await manager.smart_wait("#element", WaitCondition.VISIBLE)

if not result.success:
    # Log error, take screenshot, etc.
    print(f"Element not found: {result.message}")
    await page.screenshot(path="error.png")
    raise AssertionError(f"Element not found after {result.duration_ms}ms")
```

### 7. Use Waits in Page Objects

```python
class MyPage(BasePage):
    def wait_for_ready(self):
        """Encapsulate wait logic in page object"""
        self.assert_visible("#ready-indicator")
        self.assert_visible("#main-content")

# Usage
my_page.wait_for_ready()
```

### 8. Avoid Waits in Loops

```python
# ❌ BAD: Inefficient polling
for _ in range(10):
    try:
        await page.click("#element")
        break
    except:
        await asyncio.sleep(1)

# ✅ GOOD: Let intelligent wait handle it
await wait_for_element_visible(page, "#element")
await page.click("#element")
```

---

## Troubleshooting

### Problem: Wait Times Out

**Possible causes:**
1. Selector is incorrect
2. Element never appears
3. Timeout too short
4. Page has loading issues

**Solutions:**
```python
# 1. Verify selector
count = await page.locator("#element").count()
print(f"Element count: {count}")

# 2. Increase timeout
await wait_for_element_visible(page, "#element", timeout=60000)

# 3. Check for errors in browser console
# 4. Use hybrid wait for more attempts
result = await manager.hybrid_wait("#element", WaitCondition.VISIBLE, retry_count=5)
```

### Problem: Wait Too Slow

**Possible causes:**
1. Waiting for unnecessary conditions
2. Timeout too long
3. Network issues

**Solutions:**
```python
# 1. Use more specific condition
await manager.explicit_wait("#element", WaitCondition.ATTACHED)  # Faster than VISIBLE

# 2. Reduce timeout
await wait_for_element_visible(page, "#element", timeout=10000)

# 3. Check analytics for optimal timeout
analytics = manager.get_analytics_summary()
optimal_timeout = analytics['recommended_timeout_ms']
```

### Problem: Intermittent Failures

**Possible causes:**
1. Race conditions
2. Network variability
3. Animation conflicts

**Solutions:**
```python
# 1. Use hybrid wait for reliability
result = await manager.hybrid_wait("#element", WaitCondition.VISIBLE, retry_count=3)

# 2. Wait for animations to complete
await manager.explicit_wait("#element", WaitCondition.STABLE)

# 3. Wait for network idle
await page.wait_for_load_state("networkidle")
```

### Problem: Element Found But Not Interactable

**Possible causes:**
1. Element covered by another element
2. Element disabled
3. Element not in viewport

**Solutions:**
```python
# 1. Wait for enabled state
await manager.explicit_wait("#button", WaitCondition.ENABLED)

# 2. Scroll into view
await page.locator("#button").scroll_into_view_if_needed()

# 3. Wait for stable position
await manager.explicit_wait("#button", WaitCondition.STABLE)
```

---

## Advanced Usage

### Custom Configuration

```python
config = {
    "default_timeout": 60000,  # 60 seconds
    "implicit_wait_enabled": True,
    "implicit_wait_duration": 10000,  # 10 seconds
    "smart_wait_enabled": True,
    "context_aware": True,
    "track_analytics": True
}

manager = IntelligentWaitsManager(page, config)
```

### Parallel Waits

```python
import asyncio

# Wait for multiple elements in parallel
results = await asyncio.gather(
    manager.smart_wait("#header", WaitCondition.VISIBLE),
    manager.smart_wait("#sidebar", WaitCondition.VISIBLE),
    manager.smart_wait("#content", WaitCondition.VISIBLE)
)

# Check all succeeded
assert all(r.success for r in results)
```

### Conditional Waits

```python
# Wait for element with timeout
result = await manager.smart_wait("#element", WaitCondition.VISIBLE, timeout=5000)

if result.success:
    print(f"Element found in {result.duration_ms}ms")
else:
    print("Element not found, using fallback")
    await page.click("#fallback-button")
```

---

## Conclusion

Intelligent waits eliminate flaky tests by using AI-powered wait strategies that adapt to page conditions. By using smart waits instead of fixed delays, you get:

- ✅ Faster tests (no unnecessary waiting)
- ✅ More reliable tests (adaptive to conditions)
- ✅ Better debugging (detailed analytics)
- ✅ Self-optimizing (learns from history)

**Next Steps:**
- Review [BasePage documentation](page_objects.md)
- Check [CLI Reference](cli_reference.md)
- Explore [examples directory](../examples/)

**For more information:**
- [Quick Start Guide](quick_start.md)
- [User Guide](user_guide.md)
- [Framework Architecture](FRAMEWORK_ARCHITECTURE.md)
