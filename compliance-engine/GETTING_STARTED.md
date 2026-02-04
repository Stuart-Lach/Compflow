# Compliance Engine - Getting Started Checklist

## ✅ Setup Steps

Follow these steps to get the compliance engine running locally:

### 1. Navigate to Project Directory
```powershell
cd C:\Users\adria\Compflow\compliance-engine
```

### 2. Run Setup Script
```powershell
.\setup.ps1
```

This will:
- Create a virtual environment
- Install all dependencies
- Set up the development environment

### 3. Verify Installation
```powershell
# Activate virtual environment (if not already active)
.\.venv\Scripts\Activate.ps1

# Check Python version (should be 3.11+)
python --version

# Check installed packages
pip list
```

### 4. Run Tests
```powershell
.\run_tests.ps1
```

Expected output:
- All tests should pass
- Coverage report generated in `htmlcov/index.html`

### 5. Start the Server
```powershell
.\start_server.ps1
```

Server will be available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 6. Test the API

#### Option A: Use Swagger UI
1. Open http://localhost:8000/docs in your browser
2. Try the `/api/v1/health` endpoint
3. Upload the sample CSV using `/api/v1/runs`

#### Option B: Use cURL
```powershell
# Health check
curl http://localhost:8000/api/v1/health

# List rulesets
curl http://localhost:8000/api/v1/rulesets

# Upload sample CSV
curl -X POST "http://localhost:8000/api/v1/runs" `
  -F "file=@data/samples/payroll_input_sample_v1.csv"
```

#### Option C: Use Python
```python
import httpx

# Upload CSV
with open("data/samples/payroll_input_sample_v1.csv", "rb") as f:
    response = httpx.post(
        "http://localhost:8000/api/v1/runs",
        files={"file": ("payroll.csv", f, "text/csv")}
    )

run = response.json()
print(f"Run ID: {run['run_id']}")
print(f"Status: {run['status']}")
print(f"Total PAYE: R{run['totals']['total_paye']}")
```

## 📝 Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize if needed:

```powershell
copy .env.example .env
```

Default configuration:
- Database: SQLite (local file)
- Storage: `./storage/files`
- Log Level: INFO
- Debug Mode: ON

### Database

The SQLite database is created automatically on first run:
- Location: `compliance_engine.db` in project root
- Tables: runs, results, issues
- Auto-initialized on startup

### File Storage

Uploaded files are stored in:
- Location: `./storage/files/`
- Organized by date prefix
- Includes metadata files

## 🧪 Testing

### Run All Tests
```powershell
pytest
```

### Run Specific Test File
```powershell
pytest tests/test_calculation_paye.py -v
```

### Run with Coverage
```powershell
pytest --cov=src --cov-report=html
```

### Run End-to-End Test Only
```powershell
pytest tests/test_end_to_end_matches_expected.py -v
```

## 📊 Sample Data

Two sample CSV files are provided in `data/samples/`:

1. **payroll_input_sample_v1.csv**
   - 4 employees (3 employees, 1 contractor)
   - Various salary levels and deductions
   - Includes all optional fields

2. **payroll_expected_output_sample_v1.csv**
   - Expected results for the input CSV
   - Used by end-to-end test
   - Reference for manual verification

## 🔧 Troubleshooting

### Import Errors in IDE
**Problem**: Red squiggly lines in IDE, "Unresolved reference" errors

**Solution**: Configure Python interpreter in IDE
1. Open Settings/Preferences
2. Go to Project Interpreter
3. Select `.venv/Scripts/python.exe`
4. Reload project

### Database Locked Error
**Problem**: "database is locked" error

**Solution**: Close any database viewers or stop other server instances
```powershell
# Remove the database file and restart
rm compliance_engine.db
```

### Module Not Found
**Problem**: `ModuleNotFoundError: No module named 'app'`

**Solution**: Install package in editable mode
```powershell
pip install -e .
```

### Port Already in Use
**Problem**: "Address already in use" when starting server

**Solution**: Use a different port
```powershell
uvicorn src.app.main:app --reload --port 8001
```

## 📚 Next Steps

### 1. Update Tax Brackets
Edit `src/app/rulesets/za_2025_26_v1.py` with official SARS rates for 2025/26

### 2. Test with Your Data
1. Create your own CSV following the format in `docs/csv_contract_v1.md`
2. Upload via API
3. Verify results

### 3. Add More Test Cases
1. Create additional sample CSV files
2. Add expected output files
3. Create new test cases in `tests/`

### 4. Explore the API
1. Open http://localhost:8000/docs
2. Try all endpoints
3. Review request/response schemas

### 5. Review Documentation
- `docs/compliance_engine_spec_v1.md` - System specification
- `docs/csv_contract_v1.md` - CSV format details
- `docs/ruleset_versioning.md` - How rulesets work
- `docs/demo_workflow.md` - Usage examples
- `PROJECT_SUMMARY.md` - Complete project overview

## ✅ Success Criteria

Your setup is complete when:
- [ ] Tests pass: `pytest` runs successfully
- [ ] Server starts: http://localhost:8000/docs loads
- [ ] Health check works: GET /api/v1/health returns "healthy"
- [ ] Sample CSV uploads: POST /api/v1/runs accepts the sample file
- [ ] Results match: End-to-end test passes
- [ ] Documentation accessible: Can view Swagger UI

## 🎯 Quick Reference

| Task | Command |
|------|---------|
| Setup | `.\setup.ps1` |
| Run tests | `.\run_tests.ps1` or `pytest` |
| Start server | `.\start_server.ps1` |
| View docs | http://localhost:8000/docs |
| Upload CSV | `POST /api/v1/runs` with file |
| Check run | `GET /api/v1/runs/{run_id}` |

## 💡 Tips

1. **Keep server running**: Use `--reload` flag to auto-restart on code changes
2. **Check logs**: Server logs show request/response details
3. **Use Swagger UI**: Interactive API testing without cURL
4. **Verify database**: Use DB Browser for SQLite to inspect data
5. **Test frequently**: Run tests after making changes

## 🆘 Getting Help

If you encounter issues:

1. Check error messages in terminal
2. Review logs in console output
3. Verify Python version (3.11+)
4. Ensure virtual environment is activated
5. Check that all dependencies installed correctly

## 🎉 You're Ready!

Once all checklist items are complete, you have a fully functional compliance engine ready for:
- CSV upload and processing
- Tax calculation (PAYE, UIF, SDL)
- Validation and error reporting
- Evidence storage and audit trails
- API integration

Happy computing! 🚀

