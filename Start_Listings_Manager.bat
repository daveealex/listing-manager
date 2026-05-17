@echo off
REM Desktop launcher script for Listing Manager (Windows)
REM Save as "Start Listings Manager.bat" and double-click to run

echo Starting Listings Manager...
cd /d "%~dp0"
python run.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start dashboard!
    echo Make sure Python is installed and in your PATH.
    pause
) else (
    echo.
    echo Dashboard started successfully!
    echo Open your browser to: http://localhost:8000
    echo Press any key to stop the server...
    pause >nul
)
