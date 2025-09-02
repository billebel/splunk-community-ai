# MCP Server Documentation

## Overview

The Catalyst MCP Server is a universal Model Context Protocol (MCP) server built on FastMCP that provides domain-specific tools through configurable Universal Knowledge Packs.

## Architecture

### Core Components

- **FastMCP Server**: HTTP server implementing MCP protocol over stdio
- **Universal Knowledge Pack System**: YAML-based tool definitions
- **Multi-language Transform Engine**: Python, JavaScript, jq, and Jinja2 support
- **Dynamic Tool Loading**: Tools loaded from packs at runtime
- **Hot Reloading**: Pack updates without server restart

### Key Modules

```
catalyst_mcp/
├── main.py              # Universal MCP server entry point
├── packs/               # Knowledge Pack System
│   ├── registry.py      # Pack discovery and management
│   ├── loader.py        # Legacy pack loading
│   ├── modular_loader.py # Enhanced modular pack loader
│   ├── factory.py       # Dynamic tool creation
│   ├── transforms.py    # Multi-language transform engine
│   └── models.py        # Universal data models
├── guardrails/          # Security and performance engine
└── audit/               # Audit logging with HEC integration
```

## Configuration

### Environment Variables

Essential variables in `.env`:

```bash
# MCP Server
MCP_PORT=8443

# Splunk Connection (for splunk_basic pack)
SPLUNK_URL=https://localhost:8089
SPLUNK_USER=admin
SPLUNK_PASSWORD=your_password
SPLUNK_VERIFY_SSL=false

# LibreChat Integration
ANTHROPIC_API_KEY=your_api_key
```

### Server Startup

```bash
# Production
make up

# Development with Splunk
make dev-up

# Direct Python execution
python -m catalyst_mcp.main
```

## MCP Protocol Implementation

### Tools List
```bash
curl -X POST http://localhost:8443/mcp \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

### Tool Execution
```bash
curl -X POST http://localhost:8443/mcp \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_indexes","arguments":{"count":10}}}'
```

### Health Check
```bash
curl http://localhost:8443/health
```

## Knowledge Pack Integration

### Pack Loading Process

1. **Discovery**: Registry scans `knowledge-packs/` directory
2. **Validation**: Pack metadata and structure validation
3. **Tool Creation**: Dynamic tool generation from YAML definitions
4. **Transform Loading**: Multi-language transform engine initialization
5. **Registration**: Tools registered with MCP server

### Supported Pack Types

- **Modular Packs**: Separate YAML files for tools, prompts, resources
- **Legacy Packs**: Single YAML file with all definitions
- **Hot Reload**: Packs can be updated without server restart

### Tool Types

- **list**: Return collections of items with pagination
- **details**: Get detailed information about specific items
- **search**: Execute queries and return filtered results  
- **execute**: Perform actions or run operations

## Security & Performance

### Guardrails Engine

- **Parameter Validation**: Type checking and range validation
- **Rate Limiting**: Per-tool execution limits
- **Capability Checking**: User permission validation
- **Input Sanitization**: SQL injection and XSS prevention

### Performance Optimizations

- **JSON Output**: All tools use `output_mode: "json"` for token efficiency
- **Pagination**: Default 20 items per page, max 100
- **Transform Caching**: Compiled transforms cached in memory
- **Connection Pooling**: Persistent HTTP clients

## Error Handling

### Common Error Responses

```json
{
  "error": {
    "code": -32000,
    "message": "Tool execution failed",
    "data": {
      "tool": "list_indexes",
      "details": "Authentication failed"
    }
  }
}
```

### Debugging

```bash
# View server logs
make logs

# Development logs with Splunk
make dev-logs

# Enable debug mode
export MCP_DEBUG=true
```

## Monitoring & Audit

### Audit Logging

All tool executions logged to Splunk via HTTP Event Collector (HEC):

```json
{
  "timestamp": "2024-08-30T13:45:00Z",
  "tool": "list_indexes",
  "user": "admin",
  "parameters": {"count": 20},
  "execution_time_ms": 150,
  "status": "success"
}
```

### Metrics Collection

- Tool execution counts and timing
- Error rates by tool and user
- Resource utilization tracking
- Pack usage statistics

## Development

### Adding New Tools

1. **Configuration-driven**: Add to pack YAML files
2. **Custom Implementation**: Create specialized tool classes
3. **Transform Functions**: Add Python/JavaScript/jq transforms
4. **Testing**: Use `test_modular_system.py`

### Hot Reload Development

```bash
# Make pack changes
vim knowledge-packs/splunk_basic/tools/list-tools.yaml

# Reload without restart
curl -X POST http://localhost:8443/reload-packs
```