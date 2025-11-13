@echo off
REM Start the Agent-UI Promptfoo Adapter

echo ================================================================================
echo Starting Agent-UI Promptfoo Adapter
echo ================================================================================
echo.
echo Please make sure Agent-UI is running on port 8003 first!
echo To start Agent-UI, open another terminal and run:
echo   cd ..\agent-ui\python-backend
echo   .\venv\Scripts\Activate.ps1
echo   python -m uvicorn app.main:app --reload --port 8003
echo.
echo ================================================================================
echo.

timeout /t 3

python agentui_adapter.py

