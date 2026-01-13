# dev-run.ps1
# Full Stack Launcher for Strategy Analysis Platform V2

Write-Host "🚀 Launching Strategy Analysis Platform..." -ForegroundColor Cyan

# Resolve project root from script location
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = (Resolve-Path (Join-Path $scriptDir "..")).Path

# Activate .venv path for convenience string interpolation
$venvPython = Join-Path $rootDir ".venv\Scripts\python.exe"

# Resolve absolute path to the database to avoid any relative path confusion
$varDir = Join-Path $rootDir "var"
New-Item -ItemType Directory -Force -Path $varDir | Out-Null
$dbPath = Join-Path $varDir "trading_data.db"
Write-Host "Using Database at: $dbPath" -ForegroundColor Magenta
$packagesPath = (Resolve-Path (Join-Path $rootDir "packages")).Path
$apiSrcPath = Join-Path $rootDir "services\api_gateway\src"
$mlSrcPath = Join-Path $rootDir "services\ml_core\src"

# 9. API Gateway (Port 8000)
Write-Host "Starting API Gateway (Port 8000)..." -ForegroundColor Yellow
$apiCommand = "& { . '$rootDir\.venv\Scripts\Activate.ps1'; cd '$rootDir\services\api_gateway'; $env:TRADING_DB_PATH='$dbPath'; $env:PYTHONPATH='$packagesPath;$apiSrcPath'; python -m uvicorn src.api.main:app --reload --port 8000 }"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiCommand

# 10. ML Core (Port 5000)
Write-Host "Starting ML Core (Port 5000)..." -ForegroundColor Yellow
$mlCommand = "& { . '$rootDir\.venv\Scripts\Activate.ps1'; cd '$rootDir\services\ml_core'; $env:TRADING_DB_PATH='$dbPath'; $env:PYTHONPATH='$packagesPath;$mlSrcPath'; python -m uvicorn src.main:app --reload --port 5000 }"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $mlCommand

# 3. Frontend (Port 5173)
Write-Host "Starting Frontend (Port 5173)..." -ForegroundColor Yellow
$feCommand = "& { cd '$rootDir\frontend\quant_frontend'; npm run dev }"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $feCommand

Write-Host "✅ All services launched in separate windows." -ForegroundColor Green
Write-Host "Opening Dashboard..."
Start-Sleep -Seconds 3
Start-Process "http://localhost:5173"
