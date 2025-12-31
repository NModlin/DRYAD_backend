@echo off
REM GremlinsAI Backend - Quick Start Script (Windows)
REM Automated setup and deployment for new users

setlocal enabledelayedexpansion

REM Configuration
set DEFAULT_INSTALL_TIER=standard
set DEFAULT_LLM_PROVIDER=mock

REM Function to print colored output (Windows doesn't support colors easily)
:print_header
echo.
echo ========================================
echo %~1
echo ========================================
echo.
goto :eof

:print_step
echo [STEP] %~1
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

:print_info
echo [INFO] %~1
goto :eof

REM Function to check prerequisites
:check_prerequisites
call :print_step "Checking prerequisites..."

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    call :print_error "Docker is not installed. Please install Docker first."
    echo Visit: https://docs.docker.com/get-docker/
    exit /b 1
)

REM Check Docker Compose
docker compose version >nul 2>&1
if errorlevel 1 (
    docker-compose --version >nul 2>&1
    if errorlevel 1 (
        call :print_error "Docker Compose is not installed. Please install Docker Compose first."
        echo Visit: https://docs.docker.com/compose/install/
        exit /b 1
    )
)

REM Check Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    call :print_error "Docker is not running. Please start Docker and try again."
    exit /b 1
)

call :print_success "Prerequisites check completed"
goto :eof

REM Function to gather user preferences
:gather_preferences
call :print_step "Gathering your preferences..."

echo Welcome to GremlinsAI Backend Quick Start!
echo This script will help you set up and deploy the GremlinsAI backend system.
echo.

REM Installation tier
echo Choose your installation tier:
echo 1) Minimal    - Basic API only (1-2GB RAM)
echo 2) Standard   - Full AI features (4-6GB RAM) [Recommended]
echo 3) Full       - All features including multimodal (8GB+ RAM)
echo 4) Development - Development environment with hot reload
echo.

:tier_choice_loop
set /p tier_choice="Enter your choice (1-4) [2]: "
if "%tier_choice%"=="" set tier_choice=2

if "%tier_choice%"=="1" (
    set INSTALL_TIER=minimal
    goto llm_choice
)
if "%tier_choice%"=="2" (
    set INSTALL_TIER=standard
    goto llm_choice
)
if "%tier_choice%"=="3" (
    set INSTALL_TIER=full
    goto llm_choice
)
if "%tier_choice%"=="4" (
    set INSTALL_TIER=development
    goto llm_choice
)
echo Please enter 1, 2, 3, or 4
goto tier_choice_loop

:llm_choice
echo.
echo Choose your LLM provider:
echo 1) Mock       - Fake responses for testing [Recommended for quick start]
echo 2) OpenAI     - Use OpenAI GPT models (requires API key)
echo 3) Ollama     - Local LLM (will download models)
echo.

:llm_choice_loop
set /p llm_choice="Enter your choice (1-3) [1]: "
if "%llm_choice%"=="" set llm_choice=1

if "%llm_choice%"=="1" (
    set LLM_PROVIDER=mock
    goto domain_choice
)
if "%llm_choice%"=="2" (
    set LLM_PROVIDER=openai
    goto openai_key
)
if "%llm_choice%"=="3" (
    set LLM_PROVIDER=ollama
    goto domain_choice
)
echo Please enter 1, 2, or 3
goto llm_choice_loop

:openai_key
echo.
set /p OPENAI_API_KEY="Enter your OpenAI API key: "
if "%OPENAI_API_KEY%"=="" (
    call :print_warning "No API key provided. Falling back to mock provider."
    set LLM_PROVIDER=mock
)

:domain_choice
echo.
set /p DOMAIN="Enter your domain (or press Enter for localhost): "
if "%DOMAIN%"=="" set DOMAIN=localhost

call :print_success "Preferences gathered"
call :print_info "Installation tier: %INSTALL_TIER%"
call :print_info "LLM provider: %LLM_PROVIDER%"
call :print_info "Domain: %DOMAIN%"
goto :eof

REM Function to setup environment
:setup_environment
call :print_step "Setting up environment configuration..."

REM Create .env file from template
if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        call :print_success "Created .env file from template"
    ) else (
        call :print_error ".env.example file not found"
        exit /b 1
    )
) else (
    call :print_warning ".env file already exists. Creating backup..."
    copy .env .env.backup.%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2% >nul
)

REM Generate secure JWT secret (simplified for Windows)
for /f %%i in ('powershell -command "[System.Web.Security.Membership]::GeneratePassword(48, 0)"') do set JWT_SECRET=%%i

REM Update .env file (Windows batch string replacement)
powershell -command "(Get-Content .env) -replace 'INSTALL_TIER=.*', 'INSTALL_TIER=%INSTALL_TIER%' | Set-Content .env"
powershell -command "(Get-Content .env) -replace 'LLM_PROVIDER=.*', 'LLM_PROVIDER=%LLM_PROVIDER%' | Set-Content .env"
powershell -command "(Get-Content .env) -replace 'JWT_SECRET_KEY=.*', 'JWT_SECRET_KEY=%JWT_SECRET%' | Set-Content .env"

if "%LLM_PROVIDER%"=="openai" if not "%OPENAI_API_KEY%"=="" (
    powershell -command "(Get-Content .env) -replace 'OPENAI_API_KEY=.*', 'OPENAI_API_KEY=%OPENAI_API_KEY%' | Set-Content .env"
)

if not "%DOMAIN%"=="localhost" (
    powershell -command "(Get-Content .env) -replace 'API_BASE_URL=.*', 'API_BASE_URL=https://%DOMAIN%' | Set-Content .env"
    powershell -command "(Get-Content .env) -replace 'FRONTEND_URL=.*', 'FRONTEND_URL=https://%DOMAIN%' | Set-Content .env"
)

