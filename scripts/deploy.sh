#!/bin/bash
# Unified deployment script for Splunk AI Integration Platform
# Helps users choose and deploy the right option for their needs

set -e

echo
echo "===================================================="
echo "   Splunk AI Integration Platform - Deployment"
echo "===================================================="
echo
echo "Choose your deployment option:"
echo
echo "[1] Full Web Experience (Recommended for new users)"
echo "    - Complete web chat interface (LibreChat)"
echo "    - MCP server for AI integration"
echo "    - MongoDB for chat history"
echo "    - Requires: AI API key (Anthropic/OpenAI/Google)"
echo "    - Access: http://localhost:3080"
echo
echo "[2] MCP Server Only (For existing AI tools)"
echo "    - Lightweight MCP server only"
echo "    - Integrate with Claude Desktop, custom apps"
echo "    - No web interface"
echo "    - Access: http://localhost:8443"
echo
echo "[3] Development Environment (Includes test Splunk)"
echo "    - Complete testing environment"
echo "    - Includes Splunk Enterprise instance"
echo "    - Best for evaluation and development"
echo "    - Access: Splunk http://localhost:8000 (admin/changeme)"
echo
echo "[Q] Quit"
echo

read -p "Enter your choice [1-3, Q]: " choice

case ${choice,,} in
    q)
        echo "Exiting..."
        exit 0
        ;;
    1)
        deploy_full
        ;;
    2)
        deploy_mcp_only
        ;;
    3)
        deploy_dev
        ;;
    *)
        echo "Invalid choice. Please enter 1, 2, 3, or Q."
        exit 1
        ;;
esac

function deploy_full() {
    echo
    echo "===================================================="
    echo "   Deploying Full Web Experience"
    echo "===================================================="
    echo
    
    # Check for .env file
    if [ ! -f ".env" ]; then
        echo "Creating .env from .env.example..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            echo "Please edit .env file with your AI API keys."
            read -p "Press Enter after editing .env, or Ctrl+C to exit..."
        else
            echo "ERROR: .env.example not found"
            exit 1
        fi
    fi
    
    # Check for AI API keys
    if ! grep -q "ANTHROPIC_API_KEY=.*[^[:space:]]" .env && \
       ! grep -q "OPENAI_API_KEY=.*[^[:space:]]" .env && \
       ! grep -q "GOOGLE_API_KEY=.*[^[:space:]]" .env; then
        echo "WARNING: No AI provider API keys found in .env"
        echo "Web chat interface requires at least one AI provider API key"
        read -p "Continue anyway? (y/N): " confirm
        if [[ ! $confirm =~ ^[Yy]$ ]]; then
            echo "Please add API keys to .env file and try again"
            exit 1
        fi
    fi
    
    echo "Starting full web experience..."
    docker-compose up -d
    
    echo
    echo "===================================================="
    echo "   Deployment Successful!"
    echo "===================================================="
    echo
    echo "Web Interface: http://localhost:3080"
    echo "MCP API:       http://localhost:8443"
    echo
    echo "Next steps:"
    echo "1. Wait 30-60 seconds for all services to start"
    echo "2. Visit http://localhost:3080 to access the chat interface"
    echo "3. Test MCP server: scripts/test-mcp.sh"
    echo
    echo "To stop: docker-compose down"
}

function deploy_mcp_only() {
    echo
    echo "===================================================="
    echo "   Deploying MCP Server Only"
    echo "===================================================="
    echo
    
    # Check .env file exists
    if [ ! -f ".env" ]; then
        echo "Creating .env from .env.example..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            echo "Please edit .env file with your Splunk credentials."
            read -p "Press Enter after editing .env, or Ctrl+C to exit..."
        else
            echo "ERROR: .env.example not found"
            exit 1
        fi
    fi
    
    echo "Starting MCP server..."
    docker-compose -f docker-compose.mcp-only.yml up -d
    
    echo
    echo "===================================================="
    echo "   Deployment Successful!"
    echo "===================================================="
    echo
    echo "MCP Server: http://localhost:8443"
    echo
    echo "Next steps:"
    echo "1. Configure your MCP client (Claude Desktop, etc.)"
    echo "2. Use MCP endpoint: http://localhost:8443/mcp"
    echo "3. Test server: scripts/test-mcp.sh"
    echo
    echo "To stop: docker-compose -f docker-compose.mcp-only.yml down"
}

function deploy_dev() {
    echo
    echo "===================================================="
    echo "   Deploying Development Environment"
    echo "===================================================="
    echo
    
    # Check .env file exists
    if [ ! -f ".env" ]; then
        echo "Creating .env from .env.example..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            echo "Using defaults for development environment..."
        else
            echo "ERROR: .env.example not found"
            exit 1
        fi
    fi
    
    echo "Starting development environment..."
    docker-compose -f docker-compose.splunk.yml up -d
    
    echo
    echo "Waiting for services to start..."
    sleep 10
    
    echo
    echo "===================================================="
    echo "   Deployment Successful!"
    echo "===================================================="
    echo
    echo "Splunk Web UI: http://localhost:8000 (admin/changeme)"
    echo "Splunk API:    https://localhost:8089"
    echo "MCP Server:    http://localhost:8443"
    echo
    echo "Next steps:"
    echo "1. Wait 2-3 minutes for Splunk to fully start"
    echo "2. Login to Splunk: http://localhost:8000 (admin/changeme)"
    echo "3. Test MCP server: scripts/test-mcp.sh"
    echo "4. Stop when done: scripts/stop-dev.sh"
    echo
    echo "To stop: docker-compose -f docker-compose.splunk.yml down"
}

echo
echo "For help: Check README.md or visit our documentation"
echo