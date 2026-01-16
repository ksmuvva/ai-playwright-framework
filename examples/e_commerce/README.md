# E-commerce Example - Full User Journey

A comprehensive example demonstrating end-to-end testing of an e-commerce application with multiple user journeys.

## What This Example Demonstrates

- ✅ Complex user workflows (browse → search → add to cart → checkout)
- ✅ Multiple page objects working together
- ✅ State management (cart state)
- ✅ Form validation
- ✅ Navigation patterns
- ✅ Data-driven testing

## Test Scenarios

### Scenario 1: Guest Checkout Flow
1. Browse products
2. Search for specific item
3. Add item to cart
4. View cart
5. Proceed to checkout as guest
6. Enter shipping information
7. Complete purchase

### Scenario 2: Registered User Flow
1. Login with existing account
2. Browse product categories
3. Add multiple items to cart
4. Apply discount code
5. Checkout with saved address
6. Verify order confirmation

### Scenario 3: Product Search and Filter
1. Navigate to products page
2. Search by keyword
3. Filter by category
4. Filter by price range
5. Sort results
6. Verify filtered results

## Project Structure

```
e_commerce/
├── features/
│   ├── checkout.feature        # Checkout scenarios
│   ├── product_search.feature  # Search and filter scenarios
│   └── user_account.feature    # Account management scenarios
├── pages/
│   ├── __init__.py
│   ├── home_page.py            # Landing page
│   ├── products_page.py        # Product listing
│   ├── product_detail_page.py  # Individual product
│   ├── cart_page.py            # Shopping cart
│   ├── checkout_page.py        # Checkout process
│   └── account_page.py         # User account
└── README.md
```

## Quick Start

```bash
# Run all e-commerce tests
cpa run test --tags @e-commerce

# Run specific scenario
behave examples/e_commerce/features/checkout.feature

# Run with specific profile
cpa run test --profile dev
```

## Key Features Demonstrated

### 1. Multiple Page Objects

```python
# Navigate through pages
home = HomePage(page)
home.navigate()

products = ProductsPage(page)
home.click_products_link()
products.search_for("laptop")

detail = ProductDetailPage(page)
products.click_first_product()
detail.add_to_cart()

cart = CartPage(page)
detail.view_cart()
cart.proceed_to_checkout()
```

### 2. State Management

```python
# Cart state across pages
cart.add_item(product_id=123, quantity=2)
assert cart.get_item_count() == 2
assert cart.get_total() == 99.98
```

### 3. Data-Driven Testing

```gherkin
Scenario Outline: Search products
  When I search for "<keyword>"
  Then I should see results containing "<keyword>"
  And the result count should be greater than 0

  Examples:
    | keyword  |
    | laptop   |
    | phone    |
    | tablet   |
```

## Page Object Examples

### HomePage
```python
class HomePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page, "https://shop.example.com", "HomePage")

    def search_for(self, keyword: str):
        self.fill("#search-input", keyword)
        self.click("#search-button")
```

### CartPage
```python
class CartPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page, "https://shop.example.com", "CartPage")

    def get_items(self) -> List[CartItem]:
        items = []
        elements = self.page.locator(".cart-item")
        for element in elements.all():
            items.append(CartItem.from_element(element))
        return items

    def get_total(self) -> float:
        total_text = self.page.locator(".cart-total").text_content()
        return float(total_text.replace("$", ""))
```

## Best Practices Shown

1. **Page Object Composition** - Pages use other pages
2. **Wait Strategies** - Intelligent waits for dynamic content
3. **Selector Resilience** - Multiple fallback selectors
4. **Error Handling** - Graceful failure with clear messages
5. **Test Data Management** - External test data files
6. **Assertions** - Clear, business-readable assertions

## Test Data

Create `test_data/users.json`:
```json
{
  "guest_user": {
    "email": "guest@example.com",
    "first_name": "Test",
    "last_name": "User",
    "address": "123 Test St",
    "city": "Test City",
    "zip": "12345"
  },
  "registered_user": {
    "email": "user@example.com",
    "password": "SecurePass123!"
  }
}
```

## Running the Tests

```bash
# All e-commerce tests
behave examples/e_commerce/features/

# Specific feature file
behave examples/e_commerce/features/checkout.feature

# Specific scenario
behave examples/e_commerce/features/checkout.feature:10

# With specific tags
behave examples/e_commerce/features/ --tags @smoke

# With formatting
behave examples/e_commerce/features/ --format pretty
```

## Expected Output

```
Feature: E-commerce Checkout

  Scenario: Guest user completes purchase
    Given I am on the home page
    When I search for "wireless headphones"
    And I add the first product to cart
    And I view my cart
    And I proceed to checkout as guest
    And I enter shipping information
      | first_name | Test  |
      | last_name  | User  |
      | email      | test@example.com |
    And I select standard shipping
    And I enter payment information
    And I place my order
    Then I should see an order confirmation
    And I should receive an order number

1 scenario passed, 0 failed, 0 skipped
Duration: 45.2 seconds
```

## What You'll Learn

This example teaches:
1. **Complex Workflows** - Multi-step user journeys
2. **Page Object Composition** - Pages using pages
3. **State Management** - Cart, user session state
4. **Test Data** - External data files
5. **Data-Driven Tests** - Scenario Outlines
6. **Error Recovery** - Handling failures gracefully

## Troubleshooting

**Issue:** Cart state not persisting between pages
- **Solution:** Ensure you're using the same page context throughout the test

**Issue:** Tests flaky due to slow loading
- **Solution:** Use intelligent waits with context-aware detection

**Issue:** Dynamic product IDs causing failures
- **Solution:** Use relative selectors or data-testid attributes

## Additional Resources

- [Page Objects Guide](../../docs/page_objects.md)
- [Intelligent Waits Guide](../../docs/intelligent_waits.md)
- [Simple Login Example](../simple_login/) - Basic example first

## Next Steps

After mastering this example:
1. [API Testing Example](../api_testing/) - Backend validation
2. [Visual Regression Example](../visual_regression/) - UI comparison
3. Create your own e-commerce tests!
