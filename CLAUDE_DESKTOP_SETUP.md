# Claude Desktop MCP Connection Setup

## Quick Test: Connect Claude Desktop to Our MCP Server

### Step 1: Find Your Claude Desktop Config File

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

### Step 2: Add Our MCP Server Configuration

Open the config file and add our server configuration:

```json
{
  "mcpServers": {
    "splunk-community-ai": {
      "transport": {
        "type": "sse",
        "url": "http://localhost:8443/mcp"
      }
    }
  }
}
```

**If you already have other MCP servers configured, just add the "splunk-community-ai" entry inside the existing "mcpServers" object.**

### Step 3: Restart Claude Desktop

Close and reopen Claude Desktop completely for the configuration to take effect.

### Step 4: Test the Connection

1. **Open a new conversation in Claude Desktop**
2. **Look for the MCP indicator** - You should see a small icon or indicator showing MCP tools are available
3. **Test a simple query**: "What tools do you have available for Splunk?"

### Step 5: Expected Results

If working correctly, Claude Desktop should:
- Connect to the MCP server automatically
- Discover and load all 22 Splunk tools
- Show them as available tools in the interface
- Allow you to ask Splunk-related questions

### Troubleshooting

**Connection Issues:**
- Make sure the MCP server is running: `docker compose -f docker-compose.mcp-only.yml ps`
- Check server health: `curl http://localhost:8443/health`
- Check Claude Desktop logs for connection errors

**Tool Discovery Issues:**
- Restart Claude Desktop after config changes
- Check MCP server logs: `docker compose -f docker-compose.mcp-only.yml logs catalyst-mcp`

### What Tools Should Be Available

Claude Desktop should discover these 22 Splunk tools:
- Data discovery tools (indexes, sourcetypes, hosts)
- Search execution tools
- Knowledge object tools (macros, lookups, data models)
- System diagnostic tools
- Security guardrail tools

## Next Steps After Successful Connection

Once Claude Desktop connects successfully:
1. Test basic tool discovery
2. Try a simple Splunk query
3. Test authentication flows
4. Verify security guardrails are working

## Current MCP Server Status

- **URL:** http://localhost:8443/mcp
- **Status:** ✅ Running and healthy
- **Tools:** ✅ 22 tools loaded
- **Knowledge Packs:** ✅ 1 pack (splunk_enterprise)