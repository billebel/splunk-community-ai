# Docker Deployment Guide

This directory contains organized Docker configurations for different deployment scenarios of the Splunk Community AI platform.

## Important: Working Directory and File Locations

**⚠️ CRITICAL:** All Docker commands must be run from the **project root** (`splunk-community-ai/` directory), not from the `docker/` subdirectory.

**Required file locations (relative to project root):**
- `.env` - Environment configuration file (in project root)
- `knowledge-packs/` - MCP knowledge packs directory
- `templates/` - Authentication template files  
- `librechat.yaml` - LibreChat configuration file

**Example correct usage:**
```bash
# ✅ CORRECT: Run from project root
cd splunk-community-ai/
docker compose -f docker/docker-compose.base.yml -f docker/compose/full-stack.yml up -d

# ❌ INCORRECT: Don't run from docker/ subdirectory
cd docker/
docker compose -f docker-compose.base.yml -f compose/full-stack.yml up -d  # Will fail!
```

## Directory Structure

```
docker/
├── README.md                    # This file
├── docker-compose.base.yml      # Base service definitions
├── Dockerfile                   # MCP server container build
├── compose/                     # Deployment scenarios
│   ├── full-stack.yml          # MCP + LibreChat web interface
│   ├── mcp-only.yml           # MCP server only
│   ├── development.yml        # Full stack + dev Splunk
│   └── production.yml         # Production optimizations
└── scripts/                     # Docker helper scripts
    ├── start.sh               # Quick start script
    ├── start.bat              # Windows quick start
    └── cleanup.sh             # Container cleanup
```

## Deployment Scenarios

### 1. Full Stack Deployment (Recommended for most users)

Complete platform with web interface and all features:

```bash
# Start full stack
docker compose -f docker/docker-compose.base.yml -f docker/compose/full-stack.yml up -d

# Or use helper script
./docker/scripts/start.sh full-stack
```

**Includes:**
- Catalyst MCP Server (port 8443)
- LibreChat Web Interface (port 3080)
- MongoDB database
- Meilisearch for chat search

**Access:** http://localhost:3080

### 2. MCP Server Only

Lightweight deployment for programmatic use or integration with other MCP clients:

```bash
# Start MCP server only
docker compose -f docker/docker-compose.base.yml -f docker/compose/mcp-only.yml up -d

# Or use helper script
./docker/scripts/start.sh mcp-only
```

**Includes:**
- Catalyst MCP Server only (port 8443)

**Access:** http://localhost:8443 (MCP endpoint)

### 3. Development Environment

Full platform with development Splunk instance for testing:

```bash
# Start development environment
docker compose -f docker/docker-compose.base.yml -f docker/compose/development.yml up -d

# Or use helper script
./docker/scripts/start.sh development
```

**Includes:**
- Everything from full stack
- Development Splunk instance (ports 8000, 8089, 8088)
- Debug logging enabled
- Development optimizations

**Access:** 
- LibreChat: http://localhost:3080
- Splunk Web: http://localhost:8000 (admin/changeme)

### 4. Production Deployment

Optimized for production use with security and performance improvements:

```bash
# Start production deployment
docker compose -f docker/docker-compose.base.yml -f docker/compose/production.yml up -d

# Or use helper script
./docker/scripts/start.sh production
```

**Features:**
- Resource limits and reservations
- Enhanced security settings
- Disabled registration (LibreChat)
- Read-only volumes
- Aggressive healthchecks

## Authentication Configuration

The Docker configuration supports all three authentication methods:

### Environment Variables

Set these in your `.env` file:

```bash
# Authentication Method Selection
SPLUNK_AUTH_METHOD=basic  # or 'token' or 'passthrough'

# Splunk Connection
SPLUNK_URL=https://your-splunk:8089

# Basic Authentication
SPLUNK_USER=your-username
SPLUNK_PASSWORD=your-password

# Token Authentication (when SPLUNK_AUTH_METHOD=token)
SPLUNK_TOKEN=your-auth-token

# Optional: HEC for audit logging
SPLUNK_HEC_TOKEN=your-hec-token
SPLUNK_HEC_URL=https://your-splunk:8088
SPLUNK_HEC_INDEX=catalyst
```

### Authentication Method Support

| Method | Docker Support | Configuration |
|--------|---------------|---------------|
| Basic | ✅ Full | Set `SPLUNK_USER` and `SPLUNK_PASSWORD` |
| Token | ✅ Full | Set `SPLUNK_TOKEN` |
| Passthrough | ✅ Full | No additional env vars needed |

## Port Configuration

Default ports (configurable via environment variables):

| Service | Default Port | Environment Variable | Purpose |
|---------|--------------|---------------------|---------|
| MCP Server | 8443 | `MCP_PORT` | MCP HTTP endpoint |
| LibreChat | 3080 | `LIBRECHAT_PORT` | Web interface |
| Splunk Web | 8000 | N/A | Splunk UI (dev only) |
| Splunk API | 8089 | N/A | Management API (dev only) |
| Splunk HEC | 8088 | N/A | Event collector (dev only) |

## Volume Mounts

| Path | Purpose | Mode |
|------|---------|------|
| `./knowledge-packs` | MCP knowledge packs | ro (read-only) |
| `./templates` | Configuration templates | ro (read-only) |
| `./librechat.yaml` | LibreChat configuration | ro (read-only) |

## Healthchecks

All services include healthchecks:

- **MCP Server**: HTTP health endpoint
- **LibreChat**: Web server availability
- **MongoDB**: Database connectivity
- **Splunk**: Web interface availability

## Quick Commands

```bash
# View logs
docker compose logs -f catalyst-mcp
docker compose logs -f librechat

# Scale services (if needed)
docker compose up -d --scale catalyst-mcp=2

# Update containers
docker compose pull
docker compose up -d

# Complete cleanup
./docker/scripts/cleanup.sh
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports via environment variables
2. **Permission issues**: Ensure `.env` file is readable
3. **Splunk connection**: Verify `SPLUNK_URL` and credentials
4. **Memory issues**: Check Docker resource allocation

### Debug Mode

Enable debug logging:

```bash
# Add to .env file
MCP_DEBUG=true

# Or use development deployment
./docker/scripts/start.sh development
```

### Logs Analysis

```bash
# MCP server logs
docker compose logs catalyst-mcp | grep ERROR

# LibreChat logs
docker compose logs librechat | grep -E "(error|warn)"

# All service logs
docker compose logs --tail=100 -f
```

## Migration from Old Structure

If migrating from the old Docker setup:

1. **Stop old containers**: `docker compose down`
2. **Update scripts**: Use new helper scripts in `docker/scripts/`
3. **Check environment**: Verify `.env` file compatibility
4. **Start new deployment**: Choose appropriate scenario above

## Security Considerations

### Production Deployment
- Set strong passwords for all services
- Use HTTPS endpoints when possible
- Limit container resources
- Enable authentication on MongoDB
- Disable unnecessary services

### Network Security
- Services communicate via internal Docker network
- Only necessary ports exposed to host
- No direct database access from outside

### Data Persistence
- Named volumes for data persistence
- Automatic volume backup recommended
- Regular container updates for security patches