# dev-run-debug.ps1
# Debug Mode Launcher for Strategy Analysis Platform V2
# This script starts the Frontend but leaves the Backends for you to start via VS Code Debugger.

Write-Host "🐞 Launching Strategy Analysis Platform in DEBUG Mode..." -ForegroundColor Cyan

# Activate .venv path for convenience string interpolation
$venvPython = "$PWD\.venv\Scripts\python.exe"
$dbPath = "$PWD\trading_data.db"

Write-Host "Using Database at: $dbPath" -ForegroundColor Magenta

# 1. Frontend (Port 5173)
Write-Host "Starting Frontend (Port 5173)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { cd frontend/quant_frontend; npm run dev }"

# 2. Instructions for Backend
Write-Host "`n⚠️  BACKEND SERVICES HAVE NOT STARTED YET!" -ForegroundColor Yellow
Write-Host "   To enable breakpoints:"
Write-Host "   1. Open VS Code 'Run and Debug' tab (Ctrl+Shift+D)."
Write-Host "   2. Select 'Debug: API Gateway' (or 'Debug: All Backends')."
Write-Host "   3. Press F5 (Play Button)." -ForegroundColor Green
Write-Host "`n   Using this method, VS Code will attach to the process and your breakpoints will work."

Write-Host "`n✅ Frontend launched. Waiting for you to start Backend in VS Code..." -ForegroundColor Green
Start-Sleep -Seconds 2
