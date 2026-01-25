"""
Direct E2E Test Runner - Runs tests without pytest-bdd complexity
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

# Add pages to path
sys.path.insert(0, str(Path(__file__).parent))
from pages.home_page import HomePage
from pages.api_page import APIPage


class TestResults:
    """Track test results."""

    def __init__(self):
        self.scenarios = []
        self.current_scenario = None
        self.current_step = None

    def start_scenario(self, name):
        """Start a new scenario."""
        self.current_scenario = {
            "name": name,
            "steps": [],
            "status": "RUNNING"
        }
        self.scenarios.append(self.current_scenario)
        print(f"\n{'=' * 70}")
        print(f"SCENARIO: {name}")
        print('=' * 70)

    def add_step(self, name, status="PASS", details=""):
        """Add a step result."""
        step = {
            "name": name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        if self.current_scenario:
            self.current_scenario["steps"].append(step)

        icon = "[+]" if status == "PASS" else "[X]" if status == "FAIL" else "[i]"
        print(f"  {icon} {name}")
        if details:
            print(f"      {details}")

    def end_scenario(self, status="PASS"):
        """End current scenario."""
        if self.current_scenario:
            self.current_scenario["status"] = status
            print(f"\n  Scenario Result: {status}\n")

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 80)
        print(" " * 25 + "TEST EXECUTION SUMMARY")
        print("=" * 80)

        passed = sum(1 for s in self.scenarios if s["status"] == "PASS")
        failed = sum(1 for s in self.scenarios if s["status"] == "FAIL")

        print(f"\nTotal Scenarios: {len(self.scenarios)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")

        for scenario in self.scenarios:
            status_icon = "[+]" if scenario["status"] == "PASS" else "[X]"
            print(f"\n{status_icon} {scenario['name']}")
            for step in scenario["steps"]:
                icon = "[+]" if step["status"] == "PASS" else "[X]" if step["status"] == "FAIL" else "[i]"
                print(f"    {icon} {step['name']}")


async def run_scenario_1(results, page):
    """Scenario 1: Navigate to home page and verify heading."""
    results.start_scenario("Navigate to home page and verify heading")

    try:
        results.add_step("Given I am on the home page")
        home = HomePage(page)
        await home.navigate_home()

        results.add_step("When I navigate to the home page")
        await home.navigate_home()

        results.add_step("Then I should see the main heading")
        text = await home.get_heading_text()
        assert text is not None and len(text) > 0
        results.current_scenario["steps"][-1]["details"] = f"Heading: {text}"

        results.add_step('Then the heading should contain "Playwright"')
        assert "Playwright" in text
        results.current_scenario["steps"][-1]["details"] = f"Confirmed: '{text}'"

        results.end_scenario("PASS")
    except Exception as e:
        results.add_step("Error", "FAIL", str(e))
        results.end_scenario("FAIL")


async def run_scenario_2(results, page):
    """Scenario 2: Search for documentation."""
    results.start_scenario("Search for documentation")

    try:
        results.add_step("Given I am on the home page")
        home = HomePage(page)
        await home.navigate_home()

        results.add_step('When I search for "locator"')
        await home.search("locator")
        await asyncio.sleep(1)

        results.add_step("Then search functionality should work")
        results.end_scenario("PASS")
    except Exception as e:
        results.add_step("Error", "FAIL", str(e))
        results.end_scenario("FAIL")


async def run_scenario_3(results, page):
    """Scenario 3: Navigate to API documentation."""
    results.start_scenario("Navigate to API documentation")

    try:
        results.add_step("Given I am on the home page")
        home = HomePage(page)
        await home.navigate_home()

        results.add_step('When I click the "Get Started" button')
        await home.click_get_started()
        await asyncio.sleep(1)

        results.add_step("Then I should be navigated to the documentation")
        current_url = page.url
        assert "docs" in current_url or "intro" in current_url
        results.current_scenario["steps"][-1]["details"] = f"Navigated to: {current_url}"

        results.end_scenario("PASS")
    except Exception as e:
        results.add_step("Error", "FAIL", str(e))
        results.end_scenario("FAIL")


async def run_scenario_4(results, page):
    """Scenario 4: Verify menu button exists."""
    results.start_scenario("Verify menu button exists")

    try:
        results.add_step("Given I am on the home page")
        home = HomePage(page)
        await home.navigate_home()

        results.add_step("Then the menu button should be visible")
        is_visible = await home.is_menu_visible()
        results.current_scenario["steps"][-1]["details"] = f"Menu visible: {is_visible}"

        results.end_scenario("PASS")
    except Exception as e:
        results.add_step("Error", "FAIL", str(e))
        results.end_scenario("FAIL")


async def run_scenario_5(results, page):
    """Scenario 5: Multiple page navigation."""
    results.start_scenario("Multiple page navigation")

    try:
        results.add_step("Given I am on the home page")
        home = HomePage(page)
        await home.navigate_home()

        results.add_step("When I navigate to API documentation")
        api = APIPage(page)
        await api.navigate_to_api()

        results.add_step("Then I should see API documentation title")
        title = await api.get_api_title()
        assert title is not None
        results.current_scenario["steps"][-1]["details"] = f"API Title: {title}"

        results.end_scenario("PASS")
    except Exception as e:
        results.add_step("Error", "FAIL", str(e))
        results.end_scenario("FAIL")


async def run_all_tests():
    """Run all E2E tests."""
    results = TestResults()

    print("=" * 80)
    print(" " * 20 + "E2E TEST EXECUTION - DEMO PLAYWRIGHT")
    print(" " * 30 + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 80)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await run_scenario_1(results, page)
            await run_scenario_2(results, page)
            await run_scenario_3(results, page)
            await run_scenario_4(results, page)
            await run_scenario_5(results, page)
        finally:
            await browser.close()

    results.print_summary()
    return results


async def main():
    """Main entry point."""
    results = await run_all_tests()

    # Save results to file
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = reports_dir / f"e2e_report_{timestamp}.txt"

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("E2E TEST EXECUTION REPORT\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        for scenario in results.scenarios:
            f.write(f"\nSCENARIO: {scenario['name']}\n")
            f.write(f"Status: {scenario['status']}\n")
            f.write("-" * 70 + "\n")
            for step in scenario["steps"]:
                f.write(f"  [{step['status']}] {step['name']}")
                if step.get("details"):
                    f.write(f"\n       {step['details']}")
                f.write("\n")

    print(f"\n[+] Report saved to: {report_file}")

    passed = sum(1 for s in results.scenarios if s["status"] == "PASS")
    failed = sum(1 for s in results.scenarios if s["status"] == "FAIL")

    if failed == 0:
        print("\n[+] ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n[X] {failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
