# Splunk Community MCP Pack

> **Beta Release** - A community contribution to bring Splunk integration to AI assistants via MCP. This is what we think Splunk + AI should look like, and we're sharing it with the community that supported us for 25 years.

## What This Pack Does

A Splunk integration pack that tries to make AI assistants better at working with Splunk data. Instead of just giving AI raw access to APIs, we're experimenting with ways to help it discover what's actually in your environment and use existing Splunk knowledge.

**We built this for cybersecurity professionals** who want to chat with their Splunk data but are tired of AI making dumb queries or missing obvious patterns.

## Why This Pack is Different

### 🎯 Our Experimental Approach  
- **Discovery Over Assumptions** - We're trying to help AI discover what data actually exists rather than guessing
- **Adaptive Queries** - AI tries to construct searches based on what it finds in your environment
- **Let AI Analyze Raw Data** - Instead of pre-processing everything, we let the AI work with structured results

### 🛡️ Security-Focused Design  
- **Built-in Guardrails** - Query validation, resource limits, and safety controls
- **Audit Logging** - Basic interaction logging and access controls
- **Privacy Controls** - Data masking and field filtering capabilities

### 🧩 Modular & Extensible
- **17+ Specialized Tools** - From discovery to execution to diagnostics
- **5 AI Behavior Prompts** - We're experimenting with prompts that try to guide AI behavior
- **Modular Design** - Organized structure for understanding and extension

## Quick Setup

1. **Clone and Configure**
   ```bash
   git clone https://github.com/billebel/splunk-community-ai.git
   cd splunk-community-ai
   cp .env.example .env
   ```

2. **Configure Splunk Connection**
   ```bash
   # Edit .env with your Splunk details (required for all deployments)
   SPLUNK_URL=https://your-splunk.company.com:8089
   SPLUNK_USER=your-service-account
   SPLUNK_PASSWORD=your-password
   ```

3. **Choose Your Deployment**

   **Option A: Full Web Chat Experience**
   ```bash
   # ADDITIONAL REQUIREMENT: Add your AI API key to .env
   ANTHROPIC_API_KEY=your-claude-key  # Required for web chat
   
   # Launch with LibreChat web interface + MCP server
   docker-compose up -d
   ```
   - Chat Interface: http://localhost:3080
   - MCP Endpoint: http://localhost:8443/mcp
   
   **Option B: MCP Server Only** (No API key required)
   ```bash
   # Standalone MCP server for integration with other clients
   docker-compose -f docker-compose.mcp-only.yml up -d
   ```
   - MCP Endpoint: http://localhost:8443/mcp
   - Use with any MCP-compatible client or programmatically
   - **No AI API key needed** - your client provides the AI integration
   
   **Option C: Test with Docker Splunk**
   ```bash
   # Start test Splunk instance first
   docker-compose -f docker-compose.splunk.yml up -d
   # Then use either deployment option above
   ```

4. **Start Analyzing**
   - If using web chat: Ask *"What security data is available in our environment?"*
   - If using MCP-only: Connect your MCP client to `http://localhost:8443/mcp`

## Pack Architecture

### Core Tools by Category

#### 🔍 **Data Discovery** (4 tools)
- `list_indexes` - Find available data repositories
- `get_sourcetypes` - Understand data types and formats
- `get_hosts` - Identify systems and sources
- `find_data_sources` - Data source discovery and mapping

#### 📊 **Knowledge Objects** (6 tools)  
- `get_data_models` - Discover accelerated data structures
- `get_event_types` - Leverage existing categorization
- `get_search_macros` - Reuse established patterns
- `get_field_extractions` - Understand data schemas
- `get_lookup_tables` - Find enrichment opportunities
- `get_data_model_structure` - Deep schema analysis

#### 🔧 **System Information** (3 tools)
- `get_server_info` - Deployment status and health
- `get_splunk_apps` - Installed capabilities
- `get_user_info` - Permissions and context

#### 🛡️ **Security Guardrails** (3 tools)
- `validate_search_query` - Test query safety
- `get_guardrails_config` - View security controls  
- `test_data_masking` - Validate privacy rules

#### ⚡ **Execution Engine** (1 tool)
- `execute_splunk_search` - Run AI-constructed queries

### AI Behavior Prompts

Our pack includes 5 strategic AI behavior prompts that guide how AI assistants interact with Splunk:

#### 🎯 **Search Strategy** - Query Planning and Guidance
- **Fast-track common requests** - Authentication failures, web errors → immediate execution 
- **Discovery shortcuts** - `find_data_sources` provides ready-to-use patterns instead of manual exploration
- **Safety-first execution** - Built-in confirmation rules and resource limits
- **Example guidance**: *"For authentication failures: Use find_data_sources → Execute immediately if ≤4 hours"*

