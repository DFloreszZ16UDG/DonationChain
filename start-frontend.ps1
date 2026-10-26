$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
try { $Host.UI.RawUI.WindowTitle = "DonationChain Web" } catch {}
Push-Location "$Root\frontend"
npm run dev -- --host 127.0.0.1
Pop-Location
