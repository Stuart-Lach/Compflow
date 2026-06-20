param(
    [Parameter(Mandatory = $true)]
    [string]$BackupPath,

    [Parameter(Mandatory = $true)]
    [string]$RestoreDatabaseUrl
)

$resolvedBackup = (Resolve-Path -LiteralPath $BackupPath).Path
$manifestPath = "$resolvedBackup.sha256"

if (-not (Test-Path -LiteralPath $manifestPath)) {
    throw "Backup checksum manifest not found: $manifestPath"
}

$expectedHash = (Get-Content -LiteralPath $manifestPath -Raw).Split()[0]
$actualHash = (Get-FileHash -LiteralPath $resolvedBackup -Algorithm SHA256).Hash
if ($expectedHash -ne $actualHash) {
    throw "Backup checksum verification failed"
}

& pg_restore `
    --clean `
    --if-exists `
    --no-owner `
    --no-privileges `
    --dbname=$RestoreDatabaseUrl `
    $resolvedBackup
if ($LASTEXITCODE -ne 0) {
    throw "pg_restore failed with exit code $LASTEXITCODE"
}

$tables = & psql $RestoreDatabaseUrl -Atc `
    "select tablename from pg_tables where schemaname='public' order by tablename;"
if ($LASTEXITCODE -ne 0) {
    throw "Restore verification query failed"
}

$requiredTables = @("alembic_version", "files", "issues", "results", "runs")
foreach ($table in $requiredTables) {
    if ($tables -notcontains $table) {
        throw "Restored database is missing table: $table"
    }
}

Write-Output "Restore verified successfully"
