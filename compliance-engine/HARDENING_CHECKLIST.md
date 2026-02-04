# 🎯 HARDENING IMPLEMENTATION CHECKLIST

Use this checklist to verify all hardening changes are properly deployed and working.

---

## ✅ PRE-DEPLOYMENT CHECKLIST

### Code Review
- [x] Task 1: Package discovery fixed in pyproject.toml
- [x] Task 2: payroll_run_id added to all models and repositories
- [x] Task 3: Row preservation with fallbacks implemented
- [x] Task 4: Run-level validations separated
- [x] Task 5: Rounding documented and tested
- [ ] Task 6: Excel values extracted (blocked - needs workbook)
- [ ] Task 7: Excel match test implemented (blocked - needs workbook)

### Documentation Review
- [x] HARDENING_SUMMARY.md created
- [x] HARDENING_PROGRESS_REPORT.md created
- [x] DATABASE_MIGRATION_REQUIRED.md created
- [x] Migration script created
- [x] Excel extraction script created
- [x] Test template created
- [x] Inline code comments added

---

## 🔧 DEPLOYMENT CHECKLIST

### Environment Preparation
- [ ] Backup existing database (if production)
- [ ] Note current database location
- [ ] Verify Python 3.11+ installed
- [ ] Verify virtual environment activated

### Installation
- [ ] Run: `git pull` (or copy updated files)
- [ ] Run: `pip install -e ".[dev]"`
- [ ] Verify: No installation errors
- [ ] Test: `python -c "from app.services import ingestion; print('OK')"`

### Database Migration
- [ ] **If development**: `Remove-Item compliance.db -Force`
- [ ] **If production**: `python scripts\migrate_add_payroll_run_id.py`
- [ ] Verify: Migration script reports success
- [ ] Verify: Database contains payroll_run_id column
- [ ] Verify: Existing runs updated (if applicable)

### Server Testing
- [ ] Start server: `.\start_server.ps1`
- [ ] Check: No startup errors in console
- [ ] Check: Database initialized successfully
- [ ] Open: http://localhost:8000/docs (Swagger UI)

---

## 🧪 FUNCTIONAL TESTING CHECKLIST

### Test 1: Basic Upload
- [ ] Upload test CSV via Swagger UI or curl
- [ ] Verify: Returns 200 OK
- [ ] Verify: Response includes `payroll_run_id` field
- [ ] Verify: `payroll_run_id` matches value from CSV
- [ ] Verify: `run_id` is different from `payroll_run_id`

### Test 2: Get Run Details
- [ ] GET /api/v1/runs/{run_id}
- [ ] Verify: Returns 200 OK
- [ ] Verify: Response includes `payroll_run_id` field
- [ ] Verify: `payroll_run_id` matches CSV value
- [ ] Check: totals are present

### Test 3: Get Results
- [ ] GET /api/v1/runs/{run_id}/results
- [ ] Verify: Returns 200 OK
- [ ] Verify: Response includes `payroll_run_id` field
- [ ] Verify: Response includes `ruleset_version_used` field
- [ ] Check: Per-employee results present

### Test 4: Get Errors
- [ ] GET /api/v1/runs/{run_id}/errors
- [ ] Verify: Returns 200 OK
- [ ] Verify: Response includes `payroll_run_id` field
- [ ] Check: Validation issues listed correctly

### Test 5: Export CSV
- [ ] GET /api/v1/runs/{run_id}/export
- [ ] Verify: Returns CSV file
- [ ] Open CSV in Excel/text editor
- [ ] Verify: Metadata includes `# Payroll Run ID` line
- [ ] Verify: Payroll Run ID matches CSV input
- [ ] Check: Totals row present at bottom

### Test 6: Row Preservation
- [ ] Create test CSV with intentional errors:
  - Missing employee_id
  - Invalid date format
  - Zero basic_salary
- [ ] Upload CSV
- [ ] Verify: No silent row drops
- [ ] GET /api/v1/runs/{run_id}/errors
- [ ] Verify: All invalid rows flagged
- [ ] Verify: MISSING_EMPLOYEE_ID error present

### Test 7: Run-Level Validations
- [ ] Create CSV without annual_payroll_estimate
- [ ] Upload CSV with 3+ employees
- [ ] GET /api/v1/runs/{run_id}/errors
- [ ] Verify: SDL_ESTIMATE_MISSING appears once
- [ ] Verify: NOT repeated per employee
- [ ] Check: row_index = -1 for run-level issues

### Test 8: Rounding Verification
- [ ] Run: `pytest tests/test_end_to_end_matches_expected.py::test_rounding_matches_excel -v`
- [ ] Verify: Test passes
- [ ] Check: All rounding cases verified

---

## 📊 VALIDATION CHECKLIST

