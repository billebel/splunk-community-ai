# Knowledge Pack Creation Guide

## Overview

Knowledge Packs are YAML-based configurations that define tools, prompts, and resources for the Catalyst MCP server.

## Pack Structure

### Directory Layout

```
knowledge-packs/
└── your-pack-name/
    ├── pack.yaml           # Pack metadata and structure
    ├── tools/              # Tool definitions
    │   ├── list-tools.yaml
    │   ├── search-tools.yaml
    │   └── admin-tools.yaml
    ├── prompts/            # Prompt templates
    │   └── system-prompts.yaml
    ├── resources/          # Static resources
    │   └── documentation.yaml
    └── transforms/         # Transform functions
        ├── data-transforms.py
        ├── format-transforms.js
        └── filter-transforms.jq
```

## Pack Definition (pack.yaml)

### Basic Structure

```yaml
name: "your-pack-name"
version: "1.0.0"
description: "Essential tools for Your Domain"
author: "Your Organization"
license: "Commercial"

structure:
  type: "modular"
  tools_dir: "tools"
  prompts_dir: "prompts"
  resources_dir: "resources"
  transforms_dir: "transforms"

dependencies:
  python: ">=3.8"
  requests: ">=2.25.0"

metadata:
  domain: "your-domain"
  tags: ["api", "management", "monitoring"]
  icon: "🔧"
```

### Configuration Options

```yaml
# API Configuration
api:
  base_url: "${BASE_URL}"
  authentication:
    type: "basic"
    username: "${API_USER}"
    password: "${API_PASSWORD}"
  ssl_verify: false
  timeout: 30

# Tool Defaults
defaults:
  pagination:
    default_count: 20
    max_count: 100
  output_format: "json"
  rate_limit: 10
```

## Tool Definition

### Tool Types

#### List Tools
Return collections of items with pagination:

```yaml
tools:
  list_items:
    type: "list"
    description: "List all items"
    endpoint: "/api/v1/items"
    method: "GET"
    
    parameters:
      - name: "count"
        type: "integer"
        required: false
        default: 20
        min_value: 1
        max_value: 100
        description: "Maximum items to return"
        
      - name: "offset"
        type: "integer"
        required: false
        default: 0
        min_value: 0
        description: "Starting position for pagination"
        
      - name: "category"
        type: "string"
        required: false
        enum: ["active", "inactive", "pending"]
        description: "Filter by item category"
    
    query_params:
      count: "{count}"
      offset: "{offset}"
      filter: "{category}"
      format: "json"
    
    transform:
      type: "python"
      file: "../transforms/item-transforms.py"
      function: "transform_item_list"
```

#### Details Tools
Get specific item information:

```yaml
  get_item_details:
    type: "details"
    description: "Get detailed item information"
    endpoint: "/api/v1/items/{item_id}"
    method: "GET"
    
    parameters:
      - name: "item_id"
        type: "string"
        required: true
        description: "Unique item identifier"
        
      - name: "include_metadata"
        type: "boolean"
        required: false
        default: true
        description: "Include extended metadata"
    
    path_params:
      item_id: "{item_id}"
    
    query_params:
      metadata: "{include_metadata}"
      format: "json"
```

#### Search Tools
Execute queries with multi-step execution:

```yaml
  search_items:
    type: "search"
    description: "Search items with custom query"
    endpoint: "/api/v1/search/jobs"
    method: "POST"
    
    parameters:
      - name: "query"
        type: "string"
        required: true
        description: "Search query string"
        
      - name: "time_range"
        type: "string"
        required: false
        default: "-24h"
        description: "Time range for search"
        
      - name: "max_results"
        type: "integer"
        required: false
        default: 100
        description: "Maximum results"
    
    execution_steps:
      - name: "create_search"
        method: "POST"
        endpoint: "/api/v1/search/jobs"
        form_data:
          query: "{query}"
          earliest: "{time_range}"
          count: "{max_results}"
        response_key: "job_id"
        
      - name: "get_results"
        method: "GET"
        endpoint: "/api/v1/search/jobs/{job_id}/results"
        query_params:
          format: "json"
    
    transform:
      type: "jq"
      file: "../transforms/search-results.jq"
```

#### Execute Tools
Perform actions or operations:

```yaml
  restart_service:
    type: "execute"
    description: "Restart a service"
    endpoint: "/api/v1/services/{service_name}/restart"
    method: "POST"
    
    parameters:
      - name: "service_name"
        type: "string"
        required: true
        description: "Name of service to restart"
        
      - name: "force"
        type: "boolean"
        required: false
        default: false
        description: "Force restart even if busy"
    
    path_params:
      service_name: "{service_name}"
    
    form_data:
      force: "{force}"
    
    transform:
      type: "template"
      template: |
        ## Service Restart Result
        
        **Service:** {{ service_name }}
        **Status:** {{ status }}
        **Message:** {{ message }}
        **Timestamp:** {{ timestamp }}
```

## Transform Functions

### Python Transforms

