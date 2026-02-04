# Compflow - Compliance Engine Project

This directory contains the **Compliance Engine MVP** - an API-first payroll compliance engine for South Africa.

## 📁 Directory Structure

```
Compflow/
├── compliance-engine/         ← The complete MVP project
│   ├── README.md              Main documentation
│   ├── QUICKSTART.md          5-minute setup guide
│   ├── INDEX.md               Documentation index
│   ├── src/app/               Source code
│   ├── tests/                 Test suite
│   ├── docs/                  Technical docs
│   └── data/samples/          Sample CSV files
│
└── README.md                  ← This file
```

## 🚀 Quick Start

```powershell
cd compliance-engine
.\setup.ps1
.\start_server.ps1
```

Then open: http://localhost:8000/docs

## 📚 Documentation

**Start here**: `compliance-engine/QUICKSTART.md` or `compliance-engine/INDEX.md`

## ✅ Status

**COMPLETE** - All MVP requirements delivered:
- 8 API endpoints functional
- PAYE, UIF, SDL calculations working
- CSV upload and validation complete
- Evidence storage implemented
- 50+ tests passing
- Comprehensive documentation

## 🎯 What This Is

An **API-first payroll compliance engine** that:
- Validates payroll data against South African tax rules
- Computes PAYE, UIF, and SDL accurately
- Stores evidence for audit purposes
- Provides REST API for integration

## 🎯 What This Is NOT

- ❌ Not a payroll system (doesn't pay salaries)
- ❌ Not a SARS submission tool (validates before submission)
- ❌ Not an HR system (no employee management)

## 📊 Project Stats

- **Files**: 60+
- **Lines of Code**: 5,000+
- **Tests**: 50+
- **Documentation**: 11 files
- **API Endpoints**: 8

## 🔗 Quick Links

- **Setup Guide**: compliance-engine/GETTING_STARTED.md
- **API Docs**: http://localhost:8000/docs (when running)
- **Project Summary**: compliance-engine/PROJECT_SUMMARY.md
- **Deployment Guide**: compliance-engine/PRODUCTION_CHECKLIST.md

## 💻 Technology

- Python 3.11+
- FastAPI (async web framework)
- SQLAlchemy (database ORM)
- Pydantic (data validation)
- pytest (testing)

## 📞 Getting Help

1. Check `compliance-engine/INDEX.md` to find what you need
2. See `compliance-engine/GETTING_STARTED.md` for troubleshooting
3. Review `compliance-engine/PROJECT_SUMMARY.md` for architecture

---

**Ready to start?** Navigate to `compliance-engine` and run `.\setup.ps1`

