@echo off
setlocal

if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: failed to create venv. Make sure Python 3.11+ is installed and on PATH.
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat

echo Checking dependencies (PyQt6 is ~50 MB on first run, please wait)...
pip install -r requirements.txt --disable-pip-version-check

echo Starting sftp-sync-panel...
python src\main.py

endlocal
