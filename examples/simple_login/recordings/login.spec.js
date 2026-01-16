// Playwright Recording for Login Test
// Generated using: playwright codegen https://the-internet.herokuapp.com/login --target=python

const { test, expect } = require('@playwright/test');

test('successful login', async ({ page }) => {
  await page.goto('https://the-internet.herokuapp.com/login');
  await page.locator('#username').fill('tomsmith');
  await page.locator('#password').fill('SuperSecretPassword!');
  await page.locator('button[type="submit"]').click();
  await expect(page.locator('#flash')).toContainText('You logged into a secure area!');
  await expect(page.locator('.button.secondary')).toBeVisible();
});

test('failed login', async ({ page }) => {
  await page.goto('https://the-internet.herokuapp.com/login');
  await page.locator('#username').fill('invalid');
  await page.locator('#password').fill('invalid');
  await page.locator('button[type="submit"]').click();
  await expect(page.locator('#flash')).toContainText('Your username is invalid!');
});
