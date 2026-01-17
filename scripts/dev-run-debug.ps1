# dev-run-debug.ps1
# Debug Mode Launcher for Strategy Analysis Platform V2
# This script starts the Frontend but leaves the Backends for you to start via VS Code Debugger.

Write-Host "🐞 Launching Strategy Analysis Platform in DEBUG Mode..." -ForegroundColor Cyan

# Resolve project root from script location
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = (Resolve-Path (Join-Path $scriptDir "..")).Path

# Activate .venv path for convenience string interpolation
$venvPython = Join-Path $rootDir ".venv\Scripts\python.exe"
$varDir = Join-Path $rootDir "var"
New-Item -ItemType Directory -Force -Path $varDir | Out-Null
$dbPath = Join-Path $varDir "trading_data.db"

Write-Host "Using Database at: $dbPath" -ForegroundColor Magenta

# 1. Frontend (Port 5173)
Write-Host "Starting Frontend (Port 5173)..." -ForegroundColor Yellow
$feCommand = "& { cd '$rootDir\frontend\quant_frontend'; npm run dev }"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $feCommand

# 2. Instructions for Backend
Write-Host "`n⚠️  BACKEND SERVICES HAVE NOT STARTED YET!" -ForegroundColor Yellow
Write-Host "   To enable breakpoints:"
Write-Host "   1. Open VS Code 'Run and Debug' tab (Ctrl+Shift+D)."
Write-Host "   2. Select 'Debug: API Gateway' (or 'Debug: All Backends')."
Write-Host "   3. Press F5 (Play Button)." -ForegroundColor Green
Write-Host "`n   Using this method, VS Code will attach to the process and your breakpoints will work."

Write-Host "`n✅ Frontend launched. Waiting for you to start Backend in VS Code..." -ForegroundColor Green
Start-Sleep -Seconds 2
