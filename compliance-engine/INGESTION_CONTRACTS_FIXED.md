# ✅ INGESTION CONTRACTS FIXED - COMPLETE

**Date**: January 27, 2026  
**Status**: All function contracts are now backwards-compatible and consistent

---

## Summary of Changes

### 1. Function Contracts ✅

**`parse_csv(content: bytes) -> Tuple[List[PayrollInputRow], RunContext]`**
- Returns **exactly 2 values** for backwards compatibility
- Calls `parse_csv_with_issues()` internally and discards parse_issues
- Used by all existing unit tests

**`parse_csv_with_issues(content: bytes) -> Tuple[List[PayrollInputRow], RunContext, List[ValidationIssue]]`**
- Returns **exactly 3 values** for full audit trail
- Third value is `parse_issues`: list of ValidationIssue with code="ROW_PARSE_ERROR"
- Each parse issue includes:
  - `code="ROW_PARSE_ERROR"`
  - `severity="error"`
  - `row_index` (0-based)
  - `message` with full exception details and raw row data
  - `employee_id` (or "UNKNOWN_ROW_N" if not available)
- Used by API route for complete error tracking

###2. Test Updates ✅

**Updated tests in `tests/test_ingestion.py`:**

1. **`test_parse_valid_csv()`** - Uses `parse_csv()`, unpacks 2 values
2. **`test_parse_csv_with_optional_fields()`** - Uses `parse_csv()`, 2 values
3. **`test_parse_csv_missing_required_column()`** - Uses `parse_csv()`, expects SchemaValidationError
4. **`test_parse_csv_invalid_date()`** - Uses `parse_csv()`, expects SchemaValidationError
5. **`test_parse_csv_invalid_enum()`** - Uses `parse_csv()`, row preserved with fallback
6. **`test_parse_csv_negative_value()`** - Uses `parse_csv()`, value clamped to 0
7. **`test_parse_csv_multiple_rows()`** - Uses `parse_csv()`, 2 values
8. **`test_parse_csv_empty_optional_fields()`** - Uses `parse_csv()`, 2 values
9. **`test_parse_csv_contractor()`** - Uses `parse_csv()`, 2 values

**New tests added:**

10. **`test_parse_csv_with_issues_returns_3()`** - Tests `parse_csv_with_issues()` returns 3 values for valid CSV
11. **`test_parse_csv_with_issues_invalid_row()`** - Documents behavior for unparseable rows

### 3. API Updates ✅

**`src/app/api/v1/routes_runs.py`:**
- Imports `parse_csv_with_issues` from services
- Calls `parse_csv_with_issues(content)` to get parse issues
- Combines `parse_issues + validation_issues` for complete audit trail
- All issues stored in evidence

### 4. Service Exports ✅

**`src/app/services/__init__.py`:**
- Exports both `parse_csv` and `parse_csv_with_issues`
- Both functions available for import

### 5. End-to-End Test ✅

**`tests/test_end_to_end_matches_expected.py`:**
- Imports `parse_csv_with_issues`
- Uses 3-value return: `rows, run_context, parse_issues`
- Combines parse_issues with validation_issues
- Full audit trail maintained

---

## Implementation Details

### Parse Error Handling

When a row fails to parse:

```python
ValidationIssue(
    code="ROW_PARSE_ERROR",
    severity="error",
    field=None,
    row_index=row_num - 2,  # 0-based
    message=f"Row {row_num} parsing failed: {str(e)}. Raw data: {dict(raw_row)}",
    employee_id=row.get("employee_id", f"UNKNOWN_ROW_{row_num}")
)
```

### No Silent Row Drops

- Every row that fails parsing generates a ValidationIssue
- Raw row data included in message
- Issue stored in evidence
- User sees exactly what failed and why

---

## Testing Strategy

### Unit Tests (backwards compatible)
- Use `parse_csv()` with 2-value return
- Test valid inputs, invalid inputs, edge cases
- No breaking changes to existing tests

### Integration Tests (full audit)
- Use `parse_csv_with_issues()` with 3-value return
- Test parse issue generation
- Verify issue details (code, severity, message, raw data)

### API Tests (full audit)
- API uses `parse_csv_with_issues()`
- Combines parse_issues + validation_issues
- Complete audit trail in responses

---

## Files Modified

1. ✅ `src/app/services/ingestion.py`
   - Added `parse_csv_with_issues()` (3 values)
   - Made `parse_csv()` wrapper (2 values)

2. ✅ `src/app/services/__init__.py`
   - Exported both functions

3. ✅ `src/app/api/v1/routes_runs.py`
   - Uses `parse_csv_with_issues()`
   - Removed duplicate import

4. ✅ `tests/test_ingestion.py`
   - Fixed all tests to use `parse_csv()` (2 values)
   - Added tests for `parse_csv_with_issues()` (3 values)

5. ✅ `tests/test_end_to_end_matches_expected.py`
   - Uses `parse_csv_with_issues()` (3 values)

---

## Design Principles Applied

1. **Backwards Compatibility**: Existing code using `parse_csv()` works unchanged
2. **Explicit Contracts**: Function signatures clearly show return values
3. **Audit Trail**: API uses full 3-value return for complete evidence
4. **No Silent Failures**: Every parse error generates a structured issue
5. **Code Reuse**: `parse_csv()` calls `parse_csv_with_issues()` internally

---

## Success Criteria Met

✅ `parse_csv()` returns exactly 2 values  
✅ `parse_csv_with_issues()` returns exactly 3 values  
✅ Parse issues include ROW_PARSE_ERROR with raw row data  
✅ API uses `parse_csv_with_issues()` for full audit trail  
✅ Tests updated to match contracts  
✅ No breaking changes to existing code  
✅ Complete error transparency  

---

**Result**: All ingestion function contracts are now consistent, backwards-compatible, and provide complete audit trail when needed.

