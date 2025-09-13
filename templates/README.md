# Authentication Template Files

This directory contains template configurations for different authentication methods supported by the Splunk Community AI platform.

## Directory Structure

```
templates/
├── pack/                   # Knowledge Pack authentication templates
│   ├── pack.template.basic.yaml        # Basic username/password authentication
│   ├── pack.template.token.yaml        # Splunk token authentication
│   └── pack.template.passthrough.yaml  # User credential forwarding
│
└── librechat/             # LibreChat configuration templates
    ├── librechat.template.basic.yaml        # Basic auth LibreChat config
    ├── librechat.template.token.yaml        # Token auth LibreChat config
    └── librechat.template.passthrough.yaml  # Passthrough auth LibreChat config
```

## Authentication Methods

### 1. Basic Authentication (`basic`)
- **Use Case**: Development, testing, shared service accounts
- **Security**: Username and password stored in environment variables
- **Files**: 
  - `pack/pack.template.basic.yaml`
  - `librechat/librechat.template.basic.yaml`

### 2. Token Authentication (`token`)
- **Use Case**: Production deployments, service accounts
- **Security**: Splunk authentication token with custom header format
- **Header Format**: `Authorization: Splunk <token>`
- **Files**:
  - `pack/pack.template.token.yaml`
  - `librechat/librechat.template.token.yaml`

### 3. Passthrough Authentication (`passthrough`)
- **Use Case**: Multi-user environments, enterprise SSO integration
- **Security**: Each user's credentials forwarded from AI client
- **Files**:
  - `pack/pack.template.passthrough.yaml`
  - `librechat/librechat.template.passthrough.yaml`

## How Templates Are Used

The deployment scripts (`scripts/deploy.sh` and `scripts/deploy.bat`) automatically copy the appropriate template files based on the authentication method selected during setup:

1. User selects authentication method during deployment
2. Script copies corresponding pack template to `knowledge-packs/splunk_enterprise/pack.yaml`
3. Script copies corresponding LibreChat template to `librechat.yaml`
4. Environment variables are configured in `.env` file

## Template Customization

To customize templates for your environment:

1. **Do not modify template files directly** - they are overwritten during updates
2. Instead, copy the template you need and modify the copy
3. Update deployment scripts to use your custom templates if needed

## Environment Variables

Each authentication method requires different environment variables:

### Basic Authentication
- `SPLUNK_URL`: Splunk server URL (e.g., https://splunk:8089)
- `SPLUNK_USER`: Splunk username
- `SPLUNK_PASSWORD`: Splunk password
- `SPLUNK_AUTH_METHOD`: Set to "basic"

### Token Authentication
- `SPLUNK_URL`: Splunk server URL
- `SPLUNK_TOKEN`: Splunk authentication token
- `SPLUNK_AUTH_METHOD`: Set to "token"

### Passthrough Authentication
- `SPLUNK_URL`: Splunk server URL
- `SPLUNK_AUTH_METHOD`: Set to "passthrough"
- User credentials provided by MCP client at runtime

## Testing

Templates are validated by automated tests in:
- `tests/authentication/test_auth_methods.py`
- `tests/deployment/test_configuration.py`
- `knowledge-packs/splunk_enterprise/tests/test_pack_configuration.py`

Run tests with: `pytest tests/authentication/ -v`