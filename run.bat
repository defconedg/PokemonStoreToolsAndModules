@echo off
echo.
echo  ===============================================
echo    Pokemon Card Arbitrage Tool - Launcher
echo  ===============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.6+ and try again.
    goto :end
)

REM Check if requirements are installed
echo [INFO] Checking and installing dependencies...
pip install -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Some dependencies may not have installed correctly.
)

REM Create cache directory if needed
if not exist "cache" mkdir cache
echo [INFO] Cache directory ready

REM Check if .env file exists, if not create from example
if not exist .env (
    echo [INFO] Creating .env file from template...
    if exist .env.example (
        copy .env.example .env >nul
        echo [INFO] Created .env file from template. Please edit with your API keys.
        echo.
        echo You can get a free Pokemon TCG API key from: https://dev.pokemontcg.io/
        echo.
    ) else (
        echo [WARNING] No .env.example file found. You'll need to create a .env file manually.
    )
)

REM Run the application
echo.
echo [INFO] Starting Pokemon Card Arbitrage Tool...
echo [INFO] Press Ctrl+C to stop the server when finished
echo.
python arbitrage_tool.py

:end
pause
