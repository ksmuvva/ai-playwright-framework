@smoke @login
Feature: User Authentication
  As a registered user
  I want to log into my account
  So that I can access my personalized content

  Background:
    Given I am on the login page

  @happy-path
  Scenario: Successful login with valid credentials
    When I enter username "tomsmith"
    And I enter password "SuperSecretPassword!"
    And I click the login button
    Then I should be logged in successfully
    And I should see the welcome message

  @negative
  Scenario: Login fails with invalid username
    When I enter username "invalid_user"
    And I enter password "SuperSecretPassword!"
    And I click the login button
    Then I should see an error message "Your username is invalid!"
    And I should remain on the login page

  @negative
  Scenario: Login fails with invalid password
    When I enter username "tomsmith"
    And I enter password "WrongPassword123"
    And I click the login button
    Then I should see an error message "Your password is invalid!"
    And I should remain on the login page

  Scenario: Login page has all required elements
    Then I should see the username field
    And I should see the password field
    And I should see the login button
    And I should see the "Forgot Password" link
