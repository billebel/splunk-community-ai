# Docker Configuration Guide

## Overview

The Catalyst platform uses Docker Compose for container orchestration, providing separate configurations for production, development, and chat interface deployments.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LibreChat     │◄──►│  Catalyst MCP   │◄──►│ Domain Systems  │
│ (Chat Interface)│    │    (Server)     │    │ (via Knowledge  │
│   Port: 3080    │    │   Port: 8443    │    │     Packs)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │                       
                               │                       
                    ┌─────────────────┐           
                    │ Knowledge Packs │           
                    │- splunk_basic   │           
                    │- (future packs) │           
                    └─────────────────┘           
```

## Docker Compose Files

### Production Configuration (docker-compose.yml)

```yaml
version: '3.8'

services:
  # Catalyst MCP Server - Universal Knowledge Pack Platform
  catalyst-mcp:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: catalyst-mcp
    ports:
      - "${MCP_PORT:-8443}:8443"
    environment:
      # Core MCP Configuration
      - MCP_PORT=8443
      
      # Knowledge Pack Configuration (loaded from .env)
      # See individual knowledge pack README files for setup:
      # - knowledge-packs/splunk_basic/README.md
      # - knowledge-packs/*/README.md (future packs)
      
    env_file:
      - .env  # All pack-specific variables
      
    volumes:
      - ./knowledge-packs:/app/knowledge-packs:ro
      - ./catalyst_mcp:/app/catalyst_mcp:ro
    networks:
      - catalyst-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8443/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  # Chat interface volumes managed by separate compose files
  # See docker-compose.dev.yml or docker-compose.chat.yml

networks:
  catalyst-network:
    driver: bridge
    name: catalyst-network
```

### Development Configuration (docker-compose.dev.yml)

```yaml
version: '3.8'

services:
  catalyst-mcp:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    container_name: catalyst-mcp-dev
    ports:
      - "${MCP_PORT:-8443}:8443"
    environment:
      - MCP_PORT=8443
      - MCP_DEBUG=true
      - SPLUNK_URL=https://splunk:8089
      - SPLUNK_USER=admin
      - SPLUNK_PASSWORD=P@ssw0rd!
      - SPLUNK_VERIFY_SSL=false
      - PYTHONPATH=/app
    volumes:
      - ./knowledge-packs:/app/knowledge-packs
      - ./catalyst_mcp:/app/catalyst_mcp
      - ./scripts:/app/scripts
      - mcp_logs:/app/logs
    depends_on:
      splunk:
        condition: service_healthy
    networks:
      - catalyst-network
    restart: unless-stopped

  splunk:
    image: splunk/splunk:latest
    container_name: splunk-enterprise
    hostname: splunk
    ports:
      - "8000:8000"   # Splunk Web
      - "8089:8089"   # Management API
      - "9997:9997"   # TCP Input
      - "8088:8088"   # HEC
    environment:
      - SPLUNK_START_ARGS=--accept-license
      - SPLUNK_PASSWORD=P@ssw0rd!
      - SPLUNK_HEC_TOKEN=your-hec-token-here
    volumes:
      - splunk_data:/opt/splunk/var
      - splunk_apps:/opt/splunk/etc/apps
      - ./splunk-config:/tmp/defaults:ro
    networks:
      - catalyst-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-k", "https://localhost:8089/services/server/info"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 120s

volumes:
  mcp_logs:
  splunk_data:
  splunk_apps:

networks:
  catalyst-network:
    driver: bridge
    name: catalyst-network
```

### Chat Interface Configuration (docker-compose.chat.yml)

```yaml
version: '3.8'

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
      - ANTHROPIC_MODELS=${ANTHROPIC_MODELS}
      - MCP_ENABLED=true
      - MCP_SERVER_URL=http://catalyst-mcp:8443
    volumes:
      - ./librechat.yaml:/app/librechat.yaml:ro
      - librechat_data:/app/client/public/images
      - librechat_logs:/app/logs
    networks:
      - catalyst-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  mongodb:
    image: mongo:6.0
    container_name: LibreChat-MongoDB
    ports:
      - "27017:27017"
    environment:
      - MONGO_INITDB_DATABASE=LibreChat
    volumes:
      - mongodb_data:/data/db
      - mongodb_logs:/var/log/mongodb
    networks:
      - catalyst-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "mongo", "--eval", "db.adminCommand('ping')"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  librechat_data:
  librechat_logs:
  mongodb_data:
  mongodb_logs:
```

## Environment Configuration

### Primary Environment File (.env)

```bash
# MCP Server Configuration
MCP_PORT=8443
MCP_DEBUG=false

# Splunk Configuration
SPLUNK_URL=https://your-splunk-server:8089
SPLUNK_USER=your-service-account
SPLUNK_PASSWORD=your-secure-password
SPLUNK_VERIFY_SSL=true

# HTTP Event Collector (HEC)
HEC_TOKEN=your-hec-token
HEC_URL=https://your-splunk-server:8088

# AI Model Providers
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_MODELS=claude-opus-4-1-20250805,claude-opus-4-20250514,claude-sonnet-4-20250514

OPENAI_API_KEY=your-openai-api-key
OPENAI_MODELS=gpt-4,gpt-3.5-turbo

# LibreChat Configuration
MONGODB_URI=mongodb://mongodb:27017/LibreChat
SESSION_SECRET=your-session-secret
JWT_SECRET=your-jwt-secret
JWT_REFRESH_SECRET=your-refresh-secret

