@echo off
REM DashFleet Agent - Build EXE with PyInstaller

echo.
echo ========================================
echo DashFleet Agent - EXE Builder
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not found!
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

echo [1/4] Installing dependencies...
python -m pip install psutil pyinstaller --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo [2/4] Building EXE with PyInstaller...
pyinstaller --clean --onefile fleet_agent_simple.spec
if %errorlevel% neq 0 (
    echo Error: Build failed
    pause
    exit /b 1
)

echo [3/4] Verifying build...
if not exist "dist\dashfleet-agent.exe" (
    echo Error: dashfleet-agent.exe not found in dist folder
    pause
    exit /b 1
)

echo [4/4] Build complete!
echo.
echo ========================================
echo SUCCESS!
echo ========================================
echo.
echo EXE Location: %CD%\dist\dashfleet-agent.exe
echo Size: 
dir dist\dashfleet-agent.exe | find "dashfleet-agent.exe"
echo.
echo Usage:
echo   dist\dashfleet-agent.exe --server https://dash-fleet.com
echo.
pause
