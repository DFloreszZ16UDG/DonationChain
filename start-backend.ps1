$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$EnvFile = "$Root\backend\.env"
try { $Host.UI.RawUI.WindowTitle = "DonationChain API" } catch {}
$env:PYTHONPATH = ""

if (-not (Test-Path -LiteralPath $EnvFile)) {
    Write-Error "Falta backend/.env. Copia backend/.env.example y reemplaza los valores de ejemplo."
}

Push-Location "$Root\backend"
& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --env-file .env
Pop-Location
