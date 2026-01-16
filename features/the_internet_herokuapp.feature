Feature: Testing The Internet Herokuapp
  As a user
  I want to interact with various web elements on the-internet.herokuapp.com
  So that I can test different UI patterns and behaviors

  @checkboxes
  Scenario: Check and uncheck checkboxes
    When I navigate to the checkboxes page
    Then I should see two checkboxes
    When I check the first checkbox
    And I check the second checkbox
    And I uncheck the first checkbox
    Then the first checkbox should be unchecked
    And the second checkbox should be checked

  @authentication
  Scenario: Login and logout with valid credentials
    Given I am on the login page
    When I enter username "tomsmith"
    And I enter password "SuperSecretPassword!"
    And I click the login button
    Then I should be logged in
    And I should see a success message
    When I click the logout button
    Then I should be redirected to the login page

  @dropdown
  Scenario: Select an option from dropdown
    When I navigate to the dropdown page
    And I select option "1" from the dropdown
    Then the dropdown value should be "1"

  @hovers
  Scenario: Hover over user avatar
    When I navigate to the hovers page
    And I hover over the first avatar
    Then I should see the user name "user1"
    And I should see "View profile" text

  @navigation
  Scenario: Explore available examples
    Given I am on the home page
    Then I should see the page title "The Internet"
    And I should see at least 40 example links
    When I click the "Checkboxes" link
    Then I should be on the checkboxes page

  @form
  Scenario: Verify form elements are interactive
    When I navigate to the login page
    Then the username field should be editable
    And the password field should be editable
    And the login button should be clickable

  @screenshot
  Scenario: Capture page screenshots
    When I navigate to the checkboxes page
    Then I should capture a screenshot
    And I should capture a full page screenshot
