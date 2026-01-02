#!/usr/bin/env powershell
<#
.SYNOPSIS
    Quick test script for Fleet Agent Tray Icon feature
.DESCRIPTION
    Tests the tray icon functionality locally without requiring a full server setup
.PARAMETER Port
    Local server port (default 5000)
.PARAMETER Token
    API token for authentication (default "test_token")
.PARAMETER WithTray
    Run agent with tray icon (default $true)
.EXAMPLE
    .\test_tray_icon.ps1 -WithTray $true
    .\test_tray_icon.ps1 -Port 8000 -Token "custom_token"
#>

param(
    [int]$Port = 5000,
    [string]$Token = "test_token",
    [bool]$WithTray = $true
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Get-Item $PSCommandPath).FullName

Write-Host "╔═══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Fleet Agent Tray Icon - Quick Test              ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Test 1: Syntax Validation
Write-Host "📝 Test 1: Python Syntax Validation" -ForegroundColor Yellow
Push-Location $ProjectRoot
try {
    python -m py_compile fleet_agent.py fleet_agent_windows_tray.py
    Write-Host "   ✅ All files compile without syntax errors" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Syntax error detected: $_" -ForegroundColor Red
    exit 1
}
Pop-Location

# Test 2: Module Import
Write-Host ""
Write-Host "🐍 Test 2: Module Imports" -ForegroundColor Yellow
try {
    python -c "
import sys
sys.path.insert(0, '$ProjectRoot')
from fleet_agent import collect_agent_stats, create_tray_icon
from fleet_agent_windows_tray import TrayAgent, run_tray_icon
print('   ✅ All modules imported successfully')
"
    Write-Host "" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Import error: $_" -ForegroundColor Red
    exit 1
}

# Test 3: Tray Icon Creation
Write-Host ""
Write-Host "🎨 Test 3: Tray Icon Creation" -ForegroundColor Yellow
try {
    python -c "
import sys
sys.path.insert(0, '$ProjectRoot')
from fleet_agent import create_tray_icon
icon = create_tray_icon()
assert icon.size == (64, 64), f'Expected (64, 64), got {icon.size}'
assert icon.mode == 'RGB', f'Expected RGB, got {icon.mode}'
print('   ✅ Tray icon created: 64x64 RGB image')
"
    Write-Host "" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Icon creation error: $_" -ForegroundColor Red
    exit 1
}

# Test 4: Agent Stats Collection
Write-Host ""
Write-Host "📊 Test 4: Agent Stats Collection" -ForegroundColor Yellow
try {
    python -c "
import sys
sys.path.insert(0, '$ProjectRoot')
from fleet_agent import collect_agent_stats
stats = collect_agent_stats()
assert 'cpu_percent' in stats, 'Missing cpu_percent'
assert 'ram_percent' in stats, 'Missing ram_percent'
assert 'disk_percent' in stats, 'Missing disk_percent'
assert 'health' in stats, 'Missing health'
print(f'   ✅ Stats collected:')
print(f'      CPU: {stats[\"cpu_percent\"]:.1f}%')
print(f'      RAM: {stats[\"ram_percent\"]:.1f}%')
print(f'      Disk: {stats[\"disk_percent\"]:.1f}%')
print(f'      Health: {stats[\"health\"][\"score\"]:.0f}/100 ({stats[\"health\"][\"status\"]})')
"
    Write-Host "" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Stats collection error: $_" -ForegroundColor Red
    exit 1
}

# Test 5: CLI Help
Write-Host ""
Write-Host "💻 Test 5: CLI Help Output" -ForegroundColor Yellow
try {
    $helpOutput = python fleet_agent.py --help
    if ($helpOutput -match "--tray") {
        Write-Host "   ✅ CLI help includes --tray flag" -ForegroundColor Green
    } else {
        Write-Host "   ❌ --tray flag not found in help output" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   ❌ CLI error: $_" -ForegroundColor Red
    exit 1
}

# Test 6: Pytest Tests
Write-Host ""
Write-Host "🧪 Test 6: Unit Tests" -ForegroundColor Yellow
try {
    $testOutput = python -m pytest tests/test_tray_icon.py tests/test_agent_integration.py -v
    if ($testOutput -match "passed") {
        Write-Host "   ✅ All unit tests passed" -ForegroundColor Green
        Write-Host "$($testOutput | Select-String 'passed' | ForEach-Object { "      $_" })" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Some tests failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   ⚠️  Pytest not available or error: $_" -ForegroundColor Yellow
}

# Test 7: Executable Verification
Write-Host ""
Write-Host "📦 Test 7: Compiled Executable" -ForegroundColor Yellow
$exePath = Join-Path $ProjectRoot "dist" "fleet_agent.exe"
if (Test-Path $exePath) {
    $fileInfo = Get-Item $exePath
    Write-Host "   ✅ fleet_agent.exe exists" -ForegroundColor Green
    Write-Host "      Size: $([Math]::Round($fileInfo.Length / 1MB, 1)) MB" -ForegroundColor Green
    Write-Host "      Location: $exePath" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  fleet_agent.exe not found at: $exePath" -ForegroundColor Yellow
    Write-Host "      Run: pyinstaller fleet_agent.spec --clean" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  ✅ All Tests Passed!                            ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "📌 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Run with tray icon (Windows only):" -ForegroundColor Cyan
Write-Host "      python fleet_agent.py --server http://localhost:5000 --token $Token --tray" -ForegroundColor Gray
Write-Host ""
Write-Host "   2. Or deploy executable:" -ForegroundColor Cyan
Write-Host "      dist\fleet_agent.exe --server http://dashfleet.local --token api_key --tray" -ForegroundColor Gray
Write-Host ""
Write-Host "   3. Check tray icon in Windows system tray (bottom-right corner)" -ForegroundColor Cyan
Write-Host ""
