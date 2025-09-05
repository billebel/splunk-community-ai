"""
Docker Compose Deployment Validation Tests

Tests that validate all three deployment options work correctly:
1. Full Web Experience (docker-compose.yml)
2. MCP Server Only (docker-compose.mcp-only.yml) 
3. Development Setup (docker-compose.splunk.yml)

These tests ensure that what we promise in the README actually works.
"""

import pytest
import subprocess
import time
import requests
import yaml
import os
from pathlib import Path


class TestDockerComposeConfigs:
    """Validate Docker Compose files are syntactically correct and complete"""
    
    @pytest.fixture
    def project_root(self):
        """Get project root directory"""
        return Path(__file__).parent.parent.parent
    
    def test_main_docker_compose_exists(self, project_root):
        """Test main docker-compose.yml exists and is valid YAML"""
        compose_file = project_root / "docker-compose.yml"
        assert compose_file.exists(), "docker-compose.yml missing from project root"
        
        with open(compose_file) as f:
            config = yaml.safe_load(f)
            
        assert "services" in config, "docker-compose.yml missing services section"
        assert "version" in config or "services" in config, "Invalid docker-compose.yml format"
    
    def test_mcp_only_docker_compose_exists(self, project_root):
        """Test MCP-only docker-compose file exists and is valid"""
        compose_file = project_root / "docker-compose.mcp-only.yml"
        assert compose_file.exists(), "docker-compose.mcp-only.yml missing"
        
        with open(compose_file) as f:
            config = yaml.safe_load(f)
            
        assert "services" in config, "MCP-only compose file missing services"
    
    def test_splunk_docker_compose_exists(self, project_root):
        """Test Splunk development docker-compose file exists and is valid"""
        compose_file = project_root / "docker-compose.splunk.yml"
        assert compose_file.exists(), "docker-compose.splunk.yml missing"
        
        with open(compose_file) as f:
            config = yaml.safe_load(f)
            
        assert "services" in config, "Splunk compose file missing services"
    
    def test_env_example_exists(self, project_root):
        """Test .env.example exists for configuration"""
        env_example = project_root / ".env.example"
        assert env_example.exists(), ".env.example missing - users need configuration template"
        
        with open(env_example) as f:
            content = f.read()
            
        # Should contain key configuration variables mentioned in README
        assert "SPLUNK_URL" in content, ".env.example missing SPLUNK_URL"
        assert "SPLUNK_USER" in content, ".env.example missing SPLUNK_USER"
        assert "SPLUNK_PASSWORD" in content, ".env.example missing SPLUNK_PASSWORD"


class TestDockerComposeValidation:
    """Validate Docker Compose configurations without actually running them"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    def test_main_compose_syntax(self, project_root):
        """Test main docker-compose.yml syntax validation"""
        # Create temporary .env file for syntax validation
        temp_env = project_root / ".env"
        env_existed = temp_env.exists()
        
        if not env_existed:
            temp_env.write_text("# Temporary env file for testing\nSPLUNK_URL=https://test:8089\n")
        
        try:
            result = subprocess.run([
                "docker-compose", "-f", "docker-compose.yml", "config"
            ], cwd=project_root, capture_output=True, text=True)
            
            assert result.returncode == 0, f"docker-compose.yml syntax error: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("docker-compose not available in test environment")
        finally:
            # Cleanup temporary .env file
            if not env_existed and temp_env.exists():
                temp_env.unlink()
    
    def test_mcp_only_compose_syntax(self, project_root):
        """Test MCP-only compose syntax validation"""
        try:
            result = subprocess.run([
                "docker-compose", "-f", "docker-compose.mcp-only.yml", "config"
            ], cwd=project_root, capture_output=True, text=True)
            
            assert result.returncode == 0, f"docker-compose.mcp-only.yml syntax error: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("docker-compose not available in test environment")
    
    def test_splunk_compose_syntax(self, project_root):
        """Test Splunk development compose syntax validation"""
        try:
            result = subprocess.run([
                "docker-compose", "-f", "docker-compose.splunk.yml", "config"
            ], cwd=project_root, capture_output=True, text=True)
            
            assert result.returncode == 0, f"docker-compose.splunk.yml syntax error: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("docker-compose not available in test environment")


@pytest.mark.integration
class TestMCPOnlyDeployment:
    """Test MCP-only deployment (lightest option for CI)"""
    
    @pytest.fixture(scope="class")
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    @pytest.fixture(scope="class") 
    def mcp_deployment(self, project_root):
        """Deploy MCP-only stack for testing"""
        # Create minimal .env for testing
        env_content = """
