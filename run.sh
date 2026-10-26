#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
RUNTIME="$ROOT/.run"
NO_BROWSER=false

if [[ "${1:-}" == "--no-browser" ]]; then
  NO_BROWSER=true
fi

command -v npm >/dev/null 2>&1 || {
  echo "No se encontro Node.js/npm. Instala Node.js 22 o posterior."
  exit 1
}

if command -v python3.13 >/dev/null 2>&1; then
  SYSTEM_PYTHON="python3.13"
elif command -v python3 >/dev/null 2>&1; then
  SYSTEM_PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
  SYSTEM_PYTHON="python"
else
  echo "No se encontro Python. Instala Python 3.13."
  exit 1
fi

if [[ ! -d "$BACKEND/.venv" ]]; then
  echo "==> Creando el entorno de Python"
  "$SYSTEM_PYTHON" -m venv "$BACKEND/.venv"
fi

if [[ -x "$BACKEND/.venv/bin/python" ]]; then
  VENV_PYTHON="$BACKEND/.venv/bin/python"
elif [[ -x "$BACKEND/.venv/Scripts/python.exe" ]]; then
  VENV_PYTHON="$BACKEND/.venv/Scripts/python.exe"
else
  echo "El entorno virtual de Python no es valido."
  exit 1
fi

if ! "$VENV_PYTHON" -c "import fastapi, sqlalchemy, uvicorn, web3" >/dev/null 2>&1; then
  echo "==> Instalando dependencias del backend"
  "$VENV_PYTHON" -m pip install --upgrade pip
  "$VENV_PYTHON" -m pip install -r "$BACKEND/requirements.txt"
fi

if [[ ! -d "$FRONTEND/node_modules" ]]; then
  echo "==> Instalando dependencias de la pagina"
  (cd "$FRONTEND" && npm ci)
fi

if [[ ! -f "$BACKEND/.env" ]]; then
  echo "==> Creando la configuracion local"
  JWT_SECRET="$("$VENV_PYTHON" -c 'import secrets; print(secrets.token_urlsafe(48))')"
  sed \
    -e "s|^JWT_SECRET=.*|JWT_SECRET=$JWT_SECRET|" \
    -e "s|^DEMO_PASSWORD=.*|DEMO_PASSWORD=Donation123!|" \
    -e "s|^CORS_ORIGINS=.*|CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173|" \
    "$BACKEND/.env.example" > "$BACKEND/.env"
fi

mkdir -p "$RUNTIME"

if ! curl -fsS "http://127.0.0.1:8000/api/health" >/dev/null 2>&1; then
  echo "==> Iniciando la API"
  (cd "$BACKEND" && nohup "$VENV_PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --env-file .env > "$RUNTIME/backend.log" 2>&1 & echo $! > "$RUNTIME/backend.pid")
fi

for _ in {1..30}; do
  curl -fsS "http://127.0.0.1:8000/api/health" >/dev/null 2>&1 && break
  sleep 0.5
done
curl -fsS "http://127.0.0.1:8000/api/health" >/dev/null

if ! curl -fsS "http://127.0.0.1:5173" >/dev/null 2>&1; then
  echo "==> Iniciando la pagina web"
  (cd "$FRONTEND" && nohup npm run dev -- --host 127.0.0.1 > "$RUNTIME/frontend.log" 2>&1 & echo $! > "$RUNTIME/frontend.pid")
fi

for _ in {1..30}; do
  curl -fsS "http://127.0.0.1:5173" >/dev/null 2>&1 && break
  sleep 0.5
done
curl -fsS "http://127.0.0.1:5173" >/dev/null

echo
echo "DonationChain esta listo: http://127.0.0.1:5173"
echo "Usuario: donante@donationchain.example.com"
echo "Contrasena: Donation123!"

if [[ "$NO_BROWSER" == false ]]; then
  if [[ "$OSTYPE" == "darwin"* ]]; then
    open "http://127.0.0.1:5173"
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://127.0.0.1:5173" >/dev/null 2>&1 || true
  elif command -v cmd.exe >/dev/null 2>&1; then
    cmd.exe /c start "" "http://127.0.0.1:5173" >/dev/null 2>&1 || true
  fi
fi
