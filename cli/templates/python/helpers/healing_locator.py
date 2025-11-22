"""
Self-Healing Locator - AI-powered element finding
When a locator fails, AI analyzes the page and suggests alternatives
"""

from playwright.sync_api import Page, Locator
from typing import Optional, List, Dict
import json
import os

# Import AI client based on provider
AI_PROVIDER = os.getenv('AI_PROVIDER', 'anthropic')

if AI_PROVIDER == 'anthropic':
    try:
        from anthropic import Anthropic
        AI_CLIENT = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        AI_AVAILABLE = True
    except ImportError:
        AI_AVAILABLE = False
elif AI_PROVIDER == 'openai':
    try:
        from openai import OpenAI
        AI_CLIENT = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        AI_AVAILABLE = True
    except ImportError:
        AI_AVAILABLE = False
else:
    AI_AVAILABLE = False


class HealingLocator:
    """AI-powered self-healing locator finder"""

    def __init__(self):
        self.locator_history: Dict[str, List[str]] = {}
        self.healing_enabled = os.getenv('ENABLE_HEALING', 'true').lower() == 'true'
        self.ai_available = AI_AVAILABLE

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
            page: Playwright page object
            locator: Original locator string
            description: Human-readable element description
            timeout: Wait timeout in milliseconds

        Returns:
            Locator if found, None otherwise

        Raises:
            Exception: If element not found and healing fails
        """
        try:
            # Try original locator first
            element = page.locator(locator)
            element.wait_for(timeout=timeout, state='visible')
            return element

        except Exception as original_error:
            print(f"⚠️  Original locator failed: {locator}")

            # Attempt healing if enabled
            if self.healing_enabled and self.ai_available:
                healed_locator = self._heal_locator(page, locator, description)

                if healed_locator:
                    try:
                        element = page.locator(healed_locator)
                        element.wait_for(timeout=timeout, state='visible')

                        # Log successful healing
                        self._log_healing(locator, healed_locator)
                        print(f"✅ Healed locator: {healed_locator}")

                        return element
                    except Exception as healing_error:
                        print(f"⚠️  Healed locator also failed: {healing_error}")

            # If healing disabled or failed, raise original error
            raise original_error

    def find_element_with_alternatives(
        self,
        page: Page,
        locators: List[str],
        description: str = "",
        timeout: int = 5000
    ) -> Optional[Locator]:
        """
        Try multiple locators in order

        Args:
            page: Playwright page object
            locators: List of locator strings to try
            description: Element description
            timeout: Wait timeout per locator

        Returns:
            Locator if found with any of the alternatives
        """
        for locator in locators:
            try:
                element = page.locator(locator)
                element.wait_for(timeout=timeout, state='visible')
                print(f"✅ Found element with: {locator}")
                return element
            except:
                continue

        # If all fail, try healing with AI
        if self.healing_enabled and self.ai_available:
            healed = self._heal_locator(page, locators[0], description)
            if healed:
                try:
                    return page.locator(healed)
                except:
                    pass

        raise Exception(f"Could not find element with any locator: {locators}")

    def _heal_locator(
        self,
        page: Page,
        failed_locator: str,
        description: str
    ) -> Optional[str]:
        """
        Use AI to find alternative locator

        Args:
            page: Playwright page object
            failed_locator: The locator that failed
            description: Element description

        Returns:
            Alternative locator string or None
        """
        if not self.ai_available:
            return None

        try:
            # Get page content (limited to reduce token usage)
            page_html = page.content()[:10000]

            # Build prompt
            prompt = f"""The following locator failed to find an element:
Locator: {failed_locator}
Description: {description}

Page HTML (excerpt):
{page_html}

Suggest the best alternative locator for this element.

Priority order:
1. data-testid or data-test attributes
2. Accessible roles and labels
3. Unique text content
4. CSS selectors
5. XPath as last resort

Return ONLY a valid JSON object with this structure:
{{"locator": "suggested_locator", "confidence": 0.95, "alternatives": ["alt1", "alt2"]}}
"""

            # Call AI based on provider
            if AI_PROVIDER == 'anthropic':
                response = AI_CLIENT.messages.create(
                    model='claude-sonnet-4-5-20250929',
                    max_tokens=1000,
                    messages=[{'role': 'user', 'content': prompt}]
                )
                response_text = response.content[0].text

            elif AI_PROVIDER == 'openai':
                response = AI_CLIENT.chat.completions.create(
                    model='gpt-4',
                    max_tokens=1000,
                    messages=[{'role': 'user', 'content': prompt}]
                )
                response_text = response.choices[0].message.content

            # Parse response
            result = json.loads(response_text)
            return result.get('locator')

        except Exception as e:
            print(f"⚠️  AI healing failed: {e}")
            return None

    def _log_healing(self, original: str, healed: str):
        """
        Log healing event for analysis

        Args:
            original: Original failed locator
            healed: Successfully healed locator
        """
        if original not in self.locator_history:
            self.locator_history[original] = []

        self.locator_history[original].append(healed)

        # Write to file for framework optimization
        log_file = 'locator_healing_log.json'
        try:
            with open(log_file, 'w') as f:
                json.dump(self.locator_history, f, indent=2)
        except Exception as e:
            print(f"⚠️  Failed to log healing: {e}")

    def get_healing_stats(self) -> Dict:
        """Get statistics about healing attempts"""
        total_healings = sum(len(attempts) for attempts in self.locator_history.values())

        return {
            'total_failed_locators': len(self.locator_history),
            'total_healing_attempts': total_healings,
            'healing_history': self.locator_history
        }


# Global instance for easy access
healing_locator = HealingLocator()
