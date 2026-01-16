# E3.2 - Recording Validation

**Skill:** `e3_2_playwright_parser`
**Version:** 1.0.0
**Author:** Claude Playwright Agent Team

## Overview

The Recording Validation skill validates parsed recordings for correctness, completeness, and compatibility. It detects common issues and provides actionable feedback.

## Capabilities

- Validate action sequences
- Check selector validity
- Detect orphaned actions
- Verify timing consistency
- Generate validation reports

## Usage

```python
validator = ValidationAgent()

# Validate recording
result = await validator.run("validate", {
    "recording": {...parsed_recording...}
})

# Get validation report
report = await validator.run("report", {
    "recording_id": "rec_001"
})
```

## Validation Rules

| Rule | Description | Severity |
|------|-------------|----------|
| `selector_exists` | All selectors must be valid | Error |
| `action_order` | Actions must be in logical order | Warning |
| `timing_consistency` | No negative time deltas | Error |
| `no_orphans` | All actions have context | Warning |

## See Also

- [E3.1 - Recording Ingestion](./e3_1_parsing.md)
- [E3.3 - Action Extraction](./e3_3_enrichment.md)