#### 📊 **Dashboard Analysis** - Performance & Security Focus  
- **Format-aware analysis** - Classic XML vs Dashboard Studio detection and optimization
- **Cost optimization** - Identifies high-refresh dashboards and redundant searches
- **Security validation** - Scans for dangerous commands and patterns
- **Example guidance**: *"Execute immediately for basic inventory, confirm for comprehensive scans"*

#### ⏰ **Scheduled Search Management** - Optimization Strategy
- **Collision detection** - Identifies scheduling conflicts with specific time recommendations
- **Cost analysis** - Flags searches without index specification or excessive time ranges  
- **Performance rankings** - Scores searches by resource impact with actionable fixes
- **Example guidance**: *"Cost score >40: Add index filters, reduce time ranges, stagger from :00 minutes"*

#### 🧩 **Knowledge Objects** - Leverage Existing Assets
- **Performance priority** - Data models first (tstats can be significantly faster), then search macros
- **Enrichment discovery** - Lookup tables for context, event types for categorization
- **Usage templates** - Ready-to-use query patterns for each object type
- **Example guidance**: *"For speed: Check accelerated data models first, get tstats examples"*

#### 🔧 **System Diagnostics** - Health & Troubleshooting
- **Resource monitoring** - Memory, license, disk usage with status indicators
- **App management** - Installation status, updates, configuration issues
- **Permission auditing** - User roles, capabilities, access validation
- **Example guidance**: *"Memory >90% = Critical, License near limit = Throttling risk"*

## Real-World Usage

### SOC Analyst - Guided Security Analysis
```
Analyst: "Show me failed authentication events in the last hour"

AI Process with Strategic Guidance:
1. 🎯 Gets Search Strategy → AI receives specific guidance for security searches
   - Fast execution for authentication failures (common pattern)
   - Immediate execution approved for 1-hour timeframe
   - Recommends using find_data_sources for ready-to-use patterns

2. Discovers data efficiently → find_data_sources provides pre-built queries
   - Returns: index=security EventCode=4625 earliest=-1h
   - Includes basic performance and safety considerations

3. Executes with confidence → No discovery phase needed
   - AI uses recommended search immediately
   - Built-in result limits prevent resource issues

4. Analyzes enriched results → "15 failed logins from 3 IPs, targeting 'admin'"
```

### Threat Hunter - Performance-Focused Analysis  
```
Hunter: "Look for suspicious PowerShell activity across endpoints"

AI Process with Knowledge Object Guidance:
1. 🎯 Gets Knowledge Object Strategy → AI learns to leverage accelerated data
   - Recommends checking for data models first
   - Provides ready-to-use tstats query templates

2. Discovers accelerated data models → finds 'Endpoint.Processes' 
   - AI receives: "| tstats count from datamodel=Endpoint.Processes by _time span=1h"
   - Potentially much faster execution than traditional search

3. Applies threat logic with macro shortcuts → uses existing search macros
   - AI finds: `powershell_encoded_command` macro
   - Reuses established detection patterns

4. Correlates with lookup enrichment → adds context automatically
   - Process reputation lookups, IP geolocation
   - Timeline reconstruction with business context
```

### Security Operations - System Health Monitoring
```
Responder: "Check our detection capabilities and system health"

AI Process with System Diagnostics Guidance:
1. 🎯 Gets System Diagnostics Strategy → AI receives health check procedures
   - Server resource analysis queries
   - License compliance validation
   - Security app status verification

2. Executes health assessment:
   - System resources: "✅ Memory: 65% (Normal), License: Valid"
   - Security apps: "✅ 12 security add-ons enabled, 2 updates available"
   - User permissions: "🔑 Full admin access, 47 capabilities enabled"

3. Validates detection readiness:
   - Data model acceleration: "✅ 8 security models accelerated"
   - Scheduled searches: "⚠️ 3 searches in collision window, recommend staggering"

4. Provides actionable recommendations with priority ranking
```

## Deployment Options

This pack supports multiple deployment modes depending on your needs:

### 🌐 **Full Web Experience** (`docker-compose.yml`)
**Best for**: Interactive analysis, demonstrations, proof-of-concepts
- LibreChat web interface with authentication
- User-friendly chat interface for Splunk exploration  
- Built-in guardrails and controlled environment
- Suitable for security teams wanting to experiment with AI + Splunk
- **Requires**: Splunk credentials + AI API key (Claude, OpenAI, etc.)

