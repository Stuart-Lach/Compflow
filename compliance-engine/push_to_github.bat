@echo off
echo ========================================
echo Pushing Compliance Engine to GitHub
echo ========================================
echo.

cd C:\Users\adria\Compflow\compliance-engine

echo [1/6] Initializing git repository...
git init
if %errorlevel% neq 0 (
    echo ERROR: Git init failed
    pause
    exit /b 1
)

echo [2/6] Adding all files...
git add .
if %errorlevel% neq 0 (
    echo ERROR: Git add failed
    pause
    exit /b 1
)

echo [3/6] Creating commit...
git commit -m "Initial commit: FastAPI Compliance Engine - South African payroll compliance (PAYE, UIF, SDL) - CSV/PDF exports - Render deployment ready - PostgreSQL + SQLite support - CORS configured - 47+ tests passing"
if %errorlevel% neq 0 (
    echo ERROR: Git commit failed
    pause
    exit /b 1
)

echo [4/6] Setting main branch...
git branch -M main
if %errorlevel% neq 0 (
    echo ERROR: Branch rename failed
    pause
    exit /b 1
)

echo [5/6] Adding GitHub remote...
git remote remove origin 2>nul
git remote add origin https://github.com/Stuart-Lach/Compflow.git
if %errorlevel% neq 0 (
    echo ERROR: Remote add failed
    pause
    exit /b 1
)

echo [6/6] Pushing to GitHub...
git push -u origin main
if %errorlevel% neq 0 (
    echo ERROR: Git push failed
    echo.
    echo This might be due to:
    echo - Authentication required (you may need to authenticate in browser)
    echo - Repository already exists with different content
    echo - Network issues
    pause
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS! Repository pushed to GitHub
echo https://github.com/Stuart-Lach/Compflow
echo ========================================
pause
