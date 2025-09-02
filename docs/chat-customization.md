# Chat Interface Customization

## Overview

The Catalyst platform integrates with LibreChat through a configuration abstraction layer, allowing easy customization of chat interfaces, model providers, and MCP tool integration.

## Configuration Architecture

### chat.yml Abstraction Layer

The `chat.yml` file provides a simplified configuration interface that generates both LibreChat and Docker Compose configurations:

```yaml
# chat.yml
interface:
  title: "Catalyst AI Assistant"
  description: "AI-powered platform with domain-specific tool packs"
  default_model: "claude-3-5-haiku-20241022"

models:
  providers: ["anthropic", "openai"]
  
  anthropic:
    available: [
      "claude-opus-4-1-20250805",
      "claude-opus-4-20250514", 
      "claude-sonnet-4-20250514",
      "claude-3-7-sonnet-20250219",
      "claude-3-5-haiku-20241022",
      "claude-3-haiku-20240307"
    ]
  
  openai:
    available: [
      "gpt-4",
      "gpt-3.5-turbo"
    ]

mcp:
  enabled: true
  server_url: "http://catalyst-mcp:8443"
  tools_display: "grouped"
  
chat:
  max_messages: 100
  conversation_timeout: 3600
  enable_file_upload: true
  enable_plugins: true
```

### Generation Script

The `scripts/generate-librechat-config.py` script transforms `chat.yml` into production configurations:

```bash
# Generate configurations
cd scripts
python generate-librechat-config.py

# Files generated:
# - librechat.yaml (LibreChat configuration)  
# - docker-compose.chat.yml (Docker services)
```

## LibreChat Integration

### Generated LibreChat Configuration

```yaml
# librechat.yaml (generated)
version: 1.1.5

cache: true

fileStrategy: "firebase"
registration:
  socialLogins: ["github", "google"]

endpoints:
  anthropic:
    apiKey: "${ANTHROPIC_API_KEY}"
    baseURL: "https://api.anthropic.com"
    models:
      default: [
        "claude-opus-4-1-20250805",
        "claude-opus-4-20250514",
        "claude-sonnet-4-20250514"
      ]
      fetch: false
      userIdQuery: false

  assistants:
    disableBuilder: false
    pollIntervalMs: 500
    timeoutMs: 10000
    supportedIds: ["asst_"]
    excludeList: ["asst_"]

rateLimits:
  anthropic:
    requests: 50
    interval: "1 hour"
    
mcp:
  servers:
    catalyst:
      command: "npx"
      args: ["-y", "@anthropic-ai/mcp-server-fetch", "http://catalyst-mcp:8443"]
      env:
        MCP_SERVER_URL: "http://catalyst-mcp:8443"
```

### Docker Compose Integration

```yaml
# docker-compose.chat.yml (generated)
services:
  librechat:
    image: ghcr.io/danny-avila/librechat:latest
    container_name: LibreChat
    ports:
      - "3080:3080"
    depends_on:
      - mongodb
      - catalyst-mcp
    env_file:
      - .env
    environment:
      - HOST=0.0.0.0
      - PORT=3080
      - MONGODB_URI=mongodb://mongodb:27017/LibreChat
      - ANTHROPIC_MODELS=claude-opus-4-1-20250805,claude-opus-4-20250514
      - MCP_ENABLED=true
      - MCP_SERVER_URL=http://catalyst-mcp:8443
    volumes:
      - ./librechat.yaml:/app/librechat.yaml:ro
      - librechat_data:/app/client/public/images
    restart: unless-stopped

  mongodb:
    image: mongo:6.0
    container_name: LibreChat-MongoDB
    volumes:
      - mongodb_data:/data/db
    restart: unless-stopped
```

## Customization Options

### Interface Branding

```yaml
# chat.yml
interface:
  title: "Your Company AI"
  description: "Custom AI assistant for your domain"
  logo_url: "https://yourcompany.com/logo.png"
  theme: "dark"
  custom_css: |
    .header { background: #1a365d; }
    .sidebar { background: #2d3748; }
```

### Model Configuration

#### Adding New Providers

```yaml
models:
  providers: ["anthropic", "openai", "cohere"]
  
  cohere:
    api_key: "${COHERE_API_KEY}"
    available: [
      "command-r-plus",
      "command-r",
      "command-light"
    ]
    default: "command-r-plus"
```

#### Model-Specific Settings

```yaml
anthropic:
  available: [
    {
      "name": "claude-opus-4-1-20250805",
      "display_name": "Claude 4 Opus (Latest)",
      "max_tokens": 8192,
      "temperature": 0.7,
      "description": "Most capable model for complex reasoning"
    }
  ]
```

### MCP Tool Integration

#### Tool Display Configuration

```yaml
mcp:
  enabled: true
  server_url: "http://catalyst-mcp:8443"
  tools_display: "grouped"  # "flat", "grouped", "categorized"
  
  # Tool filtering
  tools_filter:
    include: ["list_*", "search_*"]
    exclude: ["admin_*"]
  
  # Tool grouping
  tool_groups:
    "Data Discovery":
      - "list_indexes"
      - "list_apps"
    "Search Operations":
      - "search_splunk"
      - "run_saved_search"
```

#### Custom Tool Descriptions

