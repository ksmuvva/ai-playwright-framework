# E3.3 - Action Extraction & Enrichment

**Skill:** `e3_3_action_extraction`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

The Action Extraction & Enrichment skill extracts meaningful test actions from recordings and enriches them with additional context and metadata.

## Capabilities

- Extract actions from recordings
- Classify action types
- Add action metadata
- Infer user intent
- Generate action descriptions

## Usage

```python
extractor = ActionExtractionAgent()

# Extract actions
actions = await extractor.run("extract", {
    "recording": {...parsed_recording...}
})

# Enrich actions
enriched = await extractor.run("enrich", {
    "actions": [...actions...],
    "context": {...}
})
```

## Action Types

| Type | Description | Example |
|------|-------------|---------|
| `navigation` | Page navigation | `goto` |
| `click` | Element click | `click` |
| `input` | Text input | `fill` |
| `select` | Dropdown selection | `select_option` |
| `wait` | Wait for condition | `wait_for_selector` |

## See Also

- [E3.1 - Recording Ingestion](./e3_1_parsing.md)
- [E3.2 - Recording Validation](./e3_2_validation.md)
