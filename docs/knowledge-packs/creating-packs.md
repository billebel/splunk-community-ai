# Creating Knowledge Packs

Learn how to create custom knowledge packs for Catalyst MCP Server using the pack builder toolkit.

## Prerequisites

- **[Pack Builder Toolkit](https://pypi.org/project/catalyst-pack-schemas/)** installed
- Basic understanding of the target system (API, database, etc.)
- Python knowledge for custom transforms (optional)

## Installation

```bash
# Install the pack builder toolkit
pip install catalyst-pack-schemas
```

## Quick Start: REST API Pack

### 1. Create Pack Structure

```bash
# Create a new REST API pack
catalyst-packs create crm-integration \
    --type rest \
    --description "CRM system integration" \
    --domain sales
```

This creates:
```
crm-integration/
├── pack.yaml              # Main configuration
├── tools/                 # Tool definitions
├── prompts/               # AI prompts (optional)
├── transforms/            # Data transforms (optional)
└── README.md              # Documentation
```

### 2. Configure Connection

Edit `pack.yaml`:
```yaml
metadata:
  name: crm-integration
  description: "CRM system integration"
  version: "1.0.0"
  domain: sales

connection:
  type: rest
  base_url: "https://api.yourcrm.com/v1"
  auth:
    method: bearer
    token: "${CRM_API_TOKEN}"
  timeout: 30
  rate_limit:
    requests_per_minute: 100
```

### 3. Define Tools

Create `tools/customer-tools.yaml`:
```yaml
customer_search:
  type: search
  description: "Search customers by name, email, or company"
  endpoint: "/customers/search"
  method: "GET"
  parameters:
    query:
      type: string
      description: "Search query"
      required: true
    limit:
      type: integer
      description: "Maximum results"
      default: 10

customer_details:
  type: details
  description: "Get detailed customer information"
  endpoint: "/customers/{customer_id}"
  method: "GET"
  parameters:
    customer_id:
      type: string
      description: "Customer ID"
      required: true
```

### 4. Add Environment Variables

Add to your `.env` file:
```bash
# CRM Integration
CRM_API_TOKEN=your-crm-api-token
```

### 5. Install and Test

```bash
# Copy pack to MCP server
cp -r crm-integration/ /path/to/catalyst/knowledge-packs/

# Restart MCP server to load pack
docker-compose restart catalyst-mcp

# Test with AI chat
# Ask: "Search for customers with 'ACME' in the name"
```

## Pack Types and Examples

### Database Pack
```bash
catalyst-packs create analytics-db \
    --type database \
    --description "Analytics database queries"
```

Example configuration:
```yaml
connection:
  type: database
  engine: postgresql
  host: "${DB_HOST}"
  port: 5432
  database: "${DB_NAME}"
  auth:
    method: basic
    username: "${DB_USER}"
    password: "${DB_PASSWORD}"
```

### File System Pack
```bash
catalyst-packs create document-storage \
    --type filesystem \
    --description "Document storage integration"
```

Example configuration:
```yaml
connection:
  type: filesystem
  engine: s3
  bucket: "${S3_BUCKET}"
  region: "${AWS_REGION}"
  auth:
    method: aws_iam
    config:
      access_key: "${AWS_ACCESS_KEY_ID}"
      secret_key: "${AWS_SECRET_ACCESS_KEY}"
```

## Tool Types Reference

### search
For finding records/items:
```yaml
tool_name:
  type: search
  description: "Search for items"
  endpoint: "/search"
  method: "GET"
  parameters:
    query:
      type: string
      required: true
```

### details  
For retrieving specific records:
```yaml
tool_name:
  type: details
  description: "Get item details"
  endpoint: "/items/{id}"
  method: "GET"
  parameters:
    id:
      type: string
      required: true
```

### list
For listing collections:
```yaml
tool_name:
  type: list
  description: "List all items"
  endpoint: "/items"
  method: "GET"
  parameters:
    limit:
      type: integer
      default: 50
```

### execute
For actions/operations:
```yaml
tool_name:
  type: execute
  description: "Perform action"
  endpoint: "/actions/do-something"
  method: "POST"
  parameters:
    action_data:
      type: object
      required: true
```

## Advanced Features

### Custom Transforms
Create Python transforms for data processing:

`transforms/customer_formatter.py`:
```python
def format_customer_response(response_data):
    """Format raw API response for AI consumption"""
    customers = response_data.get('data', [])
    
    formatted = []
    for customer in customers:
        formatted.append({
            'name': customer['full_name'],
            'company': customer['company_name'],
            'email': customer['primary_email'],
            'status': customer['account_status']
        })
    
    return formatted
```

Reference in tool definition:
```yaml
customer_search:
  type: search
  # ... other config ...
  transform: "transforms/customer_formatter.py:format_customer_response"
```

### AI Prompts
Define context-aware prompts in `prompts/sales-prompts.yaml`:
```yaml
customer_analysis:
  description: "Analyze customer data for sales insights"
  prompt: |
    You are a sales analyst. When analyzing customer data:
    1. Focus on engagement patterns
    2. Identify upsell opportunities  
    3. Note any red flags or churn risks
    4. Provide actionable recommendations
    
    Customer data: {customer_data}
```

## Validation

### Validate Pack Structure
```bash
# Validate your pack
catalyst-packs validate crm-integration/

# Expected output:
# ✅ Pack structure valid
# ✅ All tool definitions valid  
# ✅ Connection configuration valid
```

### Test Connection
```bash
# Test connection (if pack supports it)
catalyst-packs test-connection crm-integration/
```

## Best Practices

### 1. Security
- Use environment variables for all credentials
- Implement read-only operations when possible
- Add rate limiting to prevent API abuse
- Validate all input parameters

### 2. Naming Conventions
- Use descriptive pack names: `salesforce-crm` not `sf`
- Prefix tool names with category: `customer_search`, `order_create`
- Use consistent parameter naming across tools

### 3. Documentation
- Include comprehensive README with examples
- Document all environment variables required
- Provide sample API responses in comments

### 4. Error Handling
- Define clear error responses
- Implement graceful degradation
- Add timeout configurations

## Deployment

### 1. Development Testing
```bash
# Copy to development location
cp -r my-pack/ /path/to/catalyst/knowledge-packs/my-pack/

# Restart server
docker-compose restart catalyst-mcp
```

### 2. Production Deployment  
```bash
# Validate pack thoroughly
catalyst-packs validate my-pack/ --strict

# Deploy with proper environment variables
# Use Docker secrets or secure configuration management
```

## Next Steps

- **[Pack Reference](pack-reference.md)** - Complete YAML specification
- **[Examples](examples.md)** - Real-world pack implementations
- **[Troubleshooting](../troubleshooting/common-issues.md)** - Common issues and solutions