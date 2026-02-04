# CSV Contract v1

## Overview

This document defines the canonical CSV format for payroll data ingestion into the Compliance Engine.

## File Requirements

- **Encoding**: UTF-8
- **Delimiter**: Comma (`,`)
- **Header Row**: Required (first row)
- **Line Endings**: CRLF or LF accepted

## Required Columns

| Column | Type | Format | Description |
|--------|------|--------|-------------|
| `payroll_run_id` | String | Any | Unique identifier for this payroll run |
| `company_id` | String | Any | Company/employer identifier |
| `pay_date` | Date | YYYY-MM-DD | Date of payment |
| `tax_year` | String | YYYY_YY | Tax year (e.g., `2025_26`) |
| `payroll_frequency` | Enum | See below | Payment frequency |
| `employee_id` | String | Any | Unique employee identifier |
| `employment_type` | Enum | See below | Employment classification |
| `basic_salary` | Decimal | Positive | Basic salary amount |

## Optional Columns

### Payroll Context
| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `annual_payroll_estimate` | Decimal | null | Annual payroll for SDL determination |
| `is_sdl_liable_override` | Boolean | null | Override SDL liability calculation |
| `ruleset_version_override` | String | null | Force specific ruleset version |

### Employee Context
| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `residency_status` | Enum | `resident` | Tax residency status |
| `employment_start_date` | Date | null | Employment start date |
| `employment_end_date` | Date | null | Employment end date |

### Earnings
| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `overtime_pay` | Decimal | 0 | Overtime earnings |
| `bonus_commission` | Decimal | 0 | Bonuses and commissions |
| `allowances_taxable` | Decimal | 0 | Taxable allowances |
| `allowances_non_taxable` | Decimal | 0 | Non-taxable allowances |
| `fringe_benefits_taxable` | Decimal | 0 | Taxable fringe benefits |
| `reimbursements` | Decimal | 0 | Expense reimbursements |
| `other_earnings` | Decimal | 0 | Other taxable earnings |

### Pre-Tax Deductions
| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `pension_contribution_employee` | Decimal | 0 | Employee pension contribution |
| `retirement_annuity_employee` | Decimal | 0 | Retirement annuity contribution |
| `medical_aid_contribution_employee` | Decimal | 0 | Medical aid contribution |
| `other_pre_tax_deductions` | Decimal | 0 | Other pre-tax deductions |

### Post-Tax Deductions
| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `union_fees` | Decimal | 0 | Union membership fees |
| `garnishees` | Decimal | 0 | Court-ordered deductions |
| `other_post_tax_deductions` | Decimal | 0 | Other post-tax deductions |

## Enum Values

### `payroll_frequency`
- `monthly` - Once per month (12 periods/year)
- `weekly` - Once per week (52 periods/year)
- `fortnightly` - Every two weeks (26 periods/year)

### `employment_type`
- `employee` - Standard employee (UIF and SDL applicable)
- `contractor` - Independent contractor (UIF and SDL = 0)

### `residency_status`
- `resident` - South African tax resident
- `non_resident` - Non-resident for tax purposes

## Validation Rules

### Schema Validation (Hard Failures)
1. All required columns must be present
2. Date fields must be valid YYYY-MM-DD format
3. Enum fields must contain valid values
4. Money fields must be numeric
5. Money fields must not be negative

### Row Validation (Hard Failures)
1. `basic_salary` must be present and > 0
2. `employment_end_date` must be >= `employment_start_date` (if both provided)

### Business Rule Warnings
1. Contractor employment type triggers UIF/SDL = 0 warning
2. Missing `annual_payroll_estimate` without `is_sdl_liable_override` triggers SDL warning

## Example

```csv
payroll_run_id,company_id,pay_date,tax_year,payroll_frequency,employee_id,employment_type,basic_salary,overtime_pay,pension_contribution_employee
RUN001,COMP001,2025-03-25,2025_26,monthly,EMP001,employee,45000.00,2500.00,3600.00
RUN001,COMP001,2025-03-25,2025_26,monthly,EMP002,employee,65000.00,0,5200.00
RUN001,COMP001,2025-03-25,2025_26,monthly,CON001,contractor,35000.00,0,0
```

