# Integration Types Guide

This guide covers all supported integration types in the Catalyst MCP Universal Knowledge Pack system.

## Overview

The Catalyst MCP server supports multiple integration types through a unified adapter system. Each integration type provides specialized read-only tools and capabilities for different domains:

- **REST API** - HTTP/HTTPS API integrations (read operations)
- **Database** - SQL and NoSQL database queries and analytics
- **Message Queue** - Message queue monitoring and analysis
- **File System** - File system browsing and analysis
- **SSH/Shell** - Remote system monitoring and information gathering

**Important: MCP Design Principle**
As an MCP (Model Context Protocol) server, Catalyst follows the read-only principle. All tools are designed for monitoring, analysis, and information gathering - not for making destructive changes to systems.

## Supported Integration Types

### 1. REST API Integration (`type: "rest"`)

**Supported Systems:**
- Any HTTP/HTTPS API
- GraphQL endpoints (via POST)
- SOAP services
- Webhook integrations

**Popular REST API Integrations:**

**GitHub DevOps Monitoring** (`github_devops.example`)
- Repository analysis and health metrics
- Issues tracking and lifecycle analysis
- Pull request monitoring and review analytics  
- CI/CD workflow status and performance
- Commit history and contributor analysis
- Security vulnerability assessments
- Release tracking and deployment monitoring

**GitLab Project Management** (`gitlab_devops.example`)
- Project overview and activity monitoring
- Merge request tracking and approval workflows
- CI/CD pipeline analysis and job monitoring
- Environment deployment status
- Issue management and milestone tracking
- User activity and contribution analytics
- Project security and compliance monitoring

**Authentication Methods:**
- Basic authentication
- Bearer token
- API key (header or query parameter)
- OAuth2
- AWS IAM
- Custom headers

**Example Configuration:**
```yaml
connection:
  type: "rest"
  base_url: "https://api.example.com/v1"
  verify_ssl: true
  auth:
    method: "bearer"
    config:
      token: "{API_TOKEN}"
```

**Tool Types:**
- `list` - GET requests returning arrays
- `details` - GET requests for specific resources
- `search` - GET/POST requests with query parameters
- `execute` - Limited to read-only operations only

### 2. Database Integration (`type: "database"`)

**Supported Databases:**

#### SQL Databases:
- **PostgreSQL** (`engine: "postgresql"`)
  - Dependency: `asyncpg>=0.28.0`
  - Default port: 5432
  
- **MySQL** (`engine: "mysql"`)
  - Dependency: `aiomysql>=0.2.0`
  - Default port: 3306

- **SQLite** (`engine: "sqlite"`)
  - Dependency: `aiosqlite>=0.19.0`
  - No host/port required

#### NoSQL Databases:
- **MongoDB** (`engine: "mongodb"`)
  - Dependency: `motor>=3.3.0`
  - Default port: 27017

- **Redis** (`engine: "redis"`)
  - Dependency: `redis>=5.0.0`
  - Default port: 6379

- **Elasticsearch** (`engine: "elasticsearch"`)
  - Dependency: `elasticsearch>=8.0.0`
  - Default port: 9200

**Example Configuration:**
```yaml
connection:
  type: "database"
  engine: "postgresql"
  host: "{DB_HOST}"
  port: 5432
  database: "{DB_NAME}"
  pool_size: 10
  auth:
    method: "basic"
    config:
      username: "{DB_USER}"
      password: "{DB_PASSWORD}"
```

**Tool Types:**
- `query` - SELECT statements and analytics queries
- `list` - Table/collection listings
- `details` - Schema information and database statistics
- Note: Write operations (INSERT/UPDATE/DELETE) are not supported in MCP mode

### 3. Message Queue Integration (`type: "message_queue"`)

**Supported Systems:**
- **RabbitMQ** (`engine: "rabbitmq"`)
  - Dependency: `aio-pika>=9.3.0`
  - Default port: 5672
  
- **Apache Kafka** (`engine: "kafka"`)
  - Dependency: `aiokafka>=0.8.0`
  - Default port: 9092

