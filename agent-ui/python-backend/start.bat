@echo off
REM Start script for Python backend (Windows)

echo ================================================
echo    SecureMCP Python Backend Startup Script
echo ================================================
echo.

REM Check Python version
echo Checking Python version...
python --version
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Creating one...
    python -m venv venv
    echo Virtual environment created
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo.
echo Installing dependencies...
pip install -q -r requirements.txt

REM Download spaCy model if not present
echo.
echo Checking spaCy model...
python -c "import spacy; spacy.load('en_core_web_sm')" 2>nul
if errorlevel 1 (
    echo Downloading spaCy model...
    python -m spacy download en_core_web_sm
    echo spaCy model downloaded
) else (
    echo spaCy model already installed
)

REM Create .env if not exists
if not exist ".env" (
    echo.
    echo Creating .env file...
    (
        echo PORT=8003
        echo HOST=0.0.0.0
        echo CORS_ORIGINS=http://localhost:3000,http://localhost:3001
        echo LOG_LEVEL=INFO
        echo DEFAULT_SECURITY_LEVEL=medium
        echo MODEL_CACHE_DIR=./models
        echo USE_GPU=auto
    ) > .env
    echo .env file created
)

echo.
echo ================================================
echo    Starting FastAPI Server...
echo ================================================
echo.

REM Start the server
python app\main.py
