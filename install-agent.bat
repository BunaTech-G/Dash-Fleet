@echo off
REM DashFleet Agent - Quick Installer
REM Copy EXE and create auto-start

setlocal enabledelayedexpansion

echo.
echo ========================================
echo DashFleet Agent - Quick Install
echo ========================================
echo.

REM Check if running as admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting admin privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

REM Configuration
set "SERVER_URL=https://dash-fleet.com"
set "INSTALL_DIR=C:\DashFleet"
set "EXE_SOURCE=dist\dashfleet-agent.exe"

REM Check if EXE exists
if not exist "%EXE_SOURCE%" (
    echo Error: dashfleet-agent.exe not found!
    echo Please build the agent first by running: build-agent.bat
    pause
    exit /b 1
)

echo [1/4] Creating installation directory...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
echo Done: %INSTALL_DIR%

echo [2/4] Copying agent...
copy /Y "%EXE_SOURCE%" "%INSTALL_DIR%\dashfleet-agent.exe" >nul
echo Done: %INSTALL_DIR%\dashfleet-agent.exe

echo [3/4] Creating startup script...
(
echo @echo off
echo start /min "" "%INSTALL_DIR%\dashfleet-agent.exe" --server %SERVER_URL%
) > "%INSTALL_DIR%\start-agent.bat"
echo Done: %INSTALL_DIR%\start-agent.bat

echo [4/4] Adding to Windows startup...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "DashFleetAgent" /t REG_SZ /d "\"%INSTALL_DIR%\start-agent.bat\"" /f >nul 2>&1
echo Done: Auto-start enabled

echo.
echo ========================================
echo INSTALLATION COMPLETE!
echo ========================================
echo.
echo Agent installed to: %INSTALL_DIR%
echo Server: %SERVER_URL%
echo Auto-start: Enabled
echo.
echo To start manually:
echo   %INSTALL_DIR%\start-agent.bat
echo.
echo To uninstall:
echo   reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "DashFleetAgent" /f
echo   rmdir /s /q "%INSTALL_DIR%"
echo.
pause
