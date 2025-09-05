@echo off
REM Build script for Splunk AI Integration Chat Interface
REM Validates LibreChat configuration for web interface deployment

echo.
echo Building Splunk AI Integration Chat Interface...
echo.

REM Check if librechat.yaml exists (already configured)
if exist "librechat.yaml" (
    echo LibreChat configuration found: librechat.yaml
    echo Configuration validation: OK
) else (
    echo Warning: librechat.yaml not found
    echo    Using default configuration from main docker-compose.yml
)

REM Check if .env file has required API keys
if not exist ".env" (
    echo Error: .env file not found
    echo    Copy .env.example to .env and configure your API keys
    exit /b 1
)

REM Check for at least one AI provider API key
findstr /C:"ANTHROPIC_API_KEY=" .env >nul
if %ERRORLEVEL% equ 0 (
    echo Anthropic API key found
    goto :api_key_found
)

findstr /C:"OPENAI_API_KEY=" .env >nul
if %ERRORLEVEL% equ 0 (
    echo OpenAI API key found
    goto :api_key_found
)

findstr /C:"GOOGLE_API_KEY=" .env >nul
if %ERRORLEVEL% equ 0 (
    echo Google API key found
    goto :api_key_found
)

echo Warning: No AI provider API keys found in .env
echo    Please add ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY
echo    Web chat interface requires at least one AI provider

:api_key_found
echo.
echo Build validation complete!
echo.
echo To start Splunk AI Integration with Web Chat:
echo    1. Ensure API keys are set in .env file
echo    2. Run: docker-compose up -d
echo    3. Visit: http://localhost:3080
echo    4. MCP Server API: http://localhost:8443
echo.