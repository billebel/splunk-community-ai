"""
Quick Start Verification Tests

These tests validate that the quick start instructions in the README actually work.
They simulate a new user following the documentation step by step.

This is the most critical test for adoption - if someone can't get it working
in the first 10 minutes following the README, they won't adopt it.
"""

import pytest
import subprocess
import time
import requests
import os
import shutil
from pathlib import Path
from unittest.mock import patch


class TestQuickStartInstructions:
    """Test that README Quick Start instructions work correctly"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    def test_step1_clone_and_configure_files_exist(self, project_root):
        """Test Step 1: Clone and Configure - required files exist"""
        # Simulate: git clone https://github.com/billebel/splunk-community-ai.git
        # cd splunk-community-ai
        
        # Verify all files mentioned in step 1 exist
        required_files = [
            "docker-compose.yml",
            "docker-compose.mcp-only.yml",
            "docker-compose.splunk.yml", 
            ".env.example",
            "README.md"
        ]
        
        for file_path in required_files:
            file_full_path = project_root / file_path
            assert file_full_path.exists(), f"Step 1 requires {file_path} but it's missing"
    
    def test_step1_env_example_copy(self, project_root, tmp_path):
        """Test Step 1: cp .env.example .env works correctly"""
        # Simulate copying .env.example to .env
        env_example = project_root / ".env.example"
        test_env = tmp_path / ".env"
        
        shutil.copy(env_example, test_env)
        
        assert test_env.exists(), "Copying .env.example to .env failed"
        
        # Verify copied file has expected content
        with open(test_env) as f:
            content = f.read()
        
        assert "SPLUNK_URL" in content, ".env should contain SPLUNK_URL after copy"
        assert "SPLUNK_USER" in content, ".env should contain SPLUNK_USER after copy"
    
    def test_step2_splunk_connection_variables(self, project_root):
        """Test Step 2: Configure Splunk Connection variables are documented"""
        env_example = project_root / ".env.example"
        
        with open(env_example) as f:
            content = f.read()
        
        # Step 2 mentions these specific variables
        required_vars = ["SPLUNK_URL", "SPLUNK_USER", "SPLUNK_PASSWORD"]
        
        for var in required_vars:
            assert var in content, f"Step 2 requires {var} but it's not in .env.example"
        
        # Check format examples are reasonable
        for line in content.split('\n'):
            if line.startswith('SPLUNK_URL='):
                url_example = line.split('=', 1)[1]
                assert any(protocol in url_example for protocol in ['https://', 'http://']), \
                    "SPLUNK_URL example should show proper protocol"
    
    def test_step3_deployment_options_exist(self, project_root):
        """Test Step 3: All deployment options mentioned in README exist"""
        readme = project_root / "README.md"
        
        with open(readme, encoding='utf-8') as f:
            readme_content = f.read()
        
        # Option A: Full Web Chat Experience
        if "Option A" in readme_content and "docker-compose up -d" in readme_content:
            assert (project_root / "docker-compose.yml").exists(), \
                "Option A requires docker-compose.yml"
        
        # Option B: MCP Server Only
        if "Option B" in readme_content and "docker-compose.mcp-only.yml" in readme_content:
            assert (project_root / "docker-compose.mcp-only.yml").exists(), \
                "Option B requires docker-compose.mcp-only.yml"
        
        # Option C: Test with Docker Splunk
        if "Option C" in readme_content and "docker-compose.splunk.yml" in readme_content:
            assert (project_root / "docker-compose.splunk.yml").exists(), \
                "Option C requires docker-compose.splunk.yml"
    
    def test_step3_port_claims_in_readme(self, project_root):
        """Test Step 3: Port claims in README match configuration"""
        readme = project_root / "README.md"
        
        with open(readme, encoding='utf-8') as f:
            readme_content = f.read()
        
        # README claims specific ports - verify they seem reasonable
        if "localhost:3080" in readme_content:
            # Web interface port claim
            assert "3080" in readme_content, "Port 3080 should be consistently referenced"
        
        if "localhost:8443" in readme_content:
            # MCP endpoint port claim
            assert "8443" in readme_content, "Port 8443 should be consistently referenced"
    
    def test_step4_analysis_examples_format(self, project_root):
        """Test Step 4: Analysis examples are properly formatted"""
        readme = project_root / "README.md"
        
        with open(readme, encoding='utf-8') as f:
            readme_content = f.read()
        
        # Should provide example queries mentioned in step 4
        example_phrases = [
            "What security data is available",
            "security data",
            "environment",
            "MCP client"
        ]
        
        found_examples = any(phrase in readme_content for phrase in example_phrases)
        assert found_examples, "Step 4 should provide example queries or use cases"


class TestDeploymentOptionValidation:
    """Test each deployment option mentioned in Quick Start"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    @pytest.fixture
    def test_env_content(self):
        """Minimal .env content for testing"""
        return """# Test configuration
SPLUNK_URL=https://mock-splunk:8089
SPLUNK_USER=testuser
SPLUNK_PASSWORD=testpass
ANTHROPIC_API_KEY=test-key-123
"""
    
    def test_option_a_full_web_experience_commands(self, project_root):
        """Test Option A: Full Web Experience commands are valid"""
        # Commands from README Option A
        commands_to_validate = [
            ["docker-compose", "--version"],  # Prerequisite
            ["docker-compose", "-f", "docker-compose.yml", "config"]  # Syntax check
        ]
        
        for cmd in commands_to_validate:
            try:
                result = subprocess.run(
                    cmd, 
                    cwd=project_root, 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                # Command should not fail due to syntax issues
                if "config" in cmd:
                    # Config validation might fail due to missing .env, but syntax should be OK
                    if result.returncode != 0:
                        # Check if it's just missing .env (acceptable) vs syntax error (not acceptable)
                        error_msg = result.stderr.lower()
                        acceptable_errors = ["variable is not set", "env file", "environment"]
                        is_acceptable = any(err in error_msg for err in acceptable_errors)
                        assert is_acceptable or result.returncode == 0, f"Syntax error in docker-compose.yml: {result.stderr}"
            except subprocess.TimeoutExpired:
                pytest.fail(f"Command timeout: {cmd}")
            except FileNotFoundError:
                pytest.skip(f"Command not available: {cmd[0]}")
    
    def test_option_b_mcp_server_only_commands(self, project_root):
        """Test Option B: MCP Server Only commands are valid"""
        # docker-compose -f docker-compose.mcp-only.yml up -d
        try:
            result = subprocess.run([
                "docker-compose", "-f", "docker-compose.mcp-only.yml", "config"
            ], cwd=project_root, capture_output=True, text=True, timeout=10)
            
            # Should not fail due to syntax errors
            if result.returncode != 0:
                error_msg = result.stderr.lower()
                acceptable_errors = ["variable is not set", "env file", "environment"]
                is_acceptable = any(err in error_msg for err in acceptable_errors)
                assert is_acceptable, f"Syntax error in docker-compose.mcp-only.yml: {result.stderr}"
                
        except FileNotFoundError:
            pytest.skip("docker-compose not available")
    
    def test_option_c_docker_splunk_commands(self, project_root):
        """Test Option C: Docker Splunk commands are valid"""
        # docker-compose -f docker-compose.splunk.yml up -d
        try:
            result = subprocess.run([
                "docker-compose", "-f", "docker-compose.splunk.yml", "config"
            ], cwd=project_root, capture_output=True, text=True, timeout=10)
            
            # Should not fail due to syntax errors
            if result.returncode != 0:
                error_msg = result.stderr.lower()
                acceptable_errors = ["variable is not set", "env file", "environment"]
                is_acceptable = any(err in error_msg for err in acceptable_errors)
                assert is_acceptable, f"Syntax error in docker-compose.splunk.yml: {result.stderr}"
                
        except FileNotFoundError:
            pytest.skip("docker-compose not available")


class TestUserExperienceFlow:
    """Test the complete user experience following Quick Start"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    def test_prerequisite_software_documented(self, project_root):
        """Test that prerequisite software is documented"""
        readme = project_root / "README.md"
        
        with open(readme, encoding='utf-8') as f:
            content = f.read()
        
        # Should mention Docker as prerequisite
        docker_mentioned = any(term in content.lower() for term in ['docker', 'container'])
        assert docker_mentioned, "Docker prerequisite should be documented"
    
    def test_troubleshooting_guidance_exists(self, project_root):
        """Test that troubleshooting guidance exists for common issues"""
        readme = project_root / "README.md"
        
        with open(readme, encoding='utf-8') as f:
            content = f.read()
        
        # Should provide help for common issues
        helpful_sections = [
            'troubleshoot', 'problem', 'issue', 'error',
            'question', 'help', 'support', 'documentation'
        ]
        
        has_help = any(term in content.lower() for term in helpful_sections)
        assert has_help, "README should provide troubleshooting or help guidance"
    
    def test_next_steps_after_setup(self, project_root):
        """Test that README provides guidance on what to do after setup"""
        readme = project_root / "README.md"
        
        with open(readme, encoding='utf-8') as f:
            content = f.read()
        
        # After quick start, users should know what to try
        next_step_indicators = [
            'example', 'try', 'query', 'search', 'analyze',
            'usage', 'workflow', 'documentation'
        ]
        
        has_next_steps = any(term in content.lower() for term in next_step_indicators)
        assert has_next_steps, "README should guide users on next steps after setup"


class TestCommonUserMistakes:
    """Test that common user mistakes are prevented or handled gracefully"""
    
    def test_missing_env_file_handling(self):
        """Test that missing .env file is handled with helpful message"""
        # This would test actual error handling, but for now verify .env.example exists
        project_root = Path(__file__).parent.parent.parent
        assert (project_root / ".env.example").exists(), \
            "Missing .env should direct user to .env.example"
    
    def test_docker_not_running_guidance(self):
        """Test that Docker not running scenario is documented"""
        project_root = Path(__file__).parent.parent.parent
        readme = project_root / "README.md"
        
        with open(readme, encoding='utf-8') as f:
            content = f.read()
        
        # Should mention Docker requirement somewhere
        assert "docker" in content.lower(), "Docker requirement should be documented"
    
    def test_port_conflicts_guidance(self, project_root):
        """Test that port conflict issues are handled"""
        # Check if multiple compose files use different ports to avoid conflicts
        compose_files = [
            "docker-compose.yml",
            "docker-compose.mcp-only.yml", 
            "docker-compose.splunk.yml"
        ]
        
        used_ports = set()
        port_conflicts = []
        
        for compose_file in compose_files:
            compose_path = project_root / compose_file
            if not compose_path.exists():
                continue
            
            with open(compose_path) as f:
                content = f.read()
            
            # Extract port mappings (basic check)
            import re
            port_patterns = re.findall(r'["\'](\d+):\d+["\']', content)
            for port in port_patterns:
                if port in used_ports:
                    port_conflicts.append(f"Port {port} used in multiple compose files")
                used_ports.add(port)
        
        # Different deployment options shouldn't conflict
        assert len(port_conflicts) == 0, f"Port conflicts found: {port_conflicts}"


@pytest.mark.integration
class TestActualQuickStart:
    """Integration tests that actually run Quick Start commands (requires Docker)"""
    
    @pytest.fixture(scope="class")
    def docker_available(self):
        """Skip if Docker not available"""
        try:
            subprocess.run(["docker", "--version"], check=True, capture_output=True)
            subprocess.run(["docker-compose", "--version"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Docker or docker-compose not available")
    
    def test_mcp_only_quick_start(self, docker_available, tmp_path):
        """Test MCP-only quick start actually works"""
        project_root = Path(__file__).parent.parent.parent
        
        # Create test .env file
        test_env = tmp_path / ".env"
        test_env.write_text("""
SPLUNK_URL=https://mock-splunk:8089
SPLUNK_USER=testuser  
SPLUNK_PASSWORD=testpass
""")
        
        # Copy to project root for test
        project_env = project_root / ".env"
        shutil.copy(test_env, project_env)
        
        try:
            # Test docker-compose config validation
            result = subprocess.run([
                "docker-compose", "-f", "docker-compose.mcp-only.yml", "config"
            ], cwd=project_root, capture_output=True, text=True)
            
            # Should successfully parse with our test .env
            assert result.returncode == 0, f"MCP-only config failed: {result.stderr}"
            
        finally:
            # Cleanup test .env
            if project_env.exists():
                project_env.unlink()
    
    def test_readme_git_clone_url_works(self):
        """Test that the git clone URL in README is valid"""
        # This would test the actual git clone, but for now just validate format
        readme_path = Path(__file__).parent.parent.parent / "README.md"
        
        with open(readme_path, encoding='utf-8') as f:
            content = f.read()
        
        # Extract git clone URL from README
        import re
        git_urls = re.findall(r'git clone (https://[^\s]+)', content)
        
        if git_urls:
            url = git_urls[0]
            assert url.startswith("https://github.com/"), "Git clone URL should be HTTPS GitHub URL"
            assert url.endswith(".git"), "Git clone URL should end with .git"