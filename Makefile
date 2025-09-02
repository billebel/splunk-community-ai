# Catalyst MCP Server - FastMCP Implementation
.PHONY: help build up down logs dev-up dev-down dev-logs test clean status restart dev-restart

# Default environment
COMPOSE_FILE ?= docker-compose.yml
PROJECT_NAME ?= catalyst-mcp

# Colors for output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)Catalyst MCP Server - Universal Integration Platform$(NC)"
	@echo ""
	@echo "$(YELLOW)Production Commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -v dev | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Development Commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep dev | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Other Commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(test|clean|logs|status|restart)' | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Key Features:$(NC)"
	@echo "  • Universal Knowledge Packs (domain-agnostic tools)"
	@echo "  • Multi-adapter architecture (REST, DB, SSH, Files, Queues)"
	@echo "  • LibreChat integration with MCP protocol"
	@echo "  • Hot-reloadable knowledge packs"
	@echo "  • Multi-language transform engine"

build: ## Build the MCP server image
	@echo "$(GREEN)Building Catalyst MCP Server...$(NC)"
	docker compose build --no-cache

up: ## Start MCP server (production)
	@echo "$(GREEN)🚀 Starting Catalyst MCP Server (production)...$(NC)"
	docker compose up -d
	@echo "$(GREEN)MCP Server started!$(NC)"
	@echo "$(YELLOW)LibreChat: http://localhost:3080$(NC)"
	@echo "$(YELLOW)MCP Server: http://localhost:8443$(NC)"
	@echo "$(YELLOW)Health check: curl http://localhost:8443/health$(NC)"

down: ## Stop MCP server
	@echo "$(RED)Stopping Catalyst MCP Server...$(NC)"
	docker compose down

logs: ## Show MCP server logs
	docker compose logs -f catalyst-mcp

dev-up: ## Start development environment (with RAG API)
	@echo "$(GREEN)🚀 Starting Catalyst MCP Development Environment...$(NC)"
	@echo "$(YELLOW)Includes: MCP server, LibreChat, MongoDB, RAG API$(NC)"
	docker compose -f docker-compose.yml -f docker-compose.override.yml up -d
	@echo ""
	@echo "$(GREEN)Development environment started!$(NC)"
	@echo "$(YELLOW)LibreChat: http://localhost:3080$(NC)"
	@echo "$(YELLOW)MCP Server: http://localhost:8443$(NC)"
	@echo "$(YELLOW)RAG API: http://localhost:8001$(NC)"
	@echo "$(YELLOW)Configure SPLUNK_URL in .env to connect to your Splunk instance$(NC)"
	@echo ""
	@echo "$(GREEN)Useful commands:$(NC)"
	@echo "  make dev-logs    # Follow all service logs"
	@echo "  make test        # Test MCP endpoints"
	@echo "  make dev-down    # Stop all services"

dev-down: ## Stop development environment
	@echo "$(RED)Stopping Development Environment...$(NC)"
	docker compose -f docker-compose.yml -f docker-compose.override.yml down

dev-logs: ## Show development environment logs
	docker compose -f docker-compose.yml -f docker-compose.override.yml logs -f


test: ## Test FastMCP server endpoints
	@echo "$(GREEN)Testing FastMCP Server Endpoints...$(NC)"
	@echo ""
	@echo "$(YELLOW)1. Health Check:$(NC)"
	@curl -s http://localhost:8443/health | python -m json.tool || echo "$(RED)Health check failed - is server running?$(NC)"
	@echo ""
	@echo "$(YELLOW)2. Tool Count (should show 23+ tools):$(NC)"
	@curl -s -X POST http://localhost:8443/mcp \
		-H "Content-Type: application/json" \
		-d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}' \
		| python -c "import json, sys; data=json.load(sys.stdin); tools=data.get('result', {}).get('tools', []); print(f'Tools available: {len(tools)}'); [print(f'  - {tool[\"name\"]}: {tool[\"description\"][:60]}...') for tool in tools[:5]]" 2>/dev/null || echo "$(RED)Tools list failed$(NC)"
	@echo ""
	@echo "$(YELLOW)3. Test Core Tool (current_user):$(NC)"
	@curl -s -X POST http://localhost:8443/mcp \
		-H "Content-Type: application/json" \
		-d '{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "current_user", "arguments": {}}}' \
		| python -c "import json, sys; data=json.load(sys.stdin); result=data.get('result', {}); print('✅ Current user tool working') if not result.get('isError') else print('❌ Current user tool failed')" 2>/dev/null || echo "$(RED)Current user test failed$(NC)"
	@echo ""
	@echo "$(YELLOW)4. Test Search Tool (quick search):$(NC)"
	@curl -s -X POST http://localhost:8443/mcp \
		-H "Content-Type: application/json" \
		-d '{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "search_splunk", "arguments": {"search_query": "| stats count", "max_results": 1}}}' \
		| python -c "import json, sys; data=json.load(sys.stdin); result=data.get('result', {}); print('✅ Search tool working') if not result.get('isError') else print('❌ Search tool failed')" 2>/dev/null || echo "$(RED)Search test failed$(NC)"
	@echo ""
	@echo "$(GREEN)FastMCP Testing Complete!$(NC)"

clean: ## Clean up Docker resources
	@echo "$(RED)Cleaning up Docker resources...$(NC)"
	docker compose down --remove-orphans --volumes
	docker compose -f docker-compose.yml -f docker-compose.override.yml down --remove-orphans --volumes
	docker system prune -f
	@echo "$(GREEN)Cleanup complete!$(NC)"

status: ## Show service status
	@echo "$(GREEN)Service Status:$(NC)"
	@docker compose ps 2>/dev/null || echo "$(YELLOW)No services running$(NC)"

restart: ## Restart MCP server
	@echo "$(YELLOW)Restarting Catalyst MCP Server...$(NC)"
	docker compose restart catalyst-mcp

dev-restart: ## Restart development environment
	@echo "$(YELLOW)Restarting Development Environment...$(NC)"
	docker compose -f docker-compose.yml -f docker-compose.override.yml restart