@echo off
REM Windows batch script to start development environment

echo Starting FastMCP Synapse MCP Development Environment...
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running. Please start Docker Desktop.
    pause
    exit /b 1
)

echo This will start:
echo - Splunk Enterprise (Web UI: http://localhost:8000)
echo - FastMCP Synapse MCP Server (API: http://localhost:8443)
echo.
echo Login credentials: Check your .env file or use defaults
echo.

set /p confirm="Continue? (y/N): "
if /i not "%confirm%"=="y" (
    echo Cancelled.
    exit /b 0
)

echo.
echo Starting development environment...
docker-compose -f docker-compose.dev.yml up -d

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start development environment.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Development Environment Started!
echo ========================================
echo.
echo Splunk Web UI: http://localhost:8000
echo Splunk API:    https://localhost:8089
echo MCP Server:    http://localhost:8443
echo.
echo Login: Check your .env file or use environment defaults
echo.
echo Useful commands:
echo   scripts\stop-dev.bat     - Stop services
echo   scripts\logs-dev.bat     - View logs
echo   scripts\test-mcp.bat     - Test MCP endpoints
echo.

pause