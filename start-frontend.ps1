$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location "$Root\frontend"
npm run dev
Pop-Location
