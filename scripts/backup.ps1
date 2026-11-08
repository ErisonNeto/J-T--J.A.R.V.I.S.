param([Parameter(Mandatory=$true)][string]$Destination)
$ErrorActionPreference = 'Stop'
# PGSERVICE/PGPASSFILE configured locally; no passwords in commands, repository or logs.
New-Item -ItemType Directory -Force $Destination | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$file = Join-Path $Destination "jarvis-$stamp.dump"
& pg_dump --dbname=jt_indicadores --schema=jarvis --format=custom --file=$file
if ($LASTEXITCODE -ne 0) { throw 'Backup falhou' }
& pg_restore --list $file | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Arquivo de backup inválido' }
Write-Output $file
