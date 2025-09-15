# OAuth Setup Guide for Splunk Community AI

This guide explains how to set up OAuth authentication for secure Splunk access without storing passwords.

## Overview

OAuth authentication provides several benefits:
- **No stored passwords** - More secure than basic authentication
- **Multi-instance support** - Authenticate to multiple Splunk instances
- **User control** - Users can revoke access at any time
- **Dynamic authentication** - Works with any OAuth-enabled Splunk instance

## Prerequisites

### 1. Splunk App with OAuth Support

You need a Splunk app configured for OAuth. This can be:
- A custom Splunk app you've created
- An existing app with OAuth capabilities
- Splunk Cloud OAuth configuration

### 2. OAuth Client Configuration

In your Splunk instance, you need:
1. **Client ID** - Identifies your application
2. **Client Secret** - Authenticates your application (optional for public clients)
3. **Redirect URI** - Set to `http://localhost:8443/callback`

## Setup Steps

### 1. Configure Splunk OAuth App

In Splunk Web:
1. Go to **Settings > Server Settings > OAuth Apps**
2. Create a new OAuth app or configure existing one:
   - **App Name**: "Catalyst MCP Integration"
   - **Redirect URI**: `http://localhost:8443/callback`
   - **Scopes**: `search`, `admin` (or as needed)
3. Note the **Client ID** generated

### 2. Update Environment Configuration

Add OAuth settings to your `.env` file:
```bash
# OAuth Configuration
SPLUNK_OAUTH_CLIENT_ID=your-client-id-here
SPLUNK_OAUTH_CLIENT_SECRET=your-client-secret-here  # Optional
```

### 3. Use OAuth Knowledge Pack

Copy the OAuth-enabled pack:
```bash
cp knowledge-packs/splunk_enterprise/pack-oauth.yaml knowledge-packs/splunk_enterprise/pack.yaml
```

Or create a new OAuth-specific pack directory.

### 4. Start the Application

Run with OAuth support:
```bash
docker-compose up -d
```

## Using OAuth Authentication

### In LibreChat Web Interface

1. **Start a conversation** about Splunk
2. **AI will prompt for authentication** when needed
3. **Provide your instance details**:
   - Splunk URL: `https://your-company.splunkcloud.com`
   - Client ID: `your-oauth-client-id`
4. **Click the authentication URL** provided by the AI
5. **Complete OAuth flow** in your browser
6. **Return to LibreChat** - AI can now access your Splunk

### Example Conversation

```
User: "Search my Splunk for failed login attempts"

AI: "I need to authenticate to your Splunk instance first. Let me check your auth status."

AI: "You're not authenticated yet. I'll start the OAuth flow."

AI: "Please provide:
1. Your Splunk instance URL
2. Your OAuth client ID"

User: "https://company.splunkcloud.com and client ID abc123"

AI: "Please visit this URL to authenticate: https://company.splunkcloud.com/oauth/authorize?..."

User: [Completes OAuth in browser]

AI: "Authentication successful! Now searching for failed logins..."
```

### Multiple Instances

You can authenticate to multiple Splunk instances:
- Production: `https://prod.splunkcloud.com`
- Development: `https://dev.splunk.local`
- Testing: `https://test.splunk.company.com`

The AI will ask which instance to use for each request.

## Security Features

### Token Management
- **Automatic expiration** - Tokens expire based on Splunk configuration
- **Secure storage** - Tokens stored in memory, not persisted
- **Per-instance isolation** - Each instance has separate authentication

### Privacy Protection
- **No password storage** - Passwords never stored or logged
- **User control** - Users control what instances to authenticate with
- **Revocable access** - Users can revoke tokens through Splunk

### PKCE Support
- **Proof Key for Code Exchange** - Enhanced security for public clients
- **Dynamic challenge/verifier** - Each auth flow uses unique codes
- **Prevents code interception** - Additional layer of protection

## Troubleshooting

### Common Issues

1. **"Invalid client ID"**
   - Verify client ID matches Splunk OAuth app configuration
   - Check that OAuth app is enabled in Splunk

2. **"Redirect URI mismatch"**
   - Ensure redirect URI in Splunk app is: `http://localhost:8443/callback`
   - Check that MCP server is running on port 8443

3. **"Authentication timeout"**
   - Complete OAuth flow within time limit (usually 10 minutes)
   - Request new authentication URL if expired

4. **"Token expired"**
   - Re-authenticate using the `authenticate_splunk_instance` tool
   - Check Splunk token expiration settings

### Debug Mode

Enable debug logging:
```bash
LOG_LEVEL=DEBUG docker-compose up
```

Check MCP server logs:
```bash
docker logs catalyst-mcp
```

## Advanced Configuration

### Custom Scopes

Modify the OAuth knowledge pack to request specific scopes:
```yaml
auth:
  config:
    scopes: ["search", "admin", "edit_user"]
```

### Token Refresh

The system automatically handles token refresh when supported by Splunk.

### Enterprise Configuration

For enterprise deployments:
- Use HTTPS for production redirect URIs
- Configure proper SSL certificates
- Set up load balancing for high availability
- Consider token storage persistence for server restarts

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review MCP server logs
3. Verify Splunk OAuth app configuration
4. Test OAuth flow manually using curl/Postman
5. Open an issue on GitHub with logs and configuration details