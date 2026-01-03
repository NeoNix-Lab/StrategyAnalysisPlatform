# dev-run.ps1
# Full Stack Launcher for Strategy Analysis Platform V2

Write-Host "🚀 Launching Strategy Analysis Platform..." -ForegroundColor Cyan

# Activate .venv path for convenience string interpolation
$venvPython = "$PWD\.venv\Scripts\python.exe"

# Resolve absolute path to the database to avoid any relative path confusion
$dbPath = "$PWD\trading_data.db"
Write-Host "Using Database at: $dbPath" -ForegroundColor Magenta
$packagesPath = (Resolve-Path ".\packages").Path

# 9. API Gateway (Port 8000)
Write-Host "Starting API Gateway (Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { . .venv/Scripts/Activate.ps1; cd services/api_gateway; $env:TRADING_DB_PATH='$dbPath'; $env:PYTHONPATH='$packagesPath;$PWD/src'; python -m uvicorn src.api.main:app --reload --port 8000 }"

# 10. ML Core (Port 5000)
Write-Host "Starting ML Core (Port 5000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { . .venv/Scripts/Activate.ps1; cd services/ml_core; $env:TRADING_DB_PATH='$dbPath'; $env:PYTHONPATH='$packagesPath;$PWD/src'; python -m uvicorn src.main:app --reload --port 5000 }"

# 3. Frontend (Port 5173)
Write-Host "Starting Frontend (Port 5173)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { cd frontend/quant_frontend; npm run dev }"

Write-Host "✅ All services launched in separate windows." -ForegroundColor Green
Write-Host "Opening Dashboard..."
Start-Sleep -Seconds 3
Start-Process "http://localhost:5173"
