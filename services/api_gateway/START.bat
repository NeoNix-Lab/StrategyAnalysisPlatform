@echo off
setlocal
set SCRIPT_DIR=%~dp0
for %%I in ("%SCRIPT_DIR%..\\..") do set ROOT=%%~fI

echo ========================================
echo   Strategy Analysis Platform - Setup
echo ========================================
echo.

if not exist "%ROOT%\\var" mkdir "%ROOT%\\var"
set TRADING_DB_PATH=%ROOT%\\var\\trading_data.db
set PYTHONPATH=%ROOT%\\packages;%ROOT%\\services\\api_gateway\\src

echo [1/3] Popolamento database con dati di test...
python "%ROOT%\\scripts\\seed_data.py"
if %errorlevel% neq 0 (
    echo ERRORE: Seed fallito!
    pause
    exit /b 1
)

echo.
echo [2/3] Verifica database...
python "%ROOT%\\scripts\\check_db_integrity.py"

echo.
echo [3/3] Avvio server API...
echo Server disponibile su: http://127.0.0.1:8000
echo.
echo Per avviare il frontend, apri un altro terminale ed esegui:
echo   cd frontend\\quant_frontend
echo   npm run dev
echo.
python "%SCRIPT_DIR%run_server.py"
endlocal
