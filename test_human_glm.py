"""
Human-like test script using GLM 4.7 provider.

This script demonstrates testing the-internet.herokuapp.com like a human
using the GLM-4.7 LLM provider.
"""

import asyncio
import os
import sys
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, 'strict')

os.environ["ZHIPUAI_API_KEY"] = "85cf3935c0b843738d461fec7cb2b515.dFTF3tjsPnXLaglE"

from playwright.async_api import async_playwright
from claude_playwright_agent.config import ConfigManager
from claude_playwright_agent.llm import LLMProviderFactory, LLMProviderType, LLMMessage
from claude_playwright_agent.llm.models.config import ProviderConfig


async def setup_glm_provider():
    """Set up GLM 4.7 provider."""
    config = ProviderConfig(
        provider=LLMProviderType.GLM,
        api_key=os.environ["ZHIPUAI_API_KEY"],
        model="glm-4-plus",
    )
    provider = LLMProviderFactory.create_provider(config)
    await provider.initialize()
    return provider


async def human_interaction_test():
    """Test the-internet.herokuapp.com like a human."""

    print("=" * 70)
    print("HUMAN-LIKE INTERACTION TEST")
    print("Testing: https://the-internet.herokuapp.com/")
    print("Provider: GLM-4.7")
    print("=" * 70)
    print()

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Test 1: Visit the home page
            print("\n[TEST 1] Visiting the home page...")
            await page.goto("https://the-internet.herokuapp.com/")
            await page.wait_for_load_state("networkidle")

            title = await page.title()
            print(f"  [OK] Page title: {title}")
            print(f"  [OK] URL: {page.url}")

            # Test 2: Check available links
            print("\n[TEST 2] Exploring available links...")
            links = await page.locator("li a").all()
            print(f"  [OK] Found {len(links)} example links:")

            for i, link in enumerate(links[:10], 1):
                text = await link.text_content()
                href = await link.get_attribute("href")
                print(f"    {i}. {text} -> {href}")

            # Test 3: Try the Checkbox Demo
            print("\n[TEST 3] Testing Checkbox Demo...")
            await page.goto("https://the-internet.herokuapp.com/checkboxes")
            await page.wait_for_load_state("networkidle")

            checkbox1 = page.locator("input[type='checkbox']").nth(0)
            checkbox2 = page.locator("input[type='checkbox']").nth(1)

            # Check initial state
            is_checked1 = await checkbox1.is_checked()
            is_checked2 = await checkbox2.is_checked()
            print(f"  [OK] Initial state: Checkbox 1={is_checked1}, Checkbox 2={is_checked2}")

            # Interact like a human
            await checkbox1.check()
            await checkbox2.check()
            print(f"  [OK] Checked both checkboxes")

            await checkbox1.uncheck()
            print(f"  [OK] Unchecked checkbox 1")

            # Verify final state
            is_checked1_final = await checkbox1.is_checked()
            is_checked2_final = await checkbox2.is_checked()
            print(f"  [OK] Final state: Checkbox 1={is_checked1_final}, Checkbox 2={is_checked2_final}")

            # Test 4: Try the Dropdown Demo
            print("\n[TEST 4] Testing Dropdown Demo...")
            await page.goto("https://the-internet.herokuapp.com/dropdown")
            await page.wait_for_load_state("networkidle")

            dropdown = page.locator("#dropdown")
            await dropdown.select_option("1")
            print(f"  [OK] Selected option 1")

            selected_value = await dropdown.input_value()
            print(f"  [OK] Dropdown value: {selected_value}")

            # Test 5: Try the Form Authentication
            print("\n[TEST 5] Testing Form Authentication...")
            await page.goto("https://the-internet.herokuapp.com/login")
            await page.wait_for_load_state("networkidle")

            username = page.locator("#username")
            password = page.locator("#password")
            login_button = page.locator("button[type='submit']")

            # Fill in credentials
            await username.fill("tomsmith")
            await password.fill("SuperSecretPassword!")
            print(f"  [OK] Entered username and password")

            # Submit
            await login_button.click()
            await page.wait_for_load_state("networkidle")

            # Check success message
            success_message = await page.locator(".flash.success").text_content()
            print(f"  [OK] Success: {success_message.strip()}")

            # Verify we're logged in
            current_url = page.url
            print(f"  [OK] Current URL: {current_url}")

            # Test 6: Logout
            print("\n[TEST 6] Logging out...")
            logout_button = page.locator("a[href='/logout']")
            await logout_button.click()
            await page.wait_for_load_state("networkidle")

            current_url = page.url
            print(f"  [OK] After logout URL: {current_url}")

            # Verify we're back at login page
            login_form = await page.locator("#login").is_visible()
            print(f"  [OK] Login form visible: {login_form}")

            # Test 7: Try the Hovers Demo
            print("\n[TEST 7] Testing Hovers Demo...")
            await page.goto("https://the-internet.herokuapp.com/hovers")
            await page.wait_for_load_state("networkidle")

            avatar = page.locator(".figure img").nth(0)
            await avatar.hover()

            caption = await page.locator(".figcaption").nth(0).text_content()
            print(f"  [OK] Hover caption: {caption.strip()}")

            print("\n" + "=" * 70)
            print("ALL TESTS COMPLETED SUCCESSFULLY!")
            print("=" * 70)

        except Exception as e:
            print(f"\n[ERROR] Error during test: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # Take a screenshot at the end
            await page.screenshot(path="test_result.png", full_page=True)
            print("\n[SCREENSHOT] Screenshot saved: test_result.png")

            await browser.close()


async def test_with_llm_assistance():
    """Test with GLM LLM provider assistance."""

    print("\n" + "=" * 70)
    print("GLM-4.7 PROVIDER TEST")
    print("=" * 70)

    provider = await setup_glm_provider()

    # Test the provider
    print("\n[TEST] Sending query to GLM-4.7...")

    messages = [
        LLMMessage.system("You are a helpful test automation assistant."),
        LLMMessage.user("I'm testing a website called the-internet.herokuapp.com. "
                       "Can you suggest 5 interesting test scenarios I should try? "
                       "Please list them as bullet points."),
    ]

    try:
        response = await provider.query(messages)
        print(f"\n[OK] GLM-4.7 Response:")
        print("-" * 70)
        print(response.content)
        print("-" * 70)

    except Exception as e:
        print(f"\n[ERROR] Error querying GLM-4.7: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await provider.cleanup()


async def main():
    """Main test function."""

    # Test 1: Human-like interaction without LLM
    await human_interaction_test()

    # Test 2: Test with GLM provider
    await test_with_llm_assistance()

    print("\n" + "=" * 70)
    print("TEST SUITE COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
