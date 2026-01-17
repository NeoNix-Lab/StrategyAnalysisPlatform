# dev-test.ps1
# Universal Test Runner for Strategy Analysis Platform V2
$ErrorActionPreference = "Continue"

# Resolve project root from script location
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = (Resolve-Path (Join-Path $scriptDir "..")).Path
$packagesPath = (Resolve-Path (Join-Path $rootDir "packages\\quant_shared\\src")).Path
Write-Host "🧪 Starting Full Stack Test Suite..." -ForegroundColor Cyan

# Activate .venv
$activatePath = Join-Path $rootDir ".venv/Scripts/Activate.ps1"
if (Test-Path $activatePath) {
    . $activatePath
}

$failed = $false

# Function to run pytest and catch failure
function Run-TestGroup ($name, $path, $pythonpath) {
    Write-Host "`nTesting $name..." -ForegroundColor Yellow
    $env:PYTHONPATH = "$pythonpath;$packagesPath"
    pytest -v $path
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ $name Tests Failed!" -ForegroundColor Red
        return $true
    }
    else {
        Write-Host "✅ $name Tests Passed!" -ForegroundColor Green
        return $false
    }
}

# 1. Shared Core
$fail_shared = Run-TestGroup "Shared Core" (Join-Path $rootDir "packages/quant_shared") (Join-Path $rootDir "packages/quant_shared/src")

if ($fail_shared) { $failed = $true }

# 2. API Gateway
$fail_api = Run-TestGroup "API Gateway" (Join-Path $rootDir "services/api_gateway") (Join-Path $rootDir "services/api_gateway/src")

if ($fail_api) { $failed = $true }

# 3. ML Core
$fail_ml = Run-TestGroup "ML Core" (Join-Path $rootDir "services/ml_core") (Join-Path $rootDir "services/ml_core/src")

if ($fail_ml) { $failed = $true }

# 4. Frontend
Write-Host "`nTesting Frontend..." -ForegroundColor Yellow
Push-Location (Join-Path $rootDir "frontend/quant_frontend")
try {
    Write-Host "Current Failed Status before Frontend: $failed" -ForegroundColor Magenta
    
    # Use npm.cmd for Windows compatibility
    $npmCmd = "npm.cmd"
    if ($IsLinux -or $IsMacOS) { $npmCmd = "npm" }

    Write-Host "Running $npmCmd test..."
    
    # Run synchronously and wait
    & $npmCmd run test -- --run
    $exitCode = $LASTEXITCODE
    
    Write-Host "Frontend Test Exit Code: $exitCode" -ForegroundColor Cyan

    if ($exitCode -ne 0) {
        Write-Host "❌ Frontend Tests Failed!" -ForegroundColor Red
        $failed = $true
    }
    else {
        Write-Host "✅ Frontend Tests Passed!" -ForegroundColor Green
    }
}
catch {
    Write-Host "Error running frontend tests: $_" -ForegroundColor Red
    $failed = $true
}
finally {
    Pop-Location
}

Write-Host "`n----------------------------------------"
if ($failed) {
    Write-Host "❌ OVERALL STATUS: FAILED" -ForegroundColor Red
    exit 1
}
else {
    Write-Host "✅ OVERALL STATUS: ALL SYSTEMS GO" -ForegroundColor Green
    exit 0
}
