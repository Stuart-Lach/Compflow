# 📚 Compliance Engine - Documentation Index

Welcome to the Compliance Engine documentation! This index helps you find what you need quickly.

---

## 🚀 Getting Started (Start Here!)

| Document | Purpose | Time |
|----------|---------|------|
| **[QUICKSTART.md](QUICKSTART.md)** | Get running in 5 minutes | 5 min |
| **[GETTING_STARTED.md](GETTING_STARTED.md)** | Detailed setup guide with troubleshooting | 15 min |
| **[README.md](README.md)** | Project overview and main documentation | 10 min |

**Recommended path**: QUICKSTART → GETTING_STARTED → README

---

## 📖 Understanding the System

| Document | Purpose | Audience |
|----------|---------|----------|
| **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** | Complete project overview, architecture, design | Developers, Architects |
| **[docs/compliance_engine_spec_v1.md](docs/compliance_engine_spec_v1.md)** | System specification and business logic | Product, Compliance |
| **[docs/csv_contract_v1.md](docs/csv_contract_v1.md)** | CSV format specification | Integrators, Users |
| **[docs/ruleset_versioning.md](docs/ruleset_versioning.md)** | How tax rules are versioned | Developers, Compliance |
| **[docs/demo_workflow.md](docs/demo_workflow.md)** | Example API workflows | Integrators, Users |

---

## 🛠️ Development

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **[pyproject.toml](pyproject.toml)** | Dependencies and build configuration | Adding dependencies |
| **[.env.example](.env.example)** | Environment variables template | Configuration |
| **Setup Scripts** | Automation scripts | Setup, testing, running |
| - [setup.ps1](setup.ps1) | One-click environment setup | Initial setup |
| - [start_server.ps1](start_server.ps1) | Start the API server | Development |
| - [run_tests.ps1](run_tests.ps1) | Run test suite with coverage | Testing |

---

## 🚢 Deployment

| Document | Purpose | Audience |
|----------|---------|----------|
| **[PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)** | Pre-production readiness checklist | DevOps, SRE |

---

## 🏗️ Code Structure

### Source Code: `src/app/`

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| **[src/app/](src/app/)** | Main application | `main.py`, `config.py` |
| **[src/app/api/v1/](src/app/api/v1/)** | API routes | `routes_runs.py`, `routes_rulesets.py` |
| **[src/app/services/](src/app/services/)** | Business logic | `calculation.py`, `validation.py` |
| **[src/app/domain/](src/app/domain/)** | Domain models | `models.py`, `schema.py` |
| **[src/app/rulesets/](src/app/rulesets/)** | Tax rules as data | `za_2025_26_v1.py`, `registry.py` |
| **[src/app/storage/](src/app/storage/)** | Database & files | `db.py`, `repo_runs.py` |

### Tests: `tests/`

| File | Tests |
|------|-------|
| **[test_ingestion.py](tests/test_ingestion.py)** | CSV parsing and schema validation |
| **[test_validation.py](tests/test_validation.py)** | Business rule validation |
| **[test_calculation_paye.py](tests/test_calculation_paye.py)** | PAYE tax calculation |
| **[test_calculation_uif.py](tests/test_calculation_uif.py)** | UIF contribution calculation |
| **[test_calculation_sdl.py](tests/test_calculation_sdl.py)** | SDL levy calculation |
| **[test_end_to_end_matches_expected.py](tests/test_end_to_end_matches_expected.py)** | Full integration tests |

---

## 📊 Sample Data

| File | Purpose |
|------|---------|
| **[data/samples/payroll_input_sample_v1.csv](data/samples/payroll_input_sample_v1.csv)** | Sample payroll input (4 employees) |
| **[data/samples/payroll_expected_output_sample_v1.csv](data/samples/payroll_expected_output_sample_v1.csv)** | Expected calculation results |

---

## 🎯 Quick Reference by Task

### I want to...

#### Set up the project
→ [QUICKSTART.md](QUICKSTART.md) or [setup.ps1](setup.ps1)

