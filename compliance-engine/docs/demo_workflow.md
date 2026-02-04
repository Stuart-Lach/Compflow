# Demo Workflow

This document demonstrates a complete workflow using the Compliance Engine API.

## Prerequisites

1. Server running at `http://localhost:8000`
2. Sample CSV file ready

## Step 1: Health Check

Verify the server is running and check current ruleset:

```bash
curl http://localhost:8000/api/v1/health
```

Response:
```json
{
  "status": "healthy",
  "current_ruleset": "ZA_2025_26_v1",
  "timestamp": "2025-03-25T10:00:00Z"
}
```

## Step 2: List Available Rulesets

```bash
curl http://localhost:8000/api/v1/rulesets
```

Response:
```json
{
  "rulesets": [
    {
      "ruleset_id": "ZA_2025_26_v1",
      "description": "South Africa Tax Year 2025/26",
      "effective_from": "2025-03-01",
      "effective_to": "2026-02-28",
      "is_current": true
    }
  ]
}
```

## Step 3: Upload Payroll CSV

```bash
curl -X POST http://localhost:8000/api/v1/runs \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/samples/payroll_input_sample_v1.csv"
```

Response:
```json
{
  "run_id": "run_abc123",
  "status": "completed",
  "ruleset_version_used": "ZA_2025_26_v1",
  "created_at": "2025-03-25T10:05:00Z",
  "issue_count": {
    "errors": 0,
    "warnings": 1
  },
  "totals": {
    "employee_count": 3,
    "total_gross": 147500.00,
    "total_paye": 28542.00,
    "total_uif_employee": 1475.00,
    "total_uif_employer": 1475.00,
    "total_sdl": 1475.00,
    "total_net_pay": 112883.00
  }
}
```

## Step 4: Get Run Details

```bash
curl http://localhost:8000/api/v1/runs/run_abc123
```

Response includes full metadata and totals.

## Step 5: Get Per-Employee Results

```bash
curl http://localhost:8000/api/v1/runs/run_abc123/results
```

Response:
```json
{
  "run_id": "run_abc123",
  "results": [
    {
      "employee_id": "EMP001",
      "gross_income": 47500.00,
      "taxable_income": 43900.00,
      "paye": 8542.00,
      "uif_employee": 475.00,
      "uif_employer": 475.00,
      "sdl": 475.00,
      "net_pay": 37583.00
    },
    // ... more employees
  ],
  "totals": { ... }
}
```

## Step 6: Check Validation Issues

```bash
curl http://localhost:8000/api/v1/runs/run_abc123/errors
```

Response:
```json
{
  "run_id": "run_abc123",
  "issues": [
    {
      "row": 3,
      "employee_id": "CON001",
      "severity": "warning",
      "code": "CONTRACTOR_UIF_SDL_EXEMPT",
      "message": "Contractor: UIF and SDL computed as 0"
    }
  ]
}
```

## Step 7: Export Results

```bash
curl http://localhost:8000/api/v1/runs/run_abc123/export -o results.csv
```

Downloads a CSV with computed results for each employee.

## Error Scenarios

### Invalid CSV Format

If required columns are missing:

```json
{
  "error": "ValidationError",
  "message": "Missing required columns: basic_salary",
  "run_id": null
}
```

### Invalid Data

If row data is invalid:

```json
{
  "run_id": "run_xyz789",
  "status": "completed",
  "issue_count": {
    "errors": 2,
    "warnings": 0
  }
}
```

Check `/runs/{run_id}/errors` for details.

## Using with Python

```python
import httpx

# Upload CSV
with open("payroll.csv", "rb") as f:
    response = httpx.post(
        "http://localhost:8000/api/v1/runs",
        files={"file": ("payroll.csv", f, "text/csv")}
    )

run = response.json()
print(f"Run ID: {run['run_id']}")
print(f"Total PAYE: {run['totals']['total_paye']}")

# Get results
results = httpx.get(f"http://localhost:8000/api/v1/runs/{run['run_id']}/results")
for emp in results.json()["results"]:
    print(f"{emp['employee_id']}: Net Pay = {emp['net_pay']}")
```

