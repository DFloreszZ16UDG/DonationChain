$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = ""

function Assert-Success([string]$Step) {
    if ($LASTEXITCODE -ne 0) {
        throw "$Step falló con código $LASTEXITCODE"
    }
}

Push-Location "$Root\backend"
$Python = ".\.venv\Scripts\python.exe"
& $Python -m pytest -q
Assert-Success "Pruebas del backend"
& $Python -m ruff check app tests
Assert-Success "Ruff"
& $Python -m bandit -q -r app
Assert-Success "Bandit"
& $Python -m pip_audit -r requirements.txt
Assert-Success "Auditoría de dependencias Python"
Pop-Location

Push-Location "$Root\frontend"
npm run build
Assert-Success "Compilación del frontend"
npm audit --audit-level=high
Assert-Success "Auditoría del frontend"
Pop-Location

Push-Location "$Root\contracts"
npm test
Assert-Success "Pruebas del Smart Contract"
# Hardhat and its toolbox are build-time tools; no Node package is deployed with the contract.
npm audit --omit=dev --audit-level=high
Assert-Success "Auditoría de dependencias desplegables del contrato"
Pop-Location
