"""
Pytest configuration for BDD tests.
"""

import pytest
from playwright.async_api import async_playwright


@pytest.fixture
async def browser():
    """Browser fixture for tests."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture
async def context(browser):
    """Browser context fixture."""
    context = await browser.new_context()
    yield context
    await context.close()


@pytest.fixture
async def page(context):
    """Page fixture for tests."""
    page = await context.new_page()
    yield page
