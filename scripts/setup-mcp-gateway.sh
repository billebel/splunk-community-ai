#!/bin/bash

# Catalyst MCP Gateway Setup Script
# Sets up Docker MCP Gateway with Splunk Community AI integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MCP_SERVER_NAME="splunk-catalyst"
DOCKER_IMAGE_NAME="splunk-community-ai/catalyst-mcp"

echo -e "${BLUE}🚀 Setting up Catalyst MCP Gateway for Splunk Community AI${NC}"
echo "=================================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${BLUE}📋 Checking prerequisites...${NC}"

if ! command_exists docker; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker Desktop.${NC}"
    exit 1
fi

if ! command_exists docker-compose; then
    echo -e "${RED}❌ Docker Compose is not installed.${NC}"
    exit 1
fi

# Check if Docker MCP plugin is available
if ! docker mcp --help >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Docker MCP plugin not found. Installing...${NC}"
    echo "Please follow these steps:"
    echo "1. Enable Docker Desktop MCP Toolkit feature"
    echo "2. Download MCP Gateway CLI from GitHub releases"
    echo "3. Place binary in ~/.docker/cli-plugins/"
    echo ""
    echo "For more info: https://docs.docker.com/ai/mcp-gateway/"
    read -p "Press Enter when MCP plugin is installed..."
fi

echo -e "${GREEN}✅ Prerequisites check completed${NC}"

# Build the MCP server image
echo -e "${BLUE}🏗️  Building Catalyst MCP server image...${NC}"
cd "$PROJECT_ROOT"

docker build -f docker/Dockerfile.mcp-gateway -t "$DOCKER_IMAGE_NAME:latest" .

echo -e "${GREEN}✅ Docker image built successfully${NC}"

# Check if server already exists and remove it
if docker mcp server list | grep -q "$MCP_SERVER_NAME"; then
    echo -e "${YELLOW}⚠️  Existing MCP server found. Removing...${NC}"
    docker mcp server remove "$MCP_SERVER_NAME" || true
fi

# Register the MCP server with Docker Gateway
echo -e "${BLUE}📝 Registering MCP server with Docker Gateway...${NC}"

docker mcp server add "$MCP_SERVER_NAME" \
    --image "$DOCKER_IMAGE_NAME:latest" \
    --name "Splunk Catalyst MCP Server" \
    --description "Catalyst MCP server for Splunk integration with knowledge packs" \
    --local true

echo -e "${GREEN}✅ MCP server registered successfully${NC}"

# Set up environment variables
echo -e "${BLUE}⚙️  Setting up environment configuration...${NC}"

if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
    echo -e "${YELLOW}📝 Please edit .env file with your Splunk configuration${NC}"
fi

# Enable the server
echo -e "${BLUE}🔄 Enabling MCP server...${NC}"
docker mcp server enable "$MCP_SERVER_NAME"

echo -e "${GREEN}✅ MCP server enabled${NC}"

# Setup completion
echo ""
echo -e "${GREEN}🎉 Catalyst MCP Gateway setup completed!${NC}"
echo "=================================================="
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Edit .env file with your Splunk configuration:"
echo "   - SPLUNK_HOST=your-splunk-host"
echo "   - SPLUNK_TOKEN=your-splunk-token"
echo ""
echo "2. Start the MCP Gateway:"
echo -e "   ${YELLOW}docker mcp gateway run${NC}"
echo ""
echo "3. Connect your AI client (Claude, VS Code, etc.):"
echo -e "   ${YELLOW}docker mcp client connect claude${NC}"
echo ""
echo "4. Alternative: Use Docker Compose for development:"
echo -e "   ${YELLOW}docker-compose -f docker-compose.mcp-gateway.yml up${NC}"
echo ""
echo -e "${BLUE}Available MCP tools:${NC}"
echo "- splunk_search: Execute Splunk searches"
echo "- splunk_analysis: Analyze Splunk data"
echo "- knowledge_packs: Dynamic pack loading"
echo "- oauth_authentication: OAuth/SAML flows"
echo ""
echo -e "${BLUE}For troubleshooting:${NC}"
echo -e "   ${YELLOW}docker mcp server logs $MCP_SERVER_NAME${NC}"
echo -e "   ${YELLOW}docker mcp gateway status${NC}"