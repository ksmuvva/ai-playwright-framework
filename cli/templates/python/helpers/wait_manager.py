"""
Smart Wait Manager - AI-optimized wait management
Adapts wait times based on historical performance
"""

from playwright.sync_api import Page
from typing import Literal, Optional, Dict, Callable
import time
import json
import os

WaitState = Literal['visible', 'hidden', 'attached', 'detached']


class WaitManager:
    """Intelligent wait management with performance learning"""

    # Learning data structure for wait times
    wait_patterns: Dict[str, Dict] = {}
    _log_file = 'wait_performance_log.json'

    @classmethod
    def _load_patterns(cls):
        """Load historical wait patterns"""
        if os.path.exists(cls._log_file):
            try:
                with open(cls._log_file, 'r') as f:
                    cls.wait_patterns = json.load(f)
            except:
                pass

    @classmethod
    def _save_patterns(cls):
        """Save wait patterns for future runs"""
        try:
            with open(cls._log_file, 'w') as f:
                json.dump(cls.wait_patterns, f, indent=2)
        except:
            pass

    @classmethod
    def smart_wait(
        cls,
        page: Page,
        locator: str,
        state: WaitState = 'visible',
        timeout: Optional[int] = None
    ):
        """
        Intelligent wait that adapts based on historical data

        Args:
            page: Playwright page object
            locator: Element locator
            state: Expected element state
            timeout: Max timeout (auto-calculated if None)
        """
        # Load patterns on first use
        if not cls.wait_patterns:
            cls._load_patterns()

        # Calculate optimal timeout based on history
        if timeout is None:
            timeout = cls._calculate_optimal_timeout(locator)

        start_time = time.time()

        try:
            page.locator(locator).wait_for(state=state, timeout=timeout)
            elapsed = time.time() - start_time

            # Record successful wait
            cls._record_wait(locator, elapsed, success=True)

        except Exception as e:
            elapsed = time.time() - start_time
            cls._record_wait(locator, elapsed, success=False)
            raise e

    @classmethod
    def wait_for_element(
        cls,
        page: Page,
        locator: str,
        state: WaitState = 'visible',
        timeout: int = 10000
    ):
        """
        Wait for element with specified state

        Args:
            page: Playwright page object
            locator: Element locator
            state: Expected state
            timeout: Timeout in milliseconds
        """
        cls.smart_wait(page, locator, state, timeout)

    @classmethod
    def wait_for_navigation(
        cls,
        page: Page,
        url_pattern: str = None,
        timeout: int = 30000
    ):
        """
        Wait for navigation to complete

        Args:
            page: Playwright page object
            url_pattern: Expected URL pattern
            timeout: Timeout in milliseconds
        """
        try:
            if url_pattern:
                page.wait_for_url(url_pattern, timeout=timeout)
            else:
                page.wait_for_load_state('networkidle', timeout=timeout)
        except Exception as e:
            print(f"⚠️  Navigation wait failed: {e}")
            raise

    @classmethod
    def wait_for_power_apps_load(cls, page: Page, timeout: int = 30000):
        """
        Wait for Power Apps specific loading indicators

        Args:
            page: Playwright page object
            timeout: Timeout in milliseconds
        """
        try:
            # Wait for Power Apps loading spinner to disappear
            try:
                page.wait_for_selector(
                    '.pa-loading-spinner, .spinner, [data-id="spinner"]',
                    state='hidden',
                    timeout=timeout
                )
            except:
                pass  # Spinner might not appear

            # Wait for network idle
            page.wait_for_load_state('networkidle', timeout=timeout)

            # Wait for DOM content loaded
            page.wait_for_function(
                "() => document.readyState === 'complete'",
                timeout=timeout
            )

            # Power Apps specific: wait for main container
            try:
                page.wait_for_selector(
                    '[data-id="form-container"], .appmagic-canvas, #mainContent',
                    state='visible',
                    timeout=5000
                )
            except:
                pass  # Container might have different structure

            print("✅ Power Apps loaded")

        except Exception as e:
            print(f"⚠️  Power Apps load wait failed: {e}")

    @classmethod
    def wait_for_text(
        cls,
        page: Page,
        text: str,
        timeout: int = 10000
    ):
        """
        Wait for specific text to appear on page

        Args:
            page: Playwright page object
            text: Text to wait for
            timeout: Timeout in milliseconds
        """
        page.wait_for_selector(f'text={text}', timeout=timeout)

    @classmethod
    def wait_for_condition(
        cls,
        page: Page,
        condition: Callable,
        timeout: int = 10000,
        poll_interval: int = 100
    ):
        """
        Wait for custom condition to be true

        Args:
            page: Playwright page object
            condition: Function that returns boolean
            timeout: Timeout in milliseconds
            poll_interval: Polling interval in milliseconds
        """
        start_time = time.time()
        timeout_seconds = timeout / 1000

        while time.time() - start_time < timeout_seconds:
            if condition(page):
                return True
            time.sleep(poll_interval / 1000)

        raise TimeoutError(f"Condition not met within {timeout}ms")

    @classmethod
    def adaptive_wait(
        cls,
        page: Page,
        locator: str,
        context: str = 'default'
    ):
        """
        AI-powered adaptive wait that chooses best strategy

        Args:
            page: Playwright page object
            locator: Element locator
            context: Context hint (e.g., 'after_click', 'page_load')
        """
        # Choose wait strategy based on context
        strategies = {
            'page_load': lambda: cls.wait_for_navigation(page),
            'after_click': lambda: cls.smart_wait(page, locator, 'visible', 5000),
            'form_submit': lambda: cls.wait_for_power_apps_load(page),
            'default': lambda: cls.smart_wait(page, locator, 'visible')
        }

        strategy = strategies.get(context, strategies['default'])
        strategy()

    @classmethod
    def _calculate_optimal_timeout(cls, locator: str) -> int:
        """
        Calculate timeout based on historical performance

        Args:
            locator: Element locator

        Returns:
            Optimal timeout in milliseconds
        """
        if locator in cls.wait_patterns:
            pattern = cls.wait_patterns[locator]

            if pattern.get('successes', 0) > 0:
                avg_time = pattern.get('avg_time', 5.0)
                # Add 50% buffer
                return int(avg_time * 1.5 * 1000)

        # Default timeout
        return int(os.getenv('DEFAULT_TIMEOUT', '10000'))

    @classmethod
    def _record_wait(cls, locator: str, elapsed: float, success: bool):
        """
        Record wait performance for optimization

        Args:
            locator: Element locator
            elapsed: Time elapsed in seconds
            success: Whether wait succeeded
        """
        if locator not in cls.wait_patterns:
            cls.wait_patterns[locator] = {
                'times': [],
                'successes': 0,
                'failures': 0,
                'avg_time': 0,
                'min_time': float('inf'),
                'max_time': 0
            }

        pattern = cls.wait_patterns[locator]
        pattern['times'].append(elapsed)

        if success:
            pattern['successes'] += 1
        else:
            pattern['failures'] += 1

        # Update statistics
        pattern['avg_time'] = sum(pattern['times']) / len(pattern['times'])
        pattern['min_time'] = min(pattern['times'])
        pattern['max_time'] = max(pattern['times'])

        # Keep only last 50 times to prevent memory bloat
        if len(pattern['times']) > 50:
            pattern['times'] = pattern['times'][-50:]

        # Save periodically
        if (pattern['successes'] + pattern['failures']) % 10 == 0:
            cls._save_patterns()

    @classmethod
    def get_wait_stats(cls) -> Dict:
        """Get wait performance statistics"""
        total_waits = sum(
            p['successes'] + p['failures']
            for p in cls.wait_patterns.values()
        )

        total_successes = sum(p['successes'] for p in cls.wait_patterns.values())

        return {
            'total_waits': total_waits,
            'total_successes': total_successes,
            'success_rate': total_successes / total_waits if total_waits > 0 else 0,
            'patterns': cls.wait_patterns
        }

    @classmethod
    def optimize_waits(cls) -> list:
        """
        Analyze wait patterns and suggest optimizations

        Returns:
            List of optimization suggestions
        """
        suggestions = []

        for locator, pattern in cls.wait_patterns.items():
            if pattern['successes'] < 3:
                continue  # Not enough data

            avg_time = pattern['avg_time']
            max_time = pattern['max_time']

            # Suggest timeout reduction if element loads quickly
            if avg_time < 2.0 and max_time < 3.0:
                suggestions.append({
                    'locator': locator,
                    'type': 'reduce_timeout',
                    'current_avg': avg_time,
                    'suggested_timeout': int(max_time * 1.5 * 1000),
                    'reason': 'Element consistently loads quickly'
                })

            # Suggest timeout increase if failures are common
            failure_rate = pattern['failures'] / (pattern['successes'] + pattern['failures'])
            if failure_rate > 0.2:
                suggestions.append({
                    'locator': locator,
                    'type': 'increase_timeout',
                    'failure_rate': failure_rate,
                    'suggested_timeout': int(max_time * 2 * 1000),
                    'reason': 'High failure rate detected'
                })

        return suggestions


# Initialize on import
WaitManager._load_patterns()