#### Understand what was built
→ [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

#### Learn the CSV format
→ [docs/csv_contract_v1.md](docs/csv_contract_v1.md)

#### See API examples
→ [docs/demo_workflow.md](docs/demo_workflow.md)

#### Add a new tax year
→ [docs/ruleset_versioning.md](docs/ruleset_versioning.md)

#### Write tests
→ Look at existing tests in [tests/](tests/)

#### Deploy to production
→ [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)

#### Troubleshoot issues
→ [GETTING_STARTED.md](GETTING_STARTED.md) - Troubleshooting section

#### Understand calculations
→ [src/app/services/calculation.py](src/app/services/calculation.py)

#### Modify tax rules
→ [src/app/rulesets/za_2025_26_v1.py](src/app/rulesets/za_2025_26_v1.py)

---

## 📡 API Endpoints Reference

| Method | Endpoint | Description | See |
|--------|----------|-------------|-----|
| GET | `/api/v1/health` | Health check | [routes_health.py](src/app/api/v1/routes_health.py) |
| GET | `/api/v1/rulesets` | List rulesets | [routes_rulesets.py](src/app/api/v1/routes_rulesets.py) |
| GET | `/api/v1/rulesets/{id}` | Get ruleset details | [routes_rulesets.py](src/app/api/v1/routes_rulesets.py) |
| POST | `/api/v1/runs` | Upload CSV | [routes_runs.py](src/app/api/v1/routes_runs.py) |
| GET | `/api/v1/runs/{id}` | Get run details | [routes_runs.py](src/app/api/v1/routes_runs.py) |
| GET | `/api/v1/runs/{id}/results` | Get results | [routes_runs.py](src/app/api/v1/routes_runs.py) |
| GET | `/api/v1/runs/{id}/errors` | Get validation issues | [routes_runs.py](src/app/api/v1/routes_runs.py) |
| GET | `/api/v1/runs/{id}/export` | Export results CSV | [routes_runs.py](src/app/api/v1/routes_runs.py) |

**Live API Docs**: http://localhost:8000/docs (when server is running)

---

## 🔍 Finding Specific Information

### Calculations
- **PAYE**: [src/app/services/calculation.py](src/app/services/calculation.py) - `calculate_paye()`
- **UIF**: [src/app/services/calculation.py](src/app/services/calculation.py) - `calculate_uif()`
- **SDL**: [src/app/services/calculation.py](src/app/services/calculation.py) - `calculate_sdl()`
- **Tax Brackets**: [src/app/rulesets/za_2025_26_v1.py](src/app/rulesets/za_2025_26_v1.py)

### Validation
- **CSV Schema**: [src/app/services/ingestion.py](src/app/services/ingestion.py)
- **Business Rules**: [src/app/services/validation.py](src/app/services/validation.py)

### Storage
- **Database Models**: [src/app/storage/db.py](src/app/storage/db.py)
- **Run Repository**: [src/app/storage/repo_runs.py](src/app/storage/repo_runs.py)
- **File Storage**: [src/app/storage/repo_files.py](src/app/storage/repo_files.py)

### Configuration
- **App Config**: [src/app/config.py](src/app/config.py)
- **Environment**: [.env.example](.env.example)
- **Dependencies**: [pyproject.toml](pyproject.toml)

---

## 📞 Support & Help

### Getting Help
1. Check the troubleshooting section in [GETTING_STARTED.md](GETTING_STARTED.md)
2. Review error messages in terminal output
3. Check the logs (console output when server is running)
4. Verify Python version (3.11+)
5. Ensure virtual environment is activated

### Common Issues
- **Import errors**: Configure Python interpreter in IDE
- **Database locked**: Stop other instances
- **Module not found**: Run `pip install -e .`
- **Port in use**: Use different port with `--port` flag

---

## 🎓 Learning Path

### For New Developers
1. Read [QUICKSTART.md](QUICKSTART.md) - Get it running
2. Upload sample CSV and see results
3. Read [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Understand architecture
4. Review [src/app/services/calculation.py](src/app/services/calculation.py) - See calculations
5. Look at tests - Learn usage patterns
6. Read [docs/compliance_engine_spec_v1.md](docs/compliance_engine_spec_v1.md) - Business logic

### For Integrators
1. Read [docs/csv_contract_v1.md](docs/csv_contract_v1.md) - CSV format
2. Read [docs/demo_workflow.md](docs/demo_workflow.md) - API workflows
3. Test with [Swagger UI](http://localhost:8000/docs) - Interactive testing
4. Review sample CSVs in [data/samples/](data/samples/)

### For Compliance/Tax Experts
1. Read [docs/compliance_engine_spec_v1.md](docs/compliance_engine_spec_v1.md) - Business rules
2. Review [src/app/rulesets/za_2025_26_v1.py](src/app/rulesets/za_2025_26_v1.py) - Tax rules
3. Check [test_calculation_*.py](tests/) - Verify calculations
4. Update tax brackets with official rates

---

## 📝 Document Versions

All documentation is for **Compliance Engine MVP v0.1.0**

Last updated: January 2026

---

## 🎉 Quick Links

- **Setup**: [setup.ps1](setup.ps1)
- **Start**: [start_server.ps1](start_server.ps1)
- **Test**: [run_tests.ps1](run_tests.ps1)
- **Docs**: http://localhost:8000/docs (after starting server)
- **CSV Format**: [docs/csv_contract_v1.md](docs/csv_contract_v1.md)
- **Production**: [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)

---

**Can't find what you're looking for?** Check the main [README.md](README.md) or explore the [src/app/](src/app/) directory.

