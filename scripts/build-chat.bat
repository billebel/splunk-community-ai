@echo off
REM Build script for Splunk Chat Assistant
REM Generates LibreChat configuration from our domain-specific chat.yml

echo.
echo Building Splunk Chat Assistant...
echo.

REM Check if chat.yml exists
if not exist "chat.yml" (
    echo Error: chat.yml not found
    echo    Please create chat.yml configuration file
    exit /b 1
)

REM Generate LibreChat configuration
echo Generating LibreChat configuration...
python scripts\generate-librechat-config.py

if %ERRORLEVEL% neq 0 (
    echo Configuration generation failed
    exit /b 1
)

echo.
echo Build complete!
echo.
echo To start Splunk Chat Assistant:
echo    1. Set GOOGLE_API_KEY in .env file
echo    2. Run: docker-compose -f docker-compose.dev.yml -f docker-compose.chat.yml up -d
echo    3. Visit: http://localhost:3080
echo.