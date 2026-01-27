@echo off
REM ============================================================================
REM Test Runner Script for Takeoff Automation (Windows)
REM 
REM Usage:
REM   scripts\run_tests.bat [command]
REM
REM Commands:
REM   unit        - Run backend unit tests (pytest)
REM   integration - Run integration tests against running containers
REM   rebuild     - Rebuild Docker containers and run tests
REM ============================================================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "DOCKER_DIR=%PROJECT_ROOT%\docker"
set "COMMAND=%~1"

if "%COMMAND%"=="" set "COMMAND=help"

if "%COMMAND%"=="unit" goto :unit
if "%COMMAND%"=="integration" goto :integration
if "%COMMAND%"=="rebuild" goto :rebuild
if "%COMMAND%"=="help" goto :help
if "%COMMAND%"=="--help" goto :help
if "%COMMAND%"=="-h" goto :help

echo Unknown command: %COMMAND%
goto :help

:help
echo Test Runner for Takeoff Automation
echo.
echo Usage: %~nx0 [command]
echo.
echo Commands:
echo   unit        Run backend unit tests (pytest)
echo   integration Run integration tests against running containers
echo   rebuild     Rebuild Docker containers and run tests
echo   help        Show this help message
echo.
echo Examples:
echo   %~nx0 unit
echo   %~nx0 integration
echo   %~nx0 rebuild
goto :eof

:unit
echo ========================================
echo Running Backend Unit Tests
echo ========================================
cd /d "%PROJECT_ROOT%\docker"
docker compose exec -T api python -m pytest tests/test_ai_takeoff.py -v --tb=short
goto :eof

:integration
echo ========================================
echo Running Integration Tests
echo ========================================
cd /d "%DOCKER_DIR%"

REM Check if containers are running
docker compose ps | findstr /c:"api" | findstr /c:"running" > nul
if errorlevel 1 (
    echo Starting containers...
    docker compose up -d
    timeout /t 10 /nobreak > nul
)

REM Run integration test using curl
echo Checking API health...
curl -s http://localhost:8000/api/v1/health

echo.
echo Testing GET /ai-takeoff/providers...
curl -s http://localhost:8000/api/v1/ai-takeoff/providers

echo.
echo Integration tests require bash. Run in WSL or Git Bash:
echo   bash scripts/run_tests.sh integration
goto :eof

:rebuild
echo ========================================
echo Rebuilding Docker Containers
echo ========================================
cd /d "%DOCKER_DIR%"

echo Stopping containers...
docker compose down --remove-orphans

echo Building containers...
docker compose build

echo Starting containers...
docker compose up -d

echo Waiting for services...
timeout /t 15 /nobreak > nul

:wait_loop
curl -s http://localhost:8000/api/v1/health > nul 2>&1
if errorlevel 1 (
    echo Waiting for API...
    timeout /t 2 /nobreak > nul
    goto :wait_loop
)

echo API is ready!

REM Run unit tests
call :unit
goto :eof