```python
# transforms/item-transforms.py
def transform_item_list(data, variables=None):
    """Transform API response to clean item list."""
    items = data.get('items', [])
    
    return [
        {
            "id": item.get('id'),
            "name": item.get('name'),
            "category": item.get('category'),
            "status": item.get('status'),
            "last_updated": item.get('updated_at'),
            "summary": f"{item.get('name')} - {item.get('status')}"
        }
        for item in items
    ]

def validate_item_id(item_id):
    """Validate item ID format."""
    import re
    return re.match(r'^[a-zA-Z0-9-_]+$', item_id) is not None
```

### JavaScript Transforms

```javascript
// transforms/format-transforms.js
function formatItemData(data, variables) {
    return data.items.map(item => ({
        id: item.id,
        displayName: `${item.name} (${item.category})`,
        status: item.status.toUpperCase(),
        metadata: {
            created: new Date(item.created_at).toISOString(),
            updated: new Date(item.updated_at).toISOString()
        },
        summary: `${item.name} - Active since ${item.created_at}`
    }));
}
```

### jq Transforms

```jq
# transforms/search-results.jq
.results[] | {
  id: .id,
  title: .title,
  score: .relevance_score,
  timestamp: .created_at,
  excerpt: .description[:100] + "...",
  metadata: {
    category: .category,
    tags: .tags,
    author: .author
  },
  summary: "\(.title) (score: \(.relevance_score))"
}
```

### Template Transforms

```yaml
transform:
  type: "template"
  template: |
    ## {{ title }}
    
    **Status:** {{ status }}
    **Items Found:** {{ results|length }}
    
    {% for item in results %}
    ### {{ item.name }}
    - **ID:** {{ item.id }}
    - **Category:** {{ item.category }}
    - **Status:** {{ item.status }}
    
    {% endfor %}
```

## Prompts Definition

```yaml
# prompts/system-prompts.yaml
prompts:
  domain_expert:
    name: "Domain Expert Assistant"
    description: "Expert assistant for your domain operations"
    content: |
      You are an expert assistant for {{ domain }} operations.
      
      Available tools:
      {% for tool in tools %}
      - {{ tool.name }}: {{ tool.description }}
      {% endfor %}
      
      Guidelines:
      - Use appropriate tools for user requests
      - Provide clear explanations of actions
      - Follow security best practices
      
  troubleshooting:
    name: "Troubleshooting Guide"
    description: "Step-by-step troubleshooting assistance"
    content: |
      When troubleshooting {{ domain }} issues:
      
      1. **Identify the Problem**
         - Use search tools to find recent errors
         - Check system status and health
      
      2. **Gather Information**
         - List relevant items and configurations
         - Review logs and metrics
      
      3. **Propose Solutions**
         - Suggest specific actions
         - Provide step-by-step instructions
```

## Resources Definition

```yaml
# resources/documentation.yaml
resources:
  api_reference:
    name: "API Reference"
    description: "Complete API documentation"
    type: "uri"
    uri: "https://api.yourdomain.com/docs"
    
  troubleshooting_guide:
    name: "Troubleshooting Guide"
    description: "Common issues and solutions"
    type: "text"
    text: |
      # Common Issues
      
      ## Authentication Errors
      - Check API credentials in .env file
      - Verify user has required permissions
      
      ## Connection Timeouts
      - Increase timeout in pack configuration
      - Check network connectivity
      
  configuration_examples:
    name: "Configuration Examples"
    description: "Sample configurations"
    type: "text"
    text: |
      # Basic Configuration
      BASE_URL=https://api.yourdomain.com
      API_USER=admin
      API_PASSWORD=your_password
```

## Testing Your Pack

### Test Script

```python
#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from catalyst_mcp.packs.modular_loader import ModularPackLoader

def test_pack():
    """Test pack loading and tool creation."""
    pack_path = "knowledge-packs/your-pack-name"
    loader = ModularPackLoader()
    
    try:
        pack = loader.load_pack(pack_path)
        print(f"✓ Pack loaded: {pack.name} v{pack.version}")
        
        tools = loader.create_tools(pack)
        print(f"✓ Created {len(tools)} tools")
        
        for tool_name, tool in tools.items():
            print(f"  - {tool_name}: {tool.description}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_pack()
    sys.exit(0 if success else 1)
```

### Validation

```bash
# Test pack loading
python test_your_pack.py

# Test with MCP server
make restart
curl -X POST http://localhost:8443/mcp -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

## Best Practices

### Security
- Never hardcode credentials in YAML files
- Use environment variable references: `"${API_KEY}"`
- Validate all user inputs in transforms
- Implement rate limiting for expensive operations

### Performance
- Use pagination for all list tools (default: 20, max: 100)
- Prefer JSON output format for token efficiency
- Cache transform functions and compiled templates
- Implement connection pooling for HTTP clients

### Maintainability
- Use descriptive tool and parameter names
- Document all parameters with clear descriptions
- Organize tools into logical YAML files
- Version your packs and maintain changelog

### Error Handling
- Provide meaningful error messages
- Include debugging information in responses
- Handle API timeouts and connection errors
- Validate parameters before API calls