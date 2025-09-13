# Docker Configuration Migration Guide

This document outlines the migration from the old Docker setup to the new organized structure.

## Changes Made

### 🗂️ **File Organization**

**Before (old structure):**
```
project-root/
├── docker-compose.yml
├── docker-compose.mcp-only.yml
├── docker-compose.splunk.yml
├── docker-compose.override.yml
├── Dockerfile
└── librechat.yaml
```

**After (new structure):**
```
project-root/
├── docker/
│   ├── README.md
│   ├── MIGRATION.md
│   ├── Dockerfile
│   ├── docker-compose.base.yml
│   ├── compose/
│   │   ├── full-stack.yml
│   │   ├── mcp-only.yml
│   │   ├── development.yml
│   │   └── production.yml
│   └── scripts/
│       ├── start.sh
│       ├── start.bat
│       └── cleanup.sh
└── librechat.yaml
```

### 📋 **File Mapping**

| Old File | New File(s) | Status |
|----------|-------------|---------|
| `docker-compose.yml` | `docker/docker-compose.base.yml` + `docker/compose/full-stack.yml` | ✅ Replaced |
| `docker-compose.mcp-only.yml` | `docker/docker-compose.base.yml` + `docker/compose/mcp-only.yml` | ✅ Replaced |
| `docker-compose.splunk.yml` | `docker/docker-compose.base.yml` + `docker/compose/development.yml` | ✅ Replaced |
| `docker-compose.override.yml` | `docker/compose/development.yml` | ✅ Integrated |
| `Dockerfile` | `docker/Dockerfile` | ✅ Moved |
| `librechat.yaml` | `librechat.yaml` | ✅ Kept in place |

### 🚀 **Command Migration**

**Old Commands:**
```bash
# Full stack
docker compose up -d

# MCP only
docker compose -f docker-compose.mcp-only.yml up -d

# With development Splunk
docker compose -f docker-compose.yml -f docker-compose.splunk.yml up -d

# With overrides
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

**New Commands:**
```bash
# Full stack (equivalent to old default)
docker compose -f docker/docker-compose.base.yml -f docker/compose/full-stack.yml up -d
# OR use helper script:
./docker/scripts/start.sh full-stack -d

# MCP only
docker compose -f docker/docker-compose.base.yml -f docker/compose/mcp-only.yml up -d
# OR use helper script:
./docker/scripts/start.sh mcp-only -d

# Development environment (with Splunk)
docker compose -f docker/docker-compose.base.yml -f docker/compose/development.yml up -d
# OR use helper script:
./docker/scripts/start.sh development -d

# Production optimized
docker compose -f docker/docker-compose.base.yml -f docker/compose/production.yml up -d
# OR use helper script:
./docker/scripts/start.sh production -d
```

### ✨ **New Features**

1. **Helper Scripts**: Easy-to-use startup scripts for different scenarios
2. **Production Profile**: Optimized configuration for production deployments
3. **Authentication Support**: Full support for all three authentication methods
4. **Resource Limits**: Production deployments include resource management
5. **Comprehensive Documentation**: Detailed usage guides and troubleshooting
6. **Cleanup Tools**: Scripts for complete environment cleanup

### 🔄 **Authentication Migration**

The new Docker configuration fully supports all authentication methods:

**Environment Variables (add to `.env`):**
```bash
# Choose authentication method
SPLUNK_AUTH_METHOD=basic  # or 'token' or 'passthrough'

# Basic authentication
SPLUNK_USER=your-username
SPLUNK_PASSWORD=your-password

# Token authentication (when method=token)
SPLUNK_TOKEN=your-splunk-token

# Common settings
SPLUNK_URL=https://your-splunk:8089
```

## Migration Steps

### 1. **Stop Existing Containers**
```bash
# Stop any running containers
docker compose down
docker compose -f docker-compose.mcp-only.yml down
docker compose -f docker-compose.splunk.yml down
```

### 2. **Backup Data (Optional)**
```bash
# Backup volumes if you have important data
docker run --rm -v catalyst-mongodb-data:/data -v $(pwd):/backup alpine tar czf /backup/mongodb-backup.tar.gz /data
```

### 3. **Update Environment**
- Ensure your `.env` file includes `SPLUNK_AUTH_METHOD`
- Verify all required authentication variables are set

### 4. **Start New Configuration**
```bash
# Choose your deployment scenario
./docker/scripts/start.sh full-stack -d

# Or manually:
docker compose -f docker/docker-compose.base.yml -f docker/compose/full-stack.yml up -d
```

### 5. **Verify Operation**
```bash
# Check all services are running
docker compose ps

# Check logs
docker compose logs -f catalyst-mcp
```

## Cleanup Old Files

Once you've verified the new configuration works:

### **Remove Old Docker Files**
```bash
# These files are no longer needed:
rm docker-compose.yml
rm docker-compose.mcp-only.yml
rm docker-compose.splunk.yml
rm docker-compose.override.yml
# Dockerfile already moved to docker/
```

### **Update Scripts and Documentation**
- Update any custom scripts that reference old Docker files
- Update deployment documentation
- Update CI/CD pipelines if applicable

## Troubleshooting Migration

### **Issue: Port Conflicts**
```bash
# Check what's using ports
netstat -tulpn | grep :8443
netstat -tulpn | grep :3080

# Change ports in .env file
echo "MCP_PORT=8444" >> .env
echo "LIBRECHAT_PORT=3081" >> .env
```

### **Issue: Volume Mount Errors**
```bash
# Ensure paths exist and are accessible
ls -la knowledge-packs/
ls -la templates/
ls -la librechat.yaml
```

### **Issue: Authentication Not Working**
```bash
# Check environment variables
docker compose exec catalyst-mcp env | grep SPLUNK

# Verify .env file is loaded
cat .env | grep SPLUNK_AUTH_METHOD
```

### **Issue: Old Containers Interfering**
```bash
# Remove all catalyst-related containers
docker ps -a | grep catalyst | awk '{print $1}' | xargs docker rm -f

# Remove old networks
docker network ls | grep catalyst | awk '{print $1}' | xargs docker network rm
```

## Rollback Plan

If you need to rollback to the old configuration:

### 1. **Stop New Configuration**
```bash
./docker/scripts/cleanup.sh --containers
```

### 2. **Restore Old Files**
```bash
# Restore from git if available
git checkout HEAD~1 -- docker-compose.yml docker-compose.mcp-only.yml docker-compose.splunk.yml docker-compose.override.yml Dockerfile

# Or recreate manually from backups
```

### 3. **Start Old Configuration**
```bash
docker compose up -d
```

## Benefits of New Structure

1. **🧹 Organization**: All Docker files in dedicated directory
2. **🎯 Clarity**: Each deployment scenario clearly defined
3. **🔒 Security**: Production-optimized configurations
4. **🚀 Ease of Use**: Helper scripts for common operations
5. **📚 Documentation**: Comprehensive guides and examples
6. **🔧 Maintenance**: Easier to update and maintain
7. **🎛️ Flexibility**: Support for all authentication methods
8. **📊 Resource Management**: Production resource limits and reservations

The new structure provides a much more professional and maintainable Docker configuration while preserving all existing functionality and adding new capabilities.