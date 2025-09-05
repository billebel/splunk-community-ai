@echo off
REM Unified deployment script for Splunk AI Integration Platform
REM Helps users choose and deploy the right option for their needs

setlocal enabledelayedexpansion

echo.
echo ====================================================
echo   Splunk AI Integration Platform - Deployment
echo ====================================================
echo.
echo Choose your deployment option:
echo.
echo [1] Full Web Experience (Recommended for new users)
echo     - Complete web chat interface (LibreChat)
echo     - MCP server for AI integration
echo     - MongoDB for chat history
echo     - Requires: AI API key (Anthropic/OpenAI/Google)
echo     - Access: http://localhost:3080
echo.
echo [2] MCP Server Only (For existing AI tools)
echo     - Lightweight MCP server only
echo     - Integrate with Claude Desktop, custom apps
echo     - No web interface
echo     - Access: http://localhost:8443
echo.
echo [3] Development Environment (Includes test Splunk)
echo     - Complete testing environment
echo     - Includes Splunk Enterprise instance
echo     - Best for evaluation and development
echo     - Access: Splunk http://localhost:8000 (admin/changeme)
echo.
echo [Q] Quit
echo.

set /p choice="Enter your choice [1-3, Q]: "

if /i "%choice%"=="q" (
    echo Exiting...
    exit /b 0
)

if "%choice%"=="1" (
    goto :deploy_full
) else if "%choice%"=="2" (
    goto :deploy_mcp_only
) else if "%choice%"=="3" (
    goto :deploy_dev
) else (
    echo Invalid choice. Please enter 1, 2, 3, or Q.
    pause
    goto :end
)

:deploy_full
echo.
echo ====================================================
echo   Deploying Full Web Experience
echo ====================================================
echo.
call scripts\build-chat.bat
if errorlevel 1 (
    echo Deployment preparation failed.
    pause
    exit /b 1
)
echo Starting full web experience...
docker-compose up -d
if errorlevel 1 (
    echo Deployment failed. Check Docker logs for details.
    pause
    exit /b 1
)
echo.
echo ====================================================
echo   Deployment Successful!
echo ====================================================
echo.
echo Web Interface: http://localhost:3080
echo MCP API:       http://localhost:8443
echo.
echo Next steps:
echo 1. Wait 30-60 seconds for all services to start
echo 2. Visit http://localhost:3080 to access the chat interface
echo 3. Test MCP server: scripts\test-mcp.bat
echo.
goto :end

:deploy_mcp_only
echo.
echo ====================================================
echo   Deploying MCP Server Only
echo ====================================================
echo.
REM Check .env file exists
if not exist ".env" (
    echo Creating .env from .env.example...
    copy ".env.example" ".env" >nul
    echo Please edit .env file with your Splunk credentials.
    pause
)
echo Starting MCP server...
docker-compose -f docker-compose.mcp-only.yml up -d
if errorlevel 1 (
    echo Deployment failed. Check Docker logs for details.
    pause
    exit /b 1
)
echo.
echo ====================================================
echo   Deployment Successful!
echo ====================================================
echo.
echo MCP Server: http://localhost:8443
echo.
echo Next steps:
echo 1. Configure your MCP client (Claude Desktop, etc.)
echo 2. Use MCP endpoint: http://localhost:8443/mcp
echo 3. Test server: scripts\test-mcp.bat
echo.
goto :end

:deploy_dev
echo.
echo ====================================================
echo   Deploying Development Environment
echo ====================================================
echo.
REM Check .env file exists
if not exist ".env" (
    echo Creating .env from .env.example...
    copy ".env.example" ".env" >nul
    echo Please edit .env file if you want custom settings.
    echo Using defaults for development environment...
    pause
)
echo Starting development environment...
docker-compose -f docker-compose.splunk.yml up -d
if errorlevel 1 (
    echo Deployment failed. Check Docker logs for details.
    pause
    exit /b 1
)
echo.
echo ====================================================
echo   Deployment Successful!
echo ====================================================
echo.
echo Splunk Web UI: http://localhost:8000 (admin/changeme)
echo Splunk API:    https://localhost:8089
echo MCP Server:    http://localhost:8443
echo.
echo Next steps:
echo 1. Wait 2-3 minutes for Splunk to fully start
echo 2. Login to Splunk: http://localhost:8000 (admin/changeme)
echo 3. Test MCP server: scripts\test-mcp.bat
echo 4. Stop when done: scripts\stop-dev.bat
echo.
goto :end

:end
echo To stop services:
if "%choice%"=="1" (
    echo   docker-compose down
) else if "%choice%"=="2" (
    echo   docker-compose -f docker-compose.mcp-only.yml down
) else if "%choice%"=="3" (
    echo   scripts\stop-dev.bat
)
echo.
echo For help: Check README.md or visit our documentation
echo.
pause