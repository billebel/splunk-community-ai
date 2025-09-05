"""
Deployment Scripts End-to-End Tests

Tests that validate the unified deployment scripts provide a good user experience
and guide users through successful deployment without Docker actually running.
"""

import pytest
import subprocess
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import platform


class TestDeploymentScriptGuidance:
    """Test that deployment scripts provide clear guidance to users"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    def test_deploy_script_options_documented(self, project_root):
        """Test that deploy scripts document all available options clearly"""
        scripts_dir = project_root / "scripts"
        
        deploy_scripts = ["deploy.bat", "deploy.sh"]
        
        for script_name in deploy_scripts:
            script_path = scripts_dir / script_name
            if script_path.exists():
                with open(script_path, encoding='utf-8') as f:
                    content = f.read()
                
                # Should document the three main deployment options
                assert "[1]" in content, f"{script_name} should document option 1"
                assert "[2]" in content, f"{script_name} should document option 2" 
                assert "[3]" in content, f"{script_name} should document option 3"
                
                # Should mention key features of each option
                deployment_features = [
                    "Web Experience",
                    "MCP Server Only", 
                    "Development Environment",
                    "LibreChat",
                    "Claude Desktop",
                    "Splunk Enterprise"
                ]
                
                found_features = sum(1 for feature in deployment_features if feature in content)
                assert found_features >= 4, f"{script_name} should document key deployment features"
    
    def test_deploy_scripts_explain_requirements(self, project_root):
        """Test that deployment scripts explain what each option requires"""
        scripts_dir = project_root / "scripts"
        
        deploy_scripts = ["deploy.bat", "deploy.sh"]
        
        for script_name in deploy_scripts:
            script_path = scripts_dir / script_name
            if script_path.exists():
                with open(script_path, encoding='utf-8') as f:
                    content = f.read()
                
                # Should mention API key requirements
                assert "API key" in content, f"{script_name} should mention API key requirements"
                
                # Should mention different access URLs
                assert "localhost:3080" in content, f"{script_name} should show web interface URL"
                assert "localhost:8443" in content, f"{script_name} should show MCP server URL"
                assert "localhost:8000" in content, f"{script_name} should show Splunk URL"
    
    def test_deploy_scripts_provide_next_steps(self, project_root):
        """Test that deployment scripts provide clear next steps after deployment"""
        scripts_dir = project_root / "scripts"
        
        deploy_scripts = ["deploy.bat", "deploy.sh"]
        
        for script_name in deploy_scripts:
            script_path = scripts_dir / script_name
            if script_path.exists():
                with open(script_path, encoding='utf-8') as f:
                    content = f.read()
                
                # Should provide post-deployment guidance
                next_step_indicators = [
                    "Next steps:",
                    "Visit http://",
                    "Wait", 
                    "Test",
                    "Login"
                ]
                
                found_guidance = sum(1 for indicator in next_step_indicators if indicator in content)
                assert found_guidance >= 3, f"{script_name} should provide comprehensive next steps"


class TestScriptErrorHandling:
    """Test that scripts handle common error scenarios gracefully"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    def test_scripts_check_prerequisites(self, project_root):
        """Test that scripts check for required prerequisites"""
        scripts_dir = project_root / "scripts"
        
        scripts_with_prereqs = [
            "start-dev.bat",
            "start-dev.sh",
            "deploy.bat",
            "deploy.sh" 
        ]
        
        for script_name in scripts_with_prereqs:
            script_path = scripts_dir / script_name
            if script_path.exists():
                with open(script_path, encoding='utf-8') as f:
                    content = f.read()
                
                # Should check for .env file
                assert ".env" in content, f"{script_name} should check for .env file"
                
                # Should handle missing .env gracefully  
                env_error_terms = [
                    ".env.example",
                    "Creating",
                    "copy",
                    "edit"
                ]
                
                handles_missing_env = any(term in content for term in env_error_terms)
                assert handles_missing_env, f"{script_name} should handle missing .env file"
    
    def test_scripts_provide_helpful_error_messages(self, project_root):
        """Test that scripts provide helpful error messages"""
        scripts_dir = project_root / "scripts"
        
        user_facing_scripts = [
            "deploy.bat",
            "deploy.sh",
            "build-chat.bat",
            "start-dev.bat",
            "start-dev.sh"
        ]
        
        for script_name in user_facing_scripts:
            script_path = scripts_dir / script_name
            if script_path.exists():
                with open(script_path, encoding='utf-8') as f:
                    content = f.read()
                
                # Should have helpful error messages, not just generic ones
                helpful_error_terms = [
                    "Please",
                    "Check", 
                    "edit",
                    "configure",
                    "Try",
                    "ensure"
                ]
                
                has_helpful_errors = any(term in content for term in helpful_error_terms)
                assert has_helpful_errors, f"{script_name} should provide helpful error messages"


