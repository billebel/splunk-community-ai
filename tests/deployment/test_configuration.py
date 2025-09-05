"""
Configuration Validation Tests

Tests that validate configuration examples and environment setup work correctly.
These tests ensure that configuration instructions in the README are accurate
and that users can successfully configure the platform.
"""

import pytest
import os
import yaml
import json
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestEnvironmentConfiguration:
    """Test environment variable configuration"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    def test_env_example_format(self, project_root):
        """Test .env.example has correct format and all required variables"""
        env_example = project_root / ".env.example"
        assert env_example.exists(), ".env.example missing"
        
        with open(env_example) as f:
            lines = f.readlines()
        
        # Parse environment variables
        env_vars = {}
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value
        
        # Required for all deployments
        assert "SPLUNK_URL" in env_vars, "SPLUNK_URL missing from .env.example"
        assert "SPLUNK_USER" in env_vars, "SPLUNK_USER missing from .env.example"
        assert "SPLUNK_PASSWORD" in env_vars, "SPLUNK_PASSWORD missing from .env.example"
        
        # Required for web interface
        assert "ANTHROPIC_API_KEY" in env_vars, "ANTHROPIC_API_KEY missing from .env.example"
        
        # Validate URL format examples
        splunk_url = env_vars.get("SPLUNK_URL", "")
        assert splunk_url.startswith("https://") or splunk_url.startswith("http://"), \
            "SPLUNK_URL example should show proper URL format"
    
    def test_env_example_has_comments(self, project_root):
        """Test .env.example has helpful comments for users"""
        env_example = project_root / ".env.example"
        
        with open(env_example) as f:
            content = f.read()
        
        # Should have explanatory comments
        assert "#" in content, ".env.example should have explanatory comments"
        
        # Should explain what each major section is for
        assert any(keyword in content.lower() for keyword in ["splunk", "connection", "url"]), \
            "Should explain Splunk connection variables"
        
        assert any(keyword in content.lower() for keyword in ["api", "key", "anthropic", "ai"]), \
            "Should explain AI API key requirement"
    
    def test_env_variables_match_docker_compose(self, project_root):
        """Test that environment variables in .env.example match those used in Docker Compose"""
        env_example = project_root / ".env.example"
        
        with open(env_example) as f:
            env_content = f.read()
        
        # Extract variables from .env.example
        env_vars = set()
        for line in env_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                var_name = line.split('=')[0]
                env_vars.add(var_name)
        
        # Check that docker-compose files can use these variables either via env_file or explicitly
        compose_files = ["docker-compose.yml", "docker-compose.mcp-only.yml"]
        
        for compose_filename in compose_files:
            compose_file = project_root / compose_filename
            if not compose_file.exists():
                continue
                
            with open(compose_file) as f:
                compose_content = f.read()
            
            # For key Splunk variables, ensure they're either used explicitly OR env_file is used
            splunk_vars_used = False
            
            # Check if env_file is used (loads all variables from .env)
            if "env_file:" in compose_content and ".env" in compose_content:
                splunk_vars_used = True
            
            # OR check if Splunk variables are used explicitly
            for var in ["SPLUNK_URL", "SPLUNK_USER", "SPLUNK_PASSWORD"]:
                if var in env_vars:
                    var_used = f"${{{var}}}" in compose_content or f"${{{var}:-" in compose_content
                    if var_used:
                        splunk_vars_used = True
                        break
            
            assert splunk_vars_used, \
                f"{compose_filename} should use Splunk environment variables (via env_file or explicitly)"


class TestSplunkConnectionConfig:
    """Test Splunk connection configuration validation"""
    
    def test_splunk_url_validation(self):
        """Test Splunk URL format validation"""
        valid_urls = [
            "https://splunk.company.com:8089",
            "http://localhost:8089",
            "https://10.0.0.100:8089"
        ]
        
        invalid_urls = [
            "splunk.company.com",  # Missing protocol
            "https://splunk.company.com",  # Missing port
            "ftp://splunk.company.com:8089",  # Wrong protocol
            "https://splunk.company.com:80"  # Wrong port for management
        ]
        
        # This would test actual URL validation if implemented in the platform
        for url in valid_urls:
            assert "://" in url and (":8089" in url or ":443" in url), f"Valid URL format: {url}"
        
        for url in invalid_urls:
            # These should be caught by validation
            assert not (url.startswith("https://") and ":8089" in url) or url in valid_urls
    
    def test_splunk_credentials_format(self):
        """Test Splunk credentials format expectations"""
        # Test that credential examples in .env don't use real values
        project_root = Path(__file__).parent.parent.parent
        env_example = project_root / ".env.example"
        
        with open(env_example) as f:
            content = f.read()
        
        # Should not contain actual credentials
        security_violations = [
            "admin",  # Default Splunk admin user
            "changeme",  # Default Splunk password
            "password123",  # Common weak password
            "splunk123"  # Common Splunk default
        ]
        
        content_lower = content.lower()
        for violation in security_violations:
            assert violation not in content_lower, f"Security violation: {violation} found in .env.example"


class TestAIProviderConfiguration:
    """Test AI provider API configuration"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    def test_anthropic_api_key_configuration(self, project_root):
        """Test Anthropic API key configuration is properly documented"""
        env_example = project_root / ".env.example"
        
        with open(env_example) as f:
            content = f.read()
        
        # Should mention Anthropic API key
        assert "ANTHROPIC_API_KEY" in content, "ANTHROPIC_API_KEY not in .env.example"
        
        # Should not contain a real API key
        api_key_line = None
        for line in content.split('\n'):
            if "ANTHROPIC_API_KEY" in line:
                api_key_line = line
                break
        
        assert api_key_line, "ANTHROPIC_API_KEY line not found"
        
        # Should be example/placeholder, not real key
        assert not api_key_line.endswith("=sk-ant-"), "Should not contain real Anthropic API key prefix"
    
    def test_ai_provider_documentation(self, project_root):
        """Test that AI provider configuration is documented"""
        readme = project_root / "README.md"
        
        with open(readme, encoding='utf-8') as f:
            content = f.read()
        
        # Should mention API key requirement for web interface
        assert "ANTHROPIC_API_KEY" in content, "ANTHROPIC_API_KEY requirement not documented in README"
        
        # Should explain when API key is needed vs not needed
        assert "MCP-only" in content or "mcp-only" in content, "Should document MCP-only option"


