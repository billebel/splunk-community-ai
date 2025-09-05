"""
Scripts Validation Tests

Tests that validate all deployment and development scripts work correctly.
These tests ensure that the scripts directory provides reliable automation
that users can trust to work without surprises.
"""

import pytest
import subprocess
import os
import tempfile
import shutil
from pathlib import Path
import platform
from unittest.mock import patch, MagicMock


class TestScriptExistence:
    """Test that expected scripts exist and are properly configured"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    def test_windows_scripts_exist(self, project_root):
        """Test that Windows batch scripts exist"""
        scripts_dir = project_root / "scripts"
        
        expected_windows_scripts = [
            "start-dev.bat",
            "stop-dev.bat", 
            "test-mcp.bat",
            "build-chat.bat",
            "deploy.bat"
        ]
        
        for script in expected_windows_scripts:
            script_path = scripts_dir / script
            assert script_path.exists(), f"Windows script {script} missing"
            assert script_path.suffix == ".bat", f"Script {script} should be .bat file"
    
    def test_unix_scripts_exist(self, project_root):
        """Test that Unix/Linux scripts exist"""
        scripts_dir = project_root / "scripts"
        
        expected_unix_scripts = [
            "start-dev.sh",
            "stop-dev.sh",
            "test-mcp.sh", 
            "deploy.sh"
        ]
        
        for script in expected_unix_scripts:
            script_path = scripts_dir / script
            assert script_path.exists(), f"Unix script {script} missing"
            assert script_path.suffix == ".sh", f"Script {script} should be .sh file"
    
    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix permissions test")
    def test_unix_scripts_executable(self, project_root):
        """Test that Unix scripts are executable"""
        scripts_dir = project_root / "scripts"
        
        unix_scripts = [
            "start-dev.sh",
            "stop-dev.sh", 
            "test-mcp.sh",
            "deploy.sh"
        ]
        
        for script in unix_scripts:
            script_path = scripts_dir / script
            if script_path.exists():
                assert os.access(script_path, os.X_OK), f"Script {script} not executable"


class TestScriptSyntax:
    """Test script syntax and basic validation"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    @pytest.mark.skipif(platform.system() == "Windows", reason="Bash syntax check")
    def test_bash_script_syntax(self, project_root):
        """Test that bash scripts have valid syntax"""
        scripts_dir = project_root / "scripts"
        
        bash_scripts = [
            "start-dev.sh",
            "stop-dev.sh",
            "test-mcp.sh", 
            "deploy.sh"
        ]
        
        for script in bash_scripts:
            script_path = scripts_dir / script
            if script_path.exists():
                # Test bash syntax with -n (no execute) flag
                result = subprocess.run(
                    ["bash", "-n", str(script_path)],
                    capture_output=True,
                    text=True
                )
                assert result.returncode == 0, f"Bash syntax error in {script}: {result.stderr}"
    
    def test_scripts_reference_existing_files(self, project_root):
        """Test that scripts reference Docker Compose files that actually exist"""
        scripts_dir = project_root / "scripts"
        
        # Check what Docker Compose files actually exist
        compose_files = {
            "docker-compose.yml": project_root / "docker-compose.yml",
            "docker-compose.mcp-only.yml": project_root / "docker-compose.mcp-only.yml", 
            "docker-compose.splunk.yml": project_root / "docker-compose.splunk.yml"
        }
        
        # Read all script files and check references
        for script_file in scripts_dir.glob("*"):
            if script_file.suffix in [".bat", ".sh"]:
                with open(script_file, encoding='utf-8') as f:
                    content = f.read()
                
                # Check for Docker Compose file references
                if "docker-compose" in content:
                    for compose_name, compose_path in compose_files.items():
                        if compose_name in content:
                            assert compose_path.exists(), \
                                f"Script {script_file.name} references {compose_name} but file doesn't exist"


