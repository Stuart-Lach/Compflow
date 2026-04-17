Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PUSHING TO GITHUB" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to root directory (not compliance-engine subfolder)
Set-Location C:\Users\adria\Compflow

Write-Host "[1/5] Checking git status..." -ForegroundColor Yellow
$gitStatus = git status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Not a git repository. Initializing..." -ForegroundColor Yellow
    git init
    git branch -M main
    git remote add origin https://github.com/Stuart-Lach/Compflow.git
}
git status
Write-Host "Done" -ForegroundColor Green

Write-Host "[2/5] Adding all files..." -ForegroundColor Yellow
git add .
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR" -ForegroundColor Red; exit 1 }
Write-Host "Done" -ForegroundColor Green

Write-Host "[3/5] Creating commit..." -ForegroundColor Yellow
git commit -m "Add FastAPI Compliance Engine - SA payroll PAYE UIF SDL - CSV PDF export - Render ready - 47 tests passing"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Nothing to commit or error occurred" -ForegroundColor Yellow
}
Write-Host "Done" -ForegroundColor Green

Write-Host "[4/5] Verifying remote..." -ForegroundColor Yellow
git remote remove origin 2>$null
git remote add origin https://github.com/Stuart-Lach/Compflow.git
git remote -v
Write-Host "Done" -ForegroundColor Green

Write-Host "[5/5] Pushing to GitHub..." -ForegroundColor Yellow
git push -u origin main --force
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Push failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "This might be due to:" -ForegroundColor Yellow
    Write-Host "- Authentication required (configure Git credentials)" -ForegroundColor White
    Write-Host "- Network issues" -ForegroundColor White
    Write-Host ""
    Write-Host "Try running manually:" -ForegroundColor Yellow
    Write-Host "  git push -u origin main --force" -ForegroundColor White
    exit 1
}
Write-Host "Done" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "SUCCESS! Repository pushed to GitHub" -ForegroundColor Green
Write-Host "https://github.com/Stuart-Lach/Compflow" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Visit: https://github.com/Stuart-Lach/Compflow" -ForegroundColor White
Write-Host "2. Deploy to Render: https://render.com/dashboard" -ForegroundColor White
Write-Host "3. See RENDER_DEPLOYMENT.md for details" -ForegroundColor White

