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

REM Check if required files exist
if not exist "src\__init__.py" (
    echo ERROR: src\__init__.py not found
    echo Make sure you are running this script from the project root directory
    pause
    exit /b 1
)

if not exist "assets\icon.png" (
    echo ERROR: assets\icon.png not found
    echo Make sure the icon file exists in the assets directory
    pause
    exit /b 1
)

if not exist "gui_launcher.py" (
    echo ERROR: gui_launcher.py not found
    echo Make sure you are running this script from the project root directory
    pause
    exit /b 1
)

if not exist "hextoimage.spec" (
    echo ERROR: hextoimage.spec not found
    echo Make sure the PyInstaller spec file exists
    pause
    exit /b 1
)

echo [OK] All required files found

echo Checking dependencies...
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        echo Please check your internet connection and try again
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed successfully
) else (
    echo [OK] Dependencies already installed
)

echo.
echo Building executable...
echo This may take a few minutes...
python build.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed
    echo.
    echo Common solutions:
    echo - Make sure all required files are present
    echo - Check that Python and PyInstaller are properly installed
    echo - Ensure you have enough disk space
    echo - Try running as administrator if you get permission errors
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo [OK] Build Complete!
echo ============================================================
echo.
echo Your executable is ready at:
echo dist\HexToImage-1.0.0\bin\HexToImage.exe
echo.
echo You can now:
echo - Run the executable directly
echo - Copy the entire dist\HexToImage-1.0.0 folder to distribute
echo - The executable is standalone and requires no installation
echo.
echo Press any key to exit...
pause >nul
