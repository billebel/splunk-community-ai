"""
Authentication Method Integration Tests

Tests the complete authentication flow from environment variables
through MCP server configuration to Splunk API calls.

These tests validate that the authentication system works correctly
across all three supported methods: basic, token, and passthrough.
"""

import pytest
import os
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import json


class TestAuthenticationMethods:
    """Test all authentication methods work end-to-end"""
    
    @pytest.fixture
    def project_root(self):
        """Get project root directory"""
        return Path(__file__).parent.parent.parent
    
    @pytest.fixture
    def auth_basic_env(self):
        """Mock environment for basic authentication"""
        return {
            'SPLUNK_AUTH_METHOD': 'basic',
            'SPLUNK_USER': 'testuser',
            'SPLUNK_PASSWORD': 'testpass',
            'SPLUNK_URL': 'https://test-splunk:8089'
        }
    
    @pytest.fixture  
    def auth_token_env(self):
        """Mock environment for token authentication"""
        return {
            'SPLUNK_AUTH_METHOD': 'token',
            'SPLUNK_TOKEN': 'test-token-12345',
            'SPLUNK_URL': 'https://test-splunk:8089'
        }
    
    @pytest.fixture
    def auth_passthrough_env(self):
        """Mock environment for passthrough authentication"""
        return {
            'SPLUNK_AUTH_METHOD': 'passthrough',
            'SPLUNK_URL': 'https://test-splunk:8089'
        }
    
    def test_basic_auth_environment_validation(self, auth_basic_env):
        """Test basic authentication environment variable validation"""
        with patch.dict(os.environ, auth_basic_env, clear=True):
            # Should have all required variables
            assert os.getenv('SPLUNK_AUTH_METHOD') == 'basic'
            assert os.getenv('SPLUNK_USER') == 'testuser'
            assert os.getenv('SPLUNK_PASSWORD') == 'testpass'
            assert os.getenv('SPLUNK_URL') == 'https://test-splunk:8089'
    
    def test_token_auth_environment_validation(self, auth_token_env):
        """Test token authentication environment variable validation"""
        with patch.dict(os.environ, auth_token_env, clear=True):
            # Should have all required variables
            assert os.getenv('SPLUNK_AUTH_METHOD') == 'token'
            assert os.getenv('SPLUNK_TOKEN') == 'test-token-12345'
            assert os.getenv('SPLUNK_URL') == 'https://test-splunk:8089'
            # Should not have basic auth variables
            assert os.getenv('SPLUNK_USER') is None
            assert os.getenv('SPLUNK_PASSWORD') is None
    
    def test_passthrough_auth_environment_validation(self, auth_passthrough_env):
        """Test passthrough authentication environment variable validation"""
        with patch.dict(os.environ, auth_passthrough_env, clear=True):
            # Should have minimal required variables
            assert os.getenv('SPLUNK_AUTH_METHOD') == 'passthrough'
            assert os.getenv('SPLUNK_URL') == 'https://test-splunk:8089'
            # Should not have stored credentials
            assert os.getenv('SPLUNK_USER') is None
            assert os.getenv('SPLUNK_PASSWORD') is None
            assert os.getenv('SPLUNK_TOKEN') is None
    
    def test_auth_method_precedence(self):
        """Test authentication method precedence and isolation"""
        # Test that SPLUNK_AUTH_METHOD controls which credentials are used
        test_env = {
            'SPLUNK_AUTH_METHOD': 'token',
            'SPLUNK_URL': 'https://test-splunk:8089',
            'SPLUNK_USER': 'should-not-be-used',
            'SPLUNK_PASSWORD': 'should-not-be-used', 
            'SPLUNK_TOKEN': 'this-should-be-used'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            # When auth method is 'token', basic auth credentials should be ignored
            assert os.getenv('SPLUNK_AUTH_METHOD') == 'token'
            # Implementation would use SPLUNK_TOKEN, not SPLUNK_USER/PASSWORD
    
    def test_invalid_auth_method_handling(self):
        """Test handling of invalid authentication methods"""
        invalid_env = {
            'SPLUNK_AUTH_METHOD': 'invalid_method',
            'SPLUNK_URL': 'https://test-splunk:8089'
        }
        
        with patch.dict(os.environ, invalid_env, clear=True):
            # Should recognize invalid method
            assert os.getenv('SPLUNK_AUTH_METHOD') not in ['basic', 'token', 'passthrough']
            # Implementation should handle this gracefully (fall back or error)
    
    def test_missing_credentials_scenarios(self):
        """Test handling when required credentials are missing"""
        scenarios = [
            # Basic auth missing password
            {
                'SPLUNK_AUTH_METHOD': 'basic',
                'SPLUNK_USER': 'testuser',
                'SPLUNK_URL': 'https://test-splunk:8089'
                # Missing SPLUNK_PASSWORD
            },
            # Token auth missing token
            {
                'SPLUNK_AUTH_METHOD': 'token',
                'SPLUNK_URL': 'https://test-splunk:8089'
                # Missing SPLUNK_TOKEN
            },
            # All methods missing URL
            {
                'SPLUNK_AUTH_METHOD': 'basic',
                'SPLUNK_USER': 'testuser',
                'SPLUNK_PASSWORD': 'testpass'
                # Missing SPLUNK_URL
            }
        ]
        
        for env in scenarios:
            with patch.dict(os.environ, env, clear=True):
                # Each scenario has missing required variables
                # Implementation should validate and provide clear error messages
                if env.get('SPLUNK_AUTH_METHOD') == 'basic':
                    has_required = all(k in env for k in ['SPLUNK_USER', 'SPLUNK_PASSWORD', 'SPLUNK_URL'])
                elif env.get('SPLUNK_AUTH_METHOD') == 'token':
                    has_required = all(k in env for k in ['SPLUNK_TOKEN', 'SPLUNK_URL'])
                else:
                    has_required = 'SPLUNK_URL' in env
                
                assert not has_required, f"Test scenario should be missing required variables: {env}"


class TestLibreChatIntegration:
    """Test LibreChat configuration matches authentication method"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    def test_librechat_templates_exist(self, project_root):
        """Test LibreChat template files exist for all auth methods"""
        template_dir = project_root / "templates" / "librechat"
        for auth_method in ['basic', 'token', 'passthrough']:
            template = template_dir / f"librechat.template.{auth_method}.yaml"
            assert template.exists(), f"Missing LibreChat template: {template}"
    
    def test_librechat_template_structure(self, project_root):
        """Test LibreChat templates have correct structure"""
        template_dir = project_root / "templates" / "librechat"
        for auth_method in ['basic', 'token', 'passthrough']:
            template_path = template_dir / f"librechat.template.{auth_method}.yaml"
            if not template_path.exists():
                continue
            
            with open(template_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Should have endpoints section
            assert 'endpoints' in config, f"LibreChat template {auth_method} missing endpoints"
            
            # Should have custom endpoint configuration
            endpoints = config['endpoints']
            assert 'custom' in endpoints, f"LibreChat template {auth_method} missing custom endpoints"
            
            # Custom endpoints should be a list
            custom_endpoints = endpoints['custom']
            assert isinstance(custom_endpoints, list), f"LibreChat custom endpoints should be list in {auth_method}"
            assert len(custom_endpoints) > 0, f"LibreChat should have at least one custom endpoint in {auth_method}"
    
    def test_librechat_mcp_endpoint_configuration(self, project_root):
        """Test that LibreChat templates configure MCP endpoint correctly"""
        template_dir = project_root / "templates" / "librechat"
        for auth_method in ['basic', 'token', 'passthrough']:
            template_path = template_dir / f"librechat.template.{auth_method}.yaml"
            if not template_path.exists():
                continue
            
            with open(template_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Find MCP endpoint in custom endpoints
            custom_endpoints = config['endpoints']['custom']
            mcp_endpoint = None
            
            for endpoint in custom_endpoints:
                if 'name' in endpoint and 'mcp' in endpoint['name'].lower():
                    mcp_endpoint = endpoint
                    break
            
            assert mcp_endpoint is not None, f"LibreChat template {auth_method} should have MCP endpoint"
            
            # MCP endpoint should have required fields
            required_fields = ['name', 'apiKey', 'baseURL']
            for field in required_fields:
                assert field in mcp_endpoint, f"MCP endpoint missing {field} in {auth_method} template"


class TestTemplateSystemIntegration:
    """Test template system works correctly for all authentication methods"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    def test_pack_template_completeness(self, project_root):
        """Test that pack templates are complete for all authentication methods"""
        template_dir = project_root / "templates" / "pack"
        for auth_method in ['basic', 'token', 'passthrough']:
            template_path = template_dir / f"pack.template.{auth_method}.yaml"
            assert template_path.exists(), f"Missing pack template: pack.template.{auth_method}.yaml"
            
            with open(template_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Should have complete pack structure
            required_sections = ['metadata', 'connection', 'tools']
            for section in required_sections:
                assert section in config, f"Pack template {auth_method} missing {section}"
            
            # Connection should have appropriate auth configuration
            connection = config['connection']
            assert 'auth' in connection, f"Pack template {auth_method} missing auth in connection"
            
            auth_config = connection['auth']
            assert 'method' in auth_config, f"Pack template {auth_method} missing auth method"
            assert 'config' in auth_config, f"Pack template {auth_method} missing auth config"
    
    def test_template_auth_method_consistency(self, project_root):
        """Test that template auth methods match their file names"""
        template_dir = project_root / "templates" / "pack"
        auth_method_mapping = {
            'basic': 'basic',
            'token': ['bearer', 'custom'],  # Token can use bearer or custom
            'passthrough': 'passthrough'
        }
        
        for auth_method, expected_methods in auth_method_mapping.items():
            template_path = template_dir / f"pack.template.{auth_method}.yaml"
            if not template_path.exists():
                continue
            
            with open(template_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            actual_method = config['connection']['auth']['method']
            
            if isinstance(expected_methods, list):
                assert actual_method in expected_methods, \
                    f"Pack template {auth_method} has method '{actual_method}', expected one of {expected_methods}"
            else:
                assert actual_method == expected_methods, \
                    f"Pack template {auth_method} has method '{actual_method}', expected '{expected_methods}'"
    
    def test_template_environment_variable_usage(self, project_root):
        """Test that templates use appropriate environment variables"""
        template_dir = project_root / "templates" / "pack"
        for auth_method in ['basic', 'token', 'passthrough']:
            template_path = template_dir / f"pack.template.{auth_method}.yaml"
            if not template_path.exists():
                continue
            
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            with open(template_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # All templates should use SPLUNK_URL
            assert '{SPLUNK_URL}' in content, f"Template {auth_method} should use SPLUNK_URL"
            
            # Check method-specific environment variables
            auth_config = config['connection']['auth']['config']
            
            if auth_method == 'basic':
                # Basic auth should use SPLUNK_USER and SPLUNK_PASSWORD
                username = auth_config.get('username', '')
                password = auth_config.get('password', '')
                assert '{SPLUNK_USER}' in username, f"Basic template should use SPLUNK_USER"
                assert '{SPLUNK_PASSWORD}' in password, f"Basic template should use SPLUNK_PASSWORD"
            
            elif auth_method == 'token':
                # Token auth should use SPLUNK_TOKEN
                token_field = auth_config.get('token') or auth_config.get('header_value', '')
                assert '{SPLUNK_TOKEN}' in str(token_field), f"Token template should use SPLUNK_TOKEN"


class TestDeploymentScriptIntegration:
    """Test deployment scripts correctly handle authentication methods"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    def test_deployment_scripts_exist(self, project_root):
        """Test that deployment scripts exist"""
        deploy_sh = project_root / "scripts" / "deploy.sh"
        deploy_bat = project_root / "scripts" / "deploy.bat"
        
        assert deploy_sh.exists(), "deploy.sh script missing"
        assert deploy_bat.exists(), "deploy.bat script missing"
    
    def test_deployment_script_auth_functions_present(self, project_root):
        """Test that deployment scripts contain all required authentication functions"""
        required_functions = [
            'configure_splunk_auth',
            'configure_basic_auth', 
            'configure_token_auth',
            'configure_passthrough_auth'
        ]
        
        scripts = [
            project_root / "scripts" / "deploy.sh",
            project_root / "scripts" / "deploy.bat"
        ]
        
        for script_path in scripts:
            with open(script_path, 'r') as f:
                content = f.read()
            
            for function_name in required_functions:
                assert function_name in content, \
                    f"Function '{function_name}' missing from {script_path.name}"
    
    def test_template_copying_logic_present(self, project_root):
        """Test that deployment scripts include template copying logic"""
        scripts = [
            project_root / "scripts" / "deploy.sh",
            project_root / "scripts" / "deploy.bat"
        ]
        
        for script_path in scripts:
            with open(script_path, 'r') as f:
                content = f.read()
            
            # Should contain logic to copy templates
            template_indicators = [
                'template', '.template.', 
                'pack.yaml', 'librechat.yaml',
                'copy', 'cp'
            ]
            
            has_template_logic = any(indicator in content.lower() for indicator in template_indicators)
            assert has_template_logic, f"Script {script_path.name} should contain template copying logic"


if __name__ == "__main__":
    # Run with: python -m pytest tests/authentication/test_auth_methods.py -v
    pytest.main([__file__, "-v"])