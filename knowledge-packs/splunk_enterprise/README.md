# Splunk Community Pack - LLM Tool Calling Optimized

Open-source Splunk integration designed for LLM tool calling patterns with clean, modular architecture.

## Architecture Principles

### 🎯 LLM-First Design
- **Discovery over Assumption**: Provides tools to discover what exists rather than assuming common use cases
- **Flexible Execution**: Single `search_events` tool lets LLM construct any search based on discovered context
- **Clean Data Providers**: Transforms return structured JSON without pre-processing - let the LLM analyze

### 🧩 Modular Tool Structure
- **Logical Groupings**: Tools organized by purpose in separate YAML files
- **Focused Transforms**: Each transform module handles one domain area
- **Clean Separation**: Discovery, knowledge objects, system info, and execution clearly separated

## Tool Categories

### Core Search Tool
- **`execute_splunk_search`** - Execute any SPL search query constructed by LLM

### Data Discovery Tools (`tools/data-discovery-tools.yaml`)
- **`list_indexes`** - Discover available data sources
- **`get_sourcetypes`** - Understand data types in indexes  
- **`get_hosts`** - Identify systems in environment
- **`find_data_sources`** - Advanced data source discovery

### Knowledge Objects (`tools/knowledge-objects-tools.yaml`)
- **`get_data_models`** - Find accelerated structures for tstats optimization
- **`get_data_model_structure`** - Detailed model schema for tstats construction
- **`get_event_types`** - Leverage existing event categorization
- **`get_search_macros`** - Reuse established search patterns
- **`get_field_extractions`** - Understand field structure by sourcetype
- **`get_lookup_tables`** - Discover enrichment opportunities

### System Information (`tools/system-info-tools.yaml`)
- **`get_server_info`** - Splunk deployment status and health
- **`get_splunk_apps`** - Installed applications and capabilities
- **`get_user_info`** - Current user context and permissions

### Security Guardrails (`tools/guardrails-tools.yaml`)
- **`validate_search_query`** - Test search query safety and compliance
- **`get_guardrails_config`** - View current security controls configuration
- **`test_data_masking`** - Test data privacy and masking rules

## Workflow Prompts

### Strategic Workflow Categories (`prompts/`)
- **`search-prompts.yaml`** - Core search strategy and planning guidance
- **`dashboard-prompts.yaml`** - Dashboard creation and visualization workflows  
- **`scheduled-search-prompts.yaml`** - Automation and alerting setup guidance
- **`knowledge-objects-prompts.yaml`** - Data model and enrichment workflows
- **`system-diagnostics-prompts.yaml`** - Health monitoring and troubleshooting

## LLM Workflow Pattern

1. **Discover Context**: LLM calls discovery tools to understand available data
2. **Leverage Knowledge**: Uses knowledge object tools to find existing patterns
3. **Construct Search**: Builds appropriate SPL using discovered information
4. **Execute**: Uses `execute_splunk_search` with constructed query
5. **Analyze**: Processes structured results to answer user questions

## Example LLM Interaction

```
User: "Show me authentication failures from the last hour"

LLM Process:
1. Calls `list_indexes` → Finds 'security', 'windows', 'linux' indexes
2. Calls `get_event_types` → Discovers 'failed_login' eventtype exists
3. Calls `execute_splunk_search` with: 'eventtype="failed_login" earliest=-1h'
4. Analyzes structured results and provides insights
```

## Transform Architecture

### Clean Data Extraction
- **`transforms/search.py`** - Process oneshot search results
- **`transforms/discovery.py`** - Extract environment information  
- **`transforms/knowledge.py`** - Process knowledge object data
- **`transforms/system.py`** - Extract system status and configuration

### Key Features
- Structured JSON output optimized for LLM consumption
- Error handling with helpful context
- Field type detection and schema inference
- Usage guidance and examples included in responses

## Benefits Over Traditional Approaches

### ✅ LLM Strengths Leveraged
- **Adaptive Queries**: LLM constructs searches based on actual available data
- **Context Awareness**: Uses existing knowledge objects and patterns
- **Intelligent Analysis**: LLM finds patterns in raw data rather than pre-processed summaries

### ✅ Flexible and Extensible  
- **No Hardcoded Assumptions**: Works with any Splunk environment configuration
- **Reusable Logic**: Leverages existing macros, event types, and data models
- **Performance Optimized**: Automatically uses accelerated data models when available

### ✅ Clean Architecture
- **Modular Design**: Easy to maintain and extend
- **Focused Tools**: Each tool has a single, clear purpose
- **Professional Naming**: Clean, descriptive function and file names

## Configuration

### Environment Variables
```bash
SPLUNK_URL=https://your-splunk-instance:8089
SPLUNK_USER=your-splunk-username
SPLUNK_PASSWORD=your-splunk-password
```

### Connection Settings
- **Authentication**: Basic authentication (username/password)
- **Timeout**: 30 seconds default
- **SSL Verification**: Configurable (disabled by default for dev environments)

## Usage Notes

### For LLM Tool Calling
- Start with discovery tools to understand the environment
- Use knowledge object tools to leverage existing configurations  
- Construct targeted searches based on discovered information
- Let the LLM analyze raw structured results

### Performance Considerations
- Discovery tools are lightweight and can be called frequently
- Use `get_data_models` to identify tstats optimization opportunities
- Leverage existing `event_types` and `search_macros` for consistency
- Results are automatically limited to prevent excessive token usage

This open-source architecture provides a solid foundation for intelligent Splunk analysis powered by modern LLM capabilities.

## Community Contribution

This pack is built with love for the cybersecurity community. It represents our vision of what AI-powered security operations should look like. Contributions, feedback, and improvements are welcome!