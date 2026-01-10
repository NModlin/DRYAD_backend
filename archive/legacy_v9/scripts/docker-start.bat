@echo off
REM GremlinsAI Backend - Docker Startup Script (Windows)
REM Provides easy commands for different deployment scenarios

setlocal enabledelayedexpansion

REM Default values
if "%INSTALL_TIER%"=="" set INSTALL_TIER=standard
if "%ENVIRONMENT%"=="" set ENVIRONMENT=development

REM Function to print colored output (Windows doesn't support colors easily, so we'll use plain text)
:print_status
echo [INFO] %~1
goto :eof

:print_success
echo [SUCCESS] %~1
goto :eof

:print_warning
echo [WARNING] %~1
goto :eof

:print_error
echo [ERROR] %~1
goto :eof

REM Function to check if Docker is running
:check_docker
docker info >nul 2>&1
if errorlevel 1 (
    call :print_error "Docker is not running. Please start Docker and try again."
    exit /b 1
)
goto :eof

REM Function to check if .env file exists
:check_env_file
if not exist .env (
    call :print_warning ".env file not found. Creating from template..."
    copy .env.example .env >nul
    call :print_warning "Please edit .env file with your configuration before continuing."
    call :print_warning "At minimum, set JWT_SECRET_KEY and any API keys you plan to use."
    pause
)
goto :eof

REM Function to create necessary directories
:create_directories
call :print_status "Creating necessary directories..."
if not exist data mkdir data
if not exist logs mkdir logs
if not exist nginx\ssl mkdir nginx\ssl
if not exist monitoring mkdir monitoring
goto :eof

REM Function to start minimal installation
:start_minimal
call :print_status "Starting GremlinsAI in minimal mode..."
set INSTALL_TIER=minimal
docker-compose -f docker-compose.minimal.yml up -d
call :print_success "Minimal installation started!"
call :print_status "API available at: http://localhost:8000"
call :print_status "API Documentation: http://localhost:8000/docs"
goto :eof

REM Function to start standard installation
:start_standard
call :print_status "Starting GremlinsAI in standard mode..."
set INSTALL_TIER=standard
docker-compose up -d gremlins-api weaviate redis celery-worker
call :print_success "Standard installation started!"
call :print_status "API available at: http://localhost:8000"
call :print_status "Weaviate available at: http://localhost:8080"
call :print_status "API Documentation: http://localhost:8000/docs"
goto :eof

REM Function to start full installation
:start_full
call :print_status "Starting GremlinsAI in full mode..."
set INSTALL_TIER=full
docker-compose up -d
call :print_success "Full installation started!"
call :print_status "API available at: http://localhost:8000"
call :print_status "Weaviate available at: http://localhost:8080"
call :print_status "API Documentation: http://localhost:8000/docs"
goto :eof

REM Function to start development environment
:start_development
call :print_status "Starting GremlinsAI development environment..."
docker-compose -f docker-compose.development.yml up -d
call :print_success "Development environment started!"
call :print_status "API available at: http://localhost:8000 (with hot reload)"
call :print_status "Weaviate available at: http://localhost:8080"
call :print_status "Redis available at: http://localhost:6379"
call :print_status "API Documentation: http://localhost:8000/docs"
goto :eof

REM Function to start with local LLM
:start_with_ollama
call :print_status "Starting GremlinsAI with Ollama local LLM..."
docker-compose --profile local-llm up -d
call :print_status "Waiting for Ollama to start..."
timeout /t 10 /nobreak >nul
call :print_status "Pulling recommended model (llama3.2:3b)..."
docker exec gremlins-ollama ollama pull llama3.2:3b
call :print_success "GremlinsAI with Ollama started!"
call :print_status "API available at: http://localhost:8000"
call :print_status "Ollama available at: http://localhost:11434"
goto :eof

REM Function to stop all services
:stop_all
call :print_status "Stopping all GremlinsAI services..."
docker-compose -f docker-compose.yml down
docker-compose -f docker-compose.minimal.yml down
docker-compose -f docker-compose.development.yml down
call :print_success "All services stopped!"
goto :eof

REM Function to show status
:show_status
call :print_status "GremlinsAI Service Status:"
docker-compose ps
goto :eof

REM Function to show logs
:show_logs
set service=%~1
if "%service%"=="" set service=gremlins-api
call :print_status "Showing logs for %service%..."
docker-compose logs -f %service%
goto :eof

REM Function to run health check
:health_check
call :print_status "Running health check..."

REM Check API
curl -f http://localhost:8000/api/v1/health/status >nul 2>&1
if errorlevel 1 (
    call :print_error "✗ API is not responding"
) else (
    call :print_success "✓ API is healthy"
)

REM Check Weaviate (if running)
curl -f http://localhost:8080/v1/.well-known/ready >nul 2>&1
if errorlevel 1 (
    call :print_warning "⚠ Weaviate is not responding (may not be running)"
) else (
    call :print_success "✓ Weaviate is healthy"
)

REM Check Redis (if running)
docker exec gremlins-redis redis-cli ping >nul 2>&1
if errorlevel 1 (
    call :print_warning "⚠ Redis is not responding (may not be running)"
) else (
    call :print_success "✓ Redis is healthy"
)
goto :eof

REM Function to show help
:show_help
echo GremlinsAI Backend - Docker Management Script (Windows)
echo.
echo Usage: %~nx0 [COMMAND]
echo.
echo Commands:
echo   minimal       Start minimal installation (basic API only)
echo   standard      Start standard installation (with vector DB and multi-agent)
echo   full          Start full installation (all features including multimodal)
echo   dev           Start development environment (with hot reload)
echo   ollama        Start with local Ollama LLM
echo   stop          Stop all services
echo   status        Show service status
echo   logs [service] Show logs (default: gremlins-api)
echo   health        Run health check
echo   help          Show this help message
echo.
echo Examples:
echo   %~nx0 minimal                    # Start basic API
echo   %~nx0 standard                   # Start with AI features
echo   %~nx0 dev                        # Start development environment
echo   %~nx0 logs gremlins-api         # Show API logs
echo   %~nx0 health                     # Check service health
goto :eof

REM Main script logic
call :check_docker

if "%~1"=="" goto show_help
if "%~1"=="help" goto show_help
if "%~1"=="--help" goto show_help
if "%~1"=="-h" goto show_help

if "%~1"=="minimal" (
    call :check_env_file
    call :create_directories
    call :start_minimal
    goto :eof
)

if "%~1"=="standard" (
    call :check_env_file
    call :create_directories
    call :start_standard
    goto :eof
)

if "%~1"=="full" (
    call :check_env_file
    call :create_directories
    call :start_full
    goto :eof
)

if "%~1"=="dev" (
    call :check_env_file
    call :create_directories
    call :start_development
    goto :eof
)

if "%~1"=="development" (
    call :check_env_file
    call :create_directories
    call :start_development
    goto :eof
)

if "%~1"=="ollama" (
    call :check_env_file
    call :create_directories
    call :start_with_ollama
    goto :eof
)

if "%~1"=="stop" (
    call :stop_all
    goto :eof
)

if "%~1"=="status" (
    call :show_status
    goto :eof
)

if "%~1"=="logs" (
    call :show_logs %~2
    goto :eof
)

if "%~1"=="health" (
    call :health_check
    goto :eof
)

call :print_error "Unknown command: %~1"
call :show_help