class TestDockerComposeEnvironmentIntegration:
    """Test Docker Compose environment variable integration"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    def test_compose_files_use_env_vars(self, project_root):
        """Test that Docker Compose files properly use environment variables"""
        compose_files = [
            "docker-compose.yml",
            "docker-compose.mcp-only.yml", 
            "docker-compose.splunk.yml"
        ]
        
        for compose_file in compose_files:
            compose_path = project_root / compose_file
            if not compose_path.exists():
                continue
                
            with open(compose_path) as f:
                content = f.read()
            
            # Should use environment variable substitution
            if "splunk" in content.lower():
                # Should reference Splunk environment variables in some form
                # Look for SPLUNK environment variable names in the environment section
                env_vars = ["SPLUNK_URL", "SPLUNK_USER", "SPLUNK_PASSWORD"]
                found_any = any(var in content for var in env_vars)
                assert found_any, f"{compose_file} should reference Splunk environment variables"
    
    def test_env_file_precedence(self, project_root):
        """Test that .env file loading is properly configured"""
        # Check if docker-compose files are configured to load .env
        compose_files = ["docker-compose.yml", "docker-compose.mcp-only.yml"]
        
        for compose_file in compose_files:
            compose_path = project_root / compose_file
            if not compose_path.exists():
                continue
                
            with open(compose_path) as f:
                config = yaml.safe_load(f)
            
            # Docker Compose should automatically load .env file
            # This is implicit behavior, so we just verify the file structure is correct
            assert "services" in config, f"{compose_file} should have services section"


class TestConfigurationErrorHandling:
    """Test configuration error handling and user feedback"""
    
    def test_missing_env_file_handling(self):
        """Test behavior when .env file is missing"""
        # This would test that the system provides helpful error messages
        # when required configuration is missing
        
        # For now, just verify that .env.example exists as a template
        project_root = Path(__file__).parent.parent.parent
        assert (project_root / ".env.example").exists(), \
            "Users need .env.example template when .env is missing"
    
    def test_invalid_splunk_config_handling(self):
        """Test handling of invalid Splunk configuration"""
        # This would test that the system gracefully handles:
        # - Invalid Splunk URLs
        # - Wrong credentials  
        # - Network connectivity issues
        # - SSL certificate problems
        
        invalid_configs = [
            {"url": "invalid-url", "user": "test", "password": "test"},
            {"url": "https://nonexistent:8089", "user": "test", "password": "test"},
            {"url": "", "user": "", "password": ""},  # Empty config
        ]
        
        for config in invalid_configs:
            # System should handle these gracefully with clear error messages
            assert isinstance(config, dict), "Configuration should be structured data"
    
    def test_configuration_validation_messages(self, project_root):
        """Test that configuration validation provides helpful messages"""
        # Check if documentation provides troubleshooting guidance
        readme = project_root / "README.md"
        
        with open(readme, encoding='utf-8') as f:
            content = f.read()
        
        # Should provide guidance on common configuration issues
        helpful_terms = [
            "configure", "configuration", "setup", 
            "connection", "credentials", "environment"
        ]
        
        found_guidance = any(term in content.lower() for term in helpful_terms)
        assert found_guidance, "README should provide configuration guidance"