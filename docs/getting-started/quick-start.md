# Quick Start Guide

Get Catalyst MCP Server running with LibreChat interface in 5 minutes.

## Prerequisites

- Docker and Docker Compose
- At least one AI provider API key (Claude, GPT, or Gemini)

## 1. Clone and Setup

```bash
git clone https://github.com/billebel/catalyst.git
cd catalyst
cp .env.example .env
```

## 2. Configure API Keys

Edit `.env` file with your API keys:

```bash
# Required: At least one AI provider
ANTHROPIC_API_KEY=your-claude-api-key
OPENAI_API_KEY=your-openai-api-key        # Optional
GOOGLE_API_KEY=your-gemini-api-key        # Optional

# Required: JWT secrets (change for production!)
JWT_SECRET=your-secure-jwt-secret
JWT_REFRESH_SECRET=your-secure-refresh-secret
```

## 3. Start Services

```bash
# Start everything
docker-compose up -d

# Check status
docker-compose ps
```

## 4. Access Your AI Assistant

- **Web Chat Interface**: http://localhost:3080
- **MCP Server API**: http://localhost:8443
- **API Documentation**: http://localhost:8443/docs

## 5. Test Integration

1. Open http://localhost:3080 in your browser
2. Create an account or login
3. Start a new chat
4. Ask: "What knowledge packs are available?"

The AI assistant should respond with information about the example packs included.

## Next Steps

- **[Create Custom Packs](../knowledge-packs/creating-packs.md)** - Build your own integrations
- **[Configure AI Providers](../integrations/ai-providers.md)** - Add more AI models
- **[Production Deployment](../deployment/docker-compose.md)** - Secure production setup

## Troubleshooting

**Services won't start?**
```bash
# Check logs
docker-compose logs -f

# Common issues
docker-compose down && docker-compose up -d
```

**Can't access web interface?**
- Ensure port 3080 is available
- Check firewall settings
- Verify JWT secrets are set

**No AI responses?**
- Verify API keys are correct
- Check API key quotas/limits
- Review MCP server logs: `docker-compose logs catalyst-mcp`