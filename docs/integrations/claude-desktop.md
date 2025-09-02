# Claude Desktop Integration

Configure Claude Desktop to connect to your Catalyst MCP Server for direct AI-business system integration.

## Prerequisites

- Claude Desktop application installed
- Catalyst MCP Server running (see [Quick Start](../getting-started/quick-start.md))
- MCP server accessible on your network

## Configuration Steps

### 1. Locate Configuration File

Find your Claude Desktop configuration file:

**macOS:**
```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```bash
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux:**
```bash
~/.config/Claude/claude_desktop_config.json
```

### 2. Add MCP Server Configuration

Edit the configuration file to include your Catalyst server:

```json
{
  "mcpServers": {
    "catalyst": {
      "command": "mcp-client",
      "args": ["--url", "http://localhost:8443"],
      "description": "Catalyst MCP Server - Business system integrations"
    }
  }
}
```

For remote servers:
```json
{
  "mcpServers": {
    "catalyst": {
      "command": "mcp-client", 
      "args": ["--url", "https://your-server.com:8443"],
      "description": "Catalyst MCP Server - Business system integrations"
    }
  }
}
```

### 3. Restart Claude Desktop

Close and restart Claude Desktop application to load the new configuration.

### 4. Verify Connection

Start a new conversation and test the integration:

```
You: What knowledge packs are available?
Claude: I can see the following knowledge packs available through the Catalyst MCP server:
- PostgreSQL Analytics (database queries and reporting)
- GitHub DevOps (repository management)
- ...
```

## Advanced Configuration

### Multiple MCP Servers
```json
{
  "mcpServers": {
    "catalyst-prod": {
      "command": "mcp-client",
      "args": ["--url", "https://prod.yourcompany.com:8443"],
      "description": "Production business systems"
    },
    "catalyst-dev": {
      "command": "mcp-client", 
      "args": ["--url", "http://localhost:8443"],
      "description": "Development environment"
    }
  }
}
```

### Authentication Headers
For servers requiring authentication:
```json
{
  "mcpServers": {
    "catalyst": {
      "command": "mcp-client",
      "args": [
        "--url", "https://your-server.com:8443",
        "--header", "Authorization: Bearer your-token-here"
      ]
    }
  }
}
```

### Connection Timeout
For slow or remote connections:
```json
{
  "mcpServers": {
    "catalyst": {
      "command": "mcp-client",
      "args": [
        "--url", "http://localhost:8443",
        "--timeout", "30"
      ]
    }
  }
}
```

## Usage Examples

### Business Intelligence Queries
```
You: Show me the top 10 customers by revenue this quarter

Claude: I'll query the analytics database for the top customers by revenue this quarter.

[Uses postgresql_analytics_revenue_analysis tool]

Here are your top 10 customers by revenue for Q4 2024:
1. ACME Corp - $125,000
2. Tech Solutions Inc - $98,500
...
```

### DevOps Operations
```
You: Check the status of our main application deployment

Claude: I'll check the deployment status using the GitHub DevOps pack.

[Uses github_devops_deployment_status tool]

Current deployment status:
- Production: Healthy (v2.1.3)
- Staging: Deploying (v2.1.4) - 75% complete
- Last deployment: 2 hours ago
```

### System Monitoring
```
You: Are there any critical alerts in our infrastructure?

Claude: Let me check the monitoring systems for any critical alerts.

[Uses monitoring tools from relevant packs]

Current status:
- 0 critical alerts
- 2 warnings (high CPU on web-server-03)
- All core services operational
```

## Troubleshooting

### MCP Server Not Found
**Error**: "Failed to connect to MCP server"

**Solutions**:
1. Verify server is running: `curl http://localhost:8443/health`
2. Check firewall/network connectivity
3. Confirm URL and port are correct
4. Review server logs: `docker-compose logs catalyst-mcp`

### Configuration Not Loaded
**Issue**: No knowledge packs visible in Claude Desktop

**Solutions**:
1. Verify configuration file syntax (valid JSON)
2. Restart Claude Desktop completely
3. Check configuration file location is correct
4. Clear Claude Desktop cache (if needed)

### Connection Timeout
**Issue**: Commands timeout or fail intermittently

**Solutions**:
1. Add timeout parameter to configuration
2. Check network latency to server
3. Verify server performance and resources
4. Consider local deployment for better performance

### Permission Denied
**Issue**: Tools fail with permission errors

**Solutions**:
1. Verify environment variables are set correctly
2. Check API credentials and permissions
3. Review pack-specific documentation
4. Test pack connections independently

## Security Considerations

### Network Security
- Use HTTPS for production deployments
- Implement proper firewall rules
- Consider VPN for remote access
- Monitor connection logs

### Access Control
- Implement authentication if exposing publicly
- Use least-privilege API keys
- Regular credential rotation
- Audit tool usage

### Data Privacy
- Be aware of data flowing through Claude Desktop
- Implement appropriate data handling policies
- Consider local deployment for sensitive data
- Review Anthropic's data handling policies

## Performance Tips

### Optimize Response Times
- Deploy MCP server geographically close to users
- Use efficient database queries in packs
- Implement appropriate caching
- Monitor and optimize pack performance

### Reduce Latency
- Prefer local deployment over remote
- Optimize network path to server
- Use connection pooling where applicable
- Cache frequently accessed data

## Next Steps

- **[Custom Clients](custom-clients.md)** - Build custom MCP integrations
- **[Pack Creation](../knowledge-packs/creating-packs.md)** - Create custom business integrations
- **[Production Deployment](../deployment/docker-compose.md)** - Deploy for team use