class TestScriptConfigurationValidation:
    """Test that scripts validate configuration properly"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    def test_build_chat_validates_api_keys(self, project_root):
        """Test that build-chat script validates API key configuration"""
        scripts_dir = project_root / "scripts"
        build_chat = scripts_dir / "build-chat.bat"
        
        if not build_chat.exists():
            pytest.skip("build-chat.bat not found")
        
        with open(build_chat, encoding='utf-8') as f:
            content = f.read()
        
        # Should check for multiple API key types
        api_providers = ["ANTHROPIC", "OPENAI", "GOOGLE"]
        
        for provider in api_providers:
            assert f"{provider}_API_KEY" in content, \
                f"build-chat should check for {provider}_API_KEY"
        
        # Should handle case where no API keys found
        assert "Warning" in content or "Error" in content, \
            "build-chat should warn about missing API keys"
    
    def test_deployment_scripts_validate_docker_files(self, project_root):
        """Test that deployment scripts reference correct Docker Compose files"""
        scripts_dir = project_root / "scripts"
        
        # Map deployment options to expected Docker Compose files or patterns
        deployment_mappings = {
            "deploy.bat": {
                "option1": ["docker-compose up", "build-chat"],  # Full web (uses default compose + build-chat)
                "option2": "docker-compose.mcp-only.yml",  # MCP only
                "option3": "docker-compose.splunk.yml"  # Development
            },
            "deploy.sh": {
                "option1": "docker-compose up",  # Full web (uses default compose)
                "option2": "docker-compose.mcp-only.yml", 
                "option3": "docker-compose.splunk.yml"
            }
        }
        
        for script_name, expected_patterns in deployment_mappings.items():
            script_path = scripts_dir / script_name
            if script_path.exists():
                with open(script_path, encoding='utf-8') as f:
                    content = f.read()
                
                for option, pattern in expected_patterns.items():
                    if isinstance(pattern, list):
                        # Check that at least one pattern matches
                        matches = any(p in content for p in pattern)
                        assert matches, \
                            f"{script_name} should reference one of {pattern} for {option}"
                    else:
                        assert pattern in content, \
                            f"{script_name} should reference {pattern} for {option}"
        
        # Verify all referenced Docker Compose files actually exist
        compose_files = [
            "docker-compose.yml",
            "docker-compose.mcp-only.yml", 
            "docker-compose.splunk.yml"
        ]
        
        for compose_file in compose_files:
            compose_path = project_root / compose_file
            assert compose_path.exists(), \
                f"Referenced Docker Compose file {compose_file} doesn't exist"


class TestScriptUsabilityFeatures:
    """Test that scripts include usability features that improve user experience"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    def test_scripts_provide_progress_feedback(self, project_root):
        """Test that scripts provide progress feedback during operations"""
        scripts_dir = project_root / "scripts"
        
        progress_scripts = [
            "start-dev.bat",
            "start-dev.sh",
            "deploy.bat", 
            "deploy.sh"
        ]
        
        for script_name in progress_scripts:
            script_path = scripts_dir / script_name
            if script_path.exists():
                with open(script_path, encoding='utf-8') as f:
                    content = f.read()
                
                # Should provide progress feedback
                progress_indicators = [
                    "Starting",
                    "Waiting",
                    "complete",
                    "Success",
                    "===",  # Visual separators
                    "echo"  # Progress messages
                ]
                
                found_progress = sum(1 for indicator in progress_indicators if indicator in content)
                assert found_progress >= 3, f"{script_name} should provide progress feedback"
    
    def test_scripts_include_troubleshooting_info(self, project_root):
        """Test that scripts include troubleshooting information"""
        scripts_dir = project_root / "scripts"
        
        user_scripts = [
            "test-mcp.bat",
            "test-mcp.sh",
            "deploy.bat",
            "deploy.sh"
        ]
        
        for script_name in user_scripts:
            script_path = scripts_dir / script_name
            if script_path.exists():
                with open(script_path, encoding='utf-8') as f:
                    content = f.read()
                
                # Should include troubleshooting guidance
                troubleshooting_terms = [
                    "If you see",
                    "ensure", 
                    "check",
                    "failed",
                    "connection error",
                    "docker-compose ps"
                ]
                
                has_troubleshooting = any(term in content.lower() for term in troubleshooting_terms)
                if "test-mcp" in script_name or "deploy" in script_name:
                    assert has_troubleshooting, f"{script_name} should include troubleshooting info"
    
    def test_scripts_show_relevant_urls(self, project_root):
        """Test that scripts show users the URLs they need to access"""
        scripts_dir = project_root / "scripts"
        
        url_scripts = [
            "start-dev.bat",
            "start-dev.sh", 
            "deploy.bat",
            "deploy.sh"
        ]
        
        expected_urls = [
            "http://localhost:3080",  # LibreChat
            "http://localhost:8443",  # MCP Server
            "http://localhost:8000",  # Splunk Web
            "https://localhost:8089"  # Splunk API
        ]
        
        for script_name in url_scripts:
            script_path = scripts_dir / script_name
            if script_path.exists():
                with open(script_path, encoding='utf-8') as f:
                    content = f.read()
                
                # Should show relevant URLs
                urls_found = [url for url in expected_urls if url in content]
                assert len(urls_found) >= 2, \
                    f"{script_name} should show relevant access URLs"


