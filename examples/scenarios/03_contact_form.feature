@form @contact
Feature: Contact Form Submission
  As a website visitor
  I want to submit a contact form
  So that I can send a message to the support team

  Background:
    Given I am on the contact page

  Scenario: Successfully submit contact form with valid data
    When I enter my name "John Doe"
    And I enter my email "john.doe@example.com"
    And I enter the subject "Test Inquiry"
    And I enter the message "This is a test message for the support team."
    And I click the submit button
    Then I should see a success message "Thank you for your message!"
    And I should receive a confirmation email

  Scenario: Form validation shows error for missing required fields
    When I enter my name "John Doe"
    And I leave the email field empty
    And I click the submit button
    Then I should see an error "Email is required"

  Scenario: Form validation shows error for invalid email format
    When I enter my name "John Doe"
    And I enter my email "invalid-email"
    And I click the submit button
    Then I should see an error "Please enter a valid email address"

  @data-driven
  Scenario Outline: Submit contact form with various subjects
    When I enter my name "<name>"
    And I enter my email "<email>"
    And I enter the subject "<subject>"
    And I enter the message "<message>"
    And I click the submit button
    Then I should see a success message

    Examples:
      | name       | email                  | subject         | message                    |
      | John Doe   | john@example.com       | General Inquiry | I have a question          |
      | Jane Smith | jane@example.com       | Support Request | I need help                |
      | Bob Wilson | bob@example.com        | Feedback        | Great website!             |
