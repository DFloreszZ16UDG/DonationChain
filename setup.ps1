$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Preparando API de Python 3.13..."
py -3.13 -m venv "$Root\backend\.venv"
& "$Root\backend\.venv\Scripts\python.exe" -m pip install --upgrade pip
& "$Root\backend\.venv\Scripts\python.exe" -m pip install -r "$Root\backend\requirements-dev.txt"

Write-Host "Preparando frontend..."
Push-Location "$Root\frontend"
npm install
Pop-Location

Write-Host "Preparando Smart Contract..."
Push-Location "$Root\contracts"
npm install
Pop-Location

Write-Host "Listo. Copia backend/.env.example a backend/.env y cambia sus secretos."
