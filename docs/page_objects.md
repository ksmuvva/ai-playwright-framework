# Page Objects Guide

Complete guide to creating and using Page Objects in the Claude Playwright Agent.

## Table of Contents

1. [Introduction](#introduction)
2. [What Are Page Objects?](#what-are-page-objects)
3. [BasePage Class](#basepage-class)
4. [Creating Page Objects](#creating-page-objects)
5. [Best Practices](#best-practices)
6. [Examples](#examples)
7. [Advanced Patterns](#advanced-patterns)

---

## Introduction

Page Object Model (POM) is a design pattern that creates an object-oriented abstraction of a web page. This makes your tests:

- **More maintainable** - UI changes only affect page objects
- **More reusable** - Common actions can be shared
- **More readable** - Tests use business language, not selectors
- **More reliable** - Self-healing and better error handling

---

## What Are Page Objects?

Page Objects are classes that represent web pages in your application. They:

1. **Encapsulate page elements** - Locators are defined once
2. **Provide action methods** - Business logic, not technical details
3. **Handle assertions** - Page state verification
4. **Return other page objects** - Navigation flow

### Without Page Objects ❌

```python
# Fragile, unreadable, hard to maintain
def test_login(page):
    page.goto("https://example.com/login")
    page.fill("input[name='username']", "user")
    page.fill("input[type='password']", "pass")
    page.click("button[type='submit']")
    assert page.url == "https://example.com/dashboard"
```

### With Page Objects ✅

```python
# Clean, readable, maintainable
def test_login(page):
    login_page = LoginPage(page)
    login_page.login("user", "pass")
    assert login_page.is_on_dashboard()
```

---

## BasePage Class

The framework provides `BasePage` with common functionality:

### Location

```python
from pages.base_page import BasePage
```

### Key Features

#### Navigation

```python
from pages.base_page import BasePage

class MyPage(BasePage):
    def __init__(self, page, base_url=""):
        super().__init__(page, base_url, "MyPage")
        self.url_path = "/mypage"

    # Navigate to this page
    def navigate(self):
        self.goto(self.url_path)

    # Reload the page
    def refresh(self):
        self.reload()

    # Go back/forward
    def go_back(self):
        self.go_back()
```

#### Element Interaction

```python
# Click with retry
self.click("#submit-button")

# Fill input
self.fill("#email", "user@example.com")

# Select dropdown
self.select_option("#country", value="US")

# Check/uncheck
self.check("#terms")
self.uncheck("#newsletter")
```

#### Waiting

```python
# Wait for element
self.wait_for_selector("#result", state="visible")

# Wait for URL
self.wait_for_url("/dashboard")

# Wait for load state
self.wait_for_load_state("networkidle")
```

#### Assertions

```python
# Assertions
self.assert_url("/dashboard")
self.assert_visible("#welcome")
self.assert_text("#message", "Success")
self.assert_value("#email", "user@example.com")
self.assert_enabled("#submit")
self.assert_count(".item", 5)
```

#### Screenshots

```python
# Take screenshot
path = self.screenshot("login_success")
# Returns: screenshots/login_success.png
```

---

## Creating Page Objects

### Step 1: Define the Class

```python
from pages.base_page import BasePage
from playwright.sync_api import Page

class LoginPage(BasePage):
    """Page object for the login page."""

    def __init__(self, page: Page, base_url: str = "") -> None:
        super().__init__(page, base_url, "LoginPage")
        self.url_path = "/login"
```

### Step 2: Define Element Locators

Use Playwright's best practices:

```python
from playwright.sync_api import Page, Locator

class LoginPage(BasePage):
    # ... init code ...

    @property
    def username_input(self) -> Locator:
        """Username input field."""
        # Use flexible selectors with fallbacks
        return self.page.locator(
            "input[name='username'], "
            "input[type='email'], "
            "input[id*='username']"
        )

    @property
    def password_input(self) -> Locator:
        """Password input field."""
        return self.page.locator("input[type='password']")

    @property
    def submit_button(self) -> Locator:
        """Submit button."""
        return self.page.locator(
            "button[type='submit'], "
            "button:has-text('Log In'), "
            "input[type='submit']"
        )
```

### Step 3: Define Action Methods

```python
class LoginPage(BasePage):
    # ... locators ...

    def navigate(self) -> None:
        """Navigate to login page."""
        self.goto(self.url_path)
        self.wait_for_load_state()

    def login(
        self,
        username: str,
        password: str,
        remember_me: bool = False,
    ) -> None:
        """
        Perform login action.

        Args:
            username: User's username or email
            password: User's password
            remember_me: Check remember me checkbox
        """
        self.username_input.fill(username)
        self.password_input.fill(password)

        if remember_me:
            if self.is_visible("#remember"):
                self.check("#remember")

        self.submit_button.click()
```

### Step 4: Define Assertion Methods

```python
class LoginPage(BasePage):
    # ... actions ...

    def assert_is_loaded(self) -> None:
        """Assert login page is loaded."""
        self.wait_for_load_state()
        self.assert_visible("input[name='username'], input[type='email']")

    def assert_error_shown(self, expected_error: str) -> None:
        """Assert error message is displayed."""
        self.assert_visible(".error-message, [role='alert']")
        if expected_error:
            self.assert_text(".error-message", expected_error)
```

### Step 5: Define Navigation Methods

```python
class LoginPage(BasePage):
    # ... assertions ...

    def login_successfully(
        self,
        username: str,
        password: str,
    ) -> "DashboardPage":
        """
        Login and return DashboardPage on success.

        This demonstrates page object navigation flow.

        Returns:
            DashboardPage instance
        """
        self.login(username, password)

        # Import here to avoid circular dependency
        from pages.dashboard_page import DashboardPage

        return DashboardPage(self.page, self.base_url)
```

---

## Best Practices

### 1. Use Flexible Selectors

❌ **Bad:** Brittle selector
```python
@property
def submit_button(self):
    return self.page.locator("#main-content > div > form > button.submit-btn")
```

✅ **Good:** Flexible with fallbacks
```python
@property
def submit_button(self):
    return self.page.locator(
        "button[type='submit'], "
        "button:has-text('Submit'), "
        ".submit-button"
    )
```

### 2. Use Business Language

❌ **Bad:** Technical details
```python
def test_click_button_fill_input_click_submit(page):
    page.click("#login-btn")
    page.fill("#username", "user")
    page.click("#submit")
```

✅ **Good:** Business language
```python
def test_successful_login(page):
    login_page = LoginPage(page)
    login_page.login("user", "pass")
    assert login_page.is_on_dashboard()
```

### 3. Return Page Objects for Navigation

❌ **Bad:** Returns nothing
```python
def login(self, username, password):
    # ... login logic ...
    # Caller has to manually create DashboardPage
```

✅ **Good:** Returns next page
```python
def login_successfully(self, username, password):
    # ... login logic ...
    return DashboardPage(self.page, self.base_url)
```

### 4. Use Type Hints

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

class MyPage(BasePage):
    def __init__(self, page: Page, base_url: str = "") -> None:
        # ...
```

### 5. Document Your Code

```python
def login(
    self,
    username: str,
    password: str,
    remember_me: bool = False,
) -> None:
    """
    Perform login with username and password.

    Args:
        username: User's username or email address
        password: User's password (will not be logged)
        remember_me: Whether to check "remember me" checkbox

    Raises:
        TimeoutError: If login button not found or page doesn't load

    Example:
        >>> login_page = LoginPage(page)
        >>> login_page.login("user@example.com", "secret123")
    """
    # ... implementation ...
```

### 6. Handle Errors Gracefully

```python
def login(self, username: str, password: str) -> None:
    """Login with error handling."""
    try:
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.submit_button.click()
    except Exception as e:
        # Log the error
        self.screenshot("login_failed")
        # Re-raise with context
        raise RuntimeError(f"Login failed for user {username}") from e
```

### 7. Use Page Sections for Complex Pages

For large pages, break into sections:

```python
class LoginPage(BasePage):
    @property
    def credentials_section(self):
        """Login credentials form section."""
        return CredentialsSection(self.page)

    @property
    def social_section(self):
        """Social login section."""
        return SocialLoginSection(self.page)

class CredentialsSection:
    def __init__(self, page):
        self.page = page

    @property
    def username(self):
        return self.page.locator("#username")

    @property
    def password(self):
        return self.page.locator("#password")
```

---

## Examples

### Example 1: Simple Login Page

```python
from pages.base_page import BasePage
from playwright.sync_api import Page

class SimpleLoginPage(BasePage):
    """Simple login page example."""

    def __init__(self, page: Page, base_url: str = ""):
        super().__init__(page, base_url, "SimpleLoginPage")
        self.url_path = "/login"

    @property
    def username_input(self):
        return self.page.locator("input[name='username']")

    @property
    def password_input(self):
        return self.page.locator("input[type='password']")

    @property
    def login_button(self):
        return self.page.locator("button[type='submit']")

    def login(self, username: str, password: str) -> None:
        """Login with username and password."""
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()

    def assert_is_loaded(self) -> None:
        """Assert page is loaded."""
        self.assert_visible("input[name='username']")
```

**Usage:**

```python
def test_login(page):
    login_page = SimpleLoginPage(page)
    login_page.navigate()
    login_page.assert_is_loaded()
    login_page.login("tomsmith", "SuperSecretPassword!")
```

### Example 2: E-commerce Product Page

```python
class ProductPage(BasePage):
    """Product detail page."""

    def __init__(self, page: Page, base_url: str = ""):
        super().__init__(page, base_url, "ProductPage")

    @property
    def product_title(self):
        return self.page.locator("h1.product-title")

    @property
    def price(self):
        return self.page.locator(".price")

    @property
    def add_to_cart_button(self):
        return self.page.locator("button:has-text('Add to Cart')")

    @property
    def quantity_input(self):
        return self.page.locator("input[name='quantity']")

    def add_to_cart(self, quantity: int = 1) -> None:
        """Add product to cart."""
        self.quantity_input.fill(str(quantity))
        self.add_to_cart_button.click()

    def get_price(self) -> float:
        """Get product price as float."""
        price_text = self.price.inner_text()
        return float(price_text.replace("$", ""))

    def assert_product_title(self, expected_title: str) -> None:
        """Assert product title matches."""
        self.assert_text("h1.product-title", expected_title)
```

### Example 3: Search Results Page

```python
class SearchResultsPage(BasePage):
    """Search results page."""

    @property
    def results_list(self):
        return self.page.locator(".search-results > .result-item")

    @property
    def no_results_message(self):
        return self.page.locator(".no-results")

    def get_result_count(self) -> int:
        """Get number of results."""
        return len(self.results_list.all())

    def get_result_titles(self) -> list[str]:
        """Get list of result titles."""
        results = self.results_list.all()
        return [r.locator(".title").inner_text() for r in results]

    def click_result_by_index(self, index: int) -> None:
        """Click result by index."""
        results = self.results_list.all()
        if index < len(results):
            results[index].click()
        else:
            raise IndexError(f"Result {index} not found")

    def click_result_by_title(self, title: str) -> None:
        """Click result by title."""
        self.results_list.locator(f".result-item:has-text('{title}')").click()

    def assert_no_results(self) -> None:
        """Assert no results found."""
        self.assert_visible(".no-results")

    def assert_results_shown(self) -> None:
        """Assert results are displayed."""
        self.assert_count(".search-results > .result-item", min_count=1)
```

---

## Advanced Patterns

### Pattern 1: Page Object Factory

```python
class PageFactory:
    """Factory for creating page objects."""

    def __init__(self, page: Page, base_url: str = ""):
        self.page = page
        self.base_url = base_url

    def create_login_page(self) -> LoginPage:
        """Create login page."""
        return LoginPage(self.page, self.base_url)

    def create_dashboard_page(self) -> DashboardPage:
        """Create dashboard page."""
        return DashboardPage(self.page, self.base_url)

    def create_from_url(self, url: str) -> BasePage:
        """Create page object based on URL."""
        if "/login" in url:
            return LoginPage(self.page, self.base_url)
        elif "/dashboard" in url:
            return DashboardPage(self.page, self.base_url)
        else:
            return HomePage(self.page, self.base_url)
```

**Usage:**

```python
factory = PageFactory(page, base_url="https://example.com")
login_page = factory.create_login_page()
login_page.login("user", "pass")
```

### Pattern 2: Mixin Classes

```python
class SearchableMixin:
    """Mixin for pages with search functionality."""

    @property
    def search_input(self):
        return self.page.locator("input[type='search']")

    @property
    def search_button(self):
        return self.page.locator("button:has-text('Search')")

    def search(self, query: str) -> None:
        """Perform search."""
        self.search_input.fill(query)
        self.search_button.click()


class PaginatedMixin:
    """Mixin for pages with pagination."""

    @property
    def next_button(self):
        return self.page.locator("button:has-text('Next')")

    @property
    def prev_button(self):
        return self.page.locator("button:has-text('Previous')")

    def go_to_next_page(self) -> None:
        """Go to next page."""
        self.next_button.click()


class ProductListPage(BasePage, SearchableMixin, PaginatedMixin):
    """Product list page with search and pagination."""
    pass
```

### Pattern 3: Component Objects

```python
class LoginForm:
    """Reusable login form component."""

    def __init__(self, page: Page, selector: str = "form.login-form"):
        self.page = page
        self.form = page.locator(selector)

    @property
    def username(self):
        return self.form.locator("input[name='username']")

    @property
    def password(self):
        return self.form.locator("input[type='password']")

    @property
    def submit(self):
        return self.form.locator("button[type='submit']")

    def fill_and_submit(self, username: str, password: str) -> None:
        """Fill and submit the form."""
        self.username.fill(username)
        self.password.fill(password)
        self.submit.click()


class HomePage(BasePage):
    """Home page with login component."""

    @property
    def login_form(self):
        """Login form component."""
        return LoginForm(self.page, "#login-modal form")

    def login_via_modal(self, username: str, password: str) -> None:
        """Login using modal form."""
        self.login_form.fill_and_submit(username, password)
```

---

## Testing with Page Objects

### Example Test

```python
from behave import given, when, then
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage

@given("I am on the login page")
def step_navigate_to_login(context):
    context.login_page = LoginPage(context.page)
    context.login_page.navigate()

@when("I enter valid credentials")
def step_enter_credentials(context):
    context.login_page.login("testuser", "password123")

@then("I should be on the dashboard")
def step_assert_dashboard(context):
    dashboard = DashboardPage(context.page)
    dashboard.assert_is_loaded()
```

### Page Object in BDD Steps

```python
from pages import LoginPage, DashboardPage

def test_login_flow(page):
    # Create page objects
    login = LoginPage(page)
    dashboard = login.login_successfully("user", "pass")

    # Use dashboard methods
    dashboard.assert_welcome_message_shown()
    username = dashboard.get_username()
    assert username == "user"

    # Navigate back
    login = dashboard.logout()
    login.assert_is_loaded()
```

---

## Auto-Generation

The framework can auto-generate page objects:

```bash
# Generate from recordings
cpa generate page-objects

# Custom output
cpa generate page-objects --output-dir src/pages

# Custom base class
cpa generate page-objects --base-class CustomBasePage
```

**Generated page objects:**

```python
# Auto-generated from recordings
class AutoGeneratedLoginPage(BasePage):
    """Auto-generated from login.spec.js"""

    def __init__(self, page: Page, base_url: str = ""):
        super().__init__(page, base_url, "AutoGeneratedLoginPage")

    # Elements and methods auto-generated from recording
```

---

## Tips and Tricks

### 1. Use Page Objects for Setup/Teardown

```python
def setup_function():
    """Create page object for each test."""
    page = context.browser.new_page()
    context.login_page = LoginPage(page)

def teardown_function():
    """Cleanup."""
    context.page.close()
```

### 2. Share Page Objects Across Tests

```python
# conftest.py
@pytest.fixture
def login_page(page):
    """Shared login page fixture."""
    return LoginPage(page)

# test_file.py
def test_login(login_page):
    login_page.navigate()
    login_page.login("user", "pass")
```

### 3. Take Screenshots on Failure

```python
def test_something(page):
    try:
        # ... test code ...
    except Exception as e:
        # Take screenshot for debugging
        base_page = BasePage(page)
        base_page.screenshot("test_failed")
        raise
```

### 4. Use Page Objects for Data Generation

```python
class User:
    """Test user data."""

    @staticmethod
    def random():
        """Generate random user."""
        import random
        import string
        return User(
            username="".join(random.choices(string.ascii_lowercase, k=8)),
            email=f"test{random.randint(1000,9999)}@example.com",
            password="".join(random.choices(string.ascii_letters + string.digits, k=12))
        )

# Usage
def test_with_random_user(page):
    login_page = LoginPage(page)
    user = User.random()
    login_page.register(user.username, user.email, user.password)
```

---

## Conclusion

Page Objects are essential for maintainable test automation. By following these patterns and best practices, you'll create tests that are:

- ✅ **Readable** - Business language, not technical details
- ✅ **Maintainable** - UI changes only affect page objects
- ✅ **Reusable** - Share across multiple tests
- ✅ **Reliable** - Better error handling and self-healing

**Next Steps:**
- Review [example page objects](../pages/examples/)
- Check [BasePage API reference](../pages/base_page.py)
- Learn [advanced patterns](#advanced-patterns)

**For more information:**
- [Quick Start Guide](quick_start.md)
- [User Guide](user_guide.md)
- [CLI Reference](cli_reference.md)
