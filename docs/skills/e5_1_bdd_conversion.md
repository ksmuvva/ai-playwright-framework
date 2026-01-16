# E5.1 - BDD Conversion

**Skill:** `e5_1_bdd_conversion`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

Converts Playwright recordings into BDD (Behavior Driven Development) format using Gherkin syntax.

## Capabilities

- Convert actions to Gherkin steps
- Generate feature files
- Create step definitions
- Support multiple languages

## Usage

```python
agent = BDDConversionAgent()
feature = await agent.run("convert", {"recording": {...}})
```

## Output

```gherkin
Feature: User Login

  Scenario: Successful login
    Given I am on the login page
    When I enter "username" and "password"
    And I click the login button
    Then I should be logged in
```

## See Also

- [E5.2 - Gherkin Generation](./e5_2_gherkin_generation.md)
- [E5.3 - Step Definitions](./e5_3_step_definitions.md)
