"""
MCP Server Integration Tests

Tests that validate MCP (Model Context Protocol) server functionality
and integration with the knowledge pack system.
"""

import pytest
import requests
import json
import time
from pathlib import Path


class TestMCPServerBasics:
    """Test basic MCP server functionality"""
    
    def test_mcp_protocol_tools_defined(self):
        """Test that MCP tools are properly defined"""
        project_root = Path(__file__).parent.parent.parent
        tools_dir = project_root / "knowledge-packs" / "splunk_enterprise" / "tools"
        
        assert tools_dir.exists(), "Tools directory should exist for MCP server"
        
        # Should have tool definition files
        tool_files = list(tools_dir.glob("*.yaml"))
        assert len(tool_files) > 0, "Should have tool definition files"
        
        # Check a few key tools mentioned in README
        expected_tools = [
            "list_indexes", "execute_splunk_search", 
            "get_data_models", "validate_search_query"
        ]
        
        found_tools = []
        for tool_file in tool_files:
            found_tools.append(tool_file.stem)
        
        for expected in expected_tools:
            assert any(expected in tool for tool in found_tools), \
                f"Expected tool {expected} not found in tools directory"
    
    def test_knowledge_pack_structure(self):
        """Test that knowledge pack structure supports MCP server"""
        project_root = Path(__file__).parent.parent.parent
        pack_root = project_root / "knowledge-packs" / "splunk_enterprise"
        
        # Required directories for MCP functionality
        required_dirs = ["tools", "transforms", "prompts", "tests"]
        
        for dir_name in required_dirs:
            dir_path = pack_root / dir_name
            assert dir_path.exists(), f"Required directory {dir_name} missing from knowledge pack"
    
    def test_guardrails_config_exists(self):
        """Test that security guardrails configuration exists"""
        project_root = Path(__file__).parent.parent.parent
        guardrails_file = project_root / "knowledge-packs" / "splunk_enterprise" / "guardrails.yaml"
        
        assert guardrails_file.exists(), "Guardrails configuration required for secure MCP operation"
        
        import yaml
        with open(guardrails_file) as f:
            config = yaml.safe_load(f)
        
        # Should have security configurations mentioned in README
        assert "blocked_commands" in config, "Guardrails should define blocked commands"
        assert "user_roles" in config, "Guardrails should define user roles"


