# dev-setup.ps1
# Unified Setup Script for Strategy Analysis Platform V2
$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Strategy Analysis Platform Setup..." -ForegroundColor Cyan

# 1. Python Environment Setup
if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    # Try to find a suitable python version if available via py launcher, else default to python
    if (Get-Command "py" -ErrorAction SilentlyContinue) {
         # Prefer 3.10-3.12 for ML compatibility if specific version needed, but here we assume user handles venv creation
         # or we default to system python. Since user is manually creating venv with py -3.9, we respect that if it exists.
         python -m venv .venv
    } else {
         python -m venv .venv
    }
} else {
    Write-Host "Virtual environment found." -ForegroundColor Green
}

# Define path to the VENV python executable to force its usage
# Check for Windows by looking at env:OS or filesystem path structure
if ($IsWindows -or $env:OS -like "*Windows*") {
    $venvPython = ".\.venv\Scripts\python.exe"
} else {
    $venvPython = "./.venv/bin/python"
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
    "packages/quant_shared",
    "services/api_gateway",
    "services/ml_core"
)

foreach ($pkg in $packages) {
    Write-Host "Installing $pkg..." -ForegroundColor Yellow
    & $venvPython -m pip install -e $pkg
}

# 4. Frontend Setup
Write-Host "Setting up Frontend..." -ForegroundColor Yellow
Push-Location "frontend/quant_frontend"
try {
    npm install
} finally {
    Pop-Location
}

Write-Host "✅ Setup Complete! You can now use 'dev-run.ps1' to start the platform." -ForegroundColor Green