call :print_success "Environment configuration completed"
goto :eof

REM Function to create necessary directories
:create_directories
call :print_step "Creating necessary directories..."

if not exist data mkdir data
if not exist logs mkdir logs
if not exist nginx\ssl mkdir nginx\ssl
if not exist monitoring mkdir monitoring

call :print_success "Directories created"
goto :eof

REM Function to start services
:start_services
call :print_step "Starting GremlinsAI services..."

if "%INSTALL_TIER%"=="minimal" (
    docker-compose -f docker-compose.minimal.yml up -d
) else if "%INSTALL_TIER%"=="standard" (
    docker-compose up -d gremlins-api weaviate redis celery-worker
) else if "%INSTALL_TIER%"=="full" (
    docker-compose up -d
) else if "%INSTALL_TIER%"=="development" (
    docker-compose -f docker-compose.development.yml up -d
)

call :print_success "Services started"
goto :eof

REM Function to wait for services
:wait_for_services
call :print_step "Waiting for services to be ready..."

set max_wait=120
set wait_time=0

:wait_loop
curl -f http://localhost:8000/api/v1/health/status >nul 2>&1
if not errorlevel 1 (
    call :print_success "API is ready!"
    goto :eof
)

echo|set /p="."
timeout /t 5 /nobreak >nul
set /a wait_time+=5

if %wait_time% lss %max_wait% goto wait_loop

call :print_error "Services did not start within timeout"
call :print_info "Check logs with: docker-compose logs"
exit /b 1

REM Function to run health checks
:run_health_checks
call :print_step "Running health checks..."

REM API health check
curl -f http://localhost:8000/api/v1/health/status >nul 2>&1
if errorlevel 1 (
    call :print_error "✗ API health check failed"
    goto :eof
) else (
    call :print_success "✓ API is healthy"
)

REM Service-specific checks based on installation tier
if not "%INSTALL_TIER%"=="minimal" (
    REM Check Weaviate
    curl -f http://localhost:8080/v1/.well-known/ready >nul 2>&1
    if errorlevel 1 (
        call :print_warning "⚠ Weaviate is not responding (may still be starting)"
    ) else (
        call :print_success "✓ Weaviate is healthy"
    )
    
    REM Check Redis
    docker exec gremlins-redis redis-cli ping >nul 2>&1
    if errorlevel 1 (
        call :print_warning "⚠ Redis is not responding"
    ) else (
        call :print_success "✓ Redis is healthy"
    )
)

call :print_success "Health checks completed"
goto :eof

REM Function to setup Ollama if needed
:setup_ollama
if "%LLM_PROVIDER%"=="ollama" (
    call :print_step "Setting up Ollama local LLM..."
    
    REM Start Ollama if not already running
    docker-compose ps ollama | find "Up" >nul
    if errorlevel 1 (
        docker-compose up -d ollama
        call :print_info "Waiting for Ollama to start..."
        timeout /t 30 /nobreak >nul
    )
    
    REM Pull recommended model
    call :print_info "Downloading recommended model (llama3.2:3b)..."
    call :print_warning "This may take several minutes depending on your internet connection..."
    
    docker exec gremlins-ollama ollama pull llama3.2:3b
    if errorlevel 1 (
        call :print_error "Failed to download Ollama model"
        call :print_info "You can download it later with: docker exec gremlins-ollama ollama pull llama3.2:3b"
    ) else (
        call :print_success "Ollama model downloaded successfully"
    )
)
goto :eof

REM Function to display final information
:display_final_info
call :print_header "🎉 GremlinsAI Backend Setup Complete!"

echo Your GremlinsAI backend is now running!
echo.
echo 📍 Access Points:
echo    • API: http://localhost:8000
echo    • Documentation: http://localhost:8000/docs
echo    • Health Check: http://localhost:8000/api/v1/health/status

if not "%INSTALL_TIER%"=="minimal" (
    echo    • Weaviate: http://localhost:8080
)

echo.
echo 🔧 Management Commands:
echo    • View status: scripts\docker-start.bat status
echo    • View logs: docker-compose logs -f gremlins-api
echo    • Stop services: scripts\docker-start.bat stop
echo    • Health check: scripts\docker-start.bat health

echo.
echo 📚 Next Steps:
echo    1. Test the API: curl http://localhost:8000/api/v1/health/status
echo    2. Explore the documentation: http://localhost:8000/docs
echo    3. Check the deployment guide: DEPLOYMENT_GUIDE.md
echo    4. Set up authentication (see docs for OAuth2 setup)

if "%LLM_PROVIDER%"=="mock" (
    echo.
    call :print_info "You're using mock LLM responses. To use real AI:"
    echo    • Set up OpenAI: Add OPENAI_API_KEY to .env
    echo    • Use local LLM: Run scripts\docker-start.bat ollama
)

echo.
echo 🆘 Need Help?
echo    • Troubleshooting: TROUBLESHOOTING.md
echo    • Docker Guide: DOCKER_GUIDE.md
echo    • GitHub Issues: ^<repository-url^>/issues

echo.
call :print_success "Happy coding with GremlinsAI! 🚀"
goto :eof

REM Main execution
call :print_header "🚀 GremlinsAI Backend Quick Start"

call :check_prerequisites
if errorlevel 1 exit /b 1

call :gather_preferences
call :setup_environment
if errorlevel 1 exit /b 1

call :create_directories
call :start_services
call :wait_for_services
if errorlevel 1 exit /b 1

call :setup_ollama
call :run_health_checks
call :display_final_info
