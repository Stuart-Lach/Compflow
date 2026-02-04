# Quick Start Script for Compliance Engine
# Run this script to set up and start the development environment

Write-Host "=== Compliance Engine Setup ===" -ForegroundColor Green

# Check if virtual environment exists
if (-not (Test-Path .venv)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\.venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
python -m pip install -e ".[dev]" --quiet

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host "`nYou can now:" -ForegroundColor Cyan
Write-Host "1. Run tests: pytest" -ForegroundColor White
Write-Host "2. Start server: uvicorn src.app.main:app --reload" -ForegroundColor White
Write-Host "3. View API docs: http://localhost:8000/docs" -ForegroundColor White

