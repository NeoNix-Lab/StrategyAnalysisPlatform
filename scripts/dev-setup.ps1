# dev-setup.ps1
# Unified Setup Script for Strategy Analysis Platform V2
$ErrorActionPreference = "Stop"

# Resolve project root from script location
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = (Resolve-Path (Join-Path $scriptDir "..")).Path
$venvDir = Join-Path $rootDir ".venv"

Write-Host "🚀 Starting Strategy Analysis Platform Setup..." -ForegroundColor Cyan

# 1. Python Environment Setup
if (-not (Test-Path $venvDir)) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    # Try to find a suitable python version if available via py launcher, else default to python
    if (Get-Command "py" -ErrorAction SilentlyContinue) {
         # Prefer 3.10-3.12 for ML compatibility if specific version needed, but here we assume user handles venv creation
         # or we default to system python. Since user is manually creating venv with py -3.9, we respect that if it exists.
         python -m venv $venvDir
    } else {
         python -m venv $venvDir
    }
} else {
    Write-Host "Virtual environment found." -ForegroundColor Green
}

# Define path to the VENV python executable to force its usage
# Check for Windows by looking at env:OS or filesystem path structure
if ($IsWindows -or $env:OS -like "*Windows*") {
    $venvPython = Join-Path $venvDir "Scripts\python.exe"
} else {
    $venvPython = Join-Path $venvDir "bin/python"
}

# Verify venv python exists
if (-not (Test-Path $venvPython)) {
    Write-Error "Could not find python executable in .venv at $venvPython. Please create the venv first."
}

# 2. Upgrade pip using VENV python
Write-Host "Upgrading pip..." -ForegroundColor Yellow
& $venvPython -m pip install --upgrade pip

# 3. Install Packages in Editable Mode using VENV python
$packages = @(
    (Join-Path $rootDir "packages/quant_shared"),
    (Join-Path $rootDir "services/api_gateway"),
    (Join-Path $rootDir "services/ml_core")
)

foreach ($pkg in $packages) {
    Write-Host "Installing $pkg..." -ForegroundColor Yellow
    & $venvPython -m pip install -e $pkg
}

# 4. Frontend Setup
Write-Host "Setting up Frontend..." -ForegroundColor Yellow
Push-Location (Join-Path $rootDir "frontend/quant_frontend")
try {
    npm install
} finally {
    Pop-Location
}

Write-Host "✅ Setup Complete! You can now use 'scripts/dev-run.ps1' to start the platform." -ForegroundColor Green