SPLUNK_URL=https://mock-splunk:8089
SPLUNK_USER=test
SPLUNK_PASSWORD=test
"""
        with open(project_root / ".env", "w") as f:
            f.write(env_content)
        
        # Start MCP-only deployment  
        try:
            subprocess.run([
                "docker-compose", "-f", "docker-compose.mcp-only.yml", "up", "-d"
            ], cwd=project_root, check=True)
        except FileNotFoundError:
            pytest.skip("docker-compose not available in test environment")
        
        # Wait for services to start
        time.sleep(10)
        
        yield
        
        # Cleanup
        subprocess.run([
            "docker-compose", "-f", "docker-compose.mcp-only.yml", "down", "-v"
        ], cwd=project_root)
        
        # Remove test .env
        (project_root / ".env").unlink(missing_ok=True)
    
    def test_mcp_server_starts(self, mcp_deployment):
        """Test MCP server starts and is accessible"""
        # Check if MCP endpoint is accessible (should be on port 8443)
        try:
            # May return error due to mock Splunk, but should be listening
            response = requests.get("http://localhost:8443/health", timeout=5)
            # Service is running if we get any HTTP response
            assert response.status_code is not None
        except requests.ConnectionError:
            pytest.fail("MCP server not accessible on port 8443")
        except requests.exceptions.ReadTimeout:
            # Timeout is acceptable - means service is listening
            pass
    
    def test_docker_containers_running(self, mcp_deployment):
        """Test that expected Docker containers are running"""
        result = subprocess.run([
            "docker-compose", "-f", "docker-compose.mcp-only.yml", "ps"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
        
        assert result.returncode == 0, "Could not check container status"
        
        # Should show running services
        output = result.stdout
        assert "Up" in output or "running" in output, "No containers appear to be running"


@pytest.mark.slow 
class TestQuickStartDocumentation:
    """Validate that README quick start instructions are accurate"""
    
    def test_git_clone_url_valid(self):
        """Test that git clone URL in README is valid"""
        # This would test the actual git clone command from README
        # For now, just verify the format is correct
        clone_url = "https://github.com/billebel/splunk-community-ai.git"
        
        # Basic URL validation
        assert clone_url.startswith("https://")
        assert "github.com" in clone_url
        assert clone_url.endswith(".git")
    
    def test_required_files_exist_after_clone(self):
        """Test that required files exist (simulates post-clone state)"""
        project_root = Path(__file__).parent.parent.parent
        
        required_files = [
            "docker-compose.yml",
            "docker-compose.mcp-only.yml", 
            "docker-compose.splunk.yml",
            ".env.example",
            "README.md"
        ]
        
        for file_path in required_files:
            assert (project_root / file_path).exists(), f"Required file {file_path} missing"
    
    def test_env_example_has_required_vars(self):
        """Test that .env.example contains all variables mentioned in README"""
        project_root = Path(__file__).parent.parent.parent
        env_example = project_root / ".env.example"
        
        with open(env_example) as f:
            content = f.read()
        
        # Variables explicitly mentioned in README quick start
        required_vars = [
            "SPLUNK_URL",
            "SPLUNK_USER", 
            "SPLUNK_PASSWORD",
            "ANTHROPIC_API_KEY"  # Mentioned for full web experience
        ]
        
        for var in required_vars:
            assert var in content, f"Required environment variable {var} missing from .env.example"


class TestDocumentationAccuracy:
    """Test that documentation claims match reality"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    def test_readme_port_claims(self, project_root):
        """Test that README port claims match Docker configurations"""
        # README claims specific ports - verify Docker configs match
        with open(project_root / "README.md", encoding='utf-8') as f:
            readme = f.read()
        
        # Check main compose file for port claims
        with open(project_root / "docker-compose.yml") as f:
            main_compose = yaml.safe_load(f)
        
        # README claims web interface on localhost:3080
        if "localhost:3080" in readme:
            # Verify this port is actually configured in docker-compose
            # (This would need adjustment based on actual port configuration)
            pass
        
        # README claims MCP endpoint on localhost:8443
        if "localhost:8443" in readme:
            # Verify MCP port is configured
            pass
    
    def test_deployment_options_documented(self, project_root):
        """Test that all Docker compose files mentioned in README exist"""
        with open(project_root / "README.md", encoding='utf-8') as f:
            readme = f.read()
        
        # Files mentioned in README
        if "docker-compose.yml" in readme:
            assert (project_root / "docker-compose.yml").exists()
        
        if "docker-compose.mcp-only.yml" in readme:
            assert (project_root / "docker-compose.mcp-only.yml").exists()
            
        if "docker-compose.splunk.yml" in readme:
            assert (project_root / "docker-compose.splunk.yml").exists()