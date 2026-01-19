@search
Feature: Search Functionality
  As a website visitor
  I want to search for content
  So that I can quickly find what I'm looking for

  Background:
    Given I am on the homepage

  Scenario: Search for existing item
    When I enter "teddy bear" in the search box
    And I click the search button
    Then I should see search results
    And the results should contain "teddy bear"

  Scenario: Search with no results
    When I enter "xyz123nonexistent" in the search box
    And I click the search button
    Then I should see a "No results found" message

  Scenario: Search box is visible on all pages
    Then I should see the search box on the homepage
    When I navigate to the "Products" page
    Then I should see the search box on the Products page

  @data-driven
  Scenario Outline: Search for various products
    When I enter "<product_name>" in the search box
    And I click the search button
    Then I should see search results

    Examples:
      | product_name  |
      | teddy bear    |
      | laptop        |
      | coffee mug    |
