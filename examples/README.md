# AI Playwright Framework - Examples

Welcome to the examples directory! This folder contains working examples demonstrating various features and capabilities of the AI Playwright Framework.

## 📁 Available Examples

### 1. [simple_login/](./simple_login/)
**Level:** Beginner
**Time:** 10 minutes
**Demonstrates:** Basic test creation, page objects, BDD scenarios

A complete example showing how to:
- Record a test with Playwright
- Ingest the recording
- Generate page objects automatically
- Convert to BDD scenarios
- Run tests successfully

**Perfect for:** First-time users learning the framework

**Key Learnings:**
- Page Object Model basics
- BDD scenario writing
- Test project structure
- Running tests with CLI

---

### 2. [e_commerce/](./e_commerce/)
**Level:** Intermediate
**Time:** 30 minutes
**Demonstrates:** Complex user journeys, state management, multiple page objects

A comprehensive example testing an e-commerce application with:
- Browse products
- Search functionality
- Add to cart
- Checkout process
- User account management

**Perfect for:** Users ready for real-world testing scenarios

**Key Learnings:**
- Multi-page workflows
- State management (cart, session)
- Data-driven testing
- Page object composition
- Complex assertions

---

### 3. [api_testing/](./api_testing/)
**Level:** Intermediate
**Time:** 20 minutes
**Demonstrates:** API validation, schema testing, contract testing

API testing capabilities including:
- Request/response validation
- JSON schema validation
- Contract testing
- Authentication handling
- Performance monitoring

**Perfect for:** Backend API testing and validation

**Key Learnings:**
- API request validation
- Schema validation
- Contract testing
- Performance testing
- Error scenario testing

---

### 4. [visual_regression/](./visual_regression/)
**Level:** Advanced
**Time:** 25 minutes
**Demonstrates:** Screenshot comparison, baseline management

Visual regression testing with:
- Baseline screenshot capture
- Visual diff generation
- Ignore regions for dynamic content
- Multi-viewport testing
- Cross-browser comparison

**Perfect for:** UI consistency and design testing

**Key Learnings:**
- Screenshot comparison
- Baseline management
- Dynamic content handling
- Responsive testing
- Cross-browser testing

---

## 🚀 Quick Start

### Run Your First Example

```bash
# 1. Start with the simple login example
cd examples/simple_login

# 2. Record the test (or use the provided recording)
playwright codegen https://the-internet.herokuapp.com/login --target=python

# 3. Ingest the recording
cpa ingest recordings/login.spec.js

# 4. Run the test
cpa run test
```

### Run All Examples

```bash
# Simple login
behave examples/simple_login/features/

# E-commerce (when ready)
behave examples/e_commerce/features/

# API testing
behave examples/api_testing/features/

# Visual regression
behave examples/visual_regression/features/
```

---

## 📖 Learning Path

We recommend following this path for the best learning experience:

### Step 1: Simple Login (Beginner)
**Start here** if you're new to the framework.

**You'll learn:**
- Basic recording and ingestion
- Page object model basics
- BDD scenario structure
- Running tests

**Time:** 10 minutes

---

### Step 2: E-commerce (Intermediate)
**Next step** after mastering simple login.

**You'll learn:**
- Complex user workflows
- Multiple page objects
- State management
- Data-driven testing

**Time:** 30 minutes

---

### Step 3: Choose Your Path

**For API Testing:**
- Go to [api_testing/](./api_testing/)
- Learn request validation
- Master schema testing

**For Visual Testing:**
- Go to [visual_regression/](./visual_regression/)
- Learn screenshot comparison
- Master baseline management

---

## 🛠️ Prerequisites

Before running examples, ensure you have:

```bash
# 1. Install the framework
pip install claude-playwright-agent

# 2. Install Playwright browsers
playwright install --with-deps

# 3. Configure API key
export GLM_API_KEY=your-api-key-here

# 4. Verify installation
cpa --version
```

---

## 📂 Common Files Across Examples

Each example may contain:

```
example_name/
├── features/           # BDD feature files
│   └── *.feature       # Gherkin scenarios
├── pages/              # Page objects
│   ├── __init__.py
│   └── *_page.py       # Page object classes
├── recordings/         # Playwright recordings
│   └── *.spec.js       # Recorded tests
├── test_data/          # Test data files (optional)
└── README.md           # Example documentation
```

---

## 🎯 By Feature

### Page Object Model
All examples demonstrate POM:
- [simple_login](./simple_login/) - Basic POM
- [e_commerce](./e_commerce/) - Advanced POM with composition

### BDD Testing
All examples use BDD:
- [simple_login/features/login.feature](./simple_login/) - Basic scenarios
- [e_commerce/features/](./e_commerce/) - Complex scenarios

### Specific Skills

**Recording & Ingestion:**
- [simple_login](./simple_login/) - Basic workflow

**Intelligent Waits:**
- All examples use intelligent waits for reliable testing

**Self-Healing:**
- All examples benefit from automatic selector healing

**API Testing:**
- [api_testing](./api_testing/) - Dedicated API testing

**Visual Testing:**
- [visual_regression](./visual_regression/) - Screenshot comparison

---

## 💡 Tips for Success

### 1. Start Simple
Begin with [simple_login](./simple_login/) to understand basics.

### 2. Read the Documentation
Each example has detailed README with step-by-step instructions.

### 3. Experiment
Modify examples to fit your needs - that's how you learn!

### 4. Check Logs
If tests fail, check the logs for detailed error messages.

### 5. Use AI Assistance
The framework's AI agents can help debug and fix issues.

---

## 🐛 Troubleshooting

### Common Issues

**Issue:** Example won't run
```bash
# Solution: Check installation
cpa --version
playwright --version
```

**Issue:** Selector failures
```bash
# Solution: Enable self-healing
# Edit config/config.yaml: self_healing: true
```

**Issue:** Tests timeout
```bash
# Solution: Increase timeout in config
# Or use intelligent waits
```

---

## 📚 Additional Resources

- [Quick Start Guide](../docs/quick_start.md)
- [Page Objects Guide](../docs/page_objects.md)
- [Intelligent Waits Guide](../docs/intelligent_waits.md)
- [CLI Reference](../docs/cli_reference.md)
- [Skills Catalog](../SKILLS_CATALOG.md)

---

## 🤝 Contributing

Have an idea for a new example? We'd love to see it!

**Good example candidates:**
- Mobile app testing
- Performance testing
- Accessibility testing
- Security testing
- Database testing

**Contributing Guide:**
1. Fork the repository
2. Create your example in a new folder
3. Add comprehensive README
4. Submit a pull request

---

## 📞 Support

If you need help with any example:

1. Check the example's README for specific instructions
2. Review the [troubleshooting section](#troubleshooting)
3. Check the [main documentation](../docs/)
4. Open an issue on GitHub

---

**Happy Testing! 🎉**

Remember: The best way to learn is by doing. Start with [simple_login](./simple_login/) and work your way up!
