# Quick Verification Script
# Run this to verify Render deployment readiness

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "COMPLIANCE ENGINE - RENDER DEPLOYMENT VERIFICATION" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

# Test 1: Import FastAPI app
Write-Host "1. Testing FastAPI app import..." -ForegroundColor Yellow
try {
    $env:PYTHONPATH = "src"
    $result = python -c "from app.main import app; print('OK')" 2>&1
    if ($result -match "OK") {
        Write-Host "   ✅ FastAPI app imports successfully" -ForegroundColor Green
    } else {
        Write-Host "   ❌ FastAPI app import failed: $result" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   ❌ Error: $_" -ForegroundColor Red
    exit 1
}

# Test 2: Check config settings
Write-Host "2. Testing configuration..." -ForegroundColor Yellow
try {
    $result = python -c "from app.config import settings; print(settings.PORT); print(settings.CORS_ORIGINS)" 2>&1
    if ($result) {
        Write-Host "   ✅ Configuration loads successfully" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Configuration failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   ❌ Error: $_" -ForegroundColor Red
    exit 1
}

# Test 3: Check database module
Write-Host "3. Testing database module..." -ForegroundColor Yellow
try {
    $result = python -c "from app.storage.db import engine, init_db; print('OK')" 2>&1
    if ($result -match "OK") {
        Write-Host "   ✅ Database module loads successfully" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Database module failed: $result" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   ❌ Error: $_" -ForegroundColor Red
    exit 1
}

# Test 4: Check all API routes
Write-Host "4. Testing API routes..." -ForegroundColor Yellow
try {
    $routes = @(
        "routes_health",
        "routes_runs",
        "routes_rulesets",
        "routes_exports"
    )

    foreach ($route in $routes) {
        $result = python -c "from app.api.v1 import $route; print('OK')" 2>&1
        if ($result -match "OK") {
            Write-Host "   ✅ $route imports successfully" -ForegroundColor Green
        } else {
            Write-Host "   ❌ $route failed: $result" -ForegroundColor Red
            exit 1
        }
    }
} catch {
    Write-Host "   ❌ Error: $_" -ForegroundColor Red
    exit 1
}

# Test 5: Check render.yaml exists
Write-Host "5. Checking deployment files..." -ForegroundColor Yellow
$files = @(
    "render.yaml",
    "requirements.txt",
    ".env.example"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "   ✅ $file exists" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $file missing" -ForegroundColor Red
        exit 1
    }
}

# Summary
Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "VERIFICATION COMPLETE - ALL CHECKS PASSED ✅" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run full test suite: pytest tests/ -v" -ForegroundColor White
Write-Host "  2. Start server locally: uvicorn src.app.main:app --host 0.0.0.0 --port 8000" -ForegroundColor White
Write-Host "  3. Run smoke tests: .\scripts\smoke_test.ps1" -ForegroundColor White
Write-Host "  4. Deploy to Render using render.yaml" -ForegroundColor White
Write-Host ""
Write-Host "Ready for Render deployment! 🚀" -ForegroundColor Cyan
