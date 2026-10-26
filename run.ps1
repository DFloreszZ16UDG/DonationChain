param(
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$VenvPython = Join-Path $Backend ".venv\Scripts\python.exe"
$EnvFile = Join-Path $Backend ".env"

function Write-Step([string]$Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Test-Port([int]$Port) {
    return [bool](Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
}

function Wait-Url([string]$Url, [int]$Attempts = 30) {
    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                return $true
            }
        } catch {
            Start-Sleep -Milliseconds 500
        }
    }
    return $false
}

Write-Host "DonationChain - inicio automatico" -ForegroundColor Green

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "No se encontro Node.js/npm. Instala Node.js 22 o posterior y vuelve a ejecutar run.bat."
}

if (-not (Test-Path -LiteralPath $VenvPython)) {
    Write-Step "Creando el entorno de Python"
    $created = $false
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.13 -m venv (Join-Path $Backend ".venv")
        $created = Test-Path -LiteralPath $VenvPython
    }
    if (-not $created -and (Get-Command python -ErrorAction SilentlyContinue)) {
        $version = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
        if ($version -eq "3.13") {
            & python -m venv (Join-Path $Backend ".venv")
            $created = Test-Path -LiteralPath $VenvPython
        }
    }
    if (-not $created) {
        throw "No se encontro Python 3.13. Instalalo y vuelve a ejecutar run.bat."
    }
}

Write-Step "Comprobando dependencias del backend"
$backendReady = $true
try {
    & $VenvPython -c "import fastapi, sqlalchemy, uvicorn, web3" 2>$null
} catch {
    $backendReady = $false
}
if (-not $backendReady -or $LASTEXITCODE -ne 0) {
    & $VenvPython -m pip install --upgrade pip
    & $VenvPython -m pip install -r (Join-Path $Backend "requirements.txt")
}

if (-not (Test-Path -LiteralPath (Join-Path $Frontend "node_modules"))) {
    Write-Step "Instalando dependencias de la pagina"
    Push-Location $Frontend
    try {
        npm ci
        if ($LASTEXITCODE -ne 0) { throw "npm ci fallo" }
    } finally {
        Pop-Location
    }
}

if (-not (Test-Path -LiteralPath $EnvFile)) {
    Write-Step "Creando la configuracion local"
    $jwtSecret = & $VenvPython -c "import secrets; print(secrets.token_urlsafe(48))"
    $envContent = @"
ENVIRONMENT=development
DATABASE_URL=sqlite:///./donationchain.db
JWT_SECRET=$jwtSecret
DEMO_PASSWORD=Donation123!
ACCESS_TOKEN_MINUTES=480
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
MAX_RECEIPT_BYTES=10485760

BLOCKCHAIN_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com
BLOCKCHAIN_CHAIN_ID=11155111
BLOCKCHAIN_EXPLORER_URL=https://sepolia.etherscan.io

BLOCKCHAIN_CONTRACT_ADDRESS=
BLOCKCHAIN_PRIVATE_KEY=
"@
    Set-Content -LiteralPath $EnvFile -Value $envContent -Encoding utf8
}

if (-not (Test-Port 8000)) {
    Write-Step "Iniciando la API"
    Start-Process powershell.exe -WorkingDirectory $Root -ArgumentList @(
        "-NoExit",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", (Join-Path $Root "start-backend.ps1")
    )
}

if (-not (Wait-Url "http://127.0.0.1:8000/api/health")) {
    throw "La API no pudo iniciar. Revisa la ventana 'DonationChain API'."
}

if (-not (Test-Port 5173)) {
    Write-Step "Iniciando la pagina web"
    Start-Process powershell.exe -WorkingDirectory $Root -ArgumentList @(
        "-NoExit",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", (Join-Path $Root "start-frontend.ps1")
    )
}

if (-not (Wait-Url "http://127.0.0.1:5173")) {
    throw "La pagina no pudo iniciar. Revisa la ventana 'DonationChain Web'."
}

Write-Host "`nDonationChain esta listo." -ForegroundColor Green
Write-Host "Pagina:     http://127.0.0.1:5173"
Write-Host "API:        http://127.0.0.1:8000/docs"
Write-Host "Usuario:    donante@donationchain.example.com"
Write-Host "Contrasena: Donation123!"

if (-not $NoBrowser) {
    Start-Process "http://127.0.0.1:5173"
}
