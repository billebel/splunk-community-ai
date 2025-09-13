@echo off
REM Quick start script for Docker deployments on Windows
REM Usage: docker\scripts\start.bat [scenario]

setlocal EnableDelayedExpansion

set PROJECT_ROOT=%~dp0..\..
set DOCKER_DIR=%PROJECT_ROOT%\docker

REM Default values
set SCENARIO=full-stack
set DETACH=
set BUILD=
set PULL=

REM Parse arguments
:parse_args
if "%1"=="" goto start_deployment
if "%1"=="full-stack" (
    set SCENARIO=full-stack
    shift
    goto parse_args
)
if "%1"=="mcp-only" (
    set SCENARIO=mcp-only
    shift
    goto parse_args
)
if "%1"=="development" (
    set SCENARIO=development
    shift
    goto parse_args
)
if "%1"=="production" (
    set SCENARIO=production
    shift
    goto parse_args
)
if "%1"=="-d" (
    set DETACH=-d
    shift
    goto parse_args
)
if "%1"=="--detach" (
    set DETACH=-d
    shift
    goto parse_args
)
if "%1"=="--build" (
    set BUILD=--build
    shift
    goto parse_args
)
if "%1"=="--pull" (
    set PULL=--pull
    shift
    goto parse_args
)
if "%1"=="--help" goto show_usage
if "%1"=="-h" goto show_usage

echo Unknown option: %1
goto show_usage

:show_usage
echo Splunk Community AI - Docker Deployment
echo.
echo Usage: %0 [scenario] [options]
echo.
echo Scenarios:
echo   full-stack   : MCP Server + LibreChat Web Interface (default)
echo   mcp-only     : MCP Server only, no web interface
echo   development  : Full stack + development Splunk instance
echo   production   : Production-optimized deployment
echo.
echo Options:
echo   --detach, -d : Run in background (detached mode)
echo   --build      : Force rebuild containers
echo   --pull       : Pull latest images before starting
echo   --help, -h   : Show this help message
echo.
echo Examples:
echo   %0                           # Start full-stack in foreground
echo   %0 mcp-only -d              # Start MCP-only in background
echo   %0 production --build -d    # Rebuild and start production
echo.
goto :eof

:start_deployment
REM Check prerequisites
docker --version >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not installed or not in PATH
    exit /b 1
)

docker compose version >nul 2>&1
if errorlevel 1 (
    echo Error: Docker Compose is not available
    exit /b 1
)

REM Check for .env file
if not exist "%PROJECT_ROOT%\.env" (
    echo Warning: .env file not found at %PROJECT_ROOT%\.env
    echo Please create .env file with your configuration.
    echo You can copy from .env.example or .env.auth-examples
    echo.
    set /p confirm="Continue anyway? (y/N): "
    if /i not "!confirm!"=="y" exit /b 1
)

REM Change to project root
cd /d "%PROJECT_ROOT%"

echo Starting Splunk Community AI - %SCENARIO% deployment...
echo.

REM Build command components
set BASE_CMD=docker compose -f docker\docker-compose.base.yml -f docker\compose\%SCENARIO%.yml

REM Add options
if defined PULL (
    echo Pulling latest images...
    %BASE_CMD% pull
)

if defined BUILD (
    echo Building containers...
    %BASE_CMD% build
)

REM Start services
echo Starting services...
%BASE_CMD% up %DETACH% %BUILD%

if defined DETACH (
    echo.
    echo Services started in background!
    echo.
    echo Check status: docker compose ps
    echo View logs:    docker compose logs -f
    echo Stop:         docker compose down
    echo.
    
    REM Show access information based on scenario
    if "%SCENARIO%"=="full-stack" echo Access LibreChat: http://localhost:3080
    if "%SCENARIO%"=="development" (
        echo Access LibreChat: http://localhost:3080
        echo Splunk Web: http://localhost:8000 (admin/changeme)
    )
    if "%SCENARIO%"=="production" echo Access LibreChat: http://localhost:3080
    if "%SCENARIO%"=="mcp-only" echo MCP Endpoint: http://localhost:8443
    
    echo.
) else (
    echo.
    echo Services stopped.
)