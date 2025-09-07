"""
Pack Configuration Validation Tests

These tests validate that the pack.yaml and tool configuration files
are correctly structured and contain the proper parameters for Splunk API integration.

This is critical for ensuring that configuration changes don't break API compatibility.
"""

import pytest
import yaml
import os
from pathlib import Path


class TestPackYAMLConfiguration:
    """Test pack.yaml configuration for correct API integration"""
    
    @pytest.fixture
    def pack_config(self):
        """Load the pack.yaml configuration"""
        pack_path = Path(__file__).parent.parent / "pack.yaml"
        with open(pack_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def test_execute_splunk_search_configuration(self, pack_config):
        """
        CRITICAL TEST: Validate execute_splunk_search tool configuration
        
        This test ensures that the execute_splunk_search tool has the correct
        form_data configuration that includes the 'search' prefix fix.
        """
        # Find the execute_splunk_search tool
        tools = pack_config.get('tools', {})
        execute_search = tools.get('execute_splunk_search')
        
        assert execute_search is not None, "execute_splunk_search tool not found in pack.yaml"
        
        # Check form_data configuration
        form_data = execute_search.get('form_data', {})
        assert form_data, "form_data section missing from execute_splunk_search"
        
        # CRITICAL: Validate the search parameter includes the 'search' prefix
        search_param = form_data.get('search')
        assert search_param is not None, "search parameter missing from form_data"
        assert search_param == "search {search_query}", \
            f"search parameter should be 'search {{search_query}}', got: '{search_param}'"
        
        # Validate other required parameters
        assert form_data.get('output_mode') == 'json', "output_mode should be 'json'"
        assert form_data.get('exec_mode') == 'oneshot', "exec_mode should be 'oneshot'"
        
        # Validate parameter substitution placeholders
        assert '{earliest_time}' in form_data.get('earliest_time', ''), \
            "earliest_time should contain {earliest_time} placeholder"
        assert '{latest_time}' in form_data.get('latest_time', ''), \
            "latest_time should contain {latest_time} placeholder"
        assert '{max_results}' in form_data.get('count', ''), \
            "count should contain {max_results} placeholder"
    
    def test_tool_parameters_configuration(self, pack_config):
        """Test that tool parameters are correctly defined"""
        tools = pack_config.get('tools', {})
        execute_search = tools.get('execute_splunk_search')
        
        # Check parameters section
        parameters = execute_search.get('parameters', [])
        assert len(parameters) > 0, "execute_splunk_search should have parameters"
        
        # Convert to dict for easier checking
        param_names = [p['name'] for p in parameters]
        
        # Required parameters
        assert 'search_query' in param_names, "search_query parameter missing"
        assert 'earliest_time' in param_names, "earliest_time parameter missing"
        assert 'latest_time' in param_names, "latest_time parameter missing"
        assert 'max_results' in param_names, "max_results parameter missing"
        
        # Validate search_query parameter is required
        search_query_param = next(p for p in parameters if p['name'] == 'search_query')
        assert search_query_param.get('required') == True, \
            "search_query parameter should be required"
        assert search_query_param.get('type') == 'string', \
            "search_query parameter should be type 'string'"
    
    def test_headers_configuration(self, pack_config):
        """Test that HTTP headers are correctly configured"""
        tools = pack_config.get('tools', {})
        execute_search = tools.get('execute_splunk_search')
        
        # Check headers section
        headers = execute_search.get('headers', {})
        assert headers, "headers section missing from execute_splunk_search"
        
        # Validate Content-Type header
        content_type = headers.get('Content-Type')
        assert content_type == 'application/x-www-form-urlencoded', \
            f"Content-Type should be 'application/x-www-form-urlencoded', got: '{content_type}'"
    
    def test_endpoint_configuration(self, pack_config):
        """Test that API endpoints are correctly configured"""
        tools = pack_config.get('tools', {})
        execute_search = tools.get('execute_splunk_search')
        
        # Check endpoint and method
        endpoint = execute_search.get('endpoint')
        method = execute_search.get('method')
        
        assert endpoint == '/services/search/jobs/oneshot', \
            f"endpoint should be '/services/search/jobs/oneshot', got: '{endpoint}'"
        assert method == 'POST', \
            f"method should be 'POST', got: '{method}'"


class TestDataDiscoveryToolsConfiguration:
    """Test data-discovery-tools.yaml configuration"""
    
    @pytest.fixture
    def discovery_tools_config(self):
        """Load the data-discovery-tools.yaml configuration"""
        tools_path = Path(__file__).parent.parent / "tools" / "data-discovery-tools.yaml"
        with open(tools_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def test_get_sourcetypes_configuration(self, discovery_tools_config):
        """Test get_sourcetypes tool configuration"""
        tools = discovery_tools_config.get('tools', {})
        get_sourcetypes = tools.get('get_sourcetypes')
        
        assert get_sourcetypes is not None, "get_sourcetypes tool not found"
        
        # Check form_data
        form_data = get_sourcetypes.get('form_data', {})
        search_query = form_data.get('search')
        
        # This tool uses metadata command, which is correct (doesn't need 'search' prefix)
        assert search_query.startswith('| metadata'), \
            "get_sourcetypes should use '| metadata' command (no 'search' prefix needed)"
        
        # Validate parameter substitution
        assert '{index_name}' in search_query, \
            "search query should contain {index_name} parameter"
        assert '{max_sourcetypes}' in search_query, \
            "search query should contain {max_sourcetypes} parameter"
    
    def test_get_hosts_configuration(self, discovery_tools_config):
        """Test get_hosts tool configuration"""
        tools = discovery_tools_config.get('tools', {})
        get_hosts = tools.get('get_hosts')
        
        assert get_hosts is not None, "get_hosts tool not found"
        
        # Check form_data
        form_data = get_hosts.get('form_data', {})
        search_query = form_data.get('search')
        
        # This tool also uses metadata command, which is correct
        assert search_query.startswith('| metadata'), \
            "get_hosts should use '| metadata' command (no 'search' prefix needed)"
        
        # Validate parameter substitution
        assert '{index_filter}' in search_query, \
            "search query should contain {index_filter} parameter"
        assert '{max_hosts}' in search_query, \
            "search query should contain {max_hosts} parameter"
    
    def test_list_indexes_configuration(self, discovery_tools_config):
        """Test list_indexes tool configuration (GET endpoint)"""
        tools = discovery_tools_config.get('tools', {})
        list_indexes = tools.get('list_indexes')
        
        assert list_indexes is not None, "list_indexes tool not found"
        
        # This should be a GET request, not POST
        method = list_indexes.get('method')
        endpoint = list_indexes.get('endpoint')
        
        assert method == 'GET', f"list_indexes should use GET method, got: '{method}'"
        assert endpoint == '/services/data/indexes', \
            f"list_indexes should use '/services/data/indexes' endpoint, got: '{endpoint}'"
        
        # Should use query_params, not form_data
        query_params = list_indexes.get('query_params', {})
        assert 'output_mode' in query_params, "list_indexes should have output_mode in query_params"
        assert query_params['output_mode'] == 'json', "output_mode should be 'json'"


class TestTransformConfiguration:
    """Test transform configurations"""
    
    def test_transform_engine_support(self):
        """Test that transforms are configured for supported engines"""
        # This validates that our transforms are set up for the engines
        # that the external catalyst_mcp actually supports
        
        # Currently, Python transforms are not supported by catalyst_mcp
        # So we need to ensure we have fallback mechanisms
        
        # Check that transform files exist
        transforms_dir = Path(__file__).parent.parent / "transforms"
        
        expected_transforms = [
            "search.py",
            "discovery.py", 
            "knowledge.py",
            "system.py",
            "guardrails.py"
        ]
        
        for transform in expected_transforms:
            transform_path = transforms_dir / transform
            assert transform_path.exists(), f"Transform file missing: {transform}"
        
        # Also check the nested directory (for catalyst_mcp compatibility)
        nested_transforms_dir = transforms_dir / "transforms"
        for transform in expected_transforms:
            nested_path = nested_transforms_dir / transform
            assert nested_path.exists(), f"Nested transform file missing: {transform}"


class TestRegressionValidation:
    """Regression validation tests"""
    
    @pytest.fixture
    def pack_config(self):
        """Load the pack.yaml configuration"""
        pack_path = Path(__file__).parent.parent / "pack.yaml"
        with open(pack_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def test_search_prefix_regression_in_config(self, pack_config):
        """
        REGRESSION TEST: Validate search prefix fix in configuration
        
        This test prevents regression by ensuring that the pack.yaml
        configuration maintains the 'search {search_query}' format
        that fixed the HTTP 400 Bad Request issues.
        """
        tools = pack_config.get('tools', {})
        execute_search = tools.get('execute_splunk_search')
        
        form_data = execute_search.get('form_data', {})
        search_param = form_data.get('search')
        
        # CRITICAL: This must be exactly 'search {search_query}'
        # Any change to this format will break Splunk API integration
        assert search_param == 'search {search_query}', \
            f"REGRESSION DETECTED: search parameter changed from 'search {{search_query}}' to '{search_param}'"
        
        # Additional validation to ensure the fix remains in place
        assert search_param.startswith('search '), \
            f"REGRESSION: search parameter must start with 'search ', got: '{search_param}'"
        assert '{search_query}' in search_param, \
            f"REGRESSION: search parameter must contain {{search_query}} placeholder, got: '{search_param}'"
    
    def test_configuration_completeness(self, pack_config):
        """Test that all required configuration elements are present"""
        # Validate top-level structure
        assert 'metadata' in pack_config, "pack.yaml missing 'metadata' field"
        assert 'tools' in pack_config, "pack.yaml missing 'tools' section"
        
        # Validate metadata structure
        metadata = pack_config['metadata']
        assert 'name' in metadata, "pack.yaml metadata missing 'name' field"
        assert 'version' in metadata, "pack.yaml metadata missing 'version' field"
        
        # Validate connection configuration
        if 'connection' in pack_config:
            connection = pack_config['connection']
            assert 'type' in connection, "connection missing 'type' field"
            assert connection['type'] == 'rest', "connection type should be 'rest'"
    
    def test_parameter_validation_rules(self, pack_config):
        """Test parameter validation rules in tools"""
        tools = pack_config.get('tools', {})
        execute_search = tools.get('execute_splunk_search')
        
        parameters = execute_search.get('parameters', [])
        
        # Find max_results parameter
        max_results = next((p for p in parameters if p['name'] == 'max_results'), None)
        assert max_results is not None, "max_results parameter not found"
        
        # Validate constraints
        assert max_results.get('min_value') == 1, "max_results min_value should be 1"
        assert max_results.get('max_value') == 1000, "max_results max_value should be 1000"
        assert max_results.get('default') == 100, "max_results default should be 100"


if __name__ == "__main__":
    # Run with: python -m pytest test_pack_configuration.py -v
    pytest.main([__file__, "-v"])