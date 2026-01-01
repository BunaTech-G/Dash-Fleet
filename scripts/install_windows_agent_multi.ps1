<#
.SYNOPSIS
  Déploie `fleet_agent.exe` sur plusieurs machines Windows via PowerShell Remoting ou SMB (admin share C$).

.DESCRIPTION
  Ce script copie `fleet_agent.exe` depuis une source locale vers chaque machine listée et crée une tâche planifiée qui lance l'agent au démarrage.
  - Si `-Credential` est fourni, le script utilise PowerShell Remoting (Copy-Item -ToSession).
  - Sinon il tente une copie via le partage administratif C$ (nécessite droits admin réseau).

.PARAMETER Targets
  Liste des noms d'hôtes ou adresses IP des machines cibles. Peut être un fichier texte (one-per-line) si vous passez '@path'.

.PARAMETER Source
  Chemin local vers `fleet_agent.exe` (par défaut : .\dist\fleet_agent.exe).

.PARAMETER DestinationPath
  Chemin distant (sur chaque poste) où déposer l'exécutable (par défaut : C:\Program Files\DashFleet).

.PARAMETER Credential
  PSCredential pour l'accès distant (optionnel). Si fourni, PowerShell Remoting sera utilisé.

.PARAMETER CreateScheduledTask
  Switch : crée une tâche planifiée pour lancer l'agent au démarrage (par défaut true).

.EXAMPLE
  .\install_windows_agent_multi.ps1 -Targets server1,server2 -Source .\dist\fleet_agent.exe

#>
param(
    [Parameter(Mandatory=$true)]
    [string[]] $Targets,

    [string] $Source = ".\dist\fleet_agent.exe",

    [string] $DestinationPath = "C:\\Program Files\\DashFleet",

    [System.Management.Automation.PSCredential] $Credential,

    [switch] $CreateScheduledTask = $true
)

function _ResolveTargets([string[]] $raw) {
    $resolved = @()
    foreach ($t in $raw) {
        if ($t -like '@*') {
            $path = $t.Substring(1)
            if (Test-Path $path) {
                $lines = Get-Content $path | Where-Object { $_ -and $_ -notmatch '^#' } | ForEach-Object { $_.Trim() }
                $resolved += $lines
            }
        } else {
            $resolved += $t
        }
    }
    return $resolved
}

$targets = _ResolveTargets $Targets
if (-not (Test-Path $Source)) {
    Write-Error "Source file not found: $Source"
    exit 1
}

foreach ($t in $targets) {
    Write-Host "Processing $t..." -ForegroundColor Cyan
    try {
        $remoteDest = Join-Path -Path $DestinationPath -ChildPath ([IO.Path]::GetFileName($Source))

        if ($Credential) {
            # Use PowerShell Remoting
            Write-Host "Using PSRemoting to $t"
            $session = New-PSSession -ComputerName $t -Credential $Credential -ErrorAction Stop
            Invoke-Command -Session $session -ScriptBlock {
                param($dest)
                New-Item -Path $dest -ItemType Directory -Force | Out-Null
            } -ArgumentList $DestinationPath

            Copy-Item -Path $Source -Destination $remoteDest -ToSession $session -Force -ErrorAction Stop

            if ($CreateScheduledTask) {
                $taskName = "DashFleetAgent"
                $exePath = $remoteDest
                Invoke-Command -Session $session -ScriptBlock {
                    param($taskName, $exePath)
                    $action = New-ScheduledTaskAction -Execute $exePath
                    $trigger = New-ScheduledTaskTrigger -AtStartup
                    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -RunLevel Highest -Force
                } -ArgumentList $taskName, $exePath
            }

            Remove-PSSession $session
            Write-Host "Deployed to $t via PSRemoting." -ForegroundColor Green
        } else {
            # Try SMB copy to C$ admin share
            $share = "\\$t\C$\temp\dashfleet_deploy"
            Write-Host "Attempting SMB copy to $share"
            try {
                New-Item -Path $share -ItemType Directory -Force | Out-Null
                $destPath = Join-Path -Path $share -ChildPath ([IO.Path]::GetFileName($Source))
                Copy-Item -Path $Source -Destination $destPath -Force -ErrorAction Stop

                # Create destination folder and move file via remote command (requires admin share)
                $remoteFolder = $DestinationPath
                $moveScript = "mkdir `"$remoteFolder`" 2>$null; move `"$destPath`" `"$remoteFolder`" -Force"
                Invoke-Command -ComputerName $t -ScriptBlock { param($s) Invoke-Expression $s } -ArgumentList $moveScript -ErrorAction Stop

                if ($CreateScheduledTask) {
                    $taskName = "DashFleetAgent"
                    $exePath = Join-Path -Path $DestinationPath -ChildPath ([IO.Path]::GetFileName($Source))
                    $schtask = "schtasks /Create /RU SYSTEM /SC ONSTART /TN $taskName /TR `"$exePath`" /F"
                    Invoke-Command -ComputerName $t -ScriptBlock { param($cmd) cmd.exe /c $cmd } -ArgumentList $schtask -ErrorAction Stop
                }

                Write-Host "Deployed to $t via SMB copy." -ForegroundColor Green
            } catch {
                Write-Warning "SMB deploy failed for $t: $_. Trying PSRemoting without explicit credential..."
                try {
                    # try PSRemoting without explicit credential
                    $session = New-PSSession -ComputerName $t -ErrorAction Stop
                    Copy-Item -Path $Source -Destination $remoteDest -ToSession $session -Force -ErrorAction Stop
                    if ($CreateScheduledTask) {
                        $taskName = "DashFleetAgent"
                        $exePath = $remoteDest
                        Invoke-Command -Session $session -ScriptBlock {
                            param($taskName, $exePath)
                            $action = New-ScheduledTaskAction -Execute $exePath
                            $trigger = New-ScheduledTaskTrigger -AtStartup
                            Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -RunLevel Highest -Force
                        } -ArgumentList $taskName, $exePath
                    }
                    Remove-PSSession $session
                    Write-Host "Deployed to $t via PSRemoting (no explicit credential)." -ForegroundColor Green
                } catch {
                    Write-Error "Failed to deploy to $t: $_"
                }
            }
        }
    } catch {
        Write-Error "Unexpected error for $t: $_"
    }
}

Write-Host "Deployment finished." -ForegroundColor Cyan
