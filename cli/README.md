# Playwright AI Framework - CLI Tool

AI-powered command-line tool that generates complete test automation frameworks for Playwright with self-healing, smart waits, and AI-powered features.

## 📚 Documentation

For complete documentation, see:
- **[Usage Guide](../docs/guides/USAGE_GUIDE.md)** - Complete CLI reference and examples
- **[Main README](../README.md)** - Project overview
- **[Architecture](../ARCHITECTURE.md)** - Technical design

## 🚀 Quick Start

```bash
# Install globally (when published to NPM)
npm install -g playwright-ai-framework

# Or run from source
npm install
npm run build
npm link

# Initialize a new framework
playwright-ai init

# Record a test
playwright-ai record --url https://your-app.com

# Convert to BDD
playwright-ai convert recordings/your-test.py
```

## 📋 Features

✅ **Complete Framework Generation** - Creates production-ready test frameworks in seconds
✅ **AI-Powered Conversion** - Converts Playwright recordings to BDD scenarios
✅ **Self-Healing Locators** - AI finds elements when locators fail
✅ **Smart Wait Management** - Adapts waits based on performance history
✅ **Test Data Generation** - AI generates realistic test data
✅ **Power Apps Optimization** - Special helpers for Power Apps
✅ **BDD Support** - Behave integration out of the box
✅ **Auto-Screenshots** - Every step automatically captured

## 🏗️ Project Structure

```
cli/
├── src/
│   ├── commands/           # CLI commands
│   │   ├── init.ts        # Framework initialization
│   │   ├── record.ts      # Recording command
│   │   └── convert.ts     # BDD conversion
│   ├── generators/         # Framework generators
│   │   ├── python-generator.ts
│   │   └── template-engine.ts
│   ├── ai/                 # AI integration
│   │   ├── anthropic-client.ts
│   │   └── prompts.ts
│   ├── utils/              # Utilities
│   │   ├── file-utils.ts
│   │   └── logger.ts
│   └── types/              # TypeScript types
│       └── index.ts
├── templates/              # Framework templates
│   └── python/
│       ├── features/
│       ├── steps/
│       ├── helpers/
│       ├── fixtures/
│       └── config/
├── package.json
├── tsconfig.json
└── README.md
```

## 🎯 Commands

### `playwright-ai init`

Initialize a new test automation framework.

```bash
playwright-ai init \
  --language python \
  --project-name my-tests \
  --bdd \
  --power-apps \
  --ai-provider anthropic
```

**Options:**
- `-l, --language` - Framework language (python)
- `-n, --project-name` - Project name
- `--bdd` - Enable BDD (Behave)
- `--power-apps` - Add Power Apps helpers
- `--ai-provider` - AI provider (anthropic|openai|none)

### `playwright-ai record`

Record a new test scenario.

```bash
playwright-ai record \
  --url https://your-app.com \
  --scenario-name login \
  --convert-to-bdd
```

**Options:**
- `-u, --url` - Starting URL
- `-s, --scenario-name` - Scenario name
- `--convert-to-bdd` - Auto-convert after recording

### `playwright-ai convert`

Convert recording to BDD.

```bash
playwright-ai convert recordings/test.py --scenario-name my_test
```

**Arguments:**
- `<recording-file>` - Path to recording

**Options:**
- `-s, --scenario-name` - Override scenario name
- `-o, --output-dir` - Output directory

## 🛠️ Development

### Setup

```bash
# Clone repository
git clone https://github.com/your-org/playwright-ai-framework
cd playwright-ai-framework/cli

# Install dependencies
npm install

# Build
npm run build

# Link for local development
npm link

# Run in development mode
npm run dev -- init --help
```

### Build & Test

```bash
# Build TypeScript
npm run build

# Watch mode
npm run watch

# Run tests
npm test

# Lint
npm run lint
```

### Publishing

```bash
# Build
npm run build

# Test locally
npm link
playwright-ai init

# Publish to NPM
npm publish
```

## 📚 Documentation

