@echo off
REM Windows batch script to stop development environment

echo Stopping Splunk AI Integration Development Environment...
echo.

docker-compose -f docker-compose.splunk.yml down

if errorlevel 1 (
    echo.
    echo WARNING: Some services may not have stopped cleanly.
    echo Try: docker-compose -f docker-compose.splunk.yml down --remove-orphans
    echo.
) else (
    echo.
    echo Development environment stopped successfully.
    echo.
    echo To start again: scripts\start-dev.bat
    echo.
)

pause