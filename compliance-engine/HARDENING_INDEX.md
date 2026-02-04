# 📚 HARDENING DOCUMENTATION INDEX

Quick navigation to all hardening documentation.

---

## 🎯 START HERE

**For Quick Deployment**:
→ [`QUICKSTART_HARDENING.md`](QUICKSTART_HARDENING.md) - One-page deployment guide

**For Complete Understanding**:
→ [`HARDENING_SUMMARY.md`](HARDENING_SUMMARY.md) - Executive summary

**For Technical Details**:
→ [`HARDENING_PROGRESS_REPORT.md`](HARDENING_PROGRESS_REPORT.md) - Detailed changes

---

## 📖 BY ROLE

### Developers
1. [`HARDENING_PROGRESS_REPORT.md`](HARDENING_PROGRESS_REPORT.md) - What changed and why
2. [`DATABASE_MIGRATION_REQUIRED.md`](DATABASE_MIGRATION_REQUIRED.md) - Schema changes
3. Inline code comments - Implementation details

### QA/Testers
1. [`HARDENING_CHECKLIST.md`](HARDENING_CHECKLIST.md) - Complete test checklist
2. [`QUICKSTART_HARDENING.md`](QUICKSTART_HARDENING.md) - Quick testing steps

### DevOps/SREs
1. [`QUICKSTART_HARDENING.md`](QUICKSTART_HARDENING.md) - Deployment steps
2. [`DATABASE_MIGRATION_REQUIRED.md`](DATABASE_MIGRATION_REQUIRED.md) - Migration procedures
3. `scripts/migrate_add_payroll_run_id.py` - Migration script

### Product/Business
1. [`HARDENING_SUMMARY.md`](HARDENING_SUMMARY.md) - Impact and metrics
2. [`HARDENING_CHECKLIST.md`](HARDENING_CHECKLIST.md) - Acceptance criteria

---

## 📋 BY TOPIC