- [Usage Guide](./USAGE_GUIDE.md) - Complete usage documentation
- [Main README](../README.md) - Project overview
- [Requirements](../REQUIREMENTS.md) - Detailed requirements
- [Architecture](../ARCHITECTURE.md) - Technical architecture
- [Implementation Plan](../IMPLEMENTATION_PLAN.md) - Build roadmap

## 🏃 Examples

### Example 1: Generate Python Framework

```bash
playwright-ai init \
  --project-name my-automation \
  --language python \
  --bdd \
  --ai-provider anthropic

cd my-automation

# Configure
echo "ANTHROPIC_API_KEY=sk-ant-xxx" >> .env
echo "APP_URL=https://my-app.com" >> .env
echo "TEST_USER=test@example.com" >> .env

# Run example test
behave
```

### Example 2: Record & Convert Test

```bash
# Record
playwright-ai record --url https://shop.com --scenario-name checkout

# Convert to BDD
playwright-ai convert recordings/checkout*.py

# Run
behave features/checkout.feature
```

### Example 3: Power Apps Testing

```bash
playwright-ai init \
  --project-name powerapp-tests \
  --power-apps \
  --ai-provider anthropic

cd powerapp-tests

# Record Power Apps scenario
playwright-ai record \
  --url https://your-org.powerapps.com \
  --scenario-name create_contact \
  --convert-to-bdd

# Run
behave
```

## 🤖 AI Integration

### Anthropic (Claude) - Recommended

```bash
# Get API key from https://console.anthropic.com/
export ANTHROPIC_API_KEY=sk-ant-your-key

# Use in framework
playwright-ai init --ai-provider anthropic
```

**Features:**
- BDD scenario conversion
- Self-healing locators
- Test data generation
- Pattern analysis

### OpenAI (GPT-4)

```bash
# Get API key from https://platform.openai.com/
export OPENAI_API_KEY=sk-your-key

# Use in framework
playwright-ai init --ai-provider openai
```

### No AI (Fallback)

```bash
# Disable AI features
playwright-ai init --ai-provider none
```

**Still includes:**
- Framework generation
- Template-based BDD conversion
- Faker for test data
- Manual locator management

## 🔧 Configuration

### Environment Variables

```bash
# For CLI development
DEBUG=playwright-ai:*        # Enable debug logging
NODE_ENV=development         # Development mode
```

### Template Customization

Templates are located in `templates/python/`. You can customize:

- `helpers/` - Helper functions
- `steps/` - Step definitions
- `features/` - Example features
- `config/` - Configuration files
- `README.md.ejs` - Generated README template

## 🐛 Troubleshooting

### "Command not found: playwright-ai"

```bash
# Link the CLI globally
npm link

# Or use npx
npx playwright-ai init
```

### "TypeError: Cannot read property..."

```bash
# Rebuild
npm run build

# Or run in development mode
npm run dev -- init
```

### "Template not found"

```bash
# Ensure templates are copied during build
npm run build

# Check templates directory
ls templates/python/
```

## 📊 Metrics

**Framework Generation:**
- Time: < 30 seconds
- Files created: 15+
- Lines of code: 2000+

**AI Conversion:**
- Time: < 30 seconds per recording
- Accuracy: > 90%
- Locators extracted: Auto-detected

## 🤝 Contributing

We welcome contributions!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Code Style

- TypeScript with strict mode
- ESLint configuration
- Prettier for formatting

### Testing

```bash
# Run tests
npm test

# Test CLI locally
npm link
playwright-ai init --project-name test-project
```

## 📄 License

MIT License - see [LICENSE](../LICENSE) file

## 🙋 Support

- **Documentation**: [Usage Guide](./USAGE_GUIDE.md)
- **Issues**: [GitHub Issues](https://github.com/your-org/playwright-ai-framework/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/playwright-ai-framework/discussions)

## 🎯 Roadmap

- [x] Python framework generation
- [x] Anthropic AI integration
- [x] BDD support (Behave)
- [x] Self-healing locators
- [x] Smart waits
- [ ] TypeScript framework support
- [ ] OpenAI integration
- [ ] Visual regression testing
- [ ] API test integration
- [ ] Cloud execution support
- [ ] Mobile app testing

---

**Built with ❤️ for testers everywhere**