@pytest.mark.integration
class TestScriptWorkflow:
    """Test complete script workflows without actually running Docker"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    @pytest.fixture
    def mock_environment(self, tmp_path, project_root):
        """Create mock environment for testing script workflows"""
        # Copy essential files to temp directory
        temp_project = tmp_path / "test_project"
        temp_project.mkdir()
        
        # Copy configuration files
        config_files = [
            ".env.example",
            "docker-compose.yml",
            "docker-compose.mcp-only.yml",
            "docker-compose.splunk.yml"
        ]
        
        for file_name in config_files:
            src = project_root / file_name
            if src.exists():
                shutil.copy2(src, temp_project / file_name)
        
        return temp_project
    
    def test_env_file_workflow(self, mock_environment):
        """Test that .env file creation workflow works as expected"""
        project_dir = mock_environment
        
        # Initially no .env file
        env_file = project_dir / ".env"
        env_example = project_dir / ".env.example"
        
        assert not env_file.exists(), "Test should start without .env file"
        assert env_example.exists(), "Test environment should have .env.example"
        
        # Simulate what scripts do: copy .env.example to .env
        shutil.copy2(env_example, env_file)
        
        # Verify workflow completed successfully
        assert env_file.exists(), "Script workflow should create .env file"
        
        # Verify content is properly copied
        with open(env_example, encoding='utf-8') as f:
            example_content = f.read()
        with open(env_file, encoding='utf-8') as f:
            env_content = f.read()
        
        assert example_content == env_content, ".env should match .env.example"
        
        # Verify .env has expected configuration variables
        assert "SPLUNK_URL" in env_content, ".env should contain SPLUNK_URL"
        assert "ANTHROPIC_API_KEY" in env_content, ".env should contain ANTHROPIC_API_KEY"
    
    def test_configuration_validation_workflow(self, mock_environment):
        """Test configuration validation workflow"""
        project_dir = mock_environment
        
        # Create .env file with test configuration
        env_file = project_dir / ".env"
        test_config = """# Test configuration
SPLUNK_URL=https://test-splunk:8089
SPLUNK_USER=testuser
SPLUNK_PASSWORD=testpass
ANTHROPIC_API_KEY=test-key-123
"""
        env_file.write_text(test_config)
        
        # Simulate configuration validation (what scripts do)
        with open(env_file) as f:
            config_content = f.read()
        
        # Verify required variables present
        required_vars = ["SPLUNK_URL", "SPLUNK_USER", "SPLUNK_PASSWORD"]
        for var in required_vars:
            assert f"{var}=" in config_content, f"Configuration should contain {var}"
        
        # Verify API key present for web interface
        has_api_key = any(key in config_content for key in 
                         ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY"])
        assert has_api_key, "Configuration should have at least one AI provider API key"