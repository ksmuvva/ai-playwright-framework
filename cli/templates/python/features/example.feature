Feature: Example Feature
  As a user
  I want to perform actions in the application
  So that I can accomplish my goals

  Background:
    Given I am logged in
    And I am on the homepage

  @smoke
  Scenario: Example scenario with common steps
    When I navigate to the "dashboard" page
    Then I should see "Welcome"
    And the "user-menu" should be visible

  @example
  Scenario: Fill a form with test data
    When I navigate to the "contact" page
    And I click on "New Contact"
    And I fill "First Name" with random "first_name"
    And I fill "Last Name" with random "last_name"
    And I fill "Email" with random "email"
    And I click the "Save" button
    Then I should see "Contact created successfully"

  @skip_auth
  Scenario: Login flow
    Given I am on the "login" page
    When I fill "email" with "test@example.com"
    And I fill "password" with "password123"
    And I click the "Login" button
    Then I should be on the "home" page
    And I should see "Dashboard"
