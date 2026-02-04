# Ruleset Versioning

## Overview

Rulesets contain all tax rules, brackets, caps, and thresholds for a specific tax year. They are versioned to ensure deterministic, auditable computations.

## Versioning Scheme

### Version ID Format
```
{COUNTRY}_{TAX_YEAR_START}_{TAX_YEAR_END}_v{VERSION}
```

Examples:
- `ZA_2025_26_v1` - South Africa 2025/26 tax year, version 1
- `ZA_2024_25_v2` - South Africa 2024/25 tax year, version 2 (corrected)

### Tax Year
South African tax year runs from 1 March to 28/29 February:
- `2025_26` = 1 March 2025 to 28 February 2026

## Ruleset Contents

Each ruleset defines:

### Tax Brackets (PAYE)
```python
TAX_BRACKETS = [
    {"min": 0, "max": 237_100, "rate": 0.18, "base": 0},
    {"min": 237_101, "max": 370_500, "rate": 0.26, "base": 42_678},
    # ... more brackets
]
```

### Rebates
```python
REBATES = {
    "primary": 17_235,      # All taxpayers
    "secondary": 9_444,     # Age 65+
    "tertiary": 3_145,      # Age 75+
}
```

### Thresholds
```python
THRESHOLDS = {
    "tax_threshold_under_65": 95_750,
    "tax_threshold_65_to_74": 148_217,
    "tax_threshold_75_plus": 165_689,
}
```

### UIF Configuration
```python
UIF = {
    "employee_rate": 0.01,
    "employer_rate": 0.01,
    "monthly_cap": 17_712.00,  # R177,120 annual / 12
}
```

### SDL Configuration
```python
SDL = {
    "rate": 0.01,
    "annual_payroll_threshold": 500_000,
}
```

## Effective Dates

Each ruleset has:
- `effective_from`: Date the ruleset becomes valid (inclusive)
- `effective_to`: Date the ruleset expires (inclusive, null = current)

## Ruleset Selection

1. If `ruleset_version_override` is provided in input, use that exact version
2. Otherwise, select based on `pay_date`:
   - Find ruleset where `effective_from <= pay_date <= effective_to`
   - If multiple match (shouldn't happen), use highest version number

## Immutability

Once a ruleset is used in a compliance run:
- It MUST NOT be modified
- Corrections require a new version (e.g., v1 → v2)
- The run permanently records which version was used

## Storage

Rulesets are stored as Python code in `src/app/rulesets/`:
```
rulesets/
├── __init__.py
├── registry.py        # Ruleset lookup logic
├── za_2024_25_v1.py   # 2024/25 tax year
└── za_2025_26_v1.py   # 2025/26 tax year
```

This approach:
- Keeps rules in version control
- Makes rules testable
- Ensures deterministic behavior
- Avoids database schema complexity

## Future: Database Storage

For multi-tenant SaaS deployment, rulesets may move to database:
- Store as JSON blobs with version metadata
- Cache in memory for performance
- Maintain immutability through soft versioning

