$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Push-Location "$Root\backend"
& ".\.venv\Scripts\python.exe" -m pytest -q
& ".\.venv\Scripts\ruff.exe" check app tests
& ".\.venv\Scripts\bandit.exe" -q -r app
& ".\.venv\Scripts\pip-audit.exe" -r requirements.txt
Pop-Location

Push-Location "$Root\frontend"
npm run build
npm audit --audit-level=high
Pop-Location

Push-Location "$Root\contracts"
npm test
npm audit --audit-level=high
Pop-Location
