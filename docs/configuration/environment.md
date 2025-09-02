# Environment Configuration

Complete reference for environment variables used by Catalyst MCP Server.

## Core Server Configuration

### MCP_PORT
- **Default**: `8443`
- **Description**: Port for MCP server to listen on
- **Example**: `MCP_PORT=8443`

### MCP_HOST  
- **Default**: `0.0.0.0`
- **Description**: Host address to bind server
- **Values**: 
  - `0.0.0.0` - All interfaces (Docker)
  - `localhost` - Local only (development)
- **Example**: `MCP_HOST=0.0.0.0`

### LOG_LEVEL
- **Default**: `INFO`
- **Description**: Logging verbosity level
- **Values**: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- **Example**: `LOG_LEVEL=INFO`

## AI Provider API Keys

### Anthropic (Claude)
```bash
# Required for Claude models
ANTHROPIC_API_KEY=your-anthropic-api-key

# Optional: Specify available models
ANTHROPIC_MODELS=claude-opus-4-1-20250805,claude-sonnet-4-20250514
```

### OpenAI
```bash  
# Optional: For GPT models
OPENAI_API_KEY=your-openai-api-key

# Optional: Specify available models
OPENAI_MODELS=gpt-4,gpt-3.5-turbo
```

### Google (Gemini)
```bash
# Optional: For Gemini models  
GOOGLE_API_KEY=your-google-api-key

# Optional: Specify available models
GOOGLE_MODELS=gemini-2.5-flash,gemini-2.5-pro
```

## LibreChat Configuration

### JWT Authentication
```bash
# Required: Session management secrets
JWT_SECRET=your-jwt-secret-change-in-production
JWT_REFRESH_SECRET=your-refresh-secret-change-in-production
```

**Security Note**: Use strong, unique secrets in production. Generate with:
```bash
# Generate secure secrets
openssl rand -hex 32
```

### User Registration
```bash
# Control new user signup
ALLOW_REGISTRATION=false  # Recommended for production
ALLOW_REGISTRATION=true   # Development only
```

### OAuth Providers
```bash
# Optional: GitHub OAuth
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# Optional: Google OAuth  
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret
```

## Docker Configuration

### Container Settings
```bash
# Container network
DOCKER_NETWORK=catalyst-network

# Container names
MCP_CONTAINER_NAME=catalyst-mcp
LIBRECHAT_CONTAINER_NAME=librechat
```

### Port Mapping
```bash
# External port mappings
LIBRECHAT_PORT=3080  # Web interface
MCP_PORT=8443        # MCP server API
```

## Knowledge Pack Variables

Knowledge packs may require their own environment variables. Common patterns:

### Database Connections
```bash
# PostgreSQL example
DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp
DB_USER=username
DB_PASSWORD=password
```

### API Integrations
```bash
# REST API example
API_BASE_URL=https://api.example.com/v1
API_TOKEN=your-api-token
API_TIMEOUT=30
```

### Cloud Services
```bash
# AWS example
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-west-2
```

## Environment File Setup

### .env File Structure
```bash
# Catalyst MCP Server Configuration
# Copy from .env.example and customize

# =============================================================================
# MCP SERVER CONFIGURATION  
# =============================================================================
MCP_PORT=8443
MCP_HOST=0.0.0.0
LOG_LEVEL=INFO

# =============================================================================
# AI MODEL PROVIDER API KEYS
# =============================================================================
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key
GOOGLE_API_KEY=your-google-api-key

# =============================================================================
# LIBRECHAT CHAT INTERFACE
# =============================================================================
JWT_SECRET=your-jwt-secret-change-in-production
JWT_REFRESH_SECRET=your-refresh-secret-change-in-production
ALLOW_REGISTRATION=false

# =============================================================================
# KNOWLEDGE PACK SPECIFIC VARIABLES
# =============================================================================
# Add pack-specific variables here as needed
```

## Security Best Practices

### 1. Use Environment Variables
- Never hardcode secrets in configuration files
- Use `.env` for local development
- Use container secrets for production

### 2. Rotate Secrets Regularly  
- Change JWT secrets periodically
- Rotate API keys according to provider recommendations
- Monitor for leaked credentials

### 3. Principle of Least Privilege
- Use read-only API keys when possible
- Limit database user permissions
- Restrict network access

### 4. Version Control Safety
```bash
# Add to .gitignore
.env
.env.local
*.key
*.pem
```

## Validation

Test your configuration:
```bash
# Check MCP server starts
docker-compose up catalyst-mcp

# Verify API access
curl http://localhost:8443/health

# Test chat interface
docker-compose up librechat
```

## Next Steps

- **[Docker Configuration](docker.md)** - Container deployment details
- **[Chat Interface Setup](chat-interface.md)** - LibreChat customization
- **[Security Guide](../deployment/security.md)** - Production security