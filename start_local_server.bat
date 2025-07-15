@echo off
echo Starting Attendance Tracker Local Server...
echo.

REM Change to the directory where this batch file is located
cd /d "%~dp0"

REM Try different Python commands
set PYTHON_CMD=python
python --version >nul 2>&1
if errorlevel 1 (
    set PYTHON_CMD=python3
    python3 --version >nul 2>&1
    if errorlevel 1 (
        set PYTHON_CMD=py
        py --version >nul 2>&1
        if errorlevel 1 (
            echo ERROR: Python not found in PATH
            echo Please ensure Python is installed and added to PATH
            echo Or try running: py -m pip install -r requirements.txt
            pause
            exit /b 1
        )
    )
)

echo Using Python command: %PYTHON_CMD%
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created.
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ERROR: Virtual environment activation failed
    pause
    exit /b 1
)

REM Install/update requirements
echo Installing/updating requirements...
if exist "requirements.txt" (
    pip install -r requirements.txt
) else (
    echo ERROR: requirements.txt not found
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM Set Flask environment
set FLASK_ENV=development
set FLASK_APP=app.py

REM Start the server
echo.
echo Starting Flask development server...
echo Server will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
%PYTHON_CMD% app.py

pause 