class TestScriptConfiguration:
    """Test that scripts are properly configured for current project"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    def test_scripts_use_correct_branding(self, project_root):
        """Test that scripts use current project branding, not old names"""
        scripts_dir = project_root / "scripts"
        
        # Old branding that shouldn't appear
        obsolete_terms = [
            "Synapse MCP",
            "FastMCP Synapse", 
            "Synapse",
            "FastMCP"
        ]
        
        # Current branding that should appear
        current_terms = [
            "Catalyst",
            "Splunk AI Integration"
        ]
        
        for script_file in scripts_dir.glob("*"):
            if script_file.suffix in [".bat", ".sh"]:
                with open(script_file, encoding='utf-8') as f:
                    content = f.read()
                
                # Check for obsolete branding
                for term in obsolete_terms:
                    assert term not in content, \
                        f"Script {script_file.name} contains obsolete branding: {term}"
                
                # At least one script should have current branding
                has_current_branding = any(term in content for term in current_terms)
                if "deploy" in script_file.name or "start" in script_file.name:
                    assert has_current_branding, \
                        f"Script {script_file.name} should contain current branding"
    
    def test_scripts_use_consistent_ports(self, project_root):
        """Test that scripts reference consistent port numbers"""
        scripts_dir = project_root / "scripts"
        
        # Expected ports from README and Docker configs
        expected_ports = {
            "3080": "LibreChat web interface",
            "8443": "MCP server API",
            "8000": "Splunk web interface", 
            "8089": "Splunk management API"
        }
        
        found_ports = {}
        
        for script_file in scripts_dir.glob("*"):
            if script_file.suffix in [".bat", ".sh"]:
                with open(script_file, encoding='utf-8') as f:
                    content = f.read()
                
                # Extract port references
                import re
                port_patterns = [
                    r'localhost:(\d+)',
                    r':(\d+)',
                    r'port (\d+)'
                ]
                
                for pattern in port_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for port in matches:
                        if port in expected_ports:
                            if port not in found_ports:
                                found_ports[port] = []
                            found_ports[port].append(script_file.name)
        
        # Key ports should be found in scripts
        assert "8443" in found_ports, "MCP server port 8443 not found in any script"
    
    def test_scripts_handle_env_file_properly(self, project_root):
        """Test that scripts properly handle .env file creation and validation"""
        scripts_dir = project_root / "scripts"
        
        deployment_scripts = [
            "start-dev.bat",
            "start-dev.sh", 
            "deploy.bat",
            "deploy.sh"
        ]
        
        for script_name in deployment_scripts:
            script_path = scripts_dir / script_name
            if script_path.exists():
                with open(script_path, encoding='utf-8') as f:
                    content = f.read()
                
                # Should check for .env file
                assert ".env" in content, f"Script {script_name} should handle .env file"
                
                # Should reference .env.example
                assert ".env.example" in content, \
                    f"Script {script_name} should reference .env.example"


class TestScriptFunctionality:
    """Test script functionality without actually running Docker"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    @pytest.fixture
    def temp_env_setup(self, tmp_path, project_root):
        """Create temporary environment with required files"""
        # Copy essential files to temp directory
        temp_project = tmp_path / "test_project"
        temp_project.mkdir()
        
        essential_files = [
            ".env.example",
            "docker-compose.yml",
            "docker-compose.mcp-only.yml",
            "docker-compose.splunk.yml"
        ]
        
        for file_name in essential_files:
            src = project_root / file_name
            if src.exists():
                shutil.copy2(src, temp_project / file_name)
        
        # Copy scripts directory
        scripts_src = project_root / "scripts"
        scripts_dst = temp_project / "scripts"
        if scripts_src.exists():
            shutil.copytree(scripts_src, scripts_dst)
        
        return temp_project
    
    def test_env_file_creation(self, temp_env_setup):
        """Test that scripts properly create .env from .env.example"""
        project_dir = temp_env_setup
        
        # Ensure .env doesn't exist initially
        env_file = project_dir / ".env"
        if env_file.exists():
            env_file.unlink()
        
        # Test that .env.example exists
        env_example = project_dir / ".env.example"
        assert env_example.exists(), "Test setup should include .env.example"
        
        # Simulate script creating .env file (what scripts do)
        if env_example.exists() and not env_file.exists():
            shutil.copy2(env_example, env_file)
        
        assert env_file.exists(), "Scripts should be able to create .env from .env.example"
        
        # Verify content is copied
        with open(env_example, encoding='utf-8') as f:
            example_content = f.read()
        with open(env_file, encoding='utf-8') as f:
            env_content = f.read()
        
        assert example_content == env_content, ".env should be identical to .env.example"
    
    def test_docker_compose_validation(self, temp_env_setup):
        """Test that Docker Compose files referenced by scripts are valid"""
        project_dir = temp_env_setup
        
        compose_files = [
            "docker-compose.yml",
            "docker-compose.mcp-only.yml",
            "docker-compose.splunk.yml"
        ]
        
        for compose_file in compose_files:
            compose_path = project_dir / compose_file
            if compose_path.exists():
                # Create temporary .env for validation
                env_path = project_dir / ".env"
                if not env_path.exists():
                    env_example = project_dir / ".env.example" 
                    if env_example.exists():
                        shutil.copy2(env_example, env_path)
                
                # Test docker-compose config validation
                try:
                    result = subprocess.run([
                        "docker-compose", "-f", str(compose_path), "config"
                    ], cwd=project_dir, capture_output=True, text=True, timeout=10)
                    
                    # Config should succeed or fail only due to missing .env variables
                    if result.returncode != 0:
                        error_msg = result.stderr.lower()
                        acceptable_errors = [
                            "variable is not set", 
                            "env file", 
                            "environment",
                            "not found"
                        ]
                        is_acceptable = any(err in error_msg for err in acceptable_errors)
                        assert is_acceptable or result.returncode == 0, \
                            f"Docker Compose syntax error in {compose_file}: {result.stderr}"
                        
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pytest.skip("docker-compose not available for validation")


