// Playwright Recording for Sample Login Test
// Generated for the-internet.herokuapp.com/login
// This is a sample recording to test the framework's ingestion pipeline

const { test, expect } = require('@playwright/test');

test.describe('Login Tests', () => {
  test('successful login', async ({ page }) => {
    await page.goto('https://the-internet.herokuapp.com/login');
    await page.locator('#username').fill('tomsmith');
    await page.locator('#password').fill('SuperSecretPassword!');
    await page.locator('button[type="submit"]').click();

    // Verify successful login
    await expect(page.locator('#flash')).toContainText('You logged into a secure area!');
    await expect(page.locator('.button.secondary')).toBeVisible();
    await expect(page).toHaveURL(/.*secure/);
  });

  test('failed login with invalid username', async ({ page }) => {
    await page.goto('https://the-internet.herokuapp.com/login');
    await page.locator('#username').fill('invalid_user');
    await page.locator('#password').fill('SuperSecretPassword!');
    await page.locator('button[type="submit"]').click();

    // Verify error message
    await expect(page.locator('#flash')).toContainText('Your username is invalid!');
  });

  test('failed login with invalid password', async ({ page }) => {
    await page.goto('https://the-internet.herokuapp.com/login');
    await page.locator('#username').fill('tomsmith');
    await page.locator('#password').fill('wrong_password');
    await page.locator('button[type="submit"]').click();

    // Verify error message
    await expect(page.locator('#flash')).toContainText('Your password is invalid!');
  });

  test('logout', async ({ page }) => {
    // Login first
    await page.goto('https://the-internet.herokuapp.com/login');
    await page.locator('#username').fill('tomsmith');
    await page.locator('#password').fill('SuperSecretPassword!');
    await page.locator('button[type="submit"]').click();

    // Verify logged in
    await expect(page.locator('#flash')).toContainText('You logged into a secure area!');

    // Logout
    await page.locator('.button.secondary').click();

    // Verify logged out
    await expect(page).toHaveURL(/.*login/);
    await expect(page.locator('h2')).toContainText('Login Page');
  });
});
