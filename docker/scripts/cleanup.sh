#!/bin/bash
# Docker cleanup script for Splunk Community AI
# Removes containers, volumes, and images

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

show_usage() {
    echo "Docker cleanup script for Splunk Community AI"
    echo
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  --containers : Stop and remove containers only"
    echo "  --volumes    : Remove volumes (WARNING: Data loss!)"
    echo "  --images     : Remove built images"
    echo "  --all        : Remove everything (containers, volumes, images)"
    echo "  --force      : Skip confirmation prompts"
    echo "  --help, -h   : Show this help message"
    echo
    echo "Examples:"
    echo "  $0 --containers              # Remove containers only"
    echo "  $0 --all --force             # Remove everything without confirmation"
    echo "  $0 --volumes                 # Remove volumes (with confirmation)"
    echo
}

# Default values
CONTAINERS=false
VOLUMES=false
IMAGES=false
FORCE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --containers)
            CONTAINERS=true
            shift
            ;;
        --volumes)
            VOLUMES=true
            shift
            ;;
        --images)
            IMAGES=true
            shift
            ;;
        --all)
            CONTAINERS=true
            VOLUMES=true
            IMAGES=true
            shift
            ;;
        --force)
            FORCE=true
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

# If no specific cleanup selected, default to containers only
if [[ "$CONTAINERS" == false && "$VOLUMES" == false && "$IMAGES" == false ]]; then
    CONTAINERS=true
fi

# Change to project root
cd "$PROJECT_ROOT"

echo "Docker cleanup for Splunk Community AI"
echo "======================================="

# Stop and remove containers
if [[ "$CONTAINERS" == true ]]; then
    echo
    echo "Stopping and removing containers..."
    
    # Try to stop all scenarios
    for scenario in full-stack mcp-only development production; do
        if docker compose -f docker/docker-compose.base.yml -f docker/compose/$scenario.yml ps -q > /dev/null 2>&1; then
            echo "  Stopping $scenario deployment..."
            docker compose -f docker/docker-compose.base.yml -f docker/compose/$scenario.yml down --remove-orphans
        fi
    done
    
    # Remove any remaining catalyst containers
    echo "  Removing any remaining catalyst containers..."
    docker ps -a --filter="name=catalyst" --filter="name=librechat" --filter="name=splunk-dev" -q | xargs -r docker rm -f
    
    echo "✓ Containers removed"
fi

# Remove volumes
if [[ "$VOLUMES" == true ]]; then
    echo
    if [[ "$FORCE" == false ]]; then
        echo "WARNING: This will remove all persistent data!"
        echo "This includes:"
        echo "  - LibreChat conversation history"
        echo "  - MongoDB data"
        echo "  - Meilisearch indexes"
        echo "  - Splunk configuration and data (if using dev Splunk)"
        echo
        read -p "Are you sure you want to continue? (y/N): " confirm
        if [[ ! $confirm =~ ^[Yy]$ ]]; then
            echo "Volume cleanup cancelled."
            exit 0
        fi
    fi
    
    echo "Removing volumes..."
    
    # Remove named volumes
    VOLUME_NAMES=(
        "catalyst-librechat-data"
        "catalyst-librechat-logs"
        "catalyst-mongodb-data"
        "catalyst-meilisearch-data"
        "catalyst-splunk-etc"
        "catalyst-splunk-var"
    )
    
    for volume in "${VOLUME_NAMES[@]}"; do
        if docker volume ls -q | grep -q "^$volume$"; then
            echo "  Removing volume: $volume"
            docker volume rm "$volume"
        fi
    done
    
    echo "✓ Volumes removed"
fi

# Remove images
if [[ "$IMAGES" == true ]]; then
    echo
    if [[ "$FORCE" == false ]]; then
        echo "This will remove built Docker images."
        echo "You'll need to rebuild them on next startup."
        echo
        read -p "Continue? (y/N): " confirm
        if [[ ! $confirm =~ ^[Yy]$ ]]; then
            echo "Image cleanup cancelled."
            exit 0
        fi
    fi
    
    echo "Removing images..."
    
    # Remove catalyst-specific images
    if docker images -q splunk-community-ai_catalyst-mcp > /dev/null 2>&1; then
        echo "  Removing MCP server image..."
        docker rmi splunk-community-ai_catalyst-mcp
    fi
    
    # Remove dangling images
    DANGLING=$(docker images -f "dangling=true" -q)
    if [[ -n "$DANGLING" ]]; then
        echo "  Removing dangling images..."
        docker rmi $DANGLING
    fi
    
    echo "✓ Images removed"
fi

# Clean up Docker system
echo
echo "Running Docker system cleanup..."
docker system prune -f

echo
echo "Cleanup complete!"
echo
echo "To start fresh:"
echo "  ./docker/scripts/start.sh [scenario]"