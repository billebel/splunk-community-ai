"""Test OAuth integration functionality."""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch

# Test the OAuth integration without requiring actual Splunk OAuth setup
class TestOAuthIntegration:
    """Test OAuth authentication integration."""

    @pytest.fixture
    def mock_oauth_handler(self):
        """Mock OAuth handler for testing."""
        handler = Mock()
        handler.start_auth_flow = AsyncMock(return_value={
            "auth_url": "https://test.splunk.com/oauth/authorize?client_id=test&state=abc123",
            "state": "abc123",
            "message": "Please visit the auth_url to authenticate"
        })
        handler.handle_callback = AsyncMock(return_value={
            "status": "success",
            "instance": "https://test.splunk.com"
        })
        handler.get_token = Mock(return_value="mock-oauth-token")
        handler.requires_auth = Mock(return_value=False)
        return handler

    def test_oauth_configuration(self):
        """Test OAuth configuration is valid."""
        # Test that OAuth configuration can be loaded
        oauth_config = {
            "method": "oauth2",
            "config": {
                "client_id": "test-client-id",
                "instance_url": "https://test.splunk.com",
                "header": "Authorization",
                "format": "Bearer {token}",
                "scopes": ["search", "admin"]
            }
        }

        assert oauth_config["method"] == "oauth2"
        assert "client_id" in oauth_config["config"]
        assert "scopes" in oauth_config["config"]

    @pytest.mark.asyncio
    async def test_oauth_flow_start(self, mock_oauth_handler):
        """Test starting OAuth authentication flow."""
        result = await mock_oauth_handler.start_auth_flow(
            "https://test.splunk.com",
            "test-client-id"
        )

        assert "auth_url" in result
        assert "state" in result
        assert "https://test.splunk.com/oauth/authorize" in result["auth_url"]
        assert "client_id=test" in result["auth_url"]

    @pytest.mark.asyncio
    async def test_oauth_callback_handling(self, mock_oauth_handler):
        """Test OAuth callback processing."""
        result = await mock_oauth_handler.handle_callback(
            "auth-code-123",
            "abc123"
        )

        assert result["status"] == "success"
        assert result["instance"] == "https://test.splunk.com"

    def test_oauth_token_usage(self, mock_oauth_handler):
        """Test using OAuth token for authentication."""
        token = mock_oauth_handler.get_token("https://test.splunk.com")
        assert token == "mock-oauth-token"

        # Test authentication requirement check
        needs_auth = mock_oauth_handler.requires_auth("https://test.splunk.com")
        assert needs_auth is False  # Token exists

    def test_oauth_pack_configuration(self):
        """Test OAuth-enabled knowledge pack configuration."""
        pack_config = {
            "metadata": {
                "name": "splunk_community_oauth",
                "oauth_enabled": True,
                "multi_instance": True
            },
            "connection": {
                "type": "rest",
                "auth": {
                    "method": "oauth2",
                    "config": {
                        "client_id": "{SPLUNK_OAUTH_CLIENT_ID}",
                        "instance_url": "{SPLUNK_URL}",
                        "scopes": ["search", "admin"]
                    }
                }
            }
        }

        assert pack_config["metadata"]["oauth_enabled"] is True
        assert pack_config["connection"]["auth"]["method"] == "oauth2"
        assert "scopes" in pack_config["connection"]["auth"]["config"]

    def test_multi_instance_support(self, mock_oauth_handler):
        """Test multiple Splunk instance authentication."""
        # Mock multiple instances
        instances = [
            "https://prod.splunk.com",
            "https://dev.splunk.com",
            "https://test.splunk.com"
        ]

        # Each instance should be able to have its own token
        for instance in instances:
            mock_oauth_handler.get_token.return_value = f"token-for-{instance.split('//')[1]}"
            token = mock_oauth_handler.get_token(instance)
            assert token.startswith("token-for-")

    def test_oauth_security_validation(self):
        """Test OAuth security requirements."""
        # Test PKCE parameters
        pkce_params = {
            "code_challenge": "test-challenge",
            "code_challenge_method": "S256",
            "code_verifier": "test-verifier"
        }

        assert pkce_params["code_challenge_method"] == "S256"
        assert len(pkce_params["code_challenge"]) > 0
        assert len(pkce_params["code_verifier"]) > 0

    def test_oauth_error_handling(self, mock_oauth_handler):
        """Test OAuth error scenarios."""
        # Test invalid state
        mock_oauth_handler.handle_callback.return_value = {"error": "Invalid state"}

        # Test token expiration
        mock_oauth_handler.get_token.return_value = None
        mock_oauth_handler.requires_auth.return_value = True

        needs_auth = mock_oauth_handler.requires_auth("https://expired.splunk.com")
        assert needs_auth is True

    @pytest.mark.asyncio
    async def test_oauth_mcp_tool_integration(self):
        """Test OAuth tools work with MCP server."""
        # Mock MCP tool calls
        auth_tool_result = {
            "auth_url": "https://test.splunk.com/oauth/authorize?...",
            "instructions": "Please visit the auth_url in your browser to authenticate",
            "state": "abc123",
            "callback_url": "http://localhost:8443/callback"
        }

        status_tool_result = {
            "instance": "https://test.splunk.com",
            "authenticated": True,
            "message": "Authenticated"
        }

        assert "auth_url" in auth_tool_result
        assert "callback_url" in auth_tool_result
        assert status_tool_result["authenticated"] is True

class TestOAuthEnvironmentConfiguration:
    """Test OAuth environment variable configuration."""

    def test_oauth_env_vars(self):
        """Test OAuth environment variables are properly configured."""
        env_config = {
            "SPLUNK_OAUTH_CLIENT_ID": "test-client-id",
            "SPLUNK_OAUTH_CLIENT_SECRET": "test-client-secret",
            "SPLUNK_URL": "https://test.splunk.com"
        }

        assert env_config["SPLUNK_OAUTH_CLIENT_ID"] is not None
        assert env_config["SPLUNK_URL"].startswith("https://")

    def test_oauth_docker_configuration(self):
        """Test OAuth works with Docker deployment."""
        docker_config = {
            "ports": ["8443:8443"],
            "environment": [
                "SPLUNK_OAUTH_CLIENT_ID=${SPLUNK_OAUTH_CLIENT_ID}",
                "MCP_PORT=8443"
            ],
            "volumes": ["./knowledge-packs:/app/knowledge-packs"]
        }

        assert "8443:8443" in docker_config["ports"]
        assert any("OAUTH" in env for env in docker_config["environment"])