### Package & Installation
- [`HARDENING_PROGRESS_REPORT.md`](HARDENING_PROGRESS_REPORT.md#task-1-fix-packaging--environment-stability) - Task 1 details
- `pyproject.toml` - Package configuration

### Audit Trail (payroll_run_id)
- [`HARDENING_SUMMARY.md`](HARDENING_SUMMARY.md#task-2-audit-trail-integrity) - Summary
- [`HARDENING_PROGRESS_REPORT.md`](HARDENING_PROGRESS_REPORT.md#task-2-make-payroll_run_id-a-first-class-audit-field) - Detailed changes
- [`DATABASE_MIGRATION_REQUIRED.md`](DATABASE_MIGRATION_REQUIRED.md) - Migration guide
- `scripts/migrate_add_payroll_run_id.py` - Migration script

### Data Preservation
- [`HARDENING_SUMMARY.md`](HARDENING_SUMMARY.md#task-3-data-preservation) - Summary
- [`HARDENING_PROGRESS_REPORT.md`](HARDENING_PROGRESS_REPORT.md#task-3-eliminate-silent-row-drops-in-csv-ingestion) - Implementation
- `src/app/services/ingestion.py` - Code changes

### Validation Architecture
- [`HARDENING_SUMMARY.md`](HARDENING_SUMMARY.md#task-4-validation-architecture) - Summary
- [`HARDENING_PROGRESS_REPORT.md`](HARDENING_PROGRESS_REPORT.md#task-4-separate-run-level-vs-row-level-validations) - Implementation
- `src/app/services/validation.py` - Code changes

### Rounding & Calculations
- [`HARDENING_SUMMARY.md`](HARDENING_SUMMARY.md#task-5-deterministic-rounding) - Summary
- [`HARDENING_PROGRESS_REPORT.md`](HARDENING_PROGRESS_REPORT.md#task-5-enforce-deterministic-rounding) - Verification
- `src/app/services/calculation.py` - Code changes
- `tests/test_end_to_end_matches_expected.py` - Rounding test

### Excel Integration (Pending)
- [`TASK_6_EXCEL_EXTRACTION.md`](TASK_6_EXCEL_EXTRACTION.md) - Requirements for Task 6
- `scripts/extract_excel_values.py` - Extraction script
- `tests/test_end_to_end_matches_expected.py` - Excel match test template

---

## 🔧 SCRIPTS

### Migration
- `scripts/migrate_add_payroll_run_id.py` - Add payroll_run_id column
  - Usage: `python scripts\migrate_add_payroll_run_id.py`
  - Guide: [`DATABASE_MIGRATION_REQUIRED.md`](DATABASE_MIGRATION_REQUIRED.md)

### Excel Extraction (Task 6)
- `scripts/extract_excel_values.py` - Extract values from workbook
  - Usage: `python scripts\extract_excel_values.py`
  - Requires: `data/sa_payroll_workbook.xlsx`
  - Guide: [`TASK_6_EXCEL_EXTRACTION.md`](TASK_6_EXCEL_EXTRACTION.md)

---

## 🧪 TESTS

### Rounding Verification
- `tests/test_end_to_end_matches_expected.py::test_rounding_matches_excel`
- Run: `pytest tests/test_end_to_end_matches_expected.py::test_rounding_matches_excel -v`

### Excel Match Test (Task 7 - Pending)
- `tests/test_end_to_end_matches_expected.py::test_excel_match_synthetic_scenario`
- Status: Template ready, needs data extraction
- Run: `pytest tests/test_end_to_end_matches_expected.py -v`

---

## 📊 STATUS TRACKING

### Completed Tasks (5/7)
- ✅ Task 1: Package stability
- ✅ Task 2: Audit trail (payroll_run_id)
- ✅ Task 3: Data preservation
- ✅ Task 4: Validation architecture
- ✅ Task 5: Deterministic rounding

### Pending Tasks (2/7)
- ⏸️ Task 6: Extract Excel values
- ⏸️ Task 7: Excel match test

**Blocker**: Excel workbook (`sa_payroll_workbook.xlsx`) not yet available

---

## 🚀 QUICK LINKS

### Deployment
- [Quick Start](QUICKSTART_HARDENING.md) - Fastest deployment path
- [Checklist](HARDENING_CHECKLIST.md) - Complete verification
- [Migration](DATABASE_MIGRATION_REQUIRED.md) - Database changes

### Understanding
- [Summary](HARDENING_SUMMARY.md) - Executive overview
- [Progress Report](HARDENING_PROGRESS_REPORT.md) - Technical details
- [Excel Tasks](TASK_6_EXCEL_EXTRACTION.md) - Remaining work

### Code Changes
- `src/app/storage/db.py` - Database model
- `src/app/domain/models.py` - Domain model
- `src/app/storage/repo_runs.py` - Repository
- `src/app/services/evidence.py` - Evidence service
- `src/app/api/v1/routes_runs.py` - API routes
- `src/app/services/ingestion.py` - CSV parsing
- `src/app/services/validation.py` - Validation logic
- `src/app/services/calculation.py` - Calculations

---

## 📞 GETTING HELP

### Common Issues

**"Column payroll_run_id not found"**
→ See: [DATABASE_MIGRATION_REQUIRED.md](DATABASE_MIGRATION_REQUIRED.md)

**"Rows being silently dropped"**
→ Fixed in Task 3. Check logs for fallback warnings.

**"SDL warning appears per employee"**
→ Fixed in Task 4. Now appears once per run.

**"Can't complete Task 6/7"**
→ Requires Excel workbook. See: [TASK_6_EXCEL_EXTRACTION.md](TASK_6_EXCEL_EXTRACTION.md)

### Documentation Hierarchy

```
QUICKSTART_HARDENING.md          ← Start here for fast deployment
    ↓
HARDENING_SUMMARY.md             ← Executive overview
    ↓
HARDENING_PROGRESS_REPORT.md     ← Detailed technical changes
    ↓
HARDENING_CHECKLIST.md           ← Verification steps
    ↓
DATABASE_MIGRATION_REQUIRED.md   ← Migration procedures
    ↓
TASK_6_EXCEL_EXTRACTION.md       ← Excel requirements
    ↓
Code files + inline comments     ← Implementation details
```

---

## 📝 DOCUMENT VERSIONS

| Document | Version | Last Updated | Status |
|----------|---------|--------------|--------|
| QUICKSTART_HARDENING.md | 1.0 | 2026-01-26 | Final |
| HARDENING_SUMMARY.md | 1.0 | 2026-01-26 | Final |
| HARDENING_PROGRESS_REPORT.md | 1.0 | 2026-01-26 | Final |
| HARDENING_CHECKLIST.md | 1.0 | 2026-01-26 | Final |
| DATABASE_MIGRATION_REQUIRED.md | 1.0 | 2026-01-26 | Final |
| TASK_6_EXCEL_EXTRACTION.md | 1.0 | 2026-01-26 | Waiting |
| INDEX.md | 1.0 | 2026-01-26 | Final |

---

**Last Updated**: January 26, 2026  
**Hardening Version**: v1.0  
**Completion**: 71% (5/7 tasks)

