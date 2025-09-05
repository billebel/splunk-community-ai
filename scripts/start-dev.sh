#!/bin/bash
# Linux/Mac script to start development environment with Splunk

set -e

echo "Starting Splunk AI Integration Development Environment..."
echo

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker is not running. Please start Docker."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Please edit .env file with your Splunk credentials before continuing."
        read -p "Press Enter after editing .env, or Ctrl+C to exit..."
    else
        echo "ERROR: .env.example not found. Please create .env file manually."
        exit 1
    fi
fi

echo "This will start:"
echo "- Splunk Enterprise (Web UI: http://localhost:8000, admin/changeme)"
echo "- Catalyst MCP Server (API: http://localhost:8443)"
echo
echo "Login credentials: Check your .env file"
echo

read -p "Continue? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo
echo "Starting development environment..."
docker-compose -f docker-compose.splunk.yml up -d

echo
echo "Waiting for services to start..."
sleep 10

echo
echo "========================================"
echo "Development Environment Started!"
echo "========================================"
echo
echo "Splunk Web UI: http://localhost:8000 (admin/changeme)"
echo "Splunk API:    https://localhost:8089"
echo "MCP Server:    http://localhost:8443"
echo
echo "Next steps:"
echo "1. Wait 2-3 minutes for Splunk to fully start"
echo "2. Test MCP server: scripts/test-mcp.sh"
echo "3. View logs: docker-compose -f docker-compose.splunk.yml logs"
echo "4. Stop: docker-compose -f docker-compose.splunk.yml down"
echo