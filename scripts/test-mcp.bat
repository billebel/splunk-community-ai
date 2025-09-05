@echo off
REM Windows batch script to test MCP endpoints

echo Testing Catalyst MCP Server Endpoints...
echo.

echo 1. Health Check:
curl -s http://localhost:8443/health || echo Failed to connect to health endpoint
echo.
echo.

echo 2. MCP Server Info:
curl -s http://localhost:8443/ || echo Failed to connect to MCP server
echo.
echo.

echo 3. Tools List:
curl -s -X POST http://localhost:8443/mcp -H "Content-Type: application/json" -d "{\"jsonrpc\": \"2.0\", \"id\": 1, \"method\": \"tools/list\", \"params\": {}}" || echo Failed to get tools list
echo.
echo.

echo 4. List Indexes Test:
curl -s -X POST http://localhost:8443/mcp -H "Content-Type: application/json" -d "{\"jsonrpc\": \"2.0\", \"id\": 2, \"method\": \"tools/call\", \"params\": {\"name\": \"list_indexes\", \"arguments\": {}}}" || echo Failed to call list_indexes tool
echo.
echo.

echo 5. Get Server Info Test:
curl -s -X POST http://localhost:8443/mcp -H "Content-Type: application/json" -d "{\"jsonrpc\": \"2.0\", \"id\": 3, \"method\": \"tools/call\", \"params\": {\"name\": \"get_server_info\", \"arguments\": {}}}" || echo Failed to call get_server_info tool
echo.
echo.

echo Testing complete!
echo.
echo If you see connection errors, ensure the MCP server is running:
echo   docker-compose -f docker-compose.splunk.yml ps
echo.

pause