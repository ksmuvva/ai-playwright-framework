import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://practicetestautomation.com/practice-test-login/")
    page.get_by_role("textbox", name="Username").click()
    page.get_by_role("textbox", name="Username").click()
    page.get_by_role("textbox", name="Username").fill("student")
    page.get_by_role("textbox", name="Password").click()
    page.get_by_role("textbox", name="Password").fill("Password123")
    page.get_by_role("button", name="Submit").click()
    page.get_by_role("link", name="Courses").click()
    with page.expect_popup() as page1_info:
        page.get_by_role("link", name="Selenium WebDriver: Selenium Automation Testing with Java").click()
    page1 = page1_info.value
    page1.close()
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
