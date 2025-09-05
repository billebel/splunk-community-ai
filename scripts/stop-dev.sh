#!/bin/bash
# Linux/Mac script to stop development environment

echo "Stopping Splunk AI Integration Development Environment..."
echo

docker-compose -f docker-compose.splunk.yml down

if [ $? -eq 0 ]; then
    echo
    echo "Development environment stopped successfully."
    echo
    echo "To start again: scripts/start-dev.sh"
else
    echo
    echo "WARNING: Some services may not have stopped cleanly."
    echo "Try: docker-compose -f docker-compose.splunk.yml down --remove-orphans"
fi

echo