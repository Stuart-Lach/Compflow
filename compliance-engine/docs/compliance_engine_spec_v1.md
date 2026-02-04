# Compliance Engine Specification v1

## Overview

The Compliance Engine is an API-first payroll compliance validation and computation system for South Africa. It validates employer-provided payroll data and computes statutory deductions (PAYE, UIF, SDL) before SARS submission.

## Purpose

This system is **NOT** a payroll system. It:
- ✅ Validates payroll data against South African tax rules
- ✅ Computes PAYE, UIF (employee + employer), SDL (employer)
- ✅ Provides deterministic, auditable results
- ✅ Stores evidence for compliance purposes
- ❌ Does NOT process payments
- ❌ Does NOT generate payslips
- ❌ Does NOT submit to SARS
- ❌ Does NOT manage HR workflows

## Core Concepts

### 1. Compliance Run

A compliance run represents a single validation and computation cycle for a payroll batch. Each run:
- Has a unique identifier
- Is associated with a specific ruleset version
- Contains one or more employee records
- Produces computed outputs and validation issues
- Is immutable once created

### 2. Ruleset

A ruleset contains all tax rules, brackets, caps, and thresholds for a specific tax year. Rulesets are:
- Versioned (e.g., `ZA_2025_26_v1`)
- Immutable once published
- Have effective date ranges
- Stored as code/data, not in database

### 3. Evidence

For audit purposes, every run stores:
- Raw uploaded file (bytes)
- Normalized input rows
- Computed outputs per employee
- Validation issues (errors and warnings)
- Timestamps and metadata

## Computation Model

### Gross Income
```
gross_income = basic_salary 
             + overtime_pay 
             + bonus_commission 
             + allowances_taxable 
             + fringe_benefits_taxable 
             + other_earnings
```

### Taxable Income
```
taxable_income = gross_income 
               - pension_contribution_employee 
               - retirement_annuity_employee 
               - medical_aid_contribution_employee 
               - other_pre_tax_deductions
```

### PAYE (Pay-As-You-Earn)
Calculated using progressive tax brackets defined in the ruleset. Monthly tax is derived from annual brackets.

### UIF (Unemployment Insurance Fund)
- Employee contribution: 1% of gross income (capped)
- Employer contribution: 1% of gross income (capped)
- Contractors: 0% (exempt)

### SDL (Skills Development Levy)
- Employer contribution: 1% of gross income
- Only applicable if annual payroll > R500,000
- Contractors: 0% (exempt)

### Net Pay
```
net_pay = gross_income 
        - paye 
        - uif_employee 
        - union_fees 
        - garnishees 
        - other_post_tax_deductions
```

## Status Codes

### Run Status
- `pending`: Run created, processing not started
- `processing`: Validation and computation in progress
- `completed`: Successfully processed with results
- `failed`: Processing failed due to hard errors

### Validation Issue Severity
- `error`: Hard failure - row cannot be processed
- `warning`: Advisory - row processed with caveats

## API Design Principles

1. **Idempotency**: Repeated uploads of identical CSVs produce identical results
2. **Immutability**: Runs cannot be modified after creation
3. **Traceability**: Every computation links to a specific ruleset version
4. **Determinism**: Same inputs always produce same outputs

