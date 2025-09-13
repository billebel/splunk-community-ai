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
    docker compose up -d
    
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
    echo "Helper script: docker compose up -d"
    echo "To stop: docker compose down"
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
            configure_splunk_auth
        else
            echo "ERROR: .env.example not found"
            exit 1
        fi
    fi
    
    echo "Starting MCP server..."
    docker compose -f docker-compose.mcp-only.yml up -d
    
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
    echo "Helper script: docker compose -f docker-compose.mcp-only.yml up -d"
    echo "To stop: docker compose -f docker-compose.mcp-only.yml down"
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
    docker compose -f docker-compose.dev.yml up -d
    
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
    echo
    echo "Helper script: docker compose -f docker-compose.dev.yml up -d"
    echo "To stop: docker compose -f docker-compose.dev.yml down"
}

function configure_splunk_auth() {
    echo
    echo "===================================================="
    echo "   Splunk Authentication Configuration"
    echo "===================================================="
    echo
    echo "Choose your Splunk authentication method:"
    echo
    echo "[1] Basic Authentication (Username/Password)"
    echo "    - Traditional shared service account"
    echo "    - Good for: Development, testing, simple deployments"
    echo
    echo "[2] Token Authentication (Recommended)"  
    echo "    - Splunk authentication token"
    echo "    - More secure, easier to rotate"
    echo "    - Good for: Production, secure deployments"
    echo
    echo "[3] Passthrough Authentication (Enterprise)"
    echo "    - Each user uses their own credentials"
    echo "    - No shared service account needed"
    echo "    - Good for: Multi-user environments, enterprise SSO"
    echo
    
    while true; do
        read -p "Enter your choice [1-3]: " auth_choice
        case $auth_choice in
            1)
                configure_basic_auth
                break
                ;;
            2)
                configure_token_auth
                break
                ;;
            3)
                configure_passthrough_auth
                break
                ;;
            *)
                echo "Invalid choice. Please enter 1, 2, or 3."
                ;;
        esac
    done
}

function configure_basic_auth() {
    echo
    echo "Configuring Basic Authentication..."
    echo
    
    # Add/update auth method in .env
    if grep -q "SPLUNK_AUTH_METHOD=" .env; then
        sed -i 's/SPLUNK_AUTH_METHOD=.*/SPLUNK_AUTH_METHOD=basic/' .env
    else
        echo "SPLUNK_AUTH_METHOD=basic" >> .env
    fi
    
    # Prompt for credentials
    read -p "Enter Splunk username: " splunk_user
    read -s -p "Enter Splunk password: " splunk_password
    echo
    
    # Update .env file
    if grep -q "SPLUNK_USER=" .env; then
        sed -i "s/SPLUNK_USER=.*/SPLUNK_USER=$splunk_user/" .env
    else
        echo "SPLUNK_USER=$splunk_user" >> .env
    fi
    
    if grep -q "SPLUNK_PASSWORD=" .env; then
        sed -i "s/SPLUNK_PASSWORD=.*/SPLUNK_PASSWORD=$splunk_password/" .env
    else
        echo "SPLUNK_PASSWORD=$splunk_password" >> .env
    fi
    
    echo "✓ Basic authentication configured"
    
    # Copy appropriate pack template
    cp "templates/pack/pack.template.basic.yaml" "knowledge-packs/splunk_enterprise/pack.yaml"
    echo "✓ Pack configuration updated for basic auth"
    
    # Copy appropriate LibreChat template
    cp "templates/librechat/librechat.template.basic.yaml" "librechat.yaml"
    echo "✓ LibreChat configuration updated for basic auth"
}

function configure_token_auth() {
    echo
    echo "Configuring Token Authentication..."
    echo
    
    # Add/update auth method in .env
    if grep -q "SPLUNK_AUTH_METHOD=" .env; then
        sed -i 's/SPLUNK_AUTH_METHOD=.*/SPLUNK_AUTH_METHOD=token/' .env
    else
        echo "SPLUNK_AUTH_METHOD=token" >> .env
    fi
    
    echo "To create a Splunk token:"
    echo "1. Splunk Web: Settings > Tokens > New Token"
    echo "2. REST API: curl -k -u user:pass 'https://splunk:8089/services/authorization/tokens' -d name=catalyst-token"
    echo
    
    read -p "Enter Splunk authentication token: " splunk_token
    
    # Update .env file
    if grep -q "SPLUNK_TOKEN=" .env; then
        sed -i "s/SPLUNK_TOKEN=.*/SPLUNK_TOKEN=$splunk_token/" .env
    else
        echo "SPLUNK_TOKEN=$splunk_token" >> .env
    fi
    
    echo "✓ Token authentication configured"
    
    # Copy appropriate pack template
    cp "templates/pack/pack.template.token.yaml" "knowledge-packs/splunk_enterprise/pack.yaml"
    echo "✓ Pack configuration updated for token auth"
    
    # Copy appropriate LibreChat template
    cp "templates/librechat/librechat.template.token.yaml" "librechat.yaml"
    echo "✓ LibreChat configuration updated for token auth"
}

function configure_passthrough_auth() {
    echo
    echo "Configuring Passthrough Authentication..."
    echo
    
    # Add/update auth method in .env
    if grep -q "SPLUNK_AUTH_METHOD=" .env; then
        sed -i 's/SPLUNK_AUTH_METHOD=.*/SPLUNK_AUTH_METHOD=passthrough/' .env
    else
        echo "SPLUNK_AUTH_METHOD=passthrough" >> .env
    fi
    
    echo "✓ Passthrough authentication configured"
    
    # Copy appropriate pack template
    cp "templates/pack/pack.template.passthrough.yaml" "knowledge-packs/splunk_enterprise/pack.yaml"
    echo "✓ Pack configuration updated for passthrough auth"
    
    # Copy appropriate LibreChat template  
    cp "templates/librechat/librechat.template.passthrough.yaml" "librechat.yaml"
    echo "✓ LibreChat configuration updated for passthrough auth"
    echo
    echo "Note: Passthrough auth requires MCP client to provide user credentials."
    echo "This is ideal for multi-user environments where each user has their own Splunk account."
    echo "No additional environment variables needed."
}

echo
echo "For help: Check README.md or visit our documentation"
echo