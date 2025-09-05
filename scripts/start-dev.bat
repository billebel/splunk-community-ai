@echo off
REM Windows batch script to start development environment

echo Starting Splunk AI Integration Development Environment...
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running. Please start Docker Desktop.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo WARNING: .env file not found. Creating from .env.example...
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo Please edit .env file with your Splunk credentials before continuing.
        pause
    ) else (
        echo ERROR: .env.example not found. Please create .env file manually.
        pause
        exit /b 1
    )
)

echo This will start:
echo - Splunk Enterprise (Web UI: http://localhost:8000, admin/changeme)
echo - Catalyst MCP Server (API: http://localhost:8443)
echo.
echo Login credentials: Check your .env file
echo.

set /p confirm="Continue? (y/N): "
if /i not "%confirm%"=="y" (
    echo Cancelled.
    exit /b 0
)

echo.
echo Starting development environment...
docker-compose -f docker-compose.splunk.yml up -d

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start development environment.
    pause
    exit /b 1
)

echo.
echo Waiting for services to start...
timeout /t 10 /nobreak >nul

echo.
echo ========================================
echo Development Environment Started!
echo ========================================
echo.
echo Splunk Web UI: http://localhost:8000 (admin/changeme)
echo Splunk API:    https://localhost:8089
echo MCP Server:    http://localhost:8443
echo.
echo Next steps:
echo   1. Wait 2-3 minutes for Splunk to fully start
echo   2. Test MCP server: scripts\test-mcp.bat
echo   3. View logs: docker-compose -f docker-compose.splunk.yml logs
echo   4. Stop services: scripts\stop-dev.bat
echo.

pause