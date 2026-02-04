# Implementation Checklist - Ingestion & Validation Services

## ✅ Completed

### ingestion.py
- [x] Parse CSV bytes input
- [x] Support UTF-8 and Latin-1 encoding
- [x] Validate required columns present
- [x] Normalize empty numeric fields to Decimal("0")
- [x] Parse dates in YYYY-MM-DD format
- [x] Extract RunContext from first row
- [x] Return (rows, run_context) tuple
- [x] Handle all 8 required columns
- [x] Handle all 19 optional columns
- [x] Validate enums (employment_type, payroll_frequency, residency_status)
- [x] Normalize negative values to 0
- [x] Remove currency symbols (R, commas)
- [x] Skip rows with critical errors
- [x] Type hints throughout
- [x] Comprehensive docstrings

### validation.py
- [x] Return structured List[ValidationIssue]
- [x] ValidationIssue with required fields: code, severity, field, row_index, message
- [x] Severity as string: "error", "warn", "info"
- [x] 0-based row_index
- [x] Date range validation
- [x] Basic salary > 0 validation
- [x] Gross income > 0 validation
- [x] Contractor UIF/SDL warnings
- [x] SDL liability logic (override, estimate, threshold)
- [x] Pre-tax deductions warnings
- [x] Helper functions: filter_errors, has_errors, get_valid_row_indices
- [x] is_sdl_liable() business logic
- [x] is_uif_applicable() business logic
- [x] Type hints throughout
- [x] Comprehensive docstrings

### calculation.py ✅ NEW
- [x] Orchestrate PAYE, UIF, SDL computations
- [x] Return per-employee results
- [x] Return employer totals
- [x] Include ruleset_version_used
- [x] CalculationResult dataclass
- [x] calculate_compliance_run() main entry point
- [x] calculate_employee() for single employee
- [x] calculate_paye() with tax brackets
- [x] calculate_uif() with caps
- [x] calculate_sdl() with rates
- [x] calculate_totals() aggregation
- [x] Type hints throughout
- [x] Comprehensive docstrings

### evidence.py ✅ NEW
- [x] Repository pattern (IEvidenceRepository interface)
- [x] EvidenceRepository concrete implementation
- [x] Store raw input files
- [x] Store normalized rows (via ComplianceRun)
- [x] Store validation issues
- [x] Store calculation results
- [x] Store metadata (timestamps, ruleset version)
- [x] create_compliance_run() with RunContext
- [x] persist_compliance_run() function
- [x] store_raw_file() / retrieve_raw_file()
- [x] get_compliance_run() retrieval
- [x] generate_results_csv() export
- [x] Repository getter/setter functions
- [x] Designed for Postgres migration
- [x] Type hints throughout
- [x] Comprehensive docstrings

### Documentation
- [x] INGESTION_VALIDATION_IMPLEMENTATION.md created
- [x] CALCULATION_EVIDENCE_IMPLEMENTATION.md created ✅ NEW
- [x] Usage examples provided
- [x] Breaking changes documented
- [x] Integration points identified
- [x] Repository pattern explained ✅ NEW
- [x] Migration path to Postgres documented ✅ NEW

---

## 🔄 Next Actions Required

### 1. Update Calling Code
Files that need updates for new signatures:

- [ ] `src/app/api/v1/routes_runs.py`
  - Update to use `parse_csv() -> (rows, run_context)`
  - Update to use `validate_rows() -> List[ValidationIssue]`
  - Use new ValidationIssue structure

- [ ] `src/app/services/evidence.py`
  - Update `create_run()` to accept RunContext
  - Update to work with new ValidationIssue structure

- [ ] `tests/test_ingestion.py`
  - Update for new return signature
  - Add tests for RunContext extraction
  - Add tests for empty field normalization

- [ ] `tests/test_validation.py`
  - Update for new ValidationIssue structure
  - Update for new return signature
  - Add tests for helper functions

- [ ] `tests/test_end_to_end_matches_expected.py`
  - Update for new flow
  - Verify integration works

### 2. Test Suite Updates
- [ ] Run existing tests to identify failures
- [ ] Update test assertions for new API
- [ ] Add new test cases for:
  - Empty field normalization
  - RunContext extraction
  - ValidationIssue structure
  - Helper functions

### 3. Integration Testing
- [ ] Test with sample CSV files
- [ ] Verify empty fields normalize to 0
- [ ] Verify date parsing works
- [ ] Verify enum validation works
- [ ] Verify error vs warning distinction
- [ ] Verify run context extraction

---

## 📋 Testing Checklist

### Manual Testing
- [ ] Upload sample CSV with empty numeric fields → verify normalized to 0
- [ ] Upload CSV with invalid dates → verify error handling
- [ ] Upload CSV with invalid enums → verify error handling
- [ ] Upload CSV with contractor → verify UIF/SDL warning
- [ ] Upload CSV with SDL scenarios → verify warnings/info messages
- [ ] Upload CSV with negative values → verify normalized to 0

### Automated Testing
- [ ] Run: `pytest tests/test_ingestion.py -v`
- [ ] Run: `pytest tests/test_validation.py -v`
- [ ] Run: `pytest tests/test_end_to_end_matches_expected.py -v`
- [ ] Run: `pytest tests/ -v` (full suite)

---

## 🎯 Success Criteria

### Code Quality
- [x] Type hints on all functions
- [x] Docstrings on all functions
- [x] Clear separation of concerns
- [x] Error handling implemented
- [x] No features outside MVP scope

### Functionality
- [ ] All tests passing
- [ ] Sample CSV uploads successfully
- [ ] Empty fields normalize to 0
- [ ] Validation issues structured correctly
- [ ] Integration with rest of system works

### Documentation
- [x] Implementation documented
- [x] Usage examples provided
- [x] Breaking changes noted
- [x] API clearly described

---

## 📝 Notes

### Key Design Decisions
1. **Separation**: Ingestion handles parsing, validation handles business rules
2. **Normalization**: Empty numeric fields → 0 (not None)
3. **Structure**: ValidationIssue with exact fields as specified
4. **Errors**: Ingestion skips bad rows, validation reports all issues
5. **RunContext**: Shared run-level data extracted from first row

### Breaking Changes to Address
- `parse_csv()` return signature changed
- `validate_rows()` return signature changed
- ValidationIssue structure changed
- Need to update all callers

### Integration Points
- `routes_runs.py` - Main consumer
- `evidence.py` - Stores run context and issues
- `calculation.py` - Uses validation helpers
- Tests - Need updates for new API

---

## 🚀 Ready for Next Steps

The ingestion and validation services are **complete and ready**. The next step is to update the calling code and tests to use the new API signatures and structures.

**Priority**: Update `routes_runs.py` first, then run end-to-end tests to verify integration.

