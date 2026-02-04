# Compliance Engine - South Africa Payroll Compliance MVP

An API-first payroll compliance engine for South Africa. This system validates and computes statutory payroll outputs (PAYE, UIF, SDL) **before** SARS submission. It is deterministic and auditable.

## Features

- **CSV Upload**: Upload canonical payroll CSV files for compliance computation
- **PAYE Calculation**: Tax bracket-based Pay-As-You-Earn computation
- **UIF Calculation**: Unemployment Insurance Fund (employee + employer portions)
- **SDL Calculation**: Skills Development Levy (employer)
- **Validation**: Schema validation, business rule validation, and warnings
- **Evidence Storage**: Full audit trail with raw files, normalized data, and computed outputs
- **Versioned Rulesets**: Tax rules stored as data, versioned, with effective dates

## Quick Start

### Prerequisites

- Python 3.11+
- pip or uv package manager

### Installation

#### Option 1: Quick Setup (Windows PowerShell)

```powershell
cd compliance-engine
.\setup.ps1
```

#### Option 2: Manual Setup

```bash
cd compliance-engine

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows CMD:
.\.venv\Scripts\activate.bat
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

#### Option 3: Using uv (faster)

```bash
cd compliance-engine
uv venv
source .venv/bin/activate  # or .\.venv\Scripts\Activate.ps1 on Windows
uv pip install -e ".[dev]"
```

### Running the Server

```bash
# From compliance-engine directory
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_calculation_paye.py -v
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check with current ruleset |
| GET | `/api/v1/rulesets` | List all available rulesets |
| GET | `/api/v1/rulesets/{ruleset_id}` | Get ruleset details |
| POST | `/api/v1/runs` | Upload CSV and create compliance run |
| GET | `/api/v1/runs/{run_id}` | Get run metadata and totals |
| GET | `/api/v1/runs/{run_id}/results` | Get per-employee results |
| GET | `/api/v1/runs/{run_id}/errors` | Get validation issues |
| GET | `/api/v1/runs/{run_id}/export` | Download results as CSV |

## Sample Usage

### Upload a Payroll CSV

```bash
curl -X POST "http://localhost:8000/api/v1/runs" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/samples/payroll_input_sample_v1.csv"
```

### Check Run Results

```bash
curl "http://localhost:8000/api/v1/runs/{run_id}/results"
```

## Project Structure

```
compliance-engine/
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── docs/                          # Documentation
├── data/samples/                  # Sample CSV files
├── src/app/
│   ├── main.py                   # FastAPI application
│   ├── config.py                 # Configuration
│   ├── errors.py                 # Custom exceptions
│   ├── api/v1/                   # API routes
│   ├── services/                 # Business logic
│   ├── domain/                   # Domain models
│   ├── rulesets/                 # Tax rules as data
│   └── storage/                  # Persistence layer
└── tests/                        # Test suite
```

## Documentation

- [Compliance Engine Spec](docs/compliance_engine_spec_v1.md)
- [CSV Contract](docs/csv_contract_v1.md)
- [Ruleset Versioning](docs/ruleset_versioning.md)
- [Demo Workflow](docs/demo_workflow.md)

## License

Proprietary - All rights reserved.

