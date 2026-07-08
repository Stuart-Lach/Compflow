# Quick Verification Script
# Run this to verify Render deployment readiness.

Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "COMPLIANCE ENGINE - RENDER DEPLOYMENT VERIFICATION" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

# Test 1: Import FastAPI app
Write-Host "1. Testing FastAPI app import..." -ForegroundColor Yellow
try {
    $env:PYTHONPATH = "src"
    $result = python -c "from app.main import app; print('OK')" 2>&1
    if ($result -match "OK") {
        Write-Host "   [OK] FastAPI app imports successfully" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] FastAPI app import failed: $result" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   [FAIL] Error: $_" -ForegroundColor Red
    exit 1
}

# Test 2: Check config settings
Write-Host "2. Testing configuration..." -ForegroundColor Yellow
try {
    $result = python -c "from app.config import settings; print(settings.PORT); print(settings.CORS_ORIGINS)" 2>&1
    if ($result) {
        Write-Host "   [OK] Configuration loads successfully" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] Configuration failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   [FAIL] Error: $_" -ForegroundColor Red
    exit 1
}

# Test 3: Check database module
Write-Host "3. Testing database module..." -ForegroundColor Yellow
try {
    $result = python -c "from app.storage.db import engine, init_db; print('OK')" 2>&1
    if ($result -match "OK") {
        Write-Host "   [OK] Database module loads successfully" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] Database module failed: $result" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   [FAIL] Error: $_" -ForegroundColor Red
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
            Write-Host "   [OK] $route imports successfully" -ForegroundColor Green
        } else {
            Write-Host "   [FAIL] $route failed: $result" -ForegroundColor Red
            exit 1
        }
    }
} catch {
    Write-Host "   [FAIL] Error: $_" -ForegroundColor Red
    exit 1
}

# Test 5: Check deployment files
Write-Host "5. Checking deployment files..." -ForegroundColor Yellow
$files = @(
    "..\render.yaml",
    "requirements.txt",
    ".env.example",
    "alembic.ini",
    "docs\production_runbook.md",
    "docs\production_cutover_checklist.md"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "   [OK] $file exists" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] $file missing" -ForegroundColor Red
        exit 1
    }
}

# Test 6: Check production-stage Render variables
Write-Host "6. Checking production-stage Render variables..." -ForegroundColor Yellow
$renderYaml = Get-Content -Raw "..\render.yaml"
$requiredRenderKeys = @(
    "ADMIN_USERS",
    "ADMIN_SESSION_SECRET",
    "ADMIN_COOKIE_SECURE",
    "ALERT_WEBHOOK_URL",
    "ALERT_DEDUP_WINDOW_SECONDS"
)

foreach ($key in $requiredRenderKeys) {
    if ($renderYaml -match $key) {
        Write-Host "   [OK] $key configured in render.yaml" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] $key missing from render.yaml" -ForegroundColor Red
        exit 1
    }
}

# Summary
Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "VERIFICATION COMPLETE - ALL CHECKS PASSED" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run full test suite: pytest tests/ -v" -ForegroundColor White
Write-Host "  2. Start server locally: uvicorn app.main:app --host 0.0.0.0 --port 8000" -ForegroundColor White
Write-Host "  3. Run smoke tests: .\scripts\smoke_test.ps1" -ForegroundColor White
Write-Host "  4. Deploy to Render using render.yaml" -ForegroundColor White
Write-Host ""
Write-Host "Ready for Render deployment!" -ForegroundColor Cyan
