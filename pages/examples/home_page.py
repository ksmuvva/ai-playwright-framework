"""
Home Page Object Model.

This page object represents the application's home/landing page.
It demonstrates a page with multiple sections and various interactive elements.

Example:
    >>> from pages.home_page import HomePage
    >>>
    >>> home_page = HomePage(page, base_url="https://example.com")
    >>> home_page.search_for("product")
    >>> home_page.click_product(0)
"""

from typing import TYPE_CHECKING, List

from pages.base_page import BasePage

if TYPE_CHECKING:
    from playwright.sync_api import Page


class HomePage(BasePage):
    """
    Page object for the application home page.

    This class encapsulates home page functionality including:
    - Hero section
    - Search functionality
    - Product/item listings
    - Navigation
    - Footer elements

    Attributes:
        page: Playwright Page instance
        base_url: Base URL for the application

    Example:
        >>> home_page = HomePage(page, "https://example.com")
        >>> home_page.navigate()
        >>> home_page.search_for("laptop")
    """

    def __init__(self, page: "Page", base_url: str = "") -> None:
        """
        Initialize the HomePage.

        Args:
            page: Playwright Page instance
            base_url: Base URL for the application
        """
        super().__init__(page, base_url, "HomePage")
        self.url_path = "/"  # Root URL

    # ========================================================================
    # ELEMENT LOCATORS
    # ========================================================================

    @property
    def search_input(self):
        """Search input field."""
        return self.page.locator("input[type='search'], input[name='search'], input[placeholder*='search'], #search")

    @property
    def search_button(self):
        """Search submit button."""
        return self.page.locator("button[type='submit']:near(input[type='search']), .search-button, #search-btn")

    @property
    def hero_title(self):
        """Hero section title."""
        return self.page.locator(".hero h1, .banner h1, .hero-title")

    @property
    def product_list(self):
        """Product/item listing container."""
        return self.page.locator(".products, .items, .product-list, [data-testid='products']")

    @property
    def product_items(self):
        """Individual product items."""
        return self.page.locator(".product, .item, .product-card")

    @property
    def navigation_menu(self):
        """Main navigation menu."""
        return self.page.locator("nav, .navbar, header nav")

    @property
    def footer(self):
        """Page footer."""
        return self.page.locator("footer, .footer")

    @property
    def login_link(self):
        """Login link in navigation."""
        return self.page.locator("a:has-text('Login'), a:has-text('Sign In')")

    @property
    def cart_link(self):
        """Shopping cart link."""
        return self.page.locator("a:has-text('Cart'), .cart-link, [data-testid='cart']")

    # ========================================================================
    # PAGE ACTIONS
    # ========================================================================

    def navigate(self) -> None:
        """
        Navigate to the home page.

        Example:
            >>> home_page = HomePage(page)
            >>> home_page.navigate()
        """
        self.goto(self.url_path)
        self.wait_for_load_state()

    def search(self, query: str) -> None:
        """
        Perform a search query.

        Args:
            query: Search query text

        Example:
            >>> home_page.search("laptop")
        """
        self.search_input.fill(query)
        self.search_button.click()

    def search_for(self, query: str) -> None:
        """
        Alias for search() method.

        Args:
            query: Search query text

        Example:
            >>> home_page.search_for("phone")
        """
        self.search(query)

    def click_product(self, index: int) -> None:
        """
        Click on a product by its index.

        Args:
            index: Index of product to click (0-based)

        Example:
            >>> home_page.click_product(0)  # Click first product
        """
        products = self.product_items.all()
        if index < len(products):
            products[index].click()
        else:
            raise IndexError(f"Product index {index} out of range (total: {len(products)})")

    def click_product_by_name(self, name: str) -> None:
        """
        Click on a product by its name.

        Args:
            name: Product name to click

        Example:
            >>> home_page.click_product_by_name("iPhone 15")
        """
        self.product_items.locator(f".product:has-text('{name}'), .item:has-text('{name}')").click()

    def navigate_to_login(self) -> None:
        """
        Navigate to login page via login link.

        Example:
            >>> home_page.navigate_to_login()
        """
        self.login_link.click()

    def navigate_to_cart(self) -> None:
        """
        Navigate to shopping cart.

        Example:
            >>> home_page.navigate_to_cart()
        """
        self.cart_link.click()

    def click_nav_item(self, item_text: str) -> None:
        """
        Click on navigation menu item.

        Args:
            item_text: Text of navigation item to click

        Example:
            >>> home_page.click_nav_item("Products")
        """
        self.navigation_menu.locator(f"a:has-text('{item_text}')").click()

    def scroll_to_footer(self) -> None:
        """
        Scroll to page footer.

        Example:
            >>> home_page.scroll_to_footer()
        """
        self.footer.scroll_into_view_if_needed()

    # ========================================================================
    # ASSERTIONS
    # ========================================================================

    def assert_is_loaded(self) -> None:
        """
        Assert home page is loaded.

        Raises:
            AssertionError: If home page is not loaded

        Example:
            >>> home_page.navigate()
            >>> home_page.assert_is_loaded()
        """
        self.wait_for_load_state()
        self.assert_visible("body")

    def assert_hero_title_contains(self, text: str) -> None:
        """
        Assert hero title contains specific text.

        Args:
            text: Expected text in hero title

        Raises:
            AssertionError: If text not found

        Example:
            >>> home_page.assert_hero_title_contains("Welcome")
        """
        self.assert_text(".hero h1, .banner h1", text)

    def assert_product_count(self, count: int) -> None:
        """
        Assert number of products displayed.

        Args:
            count: Expected product count

        Raises:
            AssertionError: If count doesn't match

        Example:
            >>> home_page.assert_product_count(12)
        """
        self.assert_count(".product, .item, .product-card", count)

    def assert_search_results_visible(self) -> None:
        """
        Assert search results are visible.

        Raises:
            AssertionError: If search results not visible

        Example:
            >>> home_page.search("laptop")
            >>> home_page.assert_search_results_visible()
        """
        self.assert_visible(".products, .items, .search-results")

    def assert_cart_count(self, count: int) -> None:
        """
        Assert shopping cart shows specific item count.

        Args:
            count: Expected cart item count

        Raises:
            AssertionError: If count doesn't match

        Example:
            >>> home_page.assert_cart_count(2)
        """
        cart_badge = self.page.locator(".cart-badge, .cart-count")
        self.assert_text(".cart-badge, .cart-count", str(count))

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def get_hero_title(self) -> str:
        """
        Get hero section title text.

        Returns:
            Hero title text

        Example:
            >>> title = home_page.get_hero_title()
            >>> print(f"Hero title: {title}")
        """
        return self.hero_title.inner_text() or ""

    def get_product_names(self) -> List[str]:
        """
        Get list of all product names on page.

        Returns:
            List of product name strings

        Example:
            >>> products = home_page.get_product_names()
            >>> for product in products:
            ...     print(f"- {product}")
        """
        products = self.product_items.all()
        return [p.locator(".title, .name, h2, h3").inner_text() or "" for p in products]

    def get_product_count(self) -> int:
        """
        Get number of products on page.

        Returns:
            Product count

        Example:
            >>> count = home_page.get_product_count()
            >>> print(f"Found {count} products")
        """
        return len(self.product_items.all())

    def get_cart_count(self) -> int:
        """
        Get shopping cart item count.

        Returns:
            Cart item count (0 if no badge)

        Example:
            >>> count = home_page.get_cart_count()
            >>> print(f"Cart has {count} items")
        """
        badge = self.page.locator(".cart-badge, .cart-count")
        if badge.is_visible():
            try:
                return int(badge.inner_text())
            except ValueError:
                return 0
        return 0

    def is_search_visible(self) -> bool:
        """
        Check if search input is visible.

        Returns:
            True if visible, False otherwise

        Example:
            >>> if home_page.is_search_visible():
            ...     home_page.search("product")
        """
        return self.search_input.is_visible()

    def get_navigation_items(self) -> List[str]:
        """
        Get list of navigation menu items.

        Returns:
            List of navigation item texts

        Example:
            >>> items = home_page.get_navigation_items()
            >>> print(f"Navigation: {items}")
        """
        items = self.navigation_menu.locator("a").all()
        return [item.inner_text() for item in items]
