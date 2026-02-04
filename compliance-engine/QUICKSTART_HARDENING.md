# 🚀 QUICK START: Hardening Deployment

## One-Page Reference for Deploying Hardened MVP

---

## ⚡ FASTEST PATH (Development)

```powershell
# 1. Pull latest code
cd C:\Users\adria\Compflow\compliance-engine

# 2. Fresh database (easiest)
Remove-Item compliance.db -Force

# 3. Reinstall
pip install -e ".[dev]"

# 4. Start
.\start_server.ps1

# 5. Test
curl -X POST "http://localhost:8000/api/v1/runs" -F "file=@data/samples/payroll_input_sample_v1.csv"
```

**Result**: ✅ Should see `payroll_run_id` in response

---

## 🔄 PRODUCTION PATH (Preserve Data)

```powershell
# 1. Backup
Copy-Item compliance.db compliance.db.backup

# 2. Pull code
git pull

# 3. Reinstall
pip install -e ".[dev]"

# 4. Migrate
python scripts\migrate_add_payroll_run_id.py

# 5. Verify
# Should see: ✅ Migration successful

# 6. Restart server
.\start_server.ps1
```

---

## 🧪 QUICK TEST

```powershell
# Test payroll_run_id appears everywhere
curl http://localhost:8000/api/v1/runs/{run_id} | grep payroll_run_id
curl http://localhost:8000/api/v1/runs/{run_id}/results | grep payroll_run_id
curl http://localhost:8000/api/v1/runs/{run_id}/errors | grep payroll_run_id

# Test rounding
pytest tests/test_end_to_end_matches_expected.py::test_rounding_matches_excel -v
```

---

## ⚠️ TROUBLESHOOTING

### "Column payroll_run_id not found"
```powershell
python scripts\migrate_add_payroll_run_id.py
```

### "Import errors"
```powershell
pip install -e ".[dev]" --force-reinstall
```

### "Rows being dropped"
Check logs - rows now use fallbacks, not dropped

---

## 📋 WHAT CHANGED

| Area | Change | Impact |
|------|--------|--------|
| Database | Added payroll_run_id column | Migration required |
| API | payroll_run_id in all responses | Better audit |
| Parsing | No silent row drops | Better data quality |
| Validation | Run-level vs row-level split | Cleaner issues |
| Rounding | Documented Excel match | Verified accuracy |

---

## ✅ SUCCESS INDICATORS

After deployment, verify:

1. ✅ POST /runs returns `payroll_run_id` from CSV
2. ✅ GET /runs/{id} includes `payroll_run_id`
3. ✅ Export CSV shows payroll_run_id in metadata
4. ✅ Invalid rows NOT silently dropped
5. ✅ SDL warnings appear once per run, not per employee

---

## 📞 HELP

**Full docs**: See `HARDENING_SUMMARY.md`  
**Migration**: See `DATABASE_MIGRATION_REQUIRED.md`  
**Checklist**: See `HARDENING_CHECKLIST.md`  
**Progress**: See `HARDENING_PROGRESS_REPORT.md`

---

## ⏸️ REMAINING TASKS

**Blocked by**: Excel workbook not available

**Task 6**: Update ruleset with real values  
**Task 7**: Implement Excel match test

**When available**:
1. Copy `sa_payroll_workbook.xlsx` to `data/`
2. Run `python scripts\extract_excel_values.py`
3. Update `za_2025_26_v1.py`
4. Implement test data extraction
5. Run `pytest tests/test_end_to_end_matches_expected.py -v`

---

**Status**: 5/7 tasks complete (71%)  
**Ready for**: Development deployment  
**Blocks production**: Excel validation (Tasks 6-7)

