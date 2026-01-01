# PowerShell installer snippet for DashFleet on Windows (service)
# Run as Administrator
$installDir = "C:\Program Files\DashFleet"
New-Item -ItemType Directory -Path $installDir -Force | Out-Null
Copy-Item -Path . -Destination $installDir -Recurse -Force
python -m venv "$installDir\.venv"
& "$installDir\.venv\Scripts\pip.exe" install --upgrade pip
& "$installDir\.venv\Scripts\pip.exe" install "$installDir"

# Optionally register a scheduled task to start on boot
$action = New-ScheduledTaskAction -Execute "$installDir\.venv\Scripts\python.exe" -Argument "-m main --web --host 0.0.0.0 --port 8000"
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName "DashFleet" -Action $action -Trigger $trigger -RunLevel Highest -Force
Write-Host "DashFleet installé. Démarrez le service via le planificateur de tâches ou lancez manuellement."