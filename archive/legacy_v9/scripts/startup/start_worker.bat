@echo off
REM start_worker.bat: Script to start Celery workers for gremlinsAI Phase 5 on Windows

echo Starting gremlinsAI Celery Workers...

REM Check if Redis is accessible
echo Checking Redis connection...
redis-cli ping >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Redis is not running. Please start Redis first.
    echo To start Redis on Windows:
    echo   - Start Redis service or run redis-server.exe
    echo   - Or use Docker: docker run -d -p 6379:6379 redis:alpine
    pause
    exit /b 1
)

echo Redis is running!

REM Set environment variables if not already set
if not defined REDIS_URL set REDIS_URL=redis://localhost:6379/0

echo Starting Celery worker with the following configuration:
echo   Redis URL: %REDIS_URL%
echo   Worker name: gremlinsai-worker
echo   Concurrency: 4
echo   Log level: INFO

REM Start Celery worker
celery -A app.core.celery_app worker ^
    --loglevel=info ^
    --concurrency=4 ^
    --hostname=gremlinsai-worker@%%h ^
    --queues=default,agent_queue,document_queue,orchestration_queue ^
    --prefetch-multiplier=1 ^
    --max-tasks-per-child=1000

echo Celery worker stopped.
pause