### Database Verification
- [ ] Connect to database
- [ ] Run: `SELECT id, payroll_run_id FROM runs LIMIT 5;`
- [ ] Verify: payroll_run_id column exists
- [ ] Verify: Values are populated
- [ ] Verify: Index exists on payroll_run_id

### API Response Verification
```json
{
  "run_id": "run_20260126...",         // ✓ System-generated
  "payroll_run_id": "PAY_2025_03",     // ✓ From CSV (audit trail)
  "status": "completed",
  "ruleset_version_used": "ZA_2025_26_v1",
  "totals": { ... }
}
```

### CSV Export Verification
```csv
# Compliance Results Export
# Run ID,run_20260126...
# Payroll Run ID,PAY_2025_03        // ✓ From CSV
# Ruleset Version,ZA_2025_26_v1
...
TOTALS
4 employees,125000.00,...           // ✓ Totals row present
```

---

## 🚨 ERROR SCENARIOS TO TEST

### Scenario 1: Invalid CSV Structure
- [ ] Upload CSV with missing required columns
- [ ] Verify: Returns 400 Bad Request
- [ ] Check: Clear error message about missing columns

### Scenario 2: Mixed Valid/Invalid Rows
- [ ] Upload CSV with 5 employees, 2 have errors
- [ ] Verify: Run completes
- [ ] Verify: 5 employees in results (not 3)
- [ ] Check: 2 validation issues listed

### Scenario 3: Database Migration Not Run
- [ ] (Test in separate environment)
- [ ] Start server without migration
- [ ] Attempt CSV upload
- [ ] Verify: Error about missing payroll_run_id column
- [ ] Run migration
- [ ] Retry - should work

### Scenario 4: Duplicate payroll_run_id
- [ ] Upload same CSV twice
- [ ] Verify: Both runs created
- [ ] Verify: Different run_ids, same payroll_run_id
- [ ] Check: Both queryable independently

---

## ⏸️ EXCEL WORKBOOK CHECKLIST (Tasks 6-7)

### When Workbook is Available:

#### Task 6: Extract Values
- [ ] Copy workbook to `data/sa_payroll_workbook.xlsx`
- [ ] Run: `python scripts\extract_excel_values.py`
- [ ] Inspect: Workbook sheets and structure
- [ ] Update: extraction script with cell references
- [ ] Extract: PAYE brackets, UIF caps, SDL values
- [ ] Update: `src/app/rulesets/za_2025_26_v1.py`
- [ ] Mark: Ruleset as FINAL with date
- [ ] Commit: Frozen ruleset values

#### Task 7: Implement Excel Test
- [ ] Extract: Test data from "Inputs" sheet
- [ ] Extract: Expected outputs from "Outputs" sheet
- [ ] Implement: `create_test_csv_from_workbook()`
- [ ] Implement: `load_expected_outputs_from_workbook()`
- [ ] Run: `pytest tests/test_end_to_end_matches_expected.py -v`
- [ ] Verify: All assertions pass
- [ ] Check: Tolerance of 0.01 (1 cent)
- [ ] Fix: Any calculation discrepancies
- [ ] Document: Test results

---

## ✅ SIGN-OFF CHECKLIST

### Code Quality
- [x] All code changes reviewed
- [x] Inline comments added for key decisions
- [x] No hardcoded values (rules are data)
- [x] Type hints present
- [x] Error handling comprehensive

### Testing
- [x] Rounding test passes
- [ ] All existing tests pass
- [ ] New validation tests pass
- [ ] Excel match test passes (pending workbook)

### Documentation
- [x] Technical documentation complete
- [x] Migration guide provided
- [x] User-facing changes documented
- [x] API contract unchanged

### Deployment
- [ ] Development environment tested
- [ ] Staging environment tested
- [ ] Production deployment plan ready
- [ ] Rollback plan documented

### Final Checks
- [ ] Database migration successful
- [ ] All API endpoints working
- [ ] payroll_run_id in all responses
- [ ] No silent row drops
- [ ] Run-level validations execute once
- [ ] Rounding matches Excel
- [ ] Excel test passes (when available)

---

## 📝 NOTES

### Issues Encountered:
_Record any issues found during testing:_

- Issue:
  - Resolution:

- Issue:
  - Resolution:

### Performance Observations:
_Note any performance changes:_

- Upload time:
- Calculation time:
- Database query time:

### Additional Testing:
_Any additional tests performed:_

---

## ✅ FINAL SIGN-OFF

**Tester Name**: ___________________  
**Date**: ___________________  
**Environment**: [ ] Dev [ ] Staging [ ] Production  
**Status**: [ ] Pass [ ] Fail [ ] Conditional  

**Comments**:
_______________________________________________
_______________________________________________

**Approved for**:
- [ ] Development deployment
- [ ] Staging deployment  
- [ ] Production deployment (requires Excel tests pass)

---

**Version**: Hardening v1.0  
**Last Updated**: 2026-01-26

