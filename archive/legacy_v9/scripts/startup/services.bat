@echo off
REM GremlinsAI Service Manager for Windows
REM Quick commands to manage Weaviate, Redis, and Ollama

if "%1"=="" goto usage

if "%1"=="start" goto start
if "%1"=="stop" goto stop
if "%1"=="restart" goto restart
if "%1"=="status" goto status
if "%1"=="logs" goto logs
if "%1"=="setup" goto setup
goto usage

:start
echo Starting GremlinsAI Services...
python scripts/manage_services.py start
goto end

:stop
echo Stopping GremlinsAI Services...
python scripts/manage_services.py stop
goto end

:restart
echo Restarting GremlinsAI Services...
python scripts/manage_services.py restart
goto end

:status
python scripts/manage_services.py status
goto end

:logs
if "%2"=="" (
    python scripts/manage_services.py logs
) else (
    python scripts/manage_services.py logs --service %2
)
goto end

:setup
echo Setting up Ollama models...
python scripts/manage_services.py setup-ollama
goto end

:usage
echo.
echo GremlinsAI Service Manager
echo ========================
echo.
echo Usage: services.bat [command] [options]
echo.
echo Commands:
echo   start      - Start all services (Weaviate, Redis, Ollama)
echo   stop       - Stop all services
echo   restart    - Restart all services
echo   status     - Show service status
echo   logs       - Show service logs
echo   setup      - Download Ollama models
echo.
echo Examples:
echo   services.bat start
echo   services.bat status
echo   services.bat logs weaviate
echo   services.bat setup
echo.

:end

