Feature: Login Functionality
  As a user
  I want to login to the application
  So that I can access secure features

  @smoke @happy-path
  Scenario: Successful login with valid credentials
    Given I am on the login page
    When I enter username "tomsmith"
    And I enter password "SuperSecretPassword!"
    And I click the login button
    Then I should see a success message "You logged into a secure area!"
    And I should be redirected to the secure area
    And I should see a logout button

  @negative
  Scenario: Failed login with invalid username
    Given I am on the login page
    When I enter username "invalid_user"
    And I enter password "SuperSecretPassword!"
    And I click the login button
    Then I should see an error message "Your username is invalid!"
    And I should remain on the login page

  @negative
  Scenario: Failed login with invalid password
    Given I am on the login page
    When I enter username "tomsmith"
    And I enter password "wrong_password"
    And I click the login button
    Then I should see an error message "Your password is invalid!"
    And I should remain on the login page

  @smoke
  Scenario: Logout after successful login
    Given I am logged in as "tomsmith" with password "SuperSecretPassword!"
    When I click the logout button
    Then I should be redirected to the login page
    And I should see the login heading

  @smoke @data-driven
  Scenario Outline: Login with various credentials
    Given I am on the login page
    When I enter username "<username>"
    And I enter password "<password>"
    And I click the login button
    Then I should see result "<result>"

    Examples:
      | username   | password              | result                |
      | tomsmith   | SuperSecretPassword!  | success               |
      | invalid    | SuperSecretPassword!  | username invalid      |
      | tomsmith   | wrong_password        | password invalid      |
      |           | SuperSecretPassword!  | username invalid      |
