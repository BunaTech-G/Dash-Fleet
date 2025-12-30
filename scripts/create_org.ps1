Param(
    [Parameter(Mandatory=$true)] [string]$ActionToken,
    [string]$Name = "MyOrganization",
    [string]$Host = "http://localhost:5000"
)

$Headers = @{ Authorization = "Bearer $ActionToken"; 'Content-Type' = 'application/json' }
$Body = @{ name = $Name } | ConvertTo-Json

try {
    $resp = Invoke-RestMethod -Uri "$Host/api/orgs" -Method POST -Headers $Headers -Body $Body -TimeoutSec 15
    Write-Host "Organisation créée : id = $($resp.id)"
    Write-Host "api_key = $($resp.api_key)"
    exit 0
} catch {
    Write-Error "Requête échouée : $($_.Exception.Message)"
    if ($_.Exception.Response) {
        try { $text = $_.Exception.Response.GetResponseStream() | Select-Object -First 1 } catch { }
    }
    exit 1
}