```yaml
mcp:
  tool_overrides:
    list_indexes:
      display_name: "Browse Indexes"
      description: "View and explore available data indexes"
      icon: "📊"
      category: "Data Management"
```

### Chat Behavior

#### Conversation Settings

```yaml
chat:
  max_messages: 200
  conversation_timeout: 7200  # 2 hours
  auto_save: true
  enable_streaming: true
  
  # Response formatting
  response_format:
    code_highlighting: true
    markdown_rendering: true
    table_formatting: true
```

#### System Prompts

```yaml
prompts:
  system: |
    You are a specialized AI assistant with access to domain-specific tools.
    Always explain your actions and provide context for tool usage.
    
  welcome: |
    Welcome to Catalyst AI! I can help you with:
    - Data exploration and analysis
    - System monitoring and management
    - Automated reporting and insights
    
    What would you like to explore today?
```

## Advanced Customization

### Custom Endpoints

```yaml
# chat.yml
custom_endpoints:
  internal_api:
    name: "Internal API"
    base_url: "${INTERNAL_API_URL}"
    auth_type: "bearer"
    models: ["custom-model-v1"]
    
  proxy_endpoint:
    name: "Proxy Service"
    base_url: "http://proxy:8080/api"
    headers:
      "X-Custom-Header": "value"
```

### Plugin Integration

```yaml
plugins:
  enabled: true
  
  available:
    - name: "file_analyzer"
      description: "Analyze uploaded files"
      endpoint: "http://plugins:9000/analyze"
      
    - name: "data_visualizer"  
      description: "Create charts and graphs"
      endpoint: "http://visualizer:9001/render"

  settings:
    max_file_size: "10MB"
    allowed_types: ["pdf", "csv", "json", "txt"]
```

### Multi-Tenant Configuration

```yaml
# chat.yml
tenancy:
  enabled: true
  isolation: "domain"  # "user", "domain", "organization"
  
  domains:
    engineering:
      title: "Engineering AI"
      models: ["claude-opus-4-1-20250805"]
      tools: ["splunk_*", "github_*"]
      
    marketing:
      title: "Marketing AI"
      models: ["gpt-4"]
      tools: ["analytics_*", "social_*"]
```

## Development Workflow

### Local Development

```bash
# 1. Modify chat.yml
vim chat.yml

# 2. Regenerate configurations
cd scripts
python generate-librechat-config.py

# 3. Restart services
cd ..
docker-compose -f docker-compose.dev.yml -f docker-compose.chat.yml down
docker-compose -f docker-compose.dev.yml -f docker-compose.chat.yml up -d

# 4. Verify changes
curl http://localhost:3080/health
```

### Configuration Validation

```python
# scripts/validate-chat-config.py
import yaml
import json
from jsonschema import validate, ValidationError

def validate_chat_config(config_path="chat.yml"):
    """Validate chat.yml against schema."""
    
    schema = {
        "type": "object",
        "required": ["interface", "models"],
        "properties": {
            "interface": {
                "type": "object",
                "required": ["title", "default_model"]
            },
            "models": {
                "type": "object", 
                "required": ["providers"]
            }
        }
    }
    
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        validate(config, schema)
        print("✓ Configuration valid")
        return True
        
    except ValidationError as e:
        print(f"✗ Validation error: {e.message}")
        return False
    except Exception as e:
        print(f"✗ Error loading config: {e}")
        return False

if __name__ == "__main__":
    validate_chat_config()
```

### Hot Reload Support

```yaml
# chat.yml
development:
  hot_reload: true
  watch_files: ["chat.yml", "knowledge-packs/**/*.yaml"]
  reload_endpoint: "http://localhost:3080/api/reload"
```

## Security Configuration

### Authentication

```yaml
auth:
  providers: ["local", "oauth", "saml"]
  
  oauth:
    google:
      client_id: "${GOOGLE_CLIENT_ID}"
      client_secret: "${GOOGLE_CLIENT_SECRET}"
      
  saml:
    entity_id: "catalyst-ai"
    sso_url: "${SAML_SSO_URL}"
    certificate: "${SAML_CERT}"
```

### Rate Limiting

```yaml
security:
  rate_limits:
    requests_per_minute: 60
    tokens_per_hour: 50000
    
  content_filtering:
    enabled: true
    blocked_patterns: ["secret", "password", "api_key"]
    
  session_management:
    timeout_minutes: 120
    max_concurrent_sessions: 5
```

## Troubleshooting

### Common Issues

1. **Model Not Available**
   - Verify model name in provider's API
   - Check API key and permissions
   - Confirm model is in available list

2. **MCP Tools Not Loading**
   - Check MCP server connectivity
   - Verify tool definitions in knowledge packs
   - Review MCP server logs

3. **Configuration Not Applied**
   - Regenerate configs with generation script
   - Restart Docker services
   - Clear browser cache

### Debug Mode

```yaml
# chat.yml
debug:
  enabled: true
  log_level: "DEBUG"
  log_requests: true
  log_responses: true
  
  mcp_debug:
    trace_tools: true
    log_transforms: true
```

### Health Checks

```bash
# Check services
curl http://localhost:3080/health         # LibreChat
curl http://localhost:8443/health         # MCP Server

# Test MCP integration
curl -X POST http://localhost:3080/api/mcp/test

# Validate generated configs
python scripts/validate-chat-config.py
```