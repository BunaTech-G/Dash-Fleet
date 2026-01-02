@echo off
REM DashFleet Agent Installer for Windows
REM Run as Administrator on the target machine

setlocal enabledelayedexpansion

echo.
echo ========================================
echo   Installation Agent DashFleet
echo ========================================
echo.

REM Check admin rights
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERREUR: Ce script doit etre execute en tant qu'Administrateur!
    echo.
    echo Pour relancer en Administrateur:
    echo   - Clique-droit sur ce fichier
    echo   - Choisis "Executer en tant qu'administrateur"
    pause
    exit /b 1
)
REM Verifier si Python est vraiment installe (pas l'alias Windows Store)
echo Verification de Python...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo.
    echo Python n'est pas installe. Installation automatique...
    echo.
    
    REM Tenter d'installer via winget (Windows 10/11)
    winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
    
    if %ERRORLEVEL% neq 0 (
        echo.
        echo ERREUR: Impossible d'installer Python automatiquement.
        echo.
        echo Solution manuelle:
        echo 1. Allez sur https://www.python.org/downloads/
        echo 2. Telechargez Python 3.11 ou superieur
        echo 3. IMPORTANT: Cochez "Add Python to PATH" pendant l'installation
        echo 4. Relancez ce script apres l'installation
        echo.
        pause
        exit /b 1
    )
    
    echo Python installe avec succes!
    echo Redemarrage de la session pour actualiser le PATH...
    echo.
    
    REM Rafraichir les variables d'environnement
    for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path') do set "SysPath=%%b"
    for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path') do set "UserPath=%%b"
    set "PATH=%SysPath%;%UserPath%"
)
REM Ask for machine name
set /p MACHINE_ID="Entrez le nom de la machine (ex: wclient3): "

if "!MACHINE_ID!"=="" (
    echo ERREUR: Vous devez entrer un nom de machine!
    pause
    exit /b 1
)

echo.
echo Installation pour: !MACHINE_ID!
echo.

REM Run the PowerShell installer
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ProgressPreference = 'SilentlyContinue'; " ^
  "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/BunaTech-G/Dash-Fleet/fix/pyproject-exclude/deploy/install_simple.ps1' -OutFile $env:TEMP\install.ps1; " ^
  "& $env:TEMP\install.ps1 -ApiKey 'd2f6f9a8-3c7e-4c1f-9b0f-123456789abc' -MachineId '!MACHINE_ID!'"

if %ERRORLEVEL% equ 0 (
    echo.
    echo ========================================
    echo Installation terminee avec succes!
    echo ========================================
    echo.
    echo La machine !MACHINE_ID! est maintenant enregistree.
    echo.
    echo Elle apparaitra dans le dashboard dans quelques secondes:
    echo https://dash-fleet.com/fleet
    echo.
) else (
    echo.
    echo ERREUR: L'installation a echoue
    echo Verifie que tu as une connexion Internet et que Python est installe
    echo.
)

pause