- **Redis Pub/Sub** (`engine: "redis"`)
  - Dependency: `redis>=5.0.0`
  - Default port: 6379

- **AWS SQS** (`engine: "aws_sqs"`)
  - Dependency: `aioboto3>=12.0.0`

**Example Configuration:**
```yaml
connection:
  type: "message_queue"
  engine: "rabbitmq"
  host: "{RABBITMQ_HOST}"
  port: 5672
  auth:
    method: "basic"
    config:
      username: "{RABBITMQ_USER}"
      password: "{RABBITMQ_PASSWORD}"
```

**Tool Types:**
- `list` - Queue and exchange listings
- `details` - Queue information and statistics
- `execute` - Read-only message peeking (no consumption)
- Note: Message publishing is not supported in MCP mode

### 4. File System Integration (`type: "filesystem"`)

**Supported Storage:**

#### Local Storage:
- **Local File System** (`engine: "local"`)
  - No dependencies
  - Uses `root_path` for base directory

#### Cloud Storage:
- **AWS S3** (`engine: "s3"`)
  - Dependency: `aioboto3>=12.0.0`
  - Requires bucket configuration
  
- **Google Cloud Storage** (`engine: "gcs"`)
  - Dependency: `google-cloud-storage>=2.10.0`
  - Service account authentication

- **Azure Blob Storage** (`engine: "azure"`)
  - Dependency: `azure-storage-blob>=12.18.0`
  - Connection string authentication

#### Remote File Systems:
- **FTP** (`engine: "ftp"`)
  - Dependency: `aioftp>=0.21.0`
  - Basic authentication

- **SFTP** (`engine: "sftp"`)
  - Dependency: `asyncssh>=2.14.0`
  - SSH key authentication

**Example Configuration:**
```yaml
connection:
  type: "filesystem"
  engine: "s3"
  bucket: "{S3_BUCKET}"
  auth:
    method: "aws_iam"
    config:
      access_key: "{AWS_ACCESS_KEY_ID}"
      secret_key: "{AWS_SECRET_ACCESS_KEY}"
      region: "{AWS_REGION}"
```

**Tool Types:**
- `list` - Directory and file listings
- `details` - File metadata and information
- `execute` - File reading and analysis operations
- Note: File write/delete operations are not supported in MCP mode

### 5. SSH/Shell Integration (`type: "ssh"`)

**Supported Engines:**
- **SSH** (`engine: "ssh"`)
  - Dependency: `asyncssh>=2.14.0`
  - Remote command execution
  
- **Local Shell** (`engine: "local"`)
  - No dependencies
  - Local command execution

**Authentication Methods:**
- SSH key authentication (`method: "ssh_key"`)
- Password authentication (`method: "basic"`)
- Certificate-based authentication (`method: "cert"`)

**Example Configuration:**
```yaml
connection:
  type: "ssh"
  engine: "ssh"
  hostname: "{SSH_HOST}"
  username: "{SSH_USER}"
  auth:
    method: "ssh_key"
    config:
      private_key_file: "{SSH_PRIVATE_KEY_FILE}"
      passphrase: "{SSH_KEY_PASSPHRASE}"
```

**Tool Types:**
- `command` - Read-only system monitoring commands
- `execute` - Information gathering scripts
- Note: Commands that modify system state are not supported in MCP mode

## Creating Knowledge Packs

### Pack Structure

Each knowledge pack consists of:
- `pack.yaml` - Main configuration file
- Optional: Additional YAML files for modular organization
- Optional: `transforms/` directory for complex data transformations

### Minimal Pack Example

```yaml
metadata:
  name: "my_integration"
  version: "1.0.0"
  description: "Custom integration pack"
  vendor: "Your Organization"
  license: "MIT"
  domain: "custom"

connection:
  type: "rest"
  base_url: "{API_BASE_URL}"
  auth:
    method: "api_key"
    config:
      key: "{API_KEY}"

tools:
  get_data:
    type: "list"
    description: "Retrieve data from API"
    endpoint: "/data"
    method: "GET"
```

