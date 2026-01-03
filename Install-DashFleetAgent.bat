@echo off
REM DashFleet Agent Professional Installer Launcher
REM This script elevates to admin and runs the PowerShell installer

setlocal enabledelayedexpansion

REM Check if running as admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo DashFleet Agent Installer
    echo ========================================
    echo.
    echo This installer requires Administrator privileges.
    echo Please wait while we request elevated access...
    echo.
    
    REM Re-launch as admin
    powershell -Command "Start-Process cmd -ArgumentList '/c \"%~f0\"' -Verb RunAs"
    exit /b
)

REM Get script directory
set SCRIPT_DIR=%~dp0

REM Check if PowerShell installer exists
if not exist "%SCRIPT_DIR%Install-DashFleetAgent.ps1" (
    echo Error: Install-DashFleetAgent.ps1 not found!
    echo Please make sure the installer script is in the same directory.
    pause
    exit /b 1
)

REM Run PowerShell installer with admin privileges
cls
powershell -ExecutionPolicy Bypass -NoProfile -File "%SCRIPT_DIR%Install-DashFleetAgent.ps1"
exit /b %errorlevel%
