@echo off
REM HexToImage Windows Build Script
REM Simple one-command build for Windows users

echo.
echo ============================================================
echo HexToImage - Windows Build
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.7 or later from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Checking dependencies...
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo Dependencies already installed
)

echo.
echo Building executable...
python build.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Build Complete!
echo ============================================================
echo.
echo Your executable is ready at:
echo dist\HexToImage-1.0.0\bin\HexToImage.exe
echo.
pause
