$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..\backend')
if (!(Test-Path '.venv')) { py -3.12 -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
if (!(Test-Path '.env')) { Copy-Item ..\.env.example .env }
& .\.venv\Scripts\python.exe -m uvicorn jarvis.main:create_app --factory --host 127.0.0.1 --port 8010
