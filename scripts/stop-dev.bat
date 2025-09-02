@echo off
REM Windows batch script to stop development environment

echo Stopping Synapse MCP Development Environment...
echo.

docker-compose -f docker-compose.dev.yml down

if errorlevel 1 (
    echo.
    echo ERROR: Failed to stop development environment.
    pause
    exit /b 1
)

echo.
echo Development environment stopped.
echo.

pause