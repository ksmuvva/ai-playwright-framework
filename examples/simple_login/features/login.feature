Feature: Login Functionality
  Test login and logout functionality at the-internet.herokuapp.com

  Background:
    Given I am on the login page

  Scenario: Successful login with valid credentials
    When I enter username "tomsmith"
    And I enter password "SuperSecretPassword!"
    And I click the login button
    Then I should see a success message containing "You logged into a secure area!"
    And I should see a logout button
    And the page title should be "Secure Area"

  Scenario: Failed login with invalid credentials
    When I enter username "invalid"
    And I enter password "invalid"
    And I click the login button
    Then I should see an error message containing "Your username is invalid!"

  Scenario: Successful logout
    When I enter username "tomsmith"
    And I enter password "SuperSecretPassword!"
    And I click the login button
    And I click the logout button
    Then I should be on the login page
    And I should see the login form
