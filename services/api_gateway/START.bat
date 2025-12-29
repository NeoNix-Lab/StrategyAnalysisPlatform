@echo off
echo ========================================
echo   Strategy Analysis Platform - Setup
echo ========================================
echo.

echo [1/3] Popolamento database con dati di test...
python seed_data.py
if %errorlevel% neq 0 (
    echo ERRORE: Seed fallito!
    pause
    exit /b 1
)

echo.
echo [2/3] Verifica database...
python check_db.py

echo.
echo [3/3] Avvio server API...
echo Server disponibile su: http://127.0.0.1:8000
echo.
echo Per avviare il frontend, apri un altro terminale ed esegui:
echo   cd frontend
echo   npm run dev
echo.
python run_server.py
