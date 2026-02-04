# 🚀 Quick Start - 5 Minutes to Running

Get the Compliance Engine running in 5 minutes:

## Step 1: Setup (2 minutes)

```powershell
cd C:\Users\adria\Compflow\compliance-engine
.\setup.ps1
```

Wait for installation to complete.

## Step 2: Test (1 minute)

```powershell
.\run_tests.ps1
```

All tests should pass ✅

## Step 3: Start Server (30 seconds)

```powershell
.\start_server.ps1
```

## Step 4: Open Browser (30 seconds)

Navigate to: **http://localhost:8000/docs**

## Step 5: Upload CSV (1 minute)

1. In Swagger UI, expand **POST /api/v1/runs**
2. Click "Try it out"
3. Click "Choose File" and select: `data/samples/payroll_input_sample_v1.csv`
4. Click "Execute"

✅ **You should see:**
- `run_id`: A unique identifier
- `status`: "completed"
- `totals`: Summary with PAYE, UIF, SDL calculated

## 🎉 Done!

Your compliance engine is now running and processing payroll!

## Next Actions

### View Results
Click on **GET /api/v1/runs/{run_id}/results** and paste your run_id to see per-employee breakdowns.

### Check Documentation
- Full setup: `GETTING_STARTED.md`
- Project overview: `PROJECT_SUMMARY.md`
- CSV format: `docs/csv_contract_v1.md`

### Customize
1. Edit tax brackets in `src/app/rulesets/za_2025_26_v1.py`
2. Create your own CSV following the template
3. Upload and test!

---

**Need help?** Check `GETTING_STARTED.md` for troubleshooting.

