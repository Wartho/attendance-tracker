@echo off
REM Activate virtual environment if exists
IF EXIST venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Set environment variables
set FLASK_APP=app.py
set FLASK_ENV=development
set FLASK_DEBUG=1

REM Run the Flask app
python app.py 