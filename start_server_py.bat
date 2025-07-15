@echo off
echo Starting Attendance Tracker Local Server (using py launcher)...
echo.

REM Change to the directory where this batch file is located
cd /d "%~dp0"
echo Current directory: %CD%

REM Check if we're in the right directory by looking for key files
if not exist "app.py" (
    echo ERROR: app.py not found in current directory
    echo Looking for attendance-tracker directory...
    
    REM Try to find the attendance-tracker directory
    if exist "attendance-tracker\app.py" (
        cd attendance-tracker
        echo Found attendance-tracker directory, changed to: %CD%
    ) else (
        echo ERROR: Could not find attendance-tracker directory
        echo Please run this batch file from the attendance-tracker folder
        pause
        exit /b 1
    )
)

REM Check if py launcher is available
py --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python py launcher not found
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo Python found: 
py --version
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    py -m venv venv
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
    REM Try to install requirements, but continue even if some fail
    py -m pip install -r requirements.txt || (
        echo Some packages failed to install, trying alternative approach...
        py -m pip install Flask==3.0.2 Flask-SQLAlchemy==3.1.1 Flask-Login==0.6.3 Flask-WTF==1.2.1 email-validator==2.1.0.post1 python-dotenv==1.0.1 qrcode==7.4.2 reportlab==4.1.0 pytz==2024.1 Werkzeug==3.0.1 gunicorn==21.2.0 psycopg2-binary==2.9.9
        py -m pip install Pillow --no-cache-dir
    )
) else (
    echo ERROR: requirements.txt not found
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM Set Flask environment
set FLASK_ENV=development
set FLASK_APP=run.py

REM Start the server
echo.
echo Starting Flask development server...
echo Server will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
py run.py

pause 