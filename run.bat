@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1"
if errorlevel 1 (
  echo.
  echo No fue posible iniciar DonationChain. Revisa el mensaje anterior.
  pause
)
