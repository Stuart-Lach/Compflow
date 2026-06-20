param(
    [Parameter(Mandatory = $true)]
    [string]$DatabaseUrl,

    [string]$OutputDirectory = ".\backups"
)

$resolvedOutput = [System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $resolvedOutput -Force | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupPath = Join-Path $resolvedOutput "compflow_$timestamp.dump"

& pg_dump --format=custom --no-owner --no-privileges --file=$backupPath $DatabaseUrl
if ($LASTEXITCODE -ne 0) {
    throw "pg_dump failed with exit code $LASTEXITCODE"
}

$hash = Get-FileHash -LiteralPath $backupPath -Algorithm SHA256
$manifestPath = "$backupPath.sha256"
"$($hash.Hash)  $([System.IO.Path]::GetFileName($backupPath))" |
    Set-Content -LiteralPath $manifestPath -Encoding ascii

Write-Output $backupPath
