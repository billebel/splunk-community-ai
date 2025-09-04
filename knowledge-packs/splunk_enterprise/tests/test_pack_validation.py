"""
Test pack validation for Splunk Enterprise v2
Ensures the pack structure and configuration are valid
"""

import pytest
import os
import yaml
from jsonschema import validate, ValidationError


class TestPackStructure:
    """Test the basic pack structure and files"""
    
    @pytest.fixture
    def pack_root(self):
        """Get the pack root directory"""
        return os.path.dirname(os.path.dirname(__file__))
    
    def test_pack_yaml_exists(self, pack_root):
        """Test that pack.yaml exists and is valid"""
        pack_yaml_path = os.path.join(pack_root, 'pack.yaml')
        assert os.path.exists(pack_yaml_path), "pack.yaml should exist"
        
        with open(pack_yaml_path, 'r', encoding='utf-8') as f:
            pack_config = yaml.safe_load(f)
        
        # Basic validation
        assert 'metadata' in pack_config, "pack.yaml should have metadata section"
        assert 'connection' in pack_config, "pack.yaml should have connection section"
        assert 'tools' in pack_config, "pack.yaml should have tools section"
        
        # Metadata validation
        metadata = pack_config['metadata']
        assert 'name' in metadata, "metadata should have name"
        assert 'version' in metadata, "metadata should have version"
        assert 'description' in metadata, "metadata should have description"
        
        # Connection validation
        connection = pack_config['connection']
        assert 'type' in connection, "connection should have type"
        assert 'base_url' in connection, "connection should have base_url"
    
    def test_guardrails_config_exists(self, pack_root):
        """Test that guardrails.yaml exists and is valid"""
        guardrails_path = os.path.join(pack_root, 'guardrails.yaml')
        assert os.path.exists(guardrails_path), "guardrails.yaml should exist"
        
        with open(guardrails_path, 'r', encoding='utf-8') as f:
            guardrails_config = yaml.safe_load(f)
        
        # Validate guardrails structure
        assert 'guardrails' in guardrails_config, "Should have guardrails section"
        assert 'security' in guardrails_config, "Should have security section"
        assert 'performance' in guardrails_config, "Should have performance section"
        assert 'privacy' in guardrails_config, "Should have privacy section"
    
    def test_transform_files_exist(self, pack_root):
        """Test that required transform files exist"""
        transforms_dir = os.path.join(pack_root, 'transforms')
        assert os.path.exists(transforms_dir), "transforms directory should exist"
        
        required_transforms = [
            'guardrails.py',
            'guardrails_test.py', 
            'search.py'
        ]
        
        for transform in required_transforms:
            transform_path = os.path.join(transforms_dir, transform)
            assert os.path.exists(transform_path), f"Transform {transform} should exist"
    
    def test_tools_directory_structure(self, pack_root):
        """Test tools directory structure"""
        tools_dir = os.path.join(pack_root, 'tools')
        assert os.path.exists(tools_dir), "tools directory should exist"
        
        expected_tool_files = [
            'data-discovery-tools.yaml',
            'knowledge-objects-tools.yaml', 
            'system-info-tools.yaml',
            'guardrails-tools.yaml'
        ]
        
        for tool_file in expected_tool_files:
            tool_path = os.path.join(tools_dir, tool_file)
            assert os.path.exists(tool_path), f"Tool file {tool_file} should exist"


class TestGuardrailsConfiguration:
    """Test guardrails configuration validity"""
    
    @pytest.fixture
    def guardrails_config(self):
        """Load guardrails configuration"""
        pack_root = os.path.dirname(os.path.dirname(__file__))
        guardrails_path = os.path.join(pack_root, 'guardrails.yaml')
        
        with open(guardrails_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def test_blocked_commands_format(self, guardrails_config):
        """Test that blocked commands are properly formatted"""
        blocked_commands = guardrails_config['security']['blocked_commands']
        
        assert isinstance(blocked_commands, list), "Blocked commands should be a list"
        assert len(blocked_commands) > 0, "Should have at least some blocked commands"
        
        for command in blocked_commands:
            assert isinstance(command, str), "Each blocked command should be a string"
            assert command.startswith('|'), "Commands should start with pipe symbol"
    
    def test_security_patterns_validity(self, guardrails_config):
        """Test that security patterns are valid regex"""
        import re
        
        patterns_to_test = [
            ('blocked_patterns', guardrails_config['security']['blocked_patterns']),
            ('warning_patterns', guardrails_config['security']['warning_patterns'])
        ]
        
        for pattern_type, patterns in patterns_to_test:
            for pattern in patterns:
                try:
                    re.compile(pattern)
                except re.error as e:
                    pytest.fail(f"Invalid regex in {pattern_type}: {pattern} - {e}")
    
    def test_user_roles_configuration(self, guardrails_config):
        """Test user roles configuration"""
        user_roles = guardrails_config['user_roles']
        
        expected_roles = ['admin', 'power_user', 'standard_user', 'readonly_user']
        for role in expected_roles:
            assert role in user_roles, f"Should have {role} role configuration"
            
            role_config = user_roles[role]
            required_fields = [
                'max_time_range_days', 'max_results_per_search',
                'search_timeout_seconds', 'data_masking_enabled'
            ]
            
            for field in required_fields:
                assert field in role_config, f"Role {role} should have {field}"
    
    def test_sensitive_fields_configuration(self, guardrails_config):
        """Test sensitive fields configuration for data masking"""
        privacy_config = guardrails_config['privacy']
        
        assert 'sensitive_fields' in privacy_config, "Should have sensitive fields list"
        assert 'masking_patterns' in privacy_config, "Should have masking patterns"
        
        sensitive_fields = privacy_config['sensitive_fields']
        assert isinstance(sensitive_fields, list), "Sensitive fields should be a list"
        assert len(sensitive_fields) > 0, "Should have some sensitive fields defined"
        
        # Check for common sensitive field patterns
        expected_patterns = ['password', 'email', 'ssn', 'token']
        for pattern in expected_patterns:
            assert any(pattern in field for field in sensitive_fields), \
                f"Should include {pattern} in sensitive fields"


class TestToolsConfiguration:
    """Test tools configuration files"""
    
    @pytest.fixture
    def pack_root(self):
        return os.path.dirname(os.path.dirname(__file__))
    
    def test_tool_files_valid_yaml(self, pack_root):
        """Test that all tool files are valid YAML"""
        tools_dir = os.path.join(pack_root, 'tools')
        
        for filename in os.listdir(tools_dir):
            if filename.endswith('.yaml'):
                file_path = os.path.join(tools_dir, filename)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        config = yaml.safe_load(f)
                        assert isinstance(config, dict), f"{filename} should contain a dictionary"
                        assert 'tools' in config, f"{filename} should have tools section"
                    except yaml.YAMLError as e:
                        pytest.fail(f"Invalid YAML in {filename}: {e}")
    
    def test_guardrails_tools_configuration(self, pack_root):
        """Test guardrails tools specifically"""
        guardrails_tools_path = os.path.join(pack_root, 'tools', 'guardrails-tools.yaml')
        
        with open(guardrails_tools_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        expected_tools = [
            'validate_search_query',
            'get_guardrails_config', 
            'test_data_masking'
        ]
        
        tools = config['tools']
        for tool_name in expected_tools:
            assert tool_name in tools, f"Should have {tool_name} tool"
            
            tool_config = tools[tool_name]
            assert 'type' in tool_config, f"{tool_name} should have type"
            assert 'description' in tool_config, f"{tool_name} should have description"
            assert 'transform' in tool_config, f"{tool_name} should have transform"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])