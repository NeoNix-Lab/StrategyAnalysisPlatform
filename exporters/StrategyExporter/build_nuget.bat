@echo off
echo ==========================================
echo Building StrategyExporter NuGet Package
echo ==========================================

REM Define the output directory for the package
set OUTPUT_DIR=.\bin\Debug

REM Clean previous builds
echo Cleaning solution...
dotnet clean --configuration Release

REM Pack the project
echo Packing project...
dotnet pack --configuration Debug --output %OUTPUT_DIR%

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Packing failed.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [SUCCESS] Package created successfully in %OUTPUT_DIR%
echo.
pause
