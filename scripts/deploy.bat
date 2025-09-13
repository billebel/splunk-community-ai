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
    call :configure_splunk_auth
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
goto :end

:configure_splunk_auth
echo.
echo ====================================================
echo   Splunk Authentication Configuration
echo ====================================================
echo.
echo Choose your Splunk authentication method:
echo.
echo [1] Basic Authentication (Username/Password)
echo     - Traditional shared service account
echo     - Good for: Development, testing, simple deployments
echo.
echo [2] Token Authentication (Recommended)
echo     - Splunk authentication token
echo     - More secure, easier to rotate
echo     - Good for: Production, secure deployments
echo.
echo [3] Passthrough Authentication (Enterprise)
echo     - Each user uses their own credentials
echo     - No shared service account needed
echo     - Good for: Multi-user environments, enterprise SSO
echo.

:auth_choice_loop
set /p auth_choice="Enter your choice [1-3]: "

if "%auth_choice%"=="1" (
    call :configure_basic_auth
    goto :auth_done
) else if "%auth_choice%"=="2" (
    call :configure_token_auth
    goto :auth_done
) else if "%auth_choice%"=="3" (
    call :configure_passthrough_auth
    goto :auth_done
) else (
    echo Invalid choice. Please enter 1, 2, or 3.
    goto :auth_choice_loop
)

:configure_basic_auth
echo.
echo Configuring Basic Authentication...
echo.

REM Add/update auth method in .env
findstr /c:"SPLUNK_AUTH_METHOD=" .env >nul
if errorlevel 1 (
    echo SPLUNK_AUTH_METHOD=basic >> .env
) else (
    powershell -Command "(Get-Content .env) -replace '^SPLUNK_AUTH_METHOD=.*', 'SPLUNK_AUTH_METHOD=basic' | Set-Content .env"
)

REM Prompt for credentials
set /p splunk_user="Enter Splunk username: "
set /p splunk_password="Enter Splunk password: "

REM Update .env file
findstr /c:"SPLUNK_USER=" .env >nul
if errorlevel 1 (
    echo SPLUNK_USER=%splunk_user% >> .env
) else (
    powershell -Command "(Get-Content .env) -replace '^SPLUNK_USER=.*', 'SPLUNK_USER=%splunk_user%' | Set-Content .env"
)

findstr /c:"SPLUNK_PASSWORD=" .env >nul
if errorlevel 1 (
    echo SPLUNK_PASSWORD=%splunk_password% >> .env
) else (
    powershell -Command "(Get-Content .env) -replace '^SPLUNK_PASSWORD=.*', 'SPLUNK_PASSWORD=%splunk_password%' | Set-Content .env"
)

echo ✓ Basic authentication configured

REM Copy appropriate pack template
copy "templates\pack\pack.template.basic.yaml" "knowledge-packs\splunk_enterprise\pack.yaml" >nul
echo ✓ Pack configuration updated for basic auth

REM Copy appropriate LibreChat template
copy "templates\librechat\librechat.template.basic.yaml" "librechat.yaml" >nul
echo ✓ LibreChat configuration updated for basic auth
goto :eof

:configure_token_auth
echo.
echo Configuring Token Authentication...
echo.

REM Add/update auth method in .env
findstr /c:"SPLUNK_AUTH_METHOD=" .env >nul
if errorlevel 1 (
    echo SPLUNK_AUTH_METHOD=token >> .env
) else (
    powershell -Command "(Get-Content .env) -replace '^SPLUNK_AUTH_METHOD=.*', 'SPLUNK_AUTH_METHOD=token' | Set-Content .env"
)

echo To create a Splunk token:
echo 1. Splunk Web: Settings ^> Tokens ^> New Token
echo 2. REST API: curl -k -u user:pass "https://splunk:8089/services/authorization/tokens" -d name=catalyst-token
echo.

set /p splunk_token="Enter Splunk authentication token: "

REM Update .env file
findstr /c:"SPLUNK_TOKEN=" .env >nul
if errorlevel 1 (
    echo SPLUNK_TOKEN=%splunk_token% >> .env
) else (
    powershell -Command "(Get-Content .env) -replace '^SPLUNK_TOKEN=.*', 'SPLUNK_TOKEN=%splunk_token%' | Set-Content .env"
)

echo ✓ Token authentication configured

REM Copy appropriate pack template
copy "templates\pack\pack.template.token.yaml" "knowledge-packs\splunk_enterprise\pack.yaml" >nul
echo ✓ Pack configuration updated for token auth

REM Copy appropriate LibreChat template
copy "templates\librechat\librechat.template.token.yaml" "librechat.yaml" >nul
echo ✓ LibreChat configuration updated for token auth
goto :eof

:configure_passthrough_auth
echo.
echo Configuring Passthrough Authentication...
echo.

REM Add/update auth method in .env
findstr /c:"SPLUNK_AUTH_METHOD=" .env >nul
if errorlevel 1 (
    echo SPLUNK_AUTH_METHOD=passthrough >> .env
) else (
    powershell -Command "(Get-Content .env) -replace '^SPLUNK_AUTH_METHOD=.*', 'SPLUNK_AUTH_METHOD=passthrough' | Set-Content .env"
)

echo ✓ Passthrough authentication configured

REM Copy appropriate pack template
copy "templates\pack\pack.template.passthrough.yaml" "knowledge-packs\splunk_enterprise\pack.yaml" >nul
echo ✓ Pack configuration updated for passthrough auth

REM Copy appropriate LibreChat template
copy "templates\librechat\librechat.template.passthrough.yaml" "librechat.yaml" >nul
echo ✓ LibreChat configuration updated for passthrough auth
echo.
echo Note: Passthrough auth requires MCP client to provide user credentials.
echo This is ideal for multi-user environments where each user has their own Splunk account.
echo No additional environment variables needed.
goto :eof

:auth_done
goto :eof

:end
echo.
echo For help: Check README.md or visit our documentation
echo.
pause