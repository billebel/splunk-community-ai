@echo off
REM Windows batch script to test MCP endpoints

echo Testing FastMCP Synapse MCP Server Endpoints...
echo.

echo 1. Health Check:
curl -s http://localhost:8443/health
echo.
echo.

echo 2. MCP Info:
curl -s http://localhost:8443/mcp
echo.
echo.

echo 3. Tools List:
curl -s -X POST http://localhost:8443/mcp -H "Content-Type: application/json" -d "{\"jsonrpc\": \"2.0\", \"id\": 1, \"method\": \"tools/list\", \"params\": {}}"
echo.
echo.

echo 4. Current User Test:
curl -s -X POST http://localhost:8443/mcp -H "Content-Type: application/json" -d "{\"jsonrpc\": \"2.0\", \"id\": 2, \"method\": \"tools/call\", \"params\": {\"name\": \"current_user\", \"arguments\": {}}}"
echo.
echo.

echo Testing complete!
echo.

pause