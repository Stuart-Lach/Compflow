# Ingestion Contracts Quick Reference

## Function Signatures

### parse_csv (Backward Compatible - 2 values)
```python
from app.services.ingestion import parse_csv

rows, run_context = parse_csv(csv_bytes)
```

### parse_csv_with_issues (Full Audit - 3 values)
```python
from app.services.ingestion import parse_csv_with_issues

rows, run_context, parse_issues = parse_csv_with_issues(csv_bytes)
```

## Parse Issue Structure

```python
ValidationIssue(
    code="ROW_PARSE_ERROR",
    severity="error",
    field=None,
    row_index=0,  # 0-based index
    message="Row 2 parsing failed: ValueError(...). Raw data: {'employee_id': '', ...}",
    employee_id="UNKNOWN_ROW_2"
)
```

## When to Use Which

**Use `parse_csv()`** when:
- You only need rows and run context
- You're working with existing code
- Parse errors will be caught elsewhere

**Use `parse_csv_with_issues()`** when:
- You need complete audit trail
- You're implementing APIs
- You want to report all issues to user

## Key Features

✅ No silent row drops  
✅ All parse failures recorded  
✅ Raw row data preserved  
✅ Exception details captured  
✅ Backward compatible  

## Example Usage

```python
# Simple usage (backward compatible)
rows, run_context = parse_csv(csv_data)
for row in rows:
    process(row)

# Full audit trail
rows, run_context, parse_issues = parse_csv_with_issues(csv_data)
validation_issues = validate_rows(rows, ruleset)
all_issues = parse_issues + validation_issues

if any(i.severity == "error" for i in all_issues):
    return {"status": "failed", "issues": all_issues}
```