### Environment Variables

All pack configurations support environment variable substitution using `{VARIABLE_NAME}` syntax:

```yaml
# In pack configuration
host: "{DATABASE_HOST}"
password: "{DB_PASSWORD}"

# In your .env file  
DATABASE_HOST=localhost
DB_PASSWORD=secret123
```

### Tool Parameters

Define parameters for dynamic tool execution:

```yaml
tools:
  search_users:
    type: "query"
    description: "Search users by criteria"
    sql: "SELECT * FROM users WHERE created_at > {since_date} LIMIT {limit}"
    parameters:
      - name: "since_date"
        type: "string"
        required: true
        description: "Start date for search"
      - name: "limit"
        type: "integer"
        default: 100
        min_value: 1
        max_value: 1000
        description: "Maximum results"
```

### Response Transformation

Transform responses using multiple engines:

```yaml
tools:
  process_data:
    type: "query"
    sql: "SELECT * FROM complex_table"
    transform:
      type: "jq"
      expression: '.[] | {id: .id, name: .full_name, active: .status == "active"}'
```

Supported transform engines:
- `jq` - JSON query language
- `python` - Python code execution
- `javascript` - JavaScript transformation
- `template` - Jinja2 templates

## Dependencies

### Core Dependencies (Always Required)
```bash
pip install fastmcp httpx python-dotenv jinja2 pyyaml jq
```

### Optional Dependencies by Integration Type

Install only what you need:

```bash
# Database integrations
pip install asyncpg          # PostgreSQL
pip install aiomysql         # MySQL  
pip install aiosqlite        # SQLite
pip install motor            # MongoDB
pip install redis            # Redis
pip install elasticsearch    # Elasticsearch

# Message queues
pip install aio-pika         # RabbitMQ
pip install aiokafka         # Apache Kafka
pip install aioboto3         # AWS SQS

# Cloud storage
pip install aioboto3         # AWS S3
pip install google-cloud-storage  # Google Cloud Storage
pip install azure-storage-blob    # Azure Blob Storage

# File transfer
pip install aioftp           # FTP
pip install asyncssh         # SSH/SFTP

# SSH/Shell
pip install asyncssh         # SSH connections
```

## Configuration Validation

The system automatically validates pack configurations:

```python
from catalyst_mcp.packs.adapters import AdapterFactory

# Validate pack configuration
errors = AdapterFactory.validate_pack_configuration(pack)
if errors:
    print("Configuration errors:")
    for error in errors:
        print(f"- {error}")
```

## Error Handling

Each integration type provides standardized error handling:

```yaml
error_mapping:
  "connection refused": "Unable to connect - check host and port"
  "authentication failed": "Invalid credentials"
  "not found": "Resource does not exist"
```

## Best Practices

### Security
- Use environment variables for sensitive data
- Implement least-privilege access
- Enable SSL/TLS where available
- Use connection pooling for databases
- Implement proper secret rotation

### Performance
- Configure appropriate timeouts
- Use connection pooling for databases
- Implement retry policies
- Consider batch operations for large datasets
- Monitor resource usage

### Reliability
- Implement proper error handling
- Use transactions for critical operations
- Test connection health regularly
- Implement graceful degradation
- Plan for disaster recovery

### Maintainability
- Use descriptive tool names and descriptions
- Document parameter requirements
- Provide usage examples
- Version your knowledge packs
- Test pack configurations

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Install required dependencies
   - Check Python version compatibility

2. **Connection Failures**
   - Verify host/port configuration
   - Check firewall settings
   - Validate credentials

3. **Authentication Errors**
   - Verify environment variables
   - Check credential format
   - Test authentication separately

4. **Permission Errors**
   - Check user privileges
   - Verify resource permissions
   - Review security policies

### Debug Mode

Enable debug logging:
```bash
export MCP_DEBUG=true
export LOG_LEVEL=DEBUG
```

This comprehensive integration system enables you to connect to virtually any system through the unified Catalyst MCP platform.