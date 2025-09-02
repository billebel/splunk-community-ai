# System Architecture Overview

Catalyst MCP Server provides a complete AI-business integration platform through the Model Context Protocol (MCP).

## Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI Clients    │    │   Web Chat      │    │  External APIs  │
│                 │    │   Interface     │    │                 │
│ • Claude Desktop│    │                 │    │ • REST APIs     │
│ • Custom Apps   │    │ • LibreChat     │    │ • Databases     │
│ • ChatGPT       │    │ • Authentication│    │ • Cloud Services│
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │                      │                      │
    ┌─────▼──────────────────────▼──────────────────────▼─────┐
    │              Catalyst MCP Server                        │
    │                                                         │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
    │  │ MCP Protocol│  │ Knowledge   │  │ Connection      │  │
    │  │ Handler     │  │ Pack Loader │  │ Manager         │  │
    │  └─────────────┘  └─────────────┘  └─────────────────┘  │
    │                                                         │
    │  ┌─────────────────────────────────────────────────────┐  │
    │  │           Tool Registration & Execution            │  │
    │  └─────────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Pack Loading (Startup)
1. Server scans `knowledge-packs/` directory
2. Loads pack configurations (excluding `.example` suffix)
3. Validates connection definitions
4. Registers tools with MCP protocol

### 2. Tool Execution (Runtime)
1. AI client sends tool request via MCP
2. Server validates parameters against pack schema
3. Executes tool against target system (REST, DB, etc.)
4. Returns formatted response to AI client

### 3. Chat Interface Flow
1. User sends message via LibreChat web interface
2. LibreChat forwards to selected AI provider (Claude, GPT, etc.)
3. AI provider can call MCP tools through Catalyst server
4. Results are integrated into AI response
5. Response displayed to user in chat interface

## Key Features

### MCP Protocol Implementation
- **Full MCP Compliance**: Implements complete MCP specification
- **Tool Registration**: Automatic tool discovery from knowledge packs
- **Parameter Validation**: Type checking and schema validation
- **Error Handling**: Graceful error responses with debugging info

### Knowledge Pack System
- **Modular Architecture**: Each pack is self-contained
- **Hot Reloading**: Changes detected automatically in development
- **Connection Abstraction**: Unified interface for different system types
- **Security Controls**: Built-in rate limiting and access controls

### Multi-Client Support
- **Claude Desktop**: Native MCP integration
- **Web Interface**: LibreChat with full AI model support
- **Custom Clients**: Any MCP-compatible application
- **API Access**: Direct HTTP/JSON API for custom integrations

### Enterprise Features
- **Authentication**: JWT-based session management
- **Authorization**: Role-based access control
- **Audit Logging**: Comprehensive request/response logging
- **Monitoring**: Health checks and performance metrics

## Deployment Architecture

### Development
```
Local Machine
├── Catalyst MCP Server (Python)
├── LibreChat (Node.js)
└── Knowledge Packs (YAML + Python)
```

### Production
```
Docker Environment
├── catalyst-mcp (Container)
├── librechat (Container)  
├── mongodb (Container - LibreChat data)
└── nginx (Container - Optional reverse proxy)
```

## Security Model

### Authentication Layers
1. **API Keys**: AI provider authentication (Claude, OpenAI, etc.)
2. **JWT Tokens**: Web interface session management
3. **Environment Variables**: Secure credential storage
4. **Container Isolation**: Docker security boundaries

### Data Protection
- **No Credential Storage**: All secrets via environment variables
- **Request Validation**: Input sanitization and type checking
- **Rate Limiting**: Prevent abuse and API quota exhaustion
- **Audit Trail**: Complete request/response logging

## Next Steps

- **[MCP Protocol Details](mcp-protocol.md)** - Protocol implementation specifics
- **[Pack Loading Process](pack-loading.md)** - How knowledge packs work
- **[Configuration Reference](../configuration/environment.md)** - Environment setup