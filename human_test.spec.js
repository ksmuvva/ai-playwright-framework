const { test, expect } = require('@playwright/test');

test.describe('Human User Journey', () => {
  test('Complete user journey: Checkboxes and Login', async ({ page }) => {
    console.log('USER: Opening browser...');
    await page.goto('https://the-internet.herokuapp.com/');
    await expect(page).toHaveTitle(/The Internet/);
    console.log('USER: Homepage loaded!');
    await page.waitForTimeout(1500);
    
    const heading = await page.locator('h1').textContent();
    console.log(`USER: Saw heading: ${heading}`);
    const linkCount = await page.locator('li a').count();
    console.log(`USER: Found ${linkCount} examples`);
    await page.waitForTimeout(1000);
    
    console.log('USER: Clicking Checkboxes link...');
    await page.getByRole('link', { name: 'Checkboxes' }).click();
    console.log('USER: Navigated to Checkboxes page');
    await page.waitForTimeout(1200);
    
    const checkbox1 = page.locator('input[type="checkbox"]').nth(0);
    const checkbox2 = page.locator('input[type="checkbox"]').nth(1);
    
    await checkbox1.check();
    console.log('USER: Checked checkbox 1');
    await page.waitForTimeout(800);
    
    await checkbox2.check();
    console.log('USER: Checked checkbox 2');
    await page.waitForTimeout(800);
    
    const isChecked1 = await checkbox1.isChecked();
    const isChecked2 = await checkbox2.isChecked();
    console.log(`USER: Verified - Box 1: ${isChecked1}, Box 2: ${isChecked2}`);
    await page.waitForTimeout(1000);
    
    console.log('USER: Going to login page...');
    await page.getByRole('link', { name: 'Form Authentication' }).click();
    console.log('USER: On login page');
    await page.waitForTimeout(1200);
    
    console.log('USER: Entering credentials...');
    await page.locator('input[name="username"]').fill('tomsmith');
    console.log('USER: Entered username');
    await page.waitForTimeout(500);
    
    await page.locator('input[name="password"]').fill('SuperSecretPassword!');
    console.log('USER: Entered password');
    await page.waitForTimeout(500);
    
    console.log('USER: Clicking login button...');
    await page.getByRole('button', { name: 'Login' }).click();
    console.log('USER: Login clicked!');
    await page.waitForTimeout(1500);
    
    const url = page.url();
    console.log(`USER: Current URL: ${url}`);
    
    const successMessage = await page.locator('.flash.success').textContent();
    console.log(`USER: Success: ${successMessage.trim()}`);
    
    const logoutVisible = await page.getByRole('link', { name: 'Logout' }).isVisible();
    console.log(`USER: Logout visible: ${logoutVisible}`);
    await page.waitForTimeout(1000);
    
    console.log('USER: Testing logout...');
    await page.getByRole('link', { name: 'Logout' }).click();
    console.log('USER: Logged out!');
    await page.waitForTimeout(1000);
    
    const backAtLogin = page.url().includes('/login');
    console.log(`USER: Back at login: ${backAtLogin}`);
    console.log('USER: Test complete!');
    
    await page.screenshot({ path: 'C:/Testing_the_Framework/recordings/test_complete.png', fullPage: true });
  });
});
