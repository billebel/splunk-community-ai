# 🚀 Docker MCP Gateway Quick Start

Get started with Catalyst MCP Gateway for Splunk in under 5 minutes!

## TL;DR - Super Quick Start

```bash
# 1. Setup (one time)
./scripts/setup-mcp-gateway.sh

# 2. Configure
cp mcp-gateway.env .env
# Edit .env with your Splunk details

# 3. Start
./scripts/start-mcp-gateway.sh

# 4. Use with Claude/VS Code!
```

## What is Docker MCP Gateway?

Docker MCP Gateway is Docker's official solution for running Model Context Protocol (MCP) servers securely. It provides:

- 🔒 **Secure credential management** - No tokens in client configs
- 🏢 **Enterprise features** - Audit logs, rate limiting, access control
- 🔄 **Easy deployment** - Container-based, multi-environment support
- 🎯 **Simple integration** - Works with Claude, VS Code, and any MCP client

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌─────────────┐
│   AI Client     │    │  Docker MCP      │    │  Catalyst MCP   │    │   Splunk    │
│ (Claude/VS Code)│───▶│     Gateway      │───▶│    Container    │───▶│     API     │
│                 │    │                  │    │                 │    │             │
└─────────────────┘    └──────────────────┘    └─────────────────┘    └─────────────┘
```

## Quick Start Options

### Option 1: Automated Scripts (Recommended)

**Linux/macOS:**
```bash
# Setup
./scripts/setup-mcp-gateway.sh

# Start
./scripts/start-mcp-gateway.sh
```

**Windows:**
```powershell
# Setup
.\scripts\setup-mcp-gateway.ps1

# Start
.\scripts\start-mcp-gateway.ps1
```

### Option 2: Make Commands

```bash
# Complete setup
make -f Makefile.mcp-gateway setup

# Start gateway
make -f Makefile.mcp-gateway start

# View status
make -f Makefile.mcp-gateway status

# View logs
make -f Makefile.mcp-gateway logs
```

### Option 3: Docker Compose (Development)

```bash
# Start development environment
docker-compose -f docker-compose.mcp-gateway.yml up
```

## Configuration

### 1. Copy Environment Template
```bash
cp mcp-gateway.env .env
```

### 2. Configure Splunk Connection

Choose your authentication method:

**Token Authentication (Simplest):**
```env
SPLUNK_HOST=your-splunk-host.com
SPLUNK_TOKEN=your-hec-token
```

**OAuth Authentication:**
```env
SPLUNK_HOST=your-splunk-host.com
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret
```

**SAML/SSO Authentication:**
```env
SPLUNK_HOST=your-splunk-host.com
SAML_SSO_URL=https://your-sso.com/saml/sso
```

## Available Knowledge Packs

- **splunk_enterprise** - Core Splunk Enterprise tools
- **splunk_cloud** - Splunk Cloud Platform tools
- **splunk_oauth** - OAuth authentication flows
- **splunk_saml** - SAML/SSO authentication flows

## AI Client Connection

### Claude (Anthropic)
Once the gateway is running:
```bash
docker mcp client connect claude
```

### VS Code
```bash
docker mcp client connect vscode
```

### Custom MCP Client
- **Gateway URL:** `http://localhost:8080`
- **Server:** `splunk-catalyst`

## Common Commands

### Daily Operations
```bash
# Check everything is running
make -f Makefile.mcp-gateway status

# View real-time logs
make -f Makefile.mcp-gateway logs

# Restart if needed
make -f Makefile.mcp-gateway restart
```

### Troubleshooting
```bash
# Health check
make -f Makefile.mcp-gateway test

# View gateway logs
make -f Makefile.mcp-gateway gateway-logs

# Clean restart
make -f Makefile.mcp-gateway rebuild
```

### Development
```bash
# Start with hot reload
make -f Makefile.mcp-gateway start-dev

# Set credentials securely
make -f Makefile.mcp-gateway credentials
```

## Multi-Environment Setup

### Development
```bash
docker mcp server add splunk-dev \
  --image catalyst-mcp:dev \
  --env SPLUNK_HOST=dev-splunk.company.com
```

### Production
```bash
docker mcp server add splunk-prod \
  --image catalyst-mcp:latest \
  --env SPLUNK_HOST=prod-splunk.company.com
```

## Enterprise Deployment

For production use:

1. **Use Private Registry:**
   ```bash
   docker build -t your-registry.com/catalyst-mcp:latest .
   docker push your-registry.com/catalyst-mcp:latest
   ```

2. **Secure Credentials:**
   ```bash
   docker mcp credentials set splunk-catalyst SPLUNK_TOKEN "$(vault kv get -field=token secret/splunk)"
   ```

3. **Load Balancing:**
   ```bash
   docker mcp server add splunk-catalyst-1 --image catalyst-mcp:latest
   docker mcp server add splunk-catalyst-2 --image catalyst-mcp:latest
   ```

## Files Reference

| File | Purpose |
|------|---------|
| `scripts/setup-mcp-gateway.sh` | Automated setup (Linux/macOS) |
| `scripts/setup-mcp-gateway.ps1` | Automated setup (Windows) |
| `scripts/start-mcp-gateway.sh` | Quick start (Linux/macOS) |
| `scripts/start-mcp-gateway.ps1` | Quick start (Windows) |
| `docker-compose.mcp-gateway.yml` | Development environment |
| `docker/Dockerfile.mcp-gateway` | MCP server container |
| `mcp-gateway.env` | Environment template |
| `Makefile.mcp-gateway` | Make commands |
| `docs/mcp-gateway-setup.md` | Detailed documentation |

## Troubleshooting

### Gateway Won't Start
```bash
# Check Docker MCP plugin
docker mcp --help

# Re-run setup
./scripts/setup-mcp-gateway.sh
```

### Can't Connect to Splunk
```bash
# Test credentials manually
curl -k https://your-splunk-host:8089/services/server/info \
  -H "Authorization: Bearer your-token"

# Check server logs
make -f Makefile.mcp-gateway logs
```

### Client Connection Issues
```bash
# Check gateway status
docker mcp gateway status

# Restart gateway
make -f Makefile.mcp-gateway restart
```

## Next Steps

1. **Customize Knowledge Packs** - Add your own Splunk tools
2. **Set up Monitoring** - Add health checks and metrics
3. **Security Hardening** - Production security configuration
4. **CI/CD Integration** - Automate deployments

## Support

- **Documentation:** [docs/mcp-gateway-setup.md](docs/mcp-gateway-setup.md)
- **Docker MCP Gateway:** https://docs.docker.com/ai/mcp-gateway/
- **Issues:** https://github.com/billebel/splunk-community-ai/issues

---

**Need help?** Run `make -f Makefile.mcp-gateway help` for all available commands!