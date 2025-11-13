@echo off
REM Red Team Testing Runner for Agent-UI
REM This script runs the Promptfoo red team tests against Agent-UI

echo ========================================
echo SecureMCP Red Team Testing
echo ========================================
echo.

REM Check if adapter is running
echo [1/4] Checking if adapter is running...
curl -s http://localhost:8005/health >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Adapter is not running!
    echo Please start the adapter first:
    echo   cd promptfoo-testing
    echo   python agentui_adapter.py
    echo.
    pause
    exit /b 1
)
echo [OK] Adapter is running

REM Check if Agent-UI is running
echo [2/4] Checking if Agent-UI is running...
curl -s http://localhost:8003/api/health >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Agent-UI is not running!
    echo Please start Agent-UI first:
    echo   cd agent-ui\python-backend
    echo   python -m uvicorn app.main:app --reload --port 8003
    echo.
    pause
    exit /b 1
)
echo [OK] Agent-UI is running

REM Create results directory if it doesn't exist
echo [3/4] Preparing results directory...
if not exist "results" mkdir results
echo [OK] Results directory ready

REM Run Promptfoo tests
echo [4/4] Running security tests...
echo.
echo This will run 100 comprehensive security tests.
echo Progress will be shown below:
echo ========================================
echo.

promptfoo eval

echo.
echo ========================================
echo [COMPLETE] Red team tests finished!
echo ========================================
echo.
echo Results saved to: ./results/redteam-results.json
echo.
echo View results in browser with:
echo   promptfoo view
echo.
pause

