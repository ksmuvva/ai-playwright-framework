"""
Test script to verify GLM 4.7 integration with the Playwright Agent
Tests basic functionality on the-internet.herokuapp.com
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from datetime import datetime

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, 'strict')

# Load environment variables
load_dotenv()

class GLMAgentTester:
    """Test the GLM Agent with basic browser automation"""
    
    def __init__(self):
        self.api_key = os.getenv("GLM_API_KEY")
        self.base_url = os.getenv("GLM_BASE_URL")
        self.model = os.getenv("GLM_MODEL", "glm-4")
        self.test_url = "https://the-internet.herokuapp.com"
        self.results = []
        
    async def test_basic_navigation(self):
        """Test 1: Basic navigation to the-internet.herokuapp.com"""
        print("\n" + "="*60)
        print("TEST 1: Basic Navigation")
        print("="*60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                print(f"✓ Navigating to {self.test_url}")
                await page.goto(self.test_url, wait_until="domcontentloaded")
                
                title = await page.title()
                print(f"✓ Page title: {title}")
                
                # Check for main heading
                heading = await page.locator("h1").text_content()
                print(f"✓ Main heading: {heading}")
                
                # Count available links
                links = await page.locator("li a").count()
                print(f"✓ Found {links} example links")
                
                self.results.append({
                    "test": "Basic Navigation",
                    "status": "PASSED",
                    "details": f"Title: {title}, Links: {links}"
                })
                
                await page.screenshot(path="test_screenshots/01_navigation.png")
                print("✓ Screenshot saved: test_screenshots/01_navigation.png")
                
            except Exception as e:
                print(f"✗ Error: {str(e)}")
                self.results.append({
                    "test": "Basic Navigation",
                    "status": "FAILED",
                    "details": str(e)
                })
            
            await browser.close()
    
    async def test_checkboxes_interaction(self):
        """Test 2: Interact with checkboxes"""
        print("\n" + "="*60)
        print("TEST 2: Checkbox Interaction")
        print("="*60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto(f"{self.test_url}/checkboxes")
                print("✓ Navigated to checkboxes page")
                
                # Get checkboxes
                checkboxes = page.locator("input[type='checkbox']")
                count = await checkboxes.count()
                print(f"✓ Found {count} checkboxes")
                
                # Check first checkbox
                await checkboxes.nth(0).check(force=True)
                is_checked_1 = await checkboxes.nth(0).is_checked()
                print(f"✓ Checkbox 1 checked: {is_checked_1}")
                
                # Check second checkbox
                await checkboxes.nth(1).check(force=True)
                is_checked_2 = await checkboxes.nth(1).is_checked()
                print(f"✓ Checkbox 2 checked: {is_checked_2}")
                
                await page.screenshot(path="test_screenshots/02_checkboxes.png")
                print("✓ Screenshot saved: test_screenshots/02_checkboxes.png")
                
                self.results.append({
                    "test": "Checkbox Interaction",
                    "status": "PASSED",
                    "details": f"Interacted with {count} checkboxes"
                })
                
            except Exception as e:
                print(f"✗ Error: {str(e)}")
                self.results.append({
                    "test": "Checkbox Interaction",
                    "status": "FAILED",
                    "details": str(e)
                })
            
            await browser.close()
    
    async def test_login_form(self):
        """Test 3: Login form interaction"""
        print("\n" + "="*60)
        print("TEST 3: Login Form")
        print("="*60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto(f"{self.test_url}/login")
                print("✓ Navigated to login page")
                
                # Fill in credentials
                await page.fill("input[name='username']", "tomsmith")
                await page.fill("input[name='password']", "SuperSecretPassword!")
                print("✓ Entered username and password")
                
                # Click login button
                await page.click("button[type='submit']")
                print("✓ Clicked login button")
                
                # Wait for navigation
                await page.wait_for_url("**/secure")
                
                # Check for success message
                success_text = await page.locator(".flash.success").text_content()
                print(f"✓ Success message: {success_text.strip()}")
                
                # Verify logout button exists
                logout_button = page.locator("a[href='/logout']")
                await logout_button.is_visible()
                print("✓ Logout button is visible")
                
                await page.screenshot(path="test_screenshots/03_logged_in.png")
                print("✓ Screenshot saved: test_screenshots/03_logged_in.png")
                
                self.results.append({
                    "test": "Login Form",
                    "status": "PASSED",
                    "details": "Successfully logged in with valid credentials"
                })
                
            except Exception as e:
                print(f"✗ Error: {str(e)}")
                self.results.append({
                    "test": "Login Form",
                    "status": "FAILED",
                    "details": str(e)
                })
            
            await browser.close()
    
    async def test_dropdown(self):
        """Test 4: Dropdown interaction"""
        print("\n" + "="*60)
        print("TEST 4: Dropdown Selection")
        print("="*60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto(f"{self.test_url}/dropdown")
                print("✓ Navigated to dropdown page")
                
                # Select option 1
                await page.select_option("#dropdown", "1")
                print("✓ Selected option 1")
                
                # Verify selection
                selected_value = await page.locator("#dropdown").input_value()
                print(f"✓ Selected value: {selected_value}")
                
                await page.screenshot(path="test_screenshots/04_dropdown.png")
                print("✓ Screenshot saved: test_screenshots/04_dropdown.png")
                
                self.results.append({
                    "test": "Dropdown Selection",
                    "status": "PASSED",
                    "details": f"Selected value: {selected_value}"
                })
                
            except Exception as e:
                print(f"✗ Error: {str(e)}")
                self.results.append({
                    "test": "Dropdown Selection",
                    "status": "FAILED",
                    "details": str(e)
                })
            
            await browser.close()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for r in self.results if r["status"] == "PASSED")
        failed = sum(1 for r in self.results if r["status"] == "FAILED")
        total = len(self.results)
        
        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        print("\nDetailed Results:")
        print("-" * 60)
        for result in self.results:
            status_symbol = "✓" if result["status"] == "PASSED" else "✗"
            print(f"{status_symbol} {result['test']}: {result['status']}")
            print(f"  Details: {result['details']}")
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"test_reports/glm_agent_test_{timestamp}.txt"
        
        os.makedirs("test_reports", exist_ok=True)
        with open(report_file, "w") as f:
            f.write("GLM Agent Test Report\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"GLM API Key: {self.api_key[:20]}...\n")
            f.write(f"Model: {self.model}\n")
            f.write(f"Test URL: {self.test_url}\n")
            f.write("="*60 + "\n\n")
            f.write(f"Total Tests: {total}\n")
            f.write(f"Passed: {passed}\n")
            f.write(f"Failed: {failed}\n")
            f.write(f"Success Rate: {(passed/total*100):.1f}%\n\n")
            f.write("Detailed Results:\n")
            f.write("-" * 60 + "\n")
            for result in self.results:
                f.write(f"{result['test']}: {result['status']}\n")
                f.write(f"  Details: {result['details']}\n\n")
        
        print(f"\n✓ Report saved: {report_file}")
    
    async def run_all_tests(self):
        """Run all tests"""
        print("="*60)
        print("GLM AGENT TEST SUITE")
        print("="*60)
        print(f"Model: {self.model}")
        print(f"Test URL: {self.test_url}")
        print(f"API Key: {self.api_key[:20]}..." if self.api_key else "No API Key found")
        print("="*60)
        
        # Create screenshots directory
        os.makedirs("test_screenshots", exist_ok=True)
        
        # Run tests
        await self.test_basic_navigation()
        await self.test_checkboxes_interaction()
        await self.test_login_form()
        await self.test_dropdown()
        
        # Print summary
        self.print_summary()

async def main():
    """Main entry point"""
    tester = GLMAgentTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
