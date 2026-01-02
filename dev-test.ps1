# dev-test.ps1
# Universal Test Runner for Strategy Analysis Platform V2
$ErrorActionPreference = "Continue"

Write-Host "🧪 Starting Full Stack Test Suite..." -ForegroundColor Cyan

# Activate .venv
if (Test-Path ".venv/Scripts/Activate.ps1") {
    . .venv/Scripts/Activate.ps1
}

$failed = $false

# Function to run pytest and catch failure
function Run-TestGroup ($name, $path, $pythonpath) {
    Write-Host "`nTesting $name..." -ForegroundColor Yellow
    $env:PYTHONPATH = $pythonpath
    pytest -v $path
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ $name Tests Failed!" -ForegroundColor Red
        return $true
    } else {
        Write-Host "✅ $name Tests Passed!" -ForegroundColor Green
        return $false
    }
}

# 1. Shared Core
$fail_shared = Run-TestGroup "Shared Core" "packages/quant_shared" "$PWD/packages/quant_shared"

if ($fail_shared) { $failed = $true }

# 2. API Gateway
$fail_api = Run-TestGroup "API Gateway" "services/api_gateway" "$PWD/services/api_gateway/src"

if ($fail_api) { $failed = $true }

# 3. ML Core
$fail_ml = Run-TestGroup "ML Core" "services/ml_core" "$PWD/services/ml_core/src"

if ($fail_ml) { $failed = $true }

# 4. Frontend
Write-Host "`nTesting Frontend..." -ForegroundColor Yellow
Push-Location "frontend/quant_frontend"
try {
    npm run test -- --run
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Frontend Tests Failed!" -ForegroundColor Red
        $failed = $true
    } else {
        Write-Host "✅ Frontend Tests Passed!" -ForegroundColor Green
    }
} finally {
    Pop-Location
}

Write-Host "`n----------------------------------------"
if ($failed) {
    Write-Host "❌ OVERALL STATUS: FAILED" -ForegroundColor Red
    exit 1
} else {
    Write-Host "✅ OVERALL STATUS: ALL SYSTEMS GO" -ForegroundColor Green
    exit 0
}
