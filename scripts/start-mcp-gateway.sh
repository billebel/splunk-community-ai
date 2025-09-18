#!/bin/bash

# Quick start script for Catalyst MCP Gateway
# Starts the gateway and connects common AI clients

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

MCP_SERVER_NAME="splunk-catalyst"

echo -e "${BLUE}🚀 Starting Catalyst MCP Gateway${NC}"
echo "=================================="

# Check if MCP server is registered
if ! docker mcp server list | grep -q "$MCP_SERVER_NAME"; then
    echo -e "${RED}❌ MCP server '$MCP_SERVER_NAME' not found.${NC}"
    echo -e "${YELLOW}Run setup-mcp-gateway.sh first!${NC}"
    exit 1
fi

# Check if server is enabled
if ! docker mcp server list | grep "$MCP_SERVER_NAME" | grep -q "enabled"; then
    echo -e "${YELLOW}⚠️  Enabling MCP server...${NC}"
    docker mcp server enable "$MCP_SERVER_NAME"
fi

echo -e "${GREEN}✅ MCP server ready${NC}"

# Function to start gateway in background
start_gateway() {
    echo -e "${BLUE}🔄 Starting MCP Gateway...${NC}"

    # Check if gateway is already running
    if docker mcp gateway status >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Gateway already running. Stopping first...${NC}"
        docker mcp gateway stop >/dev/null 2>&1 || true
        sleep 2
    fi

    # Start gateway in background
    docker mcp gateway run &
    GATEWAY_PID=$!

    # Wait for gateway to be ready
    echo -e "${BLUE}⏳ Waiting for gateway to be ready...${NC}"
    for i in {1..30}; do
        if docker mcp gateway status >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Gateway is running${NC}"
            break
        fi
        sleep 1
        echo -n "."
    done

    if ! docker mcp gateway status >/dev/null 2>&1; then
        echo -e "${RED}❌ Gateway failed to start${NC}"
        exit 1
    fi
}

# Function to connect AI clients
connect_clients() {
    echo -e "${BLUE}🔗 Available AI client connections:${NC}"
    echo "1. Claude (Anthropic)"
    echo "2. VS Code"
    echo "3. Custom client"
    echo "4. Skip client connection"
    echo ""

    read -p "Select client to connect (1-4): " choice

    case $choice in
        1)
            echo -e "${BLUE}🔗 Connecting Claude...${NC}"
            docker mcp client connect claude
            echo -e "${GREEN}✅ Claude connected to MCP Gateway${NC}"
            ;;
        2)
            echo -e "${BLUE}🔗 Connecting VS Code...${NC}"
            docker mcp client connect vscode
            echo -e "${GREEN}✅ VS Code connected to MCP Gateway${NC}"
            ;;
        3)
            echo -e "${BLUE}📋 Custom client connection info:${NC}"
            echo "Gateway URL: http://localhost:8080"
            echo "Server: $MCP_SERVER_NAME"
            echo "Use this information to configure your MCP client"
            ;;
        4)
            echo -e "${YELLOW}⏭️  Skipping client connection${NC}"
            ;;
        *)
            echo -e "${YELLOW}⏭️  Invalid choice, skipping client connection${NC}"
            ;;
    esac
}

# Function to show gateway info
show_info() {
    echo ""
    echo -e "${GREEN}🎉 Catalyst MCP Gateway is running!${NC}"
    echo "===================================="
    echo ""
    echo -e "${BLUE}Gateway Status:${NC}"
    docker mcp gateway status || echo "Status check failed"
    echo ""
    echo -e "${BLUE}Available Servers:${NC}"
    docker mcp server list
    echo ""
    echo -e "${BLUE}Useful Commands:${NC}"
    echo -e "  View server logs:     ${YELLOW}docker mcp server logs $MCP_SERVER_NAME${NC}"
    echo -e "  Stop gateway:         ${YELLOW}docker mcp gateway stop${NC}"
    echo -e "  Gateway status:       ${YELLOW}docker mcp gateway status${NC}"
    echo -e "  Server management:    ${YELLOW}docker mcp server --help${NC}"
    echo ""
    echo -e "${BLUE}Knowledge Packs Available:${NC}"
    echo "- splunk_enterprise: Core Splunk Enterprise tools"
    echo "- splunk_cloud: Splunk Cloud Platform tools"
    echo "- splunk_oauth: OAuth authentication flow"
    echo "- splunk_saml: SAML/SSO authentication flow"
    echo ""
    echo -e "${BLUE}Development Mode:${NC}"
    echo -e "  For development with hot reload: ${YELLOW}docker-compose -f docker-compose.mcp-gateway.yml up${NC}"
}

# Main execution
start_gateway
connect_clients
show_info

# Keep script running to show logs
echo ""
echo -e "${BLUE}📋 Press Ctrl+C to stop the gateway${NC}"
echo -e "${BLUE}📋 Gateway logs will be shown below:${NC}"
echo "========================================="

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Stopping MCP Gateway...${NC}"
    docker mcp gateway stop >/dev/null 2>&1 || true
    echo -e "${GREEN}✅ Gateway stopped${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Show logs and wait
if [ -n "$GATEWAY_PID" ]; then
    wait $GATEWAY_PID
else
    # If we can't get the PID, just show logs
    docker mcp gateway logs --follow 2>/dev/null || sleep infinity
fi