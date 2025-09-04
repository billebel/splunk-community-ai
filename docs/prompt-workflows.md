# AI System Prompts Guide

The pack includes 5 categories of system prompts that tell the AI assistant how to behave when handling different types of requests. These are the "🎯 START HERE" tools you see referenced throughout the pack.

## How the System Prompts Work

Instead of just giving the AI a bunch of tools and hoping it figures out the right approach, we provide strategic system prompts that define:
- **Execution strategies** - When to confirm vs execute immediately
- **Tool ordering** - Which tools to use in what sequence  
- **Best practices** - Performance, security, and safety guidelines
- **Ready-to-use queries** - Common SPL patterns for typical requests

## The 5 System Prompt Categories

### 🔍 Search Strategy (`search-prompts.yaml`)
**What it tells the AI:** How to handle search requests efficiently and safely

**Key behaviors it defines:**
- Use `find_data_sources` first for common requests (gets ready-to-use search patterns)
- Execute immediately for standard searches ≤4 hours, ≤100 results
- Always confirm first for expensive operations (>4 hours, >500 results, no index filters)
- Include performance best practices (index filters, specific time ranges)

**Example decision logic:** "For authentication failures → use find_data_sources → get pre-built eventtype pattern → execute with user's time range"

### 📊 Dashboard Analysis (`dashboard-prompts.yaml`)  
**What it tells the AI:** How to handle dashboard-related requests efficiently

**Key behaviors it defines:**
- Execute immediately for basic dashboard inventory (titles, authors, apps)
- Run format detection queries (Classic vs Studio) without confirmation
- For analysis requests → execute analysis queries and present actionable findings
- Include ready-to-use queries for dashboard discovery and troubleshooting

**Example decision logic:** "Dashboard performance issue → run analysis queries → identify expensive searches → provide optimization recommendations"

### ⏰ Scheduled Search Management (`scheduled-search-prompts.yaml`)
**What it tells the AI:** How to analyze and manage scheduled searches and alerts

**Key behaviors it defines:**
- Immediate execution for search inventory and basic analysis
- Systematic approach to performance optimization
- Cost analysis with actionable recommendations
- Security validation for potentially dangerous scheduled searches

**Example decision logic:** "Alert performance issue → analyze search efficiency → check scheduling conflicts → recommend optimization steps"

### 📋 Knowledge Objects (`knowledge-objects-prompts.yaml`) 
**What it tells the AI:** How to discover and leverage Splunk's knowledge objects

**Key behaviors it defines:**
- Start with discovery to understand what knowledge objects exist
- Provide optimization recommendations using existing data models
- Execute searches immediately for knowledge object inventory
- Guide creation of new knowledge objects with best practices

**Example decision logic:** "User wants correlation search → discover data models → suggest tstats approach → provide optimized SPL"

### 🔧 System Diagnostics (`system-diagnostics-prompts.yaml`)
**What it tells the AI:** How to systematically diagnose Splunk system health

**Key behaviors it defines:**
- Execute diagnostic queries immediately (system health, apps, users)
- Include ready-to-use diagnostic SPL queries in responses
- Systematic approach: server health → resource usage → app management → user access
- Present findings with clear status indicators (✅ ⚠️ ❌)

**Example decision logic:** "System health check → run server info query → analyze resource usage → check license status → report with actionable insights"

## How AI Uses These System Prompts

The prompts are loaded into the AI's system context to guide its behavior:

1. **AI classifies the request type** (search, dashboard, diagnostic, etc.)
2. **Applies the relevant system prompt** to determine approach
3. **Follows the defined execution rules** (when to confirm vs execute immediately)
4. **Uses the recommended tool ordering** for efficiency
5. **Includes ready-to-use SPL** from the prompt when appropriate

## Examples of AI Decision-Making

### Search Request Processing
```
User: "Look for suspicious PowerShell activity"

AI system prompt logic (search-prompts.yaml):
1. This is a common security request → use find_data_sources first
2. Get pre-built PowerShell detection patterns
3. Time range not specified → confirm scope before expensive search
4. Apply performance best practices → add index filters
5. Execute with constructed SPL including ready-to-use patterns
```

### Dashboard Analysis Request  
```
User: "Why is this dashboard so slow?"

AI system prompt logic (dashboard-prompts.yaml):
1. This is performance analysis → execute diagnostic queries immediately
2. Run built-in dashboard analysis SPL from the prompt
3. Present findings with actionable optimization recommendations
4. No confirmation needed for read-only diagnostic operations
```

## What's Working and What's Not

### ✅ What seems to work well
- Discovery-first approach prevents assumptions
- Step-by-step guidance reduces errors
- Security-specific context helps AI make better choices
- Leveraging existing Splunk knowledge objects

### 🤔 What we're still figuring out
- How detailed should the AI guidance be?
- Different AI models interpret prompts differently 
- Balance between structured behavior and flexibility
- Optimal confirmation thresholds for different operations

### 🚧 Areas for improvement
- More adaptive execution rules based on user expertise
- Better error handling when operations fail
- Environment-specific prompt customization
- More sophisticated decision logic

## Customizing System Prompts

Want to modify how the AI behaves? The prompt files are in `knowledge-packs/splunk_enterprise/prompts/`. Each contains YAML with system prompt templates.

Basic structure:
```yaml
prompts:
  guided_search:
    name: "🎯 START HERE: Search Strategy"
    description: "System prompt that defines AI behavior for search requests"
    template: |
      You are a Splunk Search Assistant...
      
      ## EXECUTION RULES
      **Execute Immediately:**
      - Standard searches ≤ 4 hours
      **Always Confirm First:**  
      - Time ranges > 4 hours
```

We're still learning the best patterns here. If you have ideas or find better approaches, please share them with us!