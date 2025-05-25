@echo off
echo ========================================
echo CVLens-Agent - Local Resume Screening
echo ========================================
echo.

REM Check if .env file exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please copy env.example to .env and configure your settings.
    echo.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt > nul 2>&1

REM Download spaCy model if not present
echo Checking NLP models...
python -m spacy download en_core_web_sm > nul 2>&1

REM Create necessary directories
if not exist logs mkdir logs
if not exist data\cache mkdir data\cache
if not exist data\db mkdir data\db
if not exist data\.token mkdir data\.token

REM Run the application
echo.
echo Starting CVLens-Agent...
echo.
echo Once the app starts:
echo 1. Open your browser at http://localhost:8501
echo 2. Click "Authenticate with Microsoft" in the sidebar
echo 3. Follow the device code authentication flow
echo.
echo Press Ctrl+C to stop the application
echo ========================================
echo.

streamlit run app.py

pause 