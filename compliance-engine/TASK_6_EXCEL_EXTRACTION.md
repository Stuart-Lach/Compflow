# TASK 6: Extract Values from sa_payroll_workbook.xlsx

## Required Action

The Excel workbook at `C:\Users\adria\Downloads\files\sa_payroll_workbook.xlsx` contains the authoritative tax values.

Please copy this file to: `C:\Users\adria\Compflow\compliance-engine\data/sa_payroll_workbook.xlsx`

Once copied, I will extract the following values and update `src/app/rulesets/za_2025_26_v1.py`:

### Values to Extract:

1. **PAYE Monthly Tax Brackets**
   - Bracket ranges (min_income, max_income)
   - Tax rates
   - Base tax amounts

2. **UIF Configuration**
   - Employee rate (expected: 1%)
   - Employer rate (expected: 1%)
   - Monthly cap

3. **SDL Configuration**
   - SDL rate (expected: 1%)
   - Annual payroll threshold

4. **Tax Rebates**
   - Primary rebate
   - Secondary rebate (age 65+)
   - Tertiary rebate (age 75+)

## Current Status

⏸️ **WAITING** for Excel file to be copied to project directory.

Once available, run the script that will be created to extract and validate values.

