"""
Comprehensive tests for system transform functions
Tests server info, apps, and user context extraction
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add transforms to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'transforms'))

from system import (
    extract_server_info,
    extract_apps,
    extract_user_info,
    _safe_int
)


class TestExtractServerInfo:
    """Test server information extraction and health assessment"""
    
    @pytest.fixture
    def sample_server_info_response(self):
        """Sample Splunk server info API response"""
        return {
            "entry": [{
                "content": {
                    "version": "9.1.2",
                    "build": "b6b9c8185839",
                    "serverName": "splunk-server-01",
                    "licenseState": "OK",
                    "server_roles": ["indexer", "search_head"],
                    "cluster_mode": "master",
                    "cpu_arch": "x86_64",
                    "numberOfCores": "8",
                    "os_name": "Linux",
                    "os_version": "Ubuntu 20.04.6 LTS",
                    "physicalMemoryMB": "16384",
                    "freeMemoryMB": "4096"
                }
            }]
        }
    
    def test_extract_server_info_success(self, sample_server_info_response):
        """Test successful server info extraction"""
        result = extract_server_info(sample_server_info_response)
        
        assert result['success'] is True
        
        server_info = result['server_info']
        assert server_info['splunk_version'] == '9.1.2'
        assert server_info['server_name'] == 'splunk-server-01'
        assert server_info['license_state'] == 'OK'
        assert server_info['cluster_mode'] == 'master'
        
        # Check system info
        assert server_info['system_info']['cpu_arch'] == 'x86_64'
        assert server_info['system_info']['number_of_cores'] == 8
        assert server_info['system_info']['os_name'] == 'Linux'
        
        # Check memory calculations
        assert server_info['memory_info']['physical_memory_mb'] == 16384
        assert server_info['memory_info']['free_memory_mb'] == 4096
        assert server_info['memory_info']['memory_usage_percent'] == 75.0
        assert server_info['memory_info']['memory_status'] == 'moderate'
        
        # Check health status
        assert result['health_status'] == 'healthy'
        assert result['health_indicators'] == []
        
        # Check system summary
        assert 'Splunk 9.1.2 on splunk-server-01' in result['system_summary']
        assert '8 cores' in result['system_summary']
        assert '16384MB RAM' in result['system_summary']
    
    def test_extract_server_info_high_memory_usage(self):
        """Test server with high memory usage"""
        high_memory_response = {
            "entry": [{
                "content": {
                    "version": "9.1.2",
                    "serverName": "memory-stressed-server",
                    "licenseState": "OK",
                    "physicalMemoryMB": "8192",
                    "freeMemoryMB": "512"  # Only 6.25% free (93.75% used)
                }
            }]
        }
        
        result = extract_server_info(high_memory_response)
        
        assert result['success'] is True
        assert result['server_info']['memory_info']['memory_usage_percent'] == 93.8
        assert result['server_info']['memory_info']['memory_status'] == 'high'
        assert result['health_status'] == 'attention_needed'
        assert 'high_memory_usage' in result['health_indicators']
    
    def test_extract_server_info_license_issue(self):
        """Test server with license issues"""
        license_issue_response = {
            "entry": [{
                "content": {
                    "version": "9.1.2",
                    "serverName": "license-issue-server",
                    "licenseState": "EXPIRED",
                    "physicalMemoryMB": "8192", 
                    "freeMemoryMB": "4096"
                }
            }]
        }
        
        result = extract_server_info(license_issue_response)
        
        assert result['success'] is True
        assert result['health_status'] == 'attention_needed'
        assert 'license_issue' in result['health_indicators']
        assert result['server_info']['license_state'] == 'EXPIRED'
    
    def test_extract_server_info_missing_memory_data(self):
        """Test server info with missing memory data"""
        no_memory_response = {
            "entry": [{
                "content": {
                    "version": "9.1.2",
                    "serverName": "no-memory-data",
                    "licenseState": "OK"
                    # Missing memory fields
                }
            }]
        }
        
        result = extract_server_info(no_memory_response)
        
        assert result['success'] is True
        # Should handle missing memory data gracefully
        assert result['server_info']['memory_info']['physical_memory_mb'] == 0
        assert 'memory_usage_percent' not in result['server_info']['memory_info']
    
    def test_extract_server_info_error_handling(self):
        """Test error handling"""
        result = extract_server_info({})
        
        assert result['success'] is True
        # Function handles errors gracefully by returning defaults
        assert result['server_info']['server_name'] == 'unknown'


class TestExtractApps:
    """Test Splunk applications extraction"""
    
    @pytest.fixture
    def sample_apps_response(self):
        """Sample Splunk apps API response"""
        return {
            "entry": [
                {
                    "name": "search",
                    "content": {
                        "label": "Search & Reporting",
                        "version": "9.1.2",
                        "author": "Splunk",
                        "description": "Default search application for Splunk Enterprise",
                        "disabled": False,
                        "visible": True,
                        "configured": True
                    }
                },
                {
                    "name": "enterprise_security", 
                    "content": {
                        "label": "Splunk Enterprise Security",
                        "version": "7.3.0",
                        "author": "Splunk Inc.",
                        "description": "Premier security information and event management (SIEM) solution that provides insight into machine-generated data from security technologies such as network, endpoint, access, malware, vulnerability and identity information.",
                        "disabled": False,
                        "visible": True,
                        "configured": True
                    }
                },
                {
                    "name": "unix_app",
                    "content": {
                        "label": "Splunk Add-on for Unix and Linux",
                        "version": "8.9.0",
                        "author": "Splunk",
                        "description": "Unix and Linux monitoring capabilities",
                        "disabled": True,  # Disabled app
                        "visible": True,
                        "configured": False
                    }
                },
                {
                    "name": "internal_app",
                    "content": {
                        "label": "Internal App",
                        "version": "1.0.0", 
                        "disabled": False,
                        "visible": False  # Hidden app
                    }
                }
            ]
        }
    
    def test_extract_apps_success(self, sample_apps_response):
        """Test successful apps extraction"""
        result = extract_apps(sample_apps_response)
        
        assert result['success'] is True
        assert result['count'] == 4
        
        # Check summary counts
        summary = result['summary']
        assert summary['total_apps'] == 4
        assert 'search' in summary['enabled_apps']
        assert 'enterprise_security' in summary['enabled_apps']
        assert 'unix_app' in summary['disabled_apps']
        assert 'search' in summary['visible_apps']
        assert 'internal_app' not in summary['visible_apps']  # Hidden app excluded
        
        # Check key apps categorization
        key_apps = result['key_apps']
        assert 'enterprise_security' in key_apps['security_apps']
        assert 'unix_app' in key_apps['it_ops_apps']
        
        # Apps should be sorted with disabled last
        assert result['apps'][0]['disabled'] is False
        assert any(app['disabled'] for app in result['apps'][-2:])  # Disabled apps at end
    
    def test_extract_apps_description_truncation(self):
        """Test long description truncation"""
        long_desc_app = {
            "entry": [{
                "name": "long_desc_app",
                "content": {
                    "description": "a" * 250,  # Very long description
                    "disabled": False,
                    "visible": True
                }
            }]
        }
        
        result = extract_apps(long_desc_app)
        
        assert result['success'] is True
        app_desc = result['apps'][0]['description']
        assert len(app_desc) == 203  # 200 chars + '...'
        assert app_desc.endswith('...')
    
    def test_extract_apps_app_categorization(self):
        """Test automatic app categorization"""
        categorization_test_apps = {
            "entry": [
                {"name": "splunk_security_essentials", "content": {"disabled": False}},
                {"name": "itsi", "content": {"disabled": False}},
                {"name": "db_connect", "content": {"disabled": False}},
                {"name": "aws_addon", "content": {"disabled": False}},
                {"name": "fraud_analytics", "content": {"disabled": False}}
            ]
        }
        
        result = extract_apps(categorization_test_apps)
        
        key_apps = result['key_apps']
        assert 'splunk_security_essentials' in key_apps['security_apps']
        assert 'fraud_analytics' in key_apps['security_apps']
        assert 'itsi' in key_apps['it_ops_apps']
        assert 'db_connect' in key_apps['data_apps']
        assert 'aws_addon' in key_apps['data_apps']
    
    def test_extract_apps_empty_response(self):
        """Test empty apps response"""
        result = extract_apps({"entry": []})
        
        assert result['success'] is True
        assert result['apps'] == []
        assert result['count'] == 0
    
    def test_extract_apps_error_handling(self):
        """Test error handling"""
        result = extract_apps({"invalid": "structure"})
        
        assert result['success'] is True
        assert result['apps'] == []
        assert result['count'] == 0


class TestExtractUserInfo:
    """Test user context and permissions extraction"""
    
    @pytest.fixture
    def sample_admin_user_response(self):
        """Sample admin user context response"""
        return {
            "entry": [{
                "content": {
                    "username": "admin",
                    "realname": "System Administrator",
                    "email": "admin@company.com",
                    "roles": ["admin", "user"],
                    "defaultApp": "search",
                    "tz": "America/New_York"
                }
            }]
        }
    
    @pytest.fixture
    def sample_power_user_response(self):
        """Sample power user context response"""
        return {
            "entry": [{
                "content": {
                    "username": "power_user",
                    "realname": "Power User",
                    "roles": ["power", "user"],
                    "defaultApp": "search",
                    "tz": "UTC"
                }
            }]
        }
    
    @pytest.fixture
    def sample_standard_user_response(self):
        """Sample standard user context response"""
        return {
            "entry": [{
                "content": {
                    "username": "standard_user",
                    "realname": "Standard User",
                    "roles": ["user"],
                    "defaultApp": "search"
                }
            }]
        }
    
    def test_extract_user_info_admin(self, sample_admin_user_response):
        """Test admin user extraction"""
        result = extract_user_info(sample_admin_user_response)
        
        assert result['success'] is True
        
        user_info = result['user_info']
        assert user_info['username'] == 'admin'
        assert user_info['email'] == 'admin@company.com'
        assert 'admin' in user_info['roles']
        assert user_info['timezone'] == 'America/New_York'
        
        # Check capabilities
        capabilities = result['capabilities']
        assert capabilities['is_admin'] is True
        assert capabilities['can_search_all_indexes'] is True
        assert capabilities['can_create_knowledge_objects'] is True
        assert capabilities['can_install_apps'] is True
        assert capabilities['can_manage_users'] is True
        
        # Check user type and explanation depth
        assert result['user_type'] == 'administrator'
        assert result['recommended_explanation_depth'] == 'concise'
        assert 'admin (administrator)' in result['role_summary']
    
    def test_extract_user_info_power_user(self, sample_power_user_response):
        """Test power user extraction"""
        result = extract_user_info(sample_power_user_response)
        
        assert result['success'] is True
        
        capabilities = result['capabilities']
        assert capabilities['is_admin'] is False
        assert capabilities['is_power_user'] is True
        assert capabilities['can_search_all_indexes'] is True
        assert capabilities['can_create_knowledge_objects'] is True
        assert capabilities['can_install_apps'] is False
        
        assert result['user_type'] == 'power_user'
        assert result['recommended_explanation_depth'] == 'balanced'
    
    def test_extract_user_info_standard_user(self, sample_standard_user_response):
        """Test standard user extraction"""
        result = extract_user_info(sample_standard_user_response)
        
        assert result['success'] is True
        
        capabilities = result['capabilities']
        assert capabilities['is_admin'] is False
        assert capabilities['is_power_user'] is False
        assert capabilities['can_search_all_indexes'] is False
        assert capabilities['can_create_knowledge_objects'] is False
        
        assert result['user_type'] == 'standard_user'
        assert result['recommended_explanation_depth'] == 'detailed'
    
    def test_extract_user_info_sc_admin_role(self):
        """Test user with sc_admin role (should be treated as power user)"""
        sc_admin_response = {
            "entry": [{
                "content": {
                    "username": "sc_admin",
                    "roles": ["sc_admin", "user"]
                }
            }]
        }
        
        result = extract_user_info(sc_admin_response)
        
        assert result['success'] is True
        assert result['capabilities']['is_power_user'] is True
        assert result['capabilities']['can_create_knowledge_objects'] is False
    
    def test_extract_user_info_missing_fields(self):
        """Test user info with missing optional fields"""
        minimal_response = {
            "entry": [{
                "content": {
                    "username": "minimal_user",
                    "roles": ["user"]
                    # Missing real name, email, timezone, etc.
                }
            }]
        }
        
        result = extract_user_info(minimal_response)
        
        assert result['success'] is True
        assert result['user_info']['username'] == 'minimal_user'
        assert result['user_info']['real_name'] == ''  # Default empty string
        assert result['user_info']['timezone'] == 'UTC'  # Default timezone
    
    def test_extract_user_info_error_handling(self):
        """Test error handling"""
        result = extract_user_info({})
        
        assert result['success'] is True
        # Function handles errors gracefully by returning defaults
        assert result['user_info']['default_app'] == 'search'
        assert result['user_type'] == 'standard_user'
        assert result['recommended_explanation_depth'] == 'detailed'


class TestSafeIntUtility:
    """Test the _safe_int utility function"""
    
    def test_safe_int_integers(self):
        """Test _safe_int with integer inputs"""
        assert _safe_int(5) == 5
        assert _safe_int(0) == 0
        assert _safe_int(-10) == -10
    
    def test_safe_int_floats(self):
        """Test _safe_int with float inputs"""
        assert _safe_int(5.7) == 5
        assert _safe_int(5.2) == 5
        assert _safe_int(-3.8) == -3
    
    def test_safe_int_strings(self):
        """Test _safe_int with string inputs"""
        assert _safe_int("123") == 123
        assert _safe_int("0") == 0
        assert _safe_int("-456") == -456
        assert _safe_int("123.45") == 123
        assert _safe_int("invalid") == 0
        assert _safe_int("") == 0
    
    def test_safe_int_invalid_inputs(self):
        """Test _safe_int with invalid inputs"""
        assert _safe_int(None) == 0
        assert _safe_int([1, 2, 3]) == 0
        assert _safe_int({"key": "value"}) == 0
        assert _safe_int(object()) == 0


class TestSystemIntegrationScenarios:
    """Integration tests for system functions"""
    
    def test_complete_system_discovery_workflow(self):
        """Test complete system discovery workflow"""
        # Mock server info
        server_response = {
            "entry": [{"content": {"version": "9.1.2", "serverName": "test-server", "licenseState": "OK"}}]
        }
        
        # Mock apps
        apps_response = {
            "entry": [{"name": "search", "content": {"disabled": False, "visible": True}}]
        }
        
        # Mock user info
        user_response = {
            "entry": [{"content": {"username": "test_user", "roles": ["user"]}}]
        }
        
        # Test each system function
        server_result = extract_server_info(server_response)
        apps_result = extract_apps(apps_response)
        user_result = extract_user_info(user_response)
        
        # All should succeed
        assert server_result['success'] is True
        assert apps_result['success'] is True  
        assert user_result['success'] is True
        
        # Should provide complementary system context
        assert server_result['server_info']['splunk_version'] == '9.1.2'
        assert apps_result['summary']['total_apps'] > 0
        assert user_result['user_type'] in ['administrator', 'power_user', 'standard_user']
    
    def test_system_health_assessment_integration(self):
        """Test system health assessment across functions"""
        # Server with issues
        unhealthy_server = {
            "entry": [{
                "content": {
                    "version": "9.1.2",
                    "licenseState": "EXPIRED",
                    "physicalMemoryMB": "4096",
                    "freeMemoryMB": "256"  # High memory usage
                }
            }]
        }
        
        # Apps with many disabled
        problematic_apps = {
            "entry": [
                {"name": "app1", "content": {"disabled": True}},
                {"name": "app2", "content": {"disabled": True}},
                {"name": "app3", "content": {"disabled": False}}
            ]
        }
        
        server_result = extract_server_info(unhealthy_server)
        apps_result = extract_apps(problematic_apps)
        
        # Should detect health issues
        assert server_result['health_status'] == 'attention_needed'
        assert 'license_issue' in server_result['health_indicators']
        assert 'high_memory_usage' in server_result['health_indicators']
        
        # Should show app status
        assert len(apps_result['summary']['disabled_apps']) == 2
        assert len(apps_result['summary']['enabled_apps']) == 1
    
    def test_error_recovery_scenarios(self):
        """Test error handling across system functions"""
        error_scenarios = [
            None,  # None input
            {},    # Empty dict
            {"invalid": "structure"},  # Wrong structure
            {"entry": "not_a_list"}    # Wrong data type
        ]
        
        system_functions = [
            extract_server_info,
            extract_apps,
            extract_user_info
        ]
        
        for scenario in error_scenarios:
            for func in system_functions:
                result = func(scenario)
                # All functions should handle errors gracefully
                assert 'success' in result
                # Functions handle errors gracefully by returning success=True with defaults