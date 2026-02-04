# Smoke test for compliance-engine API (PowerShell)

Write-Host "🔥 Starting smoke test..." -ForegroundColor Cyan

# Start server in background
Write-Host "📡 Starting uvicorn server..." -ForegroundColor Yellow
$process = Start-Process -FilePath "uvicorn" -ArgumentList "src.app.main:app --host 0.0.0.0 --port 8000" -PassThru -NoNewWindow

# Wait for server to start
Write-Host "⏳ Waiting for server to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

try {
    # Test health endpoint
    Write-Host "🏥 Testing /health endpoint..." -ForegroundColor Yellow
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    Write-Host "Response: $($healthResponse | ConvertTo-Json)" -ForegroundColor Gray

    if ($healthResponse.status -eq "healthy") {
        Write-Host "✅ Health check passed!" -ForegroundColor Green
    } else {
        Write-Host "❌ Health check failed!" -ForegroundColor Red
        throw "Health check returned unexpected status"
    }

    # Test root endpoint
    Write-Host "🏠 Testing root endpoint..." -ForegroundColor Yellow
    $rootResponse = Invoke-RestMethod -Uri "http://localhost:8000/" -Method Get
    Write-Host "Response: $($rootResponse | ConvertTo-Json)" -ForegroundColor Gray

    if ($rootResponse.name -eq "compliance-engine") {
        Write-Host "✅ Root endpoint passed!" -ForegroundColor Green
    } else {
        Write-Host "❌ Root endpoint failed!" -ForegroundColor Red
        throw "Root endpoint returned unexpected data"
    }

    # Test API health (with prefix)
    Write-Host "🏥 Testing /api/v1/health endpoint..." -ForegroundColor Yellow
    $apiHealthResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/health" -Method Get
    Write-Host "Response: $($apiHealthResponse | ConvertTo-Json)" -ForegroundColor Gray

    if ($apiHealthResponse.status -eq "healthy") {
        Write-Host "✅ API health check passed!" -ForegroundColor Green
    } else {
        Write-Host "❌ API health check failed!" -ForegroundColor Red
        throw "API health check returned unexpected status"
    }

    Write-Host "✨ All smoke tests passed!" -ForegroundColor Green
    exit 0

} catch {
    Write-Host "❌ Smoke test failed: $_" -ForegroundColor Red
    exit 1

} finally {
    # Stop server
    Write-Host "🛑 Stopping server..." -ForegroundColor Yellow
    Stop-Process -Id $process.Id -Force
}
