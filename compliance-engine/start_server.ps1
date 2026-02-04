# Start Server Script
# Launches the FastAPI development server

Write-Host "=== Starting Compliance Engine Server ===" -ForegroundColor Green

# Activate virtual environment if not already active
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    .\.venv\Scripts\Activate.ps1
}

Write-Host "`nStarting server..." -ForegroundColor Cyan
Write-Host "API will be available at:" -ForegroundColor Yellow
Write-Host "  - http://localhost:8000" -ForegroundColor White
Write-Host "  - http://localhost:8000/docs (Swagger UI)" -ForegroundColor White
Write-Host "  - http://localhost:8000/redoc (ReDoc)" -ForegroundColor White
Write-Host "`nPress Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start uvicorn
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

