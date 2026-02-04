# Run Tests Script
# Executes the test suite with coverage reporting

Write-Host "=== Running Compliance Engine Tests ===" -ForegroundColor Green

# Activate virtual environment if not already active
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    .\.venv\Scripts\Activate.ps1
}

# Run tests with coverage
Write-Host "`nRunning tests..." -ForegroundColor Cyan
pytest -v --cov=src --cov-report=term-missing --cov-report=html

Write-Host "`nTests complete!" -ForegroundColor Green
Write-Host "Coverage report: htmlcov/index.html" -ForegroundColor Cyan

