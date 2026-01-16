# Simple Login Example

A complete example demonstrating basic login functionality testing with the AI Playwright Framework.

## What This Example Demonstrates

- ✅ Recording a test with Playwright
- ✅ Ingesting the recording
- ✅ Generating page objects
- ✅ Converting to BDD scenarios
- ✅ Running the tests

## Test Scenario

This example tests the login functionality at https://the-internet.herokuapp.com/login

**Steps:**
1. Navigate to login page
2. Enter username: `tomsmith`
3. Enter password: `SuperSecretPassword!`
4. Click login button
5. Verify success message appears
6. Verify logout button is visible
7. Logout and verify login page is shown

## Quick Start

### Step 1: Record the Test

```bash
playwright codegen https://the-internet.herokuapp.com/login --target=python
```

### Step 2: Ingest and Run

```bash
cpa ingest examples/simple_login/recordings/login.spec.js
cpa run test
```

## Next Steps

After this example, try:
- [E-commerce Example](../e_commerce/) - Full user journey
- [API Testing](../api_testing/) - API validation
- [Visual Regression](../visual_regression/) - Screenshot comparison