# Security
ALLOW_REGISTRATION=false
ALLOW_SOCIAL_LOGIN=true
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# Logging
LOG_LEVEL=INFO
AUDIT_LOGGING=true
```

### Development Overrides (.env.dev)

```bash
# Development-specific overrides
MCP_DEBUG=true
LOG_LEVEL=DEBUG
SPLUNK_URL=https://splunk:8089
SPLUNK_PASSWORD=P@ssw0rd!
SPLUNK_VERIFY_SSL=false
ALLOW_REGISTRATION=true
```

## Dockerfile Configuration

### Multi-stage Production Build

```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim as production

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash mcp

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY catalyst_mcp/ ./catalyst_mcp/
COPY knowledge-packs/ ./knowledge-packs/
COPY setup.py .

# Set environment variables
ENV PYTHONPATH=/app
ENV PATH=/root/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${MCP_PORT:-8443}/health || exit 1

# Switch to non-root user
USER mcp

EXPOSE 8443

CMD ["python", "-m", "catalyst_mcp.main"]

# Development stage
FROM production as development

USER root

# Install development dependencies
RUN apt-get update && apt-get install -y \
    vim \
    git \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Install additional Python packages for development
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    black \
    flake8 \
    mypy

USER mcp

# Development command with auto-reload
CMD ["python", "-m", "catalyst_mcp.main", "--reload"]
```

## Deployment Strategies

### Production Deployment

```bash
# 1. Prepare environment
cp .env.example .env
# Edit .env with production values

# 2. Build and deploy
docker-compose build --no-cache
docker-compose up -d

# 3. Verify deployment
make status
curl http://localhost:8443/health
```

### Development Deployment

```bash
# 1. Start development environment
make dev-up

# 2. Access services
# - Splunk Web: http://localhost:8000 (admin/P@ssw0rd!)
# - MCP Server: http://localhost:8443
# - API Docs: http://localhost:8443/docs

# 3. Development workflow
make dev-logs    # Monitor logs
make dev-restart # Restart after changes
```

### Full Stack with Chat

```bash
# 1. Generate chat configurations
cd scripts
python generate-librechat-config.py

# 2. Start full stack
cd ..
docker-compose -f docker-compose.dev.yml -f docker-compose.chat.yml up -d

# 3. Access chat interface
# http://localhost:3080
```

## Volume Management

### Data Persistence

```yaml
# Persistent volumes for production
volumes:
  mcp_logs:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/catalyst/logs
      
  splunk_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/splunk/data
      
  mongodb_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/mongodb/data
```

### Backup Strategies

```bash
# Backup script
#!/bin/bash
BACKUP_DIR="/backup/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup MongoDB
docker exec LibreChat-MongoDB mongodump --out "$BACKUP_DIR/mongodb"

# Backup Splunk configuration
docker exec splunk-enterprise tar -czf - /opt/splunk/etc > "$BACKUP_DIR/splunk-etc.tar.gz"

# Backup MCP logs
docker cp catalyst-mcp:/app/logs "$BACKUP_DIR/mcp-logs"

echo "Backup completed: $BACKUP_DIR"
```

## Network Configuration

### Custom Networks

```yaml
networks:
  catalyst-network:
    driver: bridge
    name: catalyst-network
    ipam:
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1
    driver_opts:
      com.docker.network.bridge.name: catalyst-br
      com.docker.network.bridge.enable_ip_masquerade: "true"
```

### Service Discovery

```yaml
# Internal service communication
services:
  catalyst-mcp:
    networks:
      catalyst-network:
        aliases:
          - mcp-server
          - catalyst-api
          
  splunk:
    networks:
      catalyst-network:
        aliases:
          - splunk-api
          - splunk-server
```

## Monitoring & Observability

### Health Checks

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8443/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Logging Configuration

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
    compress: "true"
```

### Resource Limits

```yaml
services:
  catalyst-mcp:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check port usage
   netstat -tlnp | grep :8443
   
   # Change port in .env
   MCP_PORT=8444
   ```

2. **Permission Issues**
   ```bash
   # Fix volume permissions
   sudo chown -R 999:999 /opt/mongodb/data
   sudo chown -R 1001:1001 /opt/splunk/data
   ```

3. **Memory Issues**
   ```bash
   # Increase Docker memory
   # Docker Desktop: Settings > Resources > Memory > 8GB
   
   # Check container memory
   docker stats
   ```

### Debug Commands

```bash
# Container logs
docker logs catalyst-mcp -f
docker logs LibreChat -f

# Execute into containers
docker exec -it catalyst-mcp bash
docker exec -it splunk-enterprise bash

# Network inspection
docker network inspect catalyst-network

# Service health
docker-compose ps
curl http://localhost:8443/health | jq
```

### Performance Optimization

```yaml
# Optimized production configuration
services:
  catalyst-mcp:
    environment:
      - WORKERS=4
      - WORKER_CONNECTIONS=1000
      - KEEPALIVE_TIMEOUT=65
      - MAX_REQUESTS=10000
      - MAX_REQUESTS_JITTER=1000
    deploy:
      replicas: 2
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
```

## Security Hardening

### Container Security

```dockerfile
# Security-hardened Dockerfile
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r mcp && useradd --no-log-init -r -g mcp mcp

# Set secure file permissions
COPY --chown=mcp:mcp --chmod=755 . /app

# Drop capabilities
USER mcp

# Read-only root filesystem
VOLUME /tmp
```

### Network Security

```yaml
# Firewall rules in compose
services:
  catalyst-mcp:
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
```