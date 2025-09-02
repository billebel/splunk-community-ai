#!/bin/bash
# Linux/Mac script to start development environment

set -e

echo "Starting Synapse MCP Development Environment..."
echo

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker is not running. Please start Docker."
    exit 1
fi

echo "This will start:"
echo "- Splunk Enterprise (Web UI: http://localhost:8000)"
echo "- Synapse MCP Server (API: http://localhost:8443)"
echo
echo "Login credentials: Check your .env file or use defaults"
echo

read -p "Continue? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo
echo "Starting development environment..."
docker-compose -f docker-compose.dev.yml up -d

echo
echo "========================================"
echo "Development Environment Started!"
echo "========================================"
echo
echo "Splunk Web UI: http://localhost:8000"
echo "Splunk API:    https://localhost:8089"
echo "MCP Server:    http://localhost:8443"
echo
echo "Login: Check your .env file or use environment defaults"
echo
echo "Useful commands:"
echo "  make dev-logs    # View logs"
echo "  make test        # Test MCP endpoints"
echo "  make dev-down    # Stop services"
echo