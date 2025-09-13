# Docker Quick Start

This project uses the standard Docker Compose structure for easy deployment.

## 🚀 Quick Start

```bash
# Full stack (MCP server + web chat interface) - most users want this
docker compose up -d

# Just the MCP server (for integration with existing tools)
docker compose -f docker-compose.mcp-only.yml up -d

# Development environment (includes test Splunk instance)
docker compose -f docker-compose.dev.yml up -d
```

## 📋 Prerequisites

1. **Docker Desktop** - Make sure Docker is running
2. **Environment file** - Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   # Edit .env with your Splunk connection details
   ```

## 🎯 Deployment Options

### Option 1: Full Stack (Default)
**What you get:** MCP server + LibreChat web interface + MongoDB  
**Perfect for:** New users who want everything ready to go  
**Access:** http://localhost:3080 (web) + http://localhost:8443 (MCP API)

```bash
docker compose up -d
```

### Option 2: MCP Server Only  
**What you get:** Just the MCP server  
**Perfect for:** Integration with Claude Desktop or custom applications  
**Access:** http://localhost:8443 (MCP API only)

```bash
docker compose -f docker-compose.mcp-only.yml up -d
```

### Option 3: Development Environment
**What you get:** Full stack + development Splunk instance  
**Perfect for:** Testing and evaluation  
**Access:** http://localhost:3080 (web) + http://localhost:8000 (Splunk admin/changeme)

```bash
docker compose -f docker-compose.dev.yml up -d
```

## 🔧 Common Commands

```bash
# Start services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f catalyst-mcp

# Stop everything
docker compose down

# Update and restart
docker compose pull && docker compose up -d --build
```

## 🛠️ Authentication Setup

The platform supports three authentication methods with Splunk:

### Basic Authentication (Username/Password)
```bash
# In your .env file:
SPLUNK_AUTH_METHOD=basic
SPLUNK_USER=your-username
SPLUNK_PASSWORD=your-password
SPLUNK_URL=https://your-splunk:8089
```

### Token Authentication (Recommended)
```bash
# In your .env file:  
SPLUNK_AUTH_METHOD=token
SPLUNK_TOKEN=your-splunk-token
SPLUNK_URL=https://your-splunk:8089
```

### Passthrough Authentication (Enterprise)
```bash
# In your .env file:
SPLUNK_AUTH_METHOD=passthrough
SPLUNK_URL=https://your-splunk:8089
# No additional credentials needed - user provides them
```

## 🆘 Troubleshooting

**Port conflicts?** Change ports in `.env`:
```bash
MCP_PORT=8444
LIBRECHAT_PORT=3081
```

**Connection issues?** Check your Splunk URL and credentials:
```bash
# Test MCP server health
curl http://localhost:8443/health

# Check container logs
docker compose logs catalyst-mcp
```

**Start fresh?** Clean everything and restart:
```bash
docker compose down --volumes
docker compose up -d
```

## 📚 More Information

- **Advanced configuration:** See `docker/README.md`
- **Authentication details:** See `templates/README.md` 
- **Troubleshooting:** Check container logs with `docker compose logs`

This setup follows Docker best practices and should work out-of-the-box for most users!