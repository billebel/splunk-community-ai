#!/bin/bash
# Quick start script for Docker deployments
# Usage: ./docker/scripts/start.sh [scenario]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DOCKER_DIR="$PROJECT_ROOT/docker"

# Available scenarios
SCENARIOS=("full-stack" "mcp-only" "development" "production")

show_usage() {
    echo "Splunk Community AI - Docker Deployment"
    echo
    echo "Usage: $0 [scenario] [options]"
    echo
    echo "Scenarios:"
    echo "  full-stack   : MCP Server + LibreChat Web Interface (default)"
    echo "  mcp-only     : MCP Server only, no web interface"
    echo "  development  : Full stack + development Splunk instance"  
    echo "  production   : Production-optimized deployment"
    echo
    echo "Options:"
    echo "  --detach, -d : Run in background (detached mode)"
    echo "  --build      : Force rebuild containers"
    echo "  --pull       : Pull latest images before starting"
    echo "  --help, -h   : Show this help message"
    echo
    echo "Examples:"
    echo "  $0                           # Start full-stack in foreground"
    echo "  $0 mcp-only -d              # Start MCP-only in background"
    echo "  $0 production --build -d    # Rebuild and start production"
    echo
}

# Default values
SCENARIO="full-stack"
DETACH=""
BUILD=""
PULL=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        full-stack|mcp-only|development|production)
            SCENARIO="$1"
            shift
            ;;
        --detach|-d)
            DETACH="-d"
            shift
            ;;
        --build)
            BUILD="--build"
            shift
            ;;
        --pull)
            PULL="--pull"
            shift
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate scenario
if [[ ! " ${SCENARIOS[@]} " =~ " $SCENARIO " ]]; then
    echo "Error: Invalid scenario '$SCENARIO'"
    echo "Valid scenarios: ${SCENARIOS[*]}"
    exit 1
fi

# Check prerequisites
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not available"
    exit 1
fi

# Check for .env file
if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
    echo "Warning: .env file not found at $PROJECT_ROOT/.env"
    echo "Please create .env file with your configuration."
    echo "You can copy from .env.example or .env.auth-examples"
    echo
    read -p "Continue anyway? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Change to project root
cd "$PROJECT_ROOT"

echo "Starting Splunk Community AI - $SCENARIO deployment..."
echo

# Build command
CMD="docker compose -f docker/docker-compose.base.yml -f docker/compose/$SCENARIO.yml"

# Add options
if [[ -n "$PULL" ]]; then
    echo "Pulling latest images..."
    $CMD pull
fi

if [[ -n "$BUILD" ]]; then
    echo "Building containers..."
    $CMD build
fi

# Start services
echo "Starting services..."
$CMD up $DETACH $BUILD

if [[ -n "$DETACH" ]]; then
    echo
    echo "Services started in background!"
    echo
    echo "Check status: docker compose ps"
    echo "View logs:    docker compose logs -f"
    echo "Stop:         docker compose down"
    echo
    
    # Show access information based on scenario
    case $SCENARIO in
        full-stack|development|production)
            echo "Access LibreChat: http://localhost:3080"
            ;;
        mcp-only)
            echo "MCP Endpoint: http://localhost:8443"
            ;;
    esac
    
    if [[ "$SCENARIO" == "development" ]]; then
        echo "Splunk Web: http://localhost:8000 (admin/changeme)"
    fi
    
    echo
else
    echo
    echo "Services stopped."
fi