### 🔌 **MCP Server Only** (`docker-compose.mcp-only.yml`) 
**Best for**: Integration with existing tools, programmatic access, custom clients
- Standalone MCP server without web UI
- Integrate with Claude Desktop, other MCP clients, or custom applications
- Lighter footprint - just the MCP server and pack
- Ideal for developers building on top of the MCP protocol
- **Requires**: Only Splunk credentials (no AI API key needed)

### 🧪 **Development Setup** (`docker-compose.splunk.yml`)
**Best for**: Testing, development, learning Splunk
- Includes a full Splunk Enterprise instance
- Pre-configured with sample data and indexes
- No external Splunk required
- Great for understanding how the pack works

### Integration Examples

**With Claude Desktop:**
```json
{
  "mcpServers": {
    "splunk-community": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-fetch", "http://localhost:8443/mcp"]
    }
  }
}
```

**Programmatic Usage:**
```python
import mcp
client = mcp.connect("http://localhost:8443/mcp")
result = client.call_tool("list_indexes", {})
```

## Security Features

### Built-in Safety Controls
- **Query Complexity Analysis** - Prevents resource-intensive operations
- **Time Range Enforcement** - Automatic limits on search windows  
- **Result Size Limits** - Prevents excessive data retrieval
- **Destructive Command Blocking** - No delete/modify operations allowed
- **Rate Limiting** - Protects Splunk resources from overuse

### Privacy & Compliance
- **Data Masking Rules** - Automatic PII/PHI protection
- **Field Filtering** - Hide sensitive data by role
- **Audit Trail** - Interaction logging and monitoring
- **RBAC Integration** - Respects Splunk user permissions

## Documentation

- **[Pack Architecture](docs/architecture.md)** - How we're trying to make AI assistants smarter
- **[Pack Setup Guide](docs/pack-setup.md)** - Detailed configuration
- **[AI System Prompts Guide](docs/prompt-workflows.md)** - How the 5 AI behavior prompts work
- **[Security Guardrails](docs/security-guardrails.md)** - Safety features and controls
- **[Usage Examples](docs/examples.md)** - Real security team scenarios

## Foundation Projects

Built on open-source tools we're learning with:

- **[Catalyst MCP Server](https://github.com/billebel/catalyst_mcp)** - Handles the MCP integration and chat interface
- **[Catalyst Builder](https://github.com/billebel/catalyst_builder)** - Pack validation and development tools

## Community & Development

### 🤝 We Want Your Input
This is **very early in development** - we're sharing what we've built so far and hoping you'll help us make it better. Your experience and feedback will shape where this goes.

- 🐛 **Found something broken?** → [Tell us about it](https://github.com/billebel/splunk-community-ai/issues)
- 💡 **Have ideas or suggestions?** → [Let's discuss them](https://github.com/billebel/splunk-community-ai/discussions)
- 🛠️ **Want to contribute?** → We'd love your help!

### 🚀 Help Us Extend It
- Try adding new tools in `knowledge-packs/splunk_enterprise/tools/`
- Create custom AI behavior prompts in `prompts/`
- **Try building logic in `transforms/`** - This is where we're experimenting with making AI smarter
- Add discovery patterns, safety rules, and optimization logic
- We're figuring out the best patterns as we go

### 🎯 Ideas We're Exploring
- Better correlation and detection capabilities
- Connections to SOAR platforms
- Support for other SIEM platforms
- More security-focused dashboard templates
- (What would you find useful?)

## Why We Built This

After 25 years in cybersecurity, this community has given us so much. This is our attempt to give something back - sharing what we're learning about making AI work better with security tools. We hope it's useful, and we'd love your help making it better.

## Contributors

### Learning AI-Human Collaboration

**Claude Code** (Anthropic) contributed as a development partner across multiple sessions - an experiment in AI-assisted open source development. Together we worked on architecture, security implementation, testing, and documentation. 

This collaboration helped us explore what's possible when humans and AI work together on complex software projects, but we're still learning:
- **What works well** - AI can help with code patterns, testing, and documentation
- **What's challenging** - Understanding context, making architectural decisions, knowing when we're wrong
- **What we don't know yet** - Long-term maintainability, edge cases, real-world usage patterns

We've documented our approach in **`CLAUDE.md`** - a configuration file that helps AI contributors understand project context and requirements. It's an experiment in making AI collaboration more effective, though we expect this approach will evolve as we learn more.

If you're interested in trying AI-assisted development, our `CLAUDE.md` might be a useful starting point, but expect to adapt it based on what you learn. We're all figuring this out together.

## License

MIT License - Use it, modify it, share it.

---

**Give it a try and let us know what you think!** 

*Questions? Check [our docs](docs/) or [start a conversation](https://github.com/billebel/splunk-community-ai/discussions)*