"""
AI AGENT VISUAL RECORDER
Records human-like interaction on the-internet.herokuapp.com
Shows what the AI agent will process
"""

import asyncio
import sys
import json
from datetime import datetime
from playwright.async_api import async_playwright

# UTF-8 encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, 'strict')

class VisualRecorder:
    """Records test actions with visual feedback"""
    
    def __init__(self):
        self.actions = []
        self.screenshots = []
        self.start_time = None
        
    async def record_human_journey(self):
        """Record complete human journey with visuals"""
        
        print("\n" + "="*70)
        print("🎬 AI AGENT VISUAL RECORDER")
        print("="*70)
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("📍 Target: https://the-internet.herokuapp.com")
        print("="*70 + "\n")
        
        async with async_playwright() as p:
            # Launch browser with viewport
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=1000  # Slow down to see actions
            )
            
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                record_video_dir="C:/Testing_the_Framework/recordings"
            )
            
            page = await context.new_page()
            
            try:
                # STEP 1: Navigate to homepage
                print("\n👤 HUMAN ACTION: Navigating to homepage...")
                await page.goto('https://the-internet.herokuapp.com/')
                
                title = await page.title()
                print(f"✅ PAGE LOADED: {title}")
                
                # Take screenshot
                shot1 = "C:/Testing_the_Framework/recordings/01_homepage.png"
                await page.screenshot(path=shot1)
                print(f"📸 SCREENSHOT: {shot1}")
                
                # Record action
                self.actions.append({
                    "step": 1,
                    "action": "goto",
                    "url": "https://the-internet.herokuapp.com/",
                    "title": title,
                    "screenshot": shot1,
                    "timestamp": datetime.now().isoformat()
                })
                
                await asyncio.sleep(1.5)
                
                # STEP 2: Explore page
                print("\n👤 HUMAN ACTION: Exploring the page...")
                heading = await page.locator('h1').text_content()
                link_count = await page.locator('li a').count()
                
                print(f"✅ OBSERVED: Heading = '{heading}'")
                print(f"✅ OBSERVED: Found {link_count} example links")
                
                self.actions.append({
                    "step": 2,
                    "action": "observe",
                    "heading": heading,
                    "link_count": link_count,
                    "timestamp": datetime.now().isoformat()
                })
                
                await asyncio.sleep(1)
                
                # STEP 3: Click Checkboxes link
                print("\n👤 HUMAN ACTION: Clicking 'Checkboxes' link...")
                await page.get_by_role('link', name='Checkboxes').click()
                print("✅ CLICKED: Checkboxes link")
                
                shot2 = "C:/Testing_the_Framework/recordings/02_checkboxes_page.png"
                await page.screenshot(path=shot2)
                print(f"📸 SCREENSHOT: {shot2}")
                
                self.actions.append({
                    "step": 3,
                    "action": "click",
                    "element": "Checkboxes link",
                    "selector": "role=link[name='Checkboxes']",
                    "screenshot": shot2,
                    "timestamp": datetime.now().isoformat()
                })
                
                await asyncio.sleep(1.2)
                
                # STEP 4: Check checkboxes
                print("\n👤 HUMAN ACTION: Checking checkboxes...")
                
                checkbox1 = page.locator('input[type="checkbox"]').nth(0)
                checkbox2 = page.locator('input[type="checkbox"]').nth(1)
                
                await checkbox1.check()
                print("✅ CHECKED: Checkbox 1")
                await asyncio.sleep(0.8)
                
                await checkbox2.check()
                print("✅ CHECKED: Checkbox 2")
                await asyncio.sleep(0.8)
                
                is_checked1 = await checkbox1.is_checked()
                is_checked2 = await checkbox2.is_checked()
                print(f"✅ VERIFIED: Box 1 = {is_checked1}, Box 2 = {is_checked2}")
                
                shot3 = "C:/Testing_the_Framework/recordings/03_checkboxes_checked.png"
                await page.screenshot(path=shot3)
                print(f"📸 SCREENSHOT: {shot3}")
                
                self.actions.append({
                    "step": 4,
                    "action": "check_multiple",
                    "elements": [
                        {"selector": "input[type='checkbox'] >> nth=0", "checked": True},
                        {"selector": "input[type='checkbox'] >> nth=1", "checked": True}
                    ],
                    "screenshot": shot3,
                    "timestamp": datetime.now().isoformat()
                })
                
                await asyncio.sleep(1)
                
                # STEP 5: Navigate to login
                print("\n👤 HUMAN ACTION: Going to login page...")
                await page.get_by_role('link', name='Form Authentication').click()
                print("✅ NAVIGATED: Login page")
                
                shot4 = "C:/Testing_the_Framework/recordings/04_login_page.png"
                await page.screenshot(path=shot4)
                print(f"📸 SCREENSHOT: {shot4}")
                
                self.actions.append({
                    "step": 5,
                    "action": "click",
                    "element": "Form Authentication link",
                    "selector": "role=link[name='Form Authentication']",
                    "screenshot": shot4,
                    "timestamp": datetime.now().isoformat()
                })
                
                await asyncio.sleep(1.2)
                
                # STEP 6: Fill credentials
                print("\n👤 HUMAN ACTION: Entering credentials...")
                
                await page.locator('input[name="username"]').fill('tomsmith')
                print("✅ TYPED: username = 'tomsmith'")
                await asyncio.sleep(0.5)
                
                await page.locator('input[name="password"]').fill('SuperSecretPassword!')
                print("✅ TYPED: password = '***'")
                await asyncio.sleep(0.5)
                
                self.actions.append({
                    "step": 6,
                    "action": "fill_multiple",
                    "fields": [
                        {"selector": "input[name='username']", "value": "tomsmith"},
                        {"selector": "input[name='password']", "value": "SuperSecretPassword!"}
                    ],
                    "timestamp": datetime.now().isoformat()
                })
                
                # STEP 7: Submit login
                print("\n👤 HUMAN ACTION: Clicking login button...")
                await page.get_by_role('button', name='Login').click()
                print("✅ CLICKED: Login button")
                
                await asyncio.sleep(1.5)
                
                # STEP 8: Verify login
                url = page.url()
                print(f"✅ CURRENT URL: {url}")
                
                success_msg = await page.locator('.flash.success').text_content()
                print(f"✅ SUCCESS MESSAGE: {success_msg.strip()}")
                
                logout_visible = await page.get_by_role('link', name='Logout').is_visible()
                print(f"✅ LOGOUT BUTTON: visible = {logout_visible}")
                
                shot5 = "C:/Testing_the_Framework/recordings/05_logged_in.png"
                await page.screenshot(path=shot5)
                print(f"📸 SCREENSHOT: {shot5}")
                
                self.actions.append({
                    "step": 7,
                    "action": "click",
                    "element": "Login button",
                    "selector": "role=button[name='Login']",
                    "result": {
                        "url": url,
                        "success_message": success_msg.strip(),
                        "logout_visible": logout_visible
                    },
                    "screenshot": shot5,
                    "timestamp": datetime.now().isoformat()
                })
                
                await asyncio.sleep(1)
                
                # STEP 9: Logout
                print("\n👤 HUMAN ACTION: Testing logout...")
                await page.get_by_role('link', name='Logout').click()
                print("✅ CLICKED: Logout link")
                
                await asyncio.sleep(1)
                
                back_at_login = '/login' in page.url()
                print(f"✅ VERIFIED: Back at login page = {back_at_login}")
                
                shot6 = "C:/Testing_the_Framework/recordings/06_logged_out.png"
                await page.screenshot(path=shot6)
                print(f"📸 SCREENSHOT: {shot6}")
                
                self.actions.append({
                    "step": 8,
                    "action": "click",
                    "element": "Logout link",
                    "selector": "role=link[name='Logout']",
                    "screenshot": shot6,
                    "timestamp": datetime.now().isoformat()
                })
                
                print("\n🎉 JOURNEY COMPLETE!")
                
            except Exception as e:
                print(f"\n❌ ERROR: {str(e)}")
            
            finally:
                # Save recording
                await self.save_recording()
                await browser.close()
    
    async def save_recording(self):
        """Save recording to JSON"""
        recording_file = "C:/Testing_the_Framework/recordings/human_journey.json"
        
        recording = {
            "metadata": {
                "title": "Human Journey - The Internet Herokuapp",
                "date": datetime.now().isoformat(),
                "url": "https://the-internet.herokuapp.com",
                "total_steps": len(self.actions),
                "total_screenshots": len([a for a in self.actions if 'screenshot' in a])
            },
            "actions": self.actions
        }
        
        with open(recording_file, 'w') as f:
            json.dump(recording, f, indent=2)
        
        print(f"\n💾 RECORDING SAVED: {recording_file}")
        print(f"📊 TOTAL ACTIONS: {len(self.actions)}")
        print(f"📸 TOTAL SCREENSHOTS: {recording['metadata']['total_screenshots']}")

if __name__ == "__main__":
    recorder = VisualRecorder()
    asyncio.run(recorder.record_human_journey())
