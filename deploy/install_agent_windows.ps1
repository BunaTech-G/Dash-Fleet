# Installe l'agent DashFleet sur Windows (version simple)
# Usage (exécuter en administrateur):
# .\install_agent_windows.ps1 -OrgKey "abcdef..." -AgentPath C:\opt\dashfleet\agent
param(
    [string]$OrgKey,
    [string]$AgentPath = "C:\\opt\\dashfleet"
)

if (-not $OrgKey) {
    Write-Error "OrgKey requis. Exemple: .\install_agent_windows.ps1 -OrgKey 'abcdef'"
    exit 1
}

New-Item -ItemType Directory -Path $AgentPath -Force | Out-Null

# Copie des fichiers (supposant que le dépôt est présent)
Copy-Item -Path "${PSScriptRoot}\\..\\fleet_agent.py" -Destination $AgentPath -Force

# Crée un fichier de configuration simple
$config = @"
ORG_KEY=$OrgKey
"@
Set-Content -Path (Join-Path $AgentPath "agent.conf") -Value $config -Encoding UTF8

Write-Output "Agent copié dans $AgentPath"

Write-Output "Pour exécuter l'agent manuellement :"
Write-Output "  powershell -NoProfile -ExecutionPolicy Bypass -Command \"$Env:ORG_KEY='$OrgKey'; python $AgentPath\\fleet_agent.py\""

Write-Output "Pour l'installer comme service, installez 'nssm' et exécutez :"
Write-Output "  nssm install DashFleetAgent C:\\PythonXX\\python.exe $AgentPath\\fleet_agent.py"
Write-Output "  nssm set DashFleetAgent AppEnvironmentExtra ORG_KEY=$OrgKey"
Write-Output "  nssm start DashFleetAgent"
