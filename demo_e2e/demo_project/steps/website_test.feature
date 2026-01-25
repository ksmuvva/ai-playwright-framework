Feature: Demo Playwright Website E2E Testing

  As a user
  I want to navigate the demo.playwright.dev website
  So that I can access Playwright documentation

  Background:
    Given I am on the home page

  Scenario: Navigate to home page and verify heading
    When I navigate to the home page
    Then I should see the main heading
    And the heading should contain "Playwright"

  Scenario: Search for documentation
    When I navigate to the home page
    And I search for "locator"
    Then search functionality should work

  Scenario: Navigate to API documentation
    When I navigate to the home page
    And I click the "Get Started" button
    Then I should be navigated to the documentation

  Scenario: Verify menu button exists
    When I navigate to the home page
    Then the menu button should be visible

  Scenario: Multiple page navigation
    When I navigate to the home page
    And I navigate to API documentation
    Then I should see API documentation title
