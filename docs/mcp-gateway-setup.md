# Docker MCP Gateway Setup for Splunk Community AI

This guide helps you set up Docker MCP Gateway with Catalyst MCP server for seamless Splunk integration.

## Overview

Docker MCP Gateway provides a secure, containerized way to run MCP servers and connect them to AI clients like Claude, VS Code, and others. This setup gives you:

- **Secure credential management** - No tokens in client configs
- **Multi-environment support** - Dev, staging, prod isolation
- **Enterprise features** - Audit logging, rate limiting, access control
- **Easy scaling** - Container-based deployment

## Architecture

```
AI Client (Claude/VS Code) → Docker MCP Gateway → Catalyst MCP Container → Splunk API
```

## Quick Start

### Prerequisites

1. **Docker Desktop** with MCP Toolkit feature enabled
2. **Docker MCP Gateway CLI** installed
3. **Splunk environment** with API access

### Installation

#### Option 1: Automated Setup (Recommended)

**Linux/macOS:**
```bash
./scripts/setup-mcp-gateway.sh
```

**Windows:**
```powershell
.\scripts\setup-mcp-gateway.ps1
```

#### Option 2: Manual Setup

1. **Build the MCP server image:**
   ```bash
   docker build -f docker/Dockerfile.mcp-gateway -t splunk-community-ai/catalyst-mcp:latest .
   ```

2. **Register with Docker MCP Gateway:**
   ```bash
   docker mcp server add splunk-catalyst \
     --image splunk-community-ai/catalyst-mcp:latest \
     --name "Splunk Catalyst MCP Server" \
     --local true
   ```

3. **Enable the server:**
   ```bash
   docker mcp server enable splunk-catalyst
   ```

### Configuration

1. **Copy environment template:**
   ```bash
   cp mcp-gateway.env .env
   ```

2. **Edit .env with your Splunk details:**
   ```bash
   # Basic Splunk connection
   SPLUNK_HOST=your-splunk-host.example.com
   SPLUNK_TOKEN=your-splunk-token

   # Or OAuth configuration
   OAUTH_CLIENT_ID=your-oauth-client-id
   OAUTH_CLIENT_SECRET=your-oauth-client-secret
   ```

### Starting the Gateway

#### Option 1: Quick Start Script

**Linux/macOS:**
```bash
./scripts/start-mcp-gateway.sh
```

**Windows:**
```powershell
.\scripts\start-mcp-gateway.ps1
```

#### Option 2: Manual Start

```bash
# Start the gateway
docker mcp gateway run

# Connect your AI client
docker mcp client connect claude
```

#### Option 3: Docker Compose (Development)

```bash
docker-compose -f docker-compose.mcp-gateway.yml up
```

## Available Authentication Methods

### 1. Token Authentication (Simplest)
```env
SPLUNK_HOST=your-splunk-host.com
SPLUNK_TOKEN=your-hec-token
```

### 2. OAuth Authentication
```env
SPLUNK_HOST=your-splunk-host.com
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret
```

### 3. SAML/SSO Authentication
```env
SPLUNK_HOST=your-splunk-host.com
SAML_SSO_URL=https://your-sso.com/saml/sso
SAML_ENTITY_ID=splunk-enterprise
```

## Available Knowledge Packs

The MCP server includes several pre-built knowledge packs:

- **splunk_enterprise** - Core Splunk Enterprise tools
- **splunk_cloud** - Splunk Cloud Platform tools
- **splunk_oauth** - OAuth authentication flows
- **splunk_saml** - SAML/SSO authentication flows

## AI Client Connection

### Claude (Anthropic)
```bash
docker mcp client connect claude
```

### VS Code
```bash
docker mcp client connect vscode
```

### Custom MCP Client
- **Gateway URL:** `http://localhost:8080`
- **Server Name:** `splunk-catalyst`

## Management Commands

### Server Management
```bash
# List servers
docker mcp server list

# View server logs
docker mcp server logs splunk-catalyst

# Restart server
docker mcp server restart splunk-catalyst

# Remove server
docker mcp server remove splunk-catalyst
```

### Gateway Management
```bash
# Gateway status
docker mcp gateway status

# Stop gateway
docker mcp gateway stop

# View gateway logs
docker mcp gateway logs
```

### Credential Management
```bash
# Set credentials (secure)
docker mcp credentials set splunk-catalyst SPLUNK_TOKEN your-token

# List credentials
docker mcp credentials list splunk-catalyst

# Remove credentials
docker mcp credentials remove splunk-catalyst SPLUNK_TOKEN
```

## Multi-Environment Setup

### Development Environment
```bash
docker mcp server add splunk-dev \
  --image splunk-community-ai/catalyst-mcp:dev \
  --env SPLUNK_HOST=dev-splunk.company.com \
  --env DEBUG=true
```

### Production Environment
```bash
docker mcp server add splunk-prod \
  --image splunk-community-ai/catalyst-mcp:latest \
  --env SPLUNK_HOST=prod-splunk.company.com \
  --env RATE_LIMIT_REQUESTS=50
```

## Troubleshooting

### Common Issues

1. **Gateway won't start:**
   ```bash
   # Check Docker MCP plugin
   docker mcp --help

   # Check prerequisites
   docker --version
   docker-compose --version
   ```

2. **Server registration fails:**
   ```bash
   # Remove existing server first
   docker mcp server remove splunk-catalyst

   # Re-register
   ./scripts/setup-mcp-gateway.sh
   ```

3. **Connection issues:**
   ```bash
   # Check server status
   docker mcp server list
   docker mcp server logs splunk-catalyst

   # Check gateway status
   docker mcp gateway status
   ```

4. **Splunk authentication fails:**
   ```bash
   # Test credentials
   curl -k https://your-splunk-host:8089/services/auth/login \
     -d username=your-user -d password=your-pass

   # Check token validity
   curl -k https://your-splunk-host:8089/services/server/info \
     -H "Authorization: Bearer your-token"
   ```

### Debug Mode

Enable debug logging in your `.env`:
```env
DEBUG=true
VERBOSE_LOGGING=true
LOG_LEVEL=DEBUG
```

Then restart the server:
```bash
docker mcp server restart splunk-catalyst
docker mcp server logs splunk-catalyst --follow
```

## Enterprise Deployment

For enterprise deployments, consider:

1. **Private Container Registry:**
   ```bash
   docker build -t your-registry.com/catalyst-mcp:latest .
   docker push your-registry.com/catalyst-mcp:latest
   ```

2. **Secrets Management:**
   ```bash
   # Use Docker secrets or external secret management
   docker mcp credentials set splunk-catalyst SPLUNK_TOKEN "$(vault kv get -field=token secret/splunk)"
   ```

3. **Load Balancing:**
   ```bash
   # Multiple server instances
   docker mcp server add splunk-catalyst-1 --image catalyst-mcp:latest
   docker mcp server add splunk-catalyst-2 --image catalyst-mcp:latest
   ```

4. **Monitoring:**
   ```bash
   # Health checks and monitoring
   docker mcp gateway metrics
   docker mcp server health splunk-catalyst
   ```

## Next Steps

1. **Customize Knowledge Packs** - Add your own Splunk tools
2. **Set up CI/CD** - Automate deployments
3. **Configure Monitoring** - Add observability
4. **Security Hardening** - Production security setup

For more information, see:
- [Docker MCP Gateway Documentation](https://docs.docker.com/ai/mcp-gateway/)
- [Catalyst MCP Server Documentation](../README.md)
- [Knowledge Packs Guide](./knowledge-packs.md)