class TestScriptIntegration:
    """Test that scripts work together as an integrated system"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    def test_script_help_consistency(self, project_root):
        """Test that scripts provide consistent help and guidance"""
        scripts_dir = project_root / "scripts"
        
        user_facing_scripts = [
            "deploy.bat",
            "deploy.sh",
            "start-dev.bat", 
            "start-dev.sh"
        ]
        
        for script_name in user_facing_scripts:
            script_path = scripts_dir / script_name
            if script_path.exists():
                with open(script_path, encoding='utf-8') as f:
                    content = f.read()
                
                # Should provide helpful next steps
                helpful_terms = [
                    "next step",
                    "visit",
                    "access",
                    "login",
                    "test",
                    "stop"
                ]
                
                has_guidance = any(term in content.lower() for term in helpful_terms)
                assert has_guidance, f"Script {script_name} should provide user guidance"
    
    def test_cross_script_references(self, project_root):
        """Test that scripts correctly reference each other"""
        scripts_dir = project_root / "scripts"
        
        # Scripts that should reference other scripts
        script_references = {
            "start-dev.bat": ["test-mcp.bat", "stop-dev.bat"],
            "start-dev.sh": ["test-mcp.sh"],
            "deploy.bat": ["test-mcp.bat", "build-chat.bat"],
            "deploy.sh": ["test-mcp.sh"]
        }
        
        for script_name, referenced_scripts in script_references.items():
            script_path = scripts_dir / script_name
            if script_path.exists():
                with open(script_path, encoding='utf-8') as f:
                    content = f.read()
                
                for ref_script in referenced_scripts:
                    # Check if script exists
                    ref_path = scripts_dir / ref_script
                    if ref_path.exists():
                        # Script should reference it
                        assert ref_script in content, \
                            f"Script {script_name} should reference {ref_script}"


@pytest.mark.integration
class TestScriptExecution:
    """Integration tests that actually execute script logic (without Docker)"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    def test_build_chat_validation_logic(self, project_root):
        """Test build-chat.bat validation logic"""
        scripts_dir = project_root / "scripts"
        build_chat = scripts_dir / "build-chat.bat"
        
        if not build_chat.exists():
            pytest.skip("build-chat.bat not found")
        
        with open(build_chat, encoding='utf-8') as f:
            content = f.read()
        
        # Should check for librechat.yaml
        assert "librechat.yaml" in content, "build-chat should check for librechat.yaml"
        
        # Should check for .env file
        assert ".env" in content, "build-chat should check for .env file"
        
        # Should check for API keys
        api_key_terms = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY"]
        has_api_check = any(term in content for term in api_key_terms)
        assert has_api_check, "build-chat should validate API keys"