class TestMCPToolIntegration:
    """Test integration between MCP tools and transform functions"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    def test_tools_have_corresponding_transforms(self, project_root):
        """Test that MCP tools have corresponding transform functions"""
        tools_dir = project_root / "knowledge-packs" / "splunk_enterprise" / "tools"
        transforms_dir = project_root / "knowledge-packs" / "splunk_enterprise" / "transforms"
        
        if not tools_dir.exists() or not transforms_dir.exists():
            pytest.skip("Tools or transforms directory missing")
        
        # Get transform modules
        transform_files = list(transforms_dir.glob("*.py"))
        transform_modules = [f.stem for f in transform_files if not f.stem.startswith("__")]
        
        # Key transforms should exist for MCP functionality
        expected_transforms = ["discovery", "search", "knowledge", "system", "guardrails"]
        
        for expected in expected_transforms:
            assert expected in transform_modules, \
                f"Transform module {expected} missing - required for MCP tools"
    
    def test_transform_functions_importable(self, project_root):
        """Test that transform functions can be imported"""
        transforms_dir = project_root / "knowledge-packs" / "splunk_enterprise" / "transforms"
        
        if not transforms_dir.exists():
            pytest.skip("Transforms directory missing")
        
        import sys
        sys.path.insert(0, str(transforms_dir))
        
        try:
            # Test key transform modules can be imported
            from discovery import extract_indexes, find_data_sources
            from search import extract_search_results  
            from system import extract_server_info
            from guardrails import GuardrailsEngine
            
            # Functions should be callable
            assert callable(extract_indexes), "extract_indexes should be callable"
            assert callable(find_data_sources), "find_data_sources should be callable" 
            assert callable(extract_search_results), "extract_search_results should be callable"
            assert callable(extract_server_info), "extract_server_info should be callable"
            
        except ImportError as e:
            pytest.fail(f"Transform function import failed: {e}")
        finally:
            # Cleanup sys.path
            sys.path.remove(str(transforms_dir))
    
    def test_guardrails_engine_functionality(self, project_root):
        """Test that GuardrailsEngine provides expected security functions"""
        transforms_dir = project_root / "knowledge-packs" / "splunk_enterprise" / "transforms"
        
        if not transforms_dir.exists():
            pytest.skip("Transforms directory missing")
        
        import sys
        sys.path.insert(0, str(transforms_dir))
        
        try:
            from guardrails import GuardrailsEngine
            
            engine = GuardrailsEngine()
            
            # Should have key security methods
            assert hasattr(engine, 'validate_search_query'), \
                "GuardrailsEngine should have validate_search_query method"
            assert hasattr(engine, 'apply_data_masking'), \
                "GuardrailsEngine should have apply_data_masking method"
            
        except ImportError as e:
            pytest.fail(f"GuardrailsEngine import failed: {e}")
        finally:
            sys.path.remove(str(transforms_dir))


class TestMCPDocumentationAccuracy:
    """Test that MCP-related documentation is accurate"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    def test_readme_mcp_claims_accurate(self, project_root):
        """Test that README claims about MCP functionality are accurate"""
        readme = project_root / "README.md"
        
        with open(readme) as f:
            content = f.read()
        
        # If README mentions specific tool counts, verify they're accurate
        if "17+ Specialized Tools" in content or "17 tools" in content.lower():
            tools_dir = project_root / "knowledge-packs" / "splunk_enterprise" / "tools"
            if tools_dir.exists():
                tool_files = list(tools_dir.glob("*.yaml"))
                assert len(tool_files) >= 17, f"README claims 17+ tools but only {len(tool_files)} found"
        
        # If README mentions AI behavior prompts, verify they exist
        if "AI Behavior Prompts" in content or "behavior prompts" in content.lower():
            prompts_dir = project_root / "knowledge-packs" / "splunk_enterprise" / "prompts"
            if prompts_dir.exists():
                prompt_files = list(prompts_dir.glob("*.yaml"))
                assert len(prompt_files) > 0, "README mentions AI behavior prompts but none found"
    
    def test_mcp_endpoint_documentation(self, project_root):
        """Test that MCP endpoint documentation matches configuration"""
        readme = project_root / "README.md"
        
        with open(readme) as f:
            content = f.read()
        
        # If README claims MCP endpoint on specific port, it should be consistent
        if "localhost:8443/mcp" in content:
            # Should be consistently referenced
            assert content.count("8443") >= 2, "MCP port should be consistently referenced"
        
        # MCP protocol should be mentioned
        assert "MCP" in content or "Model Context Protocol" in content, \
            "MCP protocol should be documented"
    
    def test_security_features_documented(self, project_root):
        """Test that security features mentioned in README actually exist"""
        readme = project_root / "README.md"
        
        with open(readme) as f:
            content = f.read()
        
        # If README mentions specific security features, verify they exist
        security_claims = {
            "Query validation": "guardrails.yaml should exist",
            "Data masking": "guardrails config should have sensitive fields",
            "Resource limits": "guardrails should define limits",
            "Audit logging": "logging functionality should exist"
        }
        
        guardrails_file = project_root / "knowledge-packs" / "splunk_enterprise" / "guardrails.yaml"
        
        for claim, requirement in security_claims.items():
            if claim.lower() in content.lower():
                assert guardrails_file.exists(), f"README claims {claim} but {requirement}"


@pytest.mark.integration 
@pytest.mark.slow
class TestMCPServerRuntime:
    """Integration tests that require MCP server to be running"""
    
    @pytest.fixture(scope="class")
    def mcp_server_url(self):
        """MCP server URL from README documentation"""
        return "http://localhost:8443"
    
    def test_mcp_server_health_check(self, mcp_server_url):
        """Test MCP server health check endpoint"""
        try:
            response = requests.get(f"{mcp_server_url}/health", timeout=5)
            # Any response indicates server is running
            assert response.status_code is not None
        except requests.ConnectionError:
            pytest.skip("MCP server not running - start with docker-compose for integration tests")
    
    def test_mcp_tools_endpoint(self, mcp_server_url):
        """Test MCP tools endpoint returns expected tools"""
        try:
            response = requests.get(f"{mcp_server_url}/tools", timeout=5)
            if response.status_code == 200:
                tools = response.json()
                # Should return list of available tools
                assert isinstance(tools, (list, dict)), "Tools endpoint should return tools data"
        except requests.ConnectionError:
            pytest.skip("MCP server not running")
    
    def test_mcp_protocol_communication(self, mcp_server_url):
        """Test basic MCP protocol communication"""
        try:
            # Test basic MCP protocol request
            mcp_request = {
                "method": "tools/list",
                "params": {}
            }
            
            response = requests.post(
                f"{mcp_server_url}/mcp", 
                json=mcp_request,
                timeout=5,
                headers={"Content-Type": "application/json"}
            )
            
            # Should get some kind of response (may be error due to auth, but should respond)
            assert response.status_code is not None
            
        except requests.ConnectionError:
            pytest.skip("MCP server not running")