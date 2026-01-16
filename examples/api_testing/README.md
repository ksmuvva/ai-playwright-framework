# API Testing Example

Demonstrates API validation and testing capabilities using the AI Playwright Framework.

## What This Example Demonstrates

- ✅ API request/response validation
- ✅ Schema validation with JSON Schema
- ✅ Contract testing
- ✅ Performance testing for APIs
- ✅ Authentication handling
- ✅ Error scenario testing

## Test Scenarios

### 1. User API Validation
- GET /api/users - List all users
- GET /api/users/{id} - Get specific user
- POST /api/users - Create new user
- PUT /api/users/{id} - Update user
- DELETE /api/users/{id} - Delete user

### 2. Product API Testing
- GET /api/products - List products with pagination
- GET /api/products?search=keyword - Search products
- POST /api/products - Create product (admin only)

### 3. Authentication API
- POST /api/auth/login - User login
- POST /api/auth/logout - User logout
- POST /api/auth/refresh - Refresh token

## Quick Start

```bash
# Run API tests
cpa run test examples/api_testing/features/

# With API monitoring
cpa run test --record-api
```

## Example Feature File

```gherkin
Feature: User API Testing
  Validate User API endpoints

  Scenario: Get all users
    When I send GET request to "/api/users"
    Then the response status should be 200
    And the response should be a list
    And each user should have required fields

  Scenario: Create new user
    Given I have user data:
      | name | Test User |
      | email | test@example.com |
    When I send POST request to "/api/users" with the data
    Then the response status should be 201
    And the response should contain user id
    And the user should be created in database
```

## Page Object for API Testing

```python
from pages.base_page import BasePage

class APIPage(BasePage):
    """API testing utilities"""

    def __init__(self, page: Page):
        super().__init__(page, "", "APIPage")

    async def get(self, endpoint: str, headers: dict = None):
        """Send GET request"""
        response = await self.page.request.get(endpoint, headers=headers)
        return response

    async def post(self, endpoint: str, data: dict, headers: dict = None):
        """Send POST request"""
        response = await self.page.request.post(
            endpoint,
            data=data,
            headers=headers
        )
        return response
```

## What You'll Learn

- API request validation
- Schema validation
- Contract testing
- Performance monitoring
- Authentication handling
