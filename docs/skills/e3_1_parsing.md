# E3.1 - Recording Ingestion & Parsing

**Skill:** `e3_1_ingestion_agent`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

The Recording Ingestion & Parsing skill handles ingesting Playwright recordings from various sources and parsing them into structured test data. It supports multiple recording formats and provides validation.

## Capabilities

- Parse Playwright Trace Viewer recordings
- Convert recordings to test actions
- Validate recording structure
- Extract test metadata
- Handle recording errors

## Usage

```python
ingestion = IngestionAgent()

# Parse recording file
result = await ingestion.run("parse", {
    "recording_path": "recordings/login_test.har",
    "format": "har"
})

# Parse from JSON
result = await ingestion.run("parse_json", {
    "recording_data": {...}
})
```

## Recording Formats Supported

| Format | Extension | Description |
|--------|-----------|-------------|
| HAR | `.har` | HTTP Archive format |
| JSON | `.json` | Playwright recording JSON |
| Trace | `.zip` | Playwright trace file |

## Parsed Output Structure

```json
{
  "actions": [
    {
      "type": "click",
      "selector": "#login-button",
      "timestamp": 1234567890
    }
  ],
  "metadata": {
    "url": "https://example.com",
    "title": "Login Test"
  }
}
```

## See Also

- [E3.2 - Recording Validation](./e3_2_validation.md)
- [E3.3 - Action Extraction](./e3_3_enrichment.md)
