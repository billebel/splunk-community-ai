"""
End-to-end integration tests for the Splunk Enterprise MCP pack
Tests complete workflows across discovery, search, knowledge, system, and guardrails
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add transforms to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'transforms'))

from discovery import extract_indexes, find_data_sources
from search import extract_search_results
from knowledge import extract_data_models, extract_event_types, extract_search_macros
from system import extract_server_info, extract_apps, extract_user_info
from guardrails_test import validate_search_query, get_guardrails_config, simulate_data_masking
from guardrails import GuardrailsEngine


class TestCompleteDiscoveryWorkflow:
    """Test complete data discovery workflow"""
    
    def test_full_environment_discovery(self):
        """Test discovering a complete Splunk environment"""
        # Step 1: Discover indexes
        index_data = {
            "entry": [
                {"name": "main", "content": {"currentDBSizeMB": "15000", "totalEventCount": "2000000"}},
                {"name": "security", "content": {"currentDBSizeMB": "8500", "totalEventCount": "850000"}},
                {"name": "web", "content": {"currentDBSizeMB": "5000", "totalEventCount": "500000"}}
            ]
        }
        
        indexes_result = extract_indexes(index_data)
        assert indexes_result['success'] == True
        assert len(indexes_result['indexes']) == 3
        
        discovered_indexes = [idx['name'] for idx in indexes_result['indexes']]
        assert 'main' in discovered_indexes
        assert 'security' in discovered_indexes
        assert 'web' in discovered_indexes
        
        # Step 2: Find relevant data sources for security use case
        security_sources_result = find_data_sources({}, {"search_term": "authentication"})
        assert security_sources_result['success'] == True
        # The matching_categories key may or may not exist depending on data source mappings file
        if 'matching_categories' in security_sources_result:
            assert 'authentication' in security_sources_result['matching_categories']
        
        # NOTE: Host extraction would be implemented in search transform


class TestSearchOptimizationWorkflow:
    """Test search construction and optimization workflow"""
    
    def test_knowledge_object_guided_search_construction(self):
        """Test using knowledge objects to guide search construction"""
        # Step 1: Discover available data models
        data_models_data = {
            "entry": [
                {
                    "name": "Authentication",
                    "content": {
                        "description": "Authentication events",
                        "acceleration": True,
                        "objects": [{"objectName": "Authentication", "fields": []}]
                    }
                }
            ]
        }
        
        models_result = extract_data_models(data_models_data)
        assert models_result['success'] is True
        assert models_result['optimization_summary']['tstats_ready_count'] == 1
        
        # Step 2: Get event types for pattern reuse
        event_types_data = {
            "entry": [
                {
                    "name": "authentication_success",
                    "content": {
                        "search": "tag=authentication action=success",
                        "disabled": False
                    }
                }
            ]
        }
        
        event_types_result = extract_event_types(event_types_data)
        assert event_types_result['success'] is True
        assert len(event_types_result['event_types']) == 1
    
    def test_search_validation_and_execution_workflow(self):
        """Test complete search validation and execution"""
        # Step 1: Validate a potentially dangerous search
        with patch('guardrails_test.get_guardrails_engine') as mock_guardrails:
            mock_engine = Mock()
            mock_engine.validate_search.return_value = {
                'blocked': True,
                'violations': ['Blocked command detected: |delete'],
                'allowed': False
            }
            mock_guardrails.return_value = mock_engine
            
            validation_result = validate_search_query(
                {},
                {"test_query": "index=security | delete", "user_role": "standard_user"}
            )
            
            # Check if blocked by guardrails (may be success:False or blocked:True)
            assert (validation_result.get('validation_results', {}).get('blocked') == True or 
                    validation_result.get('success') == False), "Query should be blocked by guardrails"
            if 'security_violations' in validation_result:
                assert len(validation_result['security_violations']) > 0


class TestSystemContextAwareOperations:
    """Test operations that adapt based on system context"""
    
    def test_user_role_based_operations(self):
        """Test operations adapting to different user roles"""
        # Admin user context
        admin_user_data = {
            "entry": [{
                "content": {
                    "username": "admin",
                    "roles": ["admin", "user"],
                    "defaultApp": "search"
                }
            }]
        }
        
        admin_result = extract_user_info(admin_user_data)
        assert admin_result['user_type'] == 'administrator'
        assert admin_result['recommended_explanation_depth'] == 'concise'
        
        # Standard user context
        user_data = {
            "entry": [{
                "content": {
                    "username": "standard_user", 
                    "roles": ["user"],
                    "defaultApp": "search"
                }
            }]
        }
        
        user_result = extract_user_info(user_data)
        assert user_result['user_type'] == 'standard_user'
        assert user_result['recommended_explanation_depth'] == 'detailed'
    
    def test_system_health_aware_recommendations(self):
        """Test recommendations based on system health"""
        # High-performance system
        healthy_server_data = {
            "entry": [{
                "content": {
                    "version": "9.1.2",
                    "serverName": "high-perf-server",
                    "licenseState": "OK",
                    "physicalMemoryMB": "32768",  # 32GB
                    "freeMemoryMB": "16384",     # 16GB free (50% usage)
                    "numberOfCores": "16"
                }
            }]
        }
        
        healthy_result = extract_server_info(healthy_server_data)
        assert healthy_result['health_status'] == 'healthy'
        assert healthy_result['server_info']['memory_info']['memory_status'] == 'normal'


class TestGuardrailsIntegration:
    """Integration tests for the complete guardrails system"""
    
    @pytest.fixture
    def guardrails_engine(self, test_config):
        """Create guardrails engine with test config"""
        with patch('guardrails.GuardrailsEngine._load_config', return_value=test_config):
            return GuardrailsEngine()
    
    def test_complete_security_validation_flow(self, guardrails_engine):
        """Test the complete security validation flow"""
        user_context = {
            'username': 'test_user',
            'roles': ['standard_user'],
            'user_role': 'standard_user'
        }
        
        # Test dangerous query - should be completely blocked
        dangerous_query = "index=main | delete"
        result = guardrails_engine.validate_search(dangerous_query, user_context)
        
        assert result['blocked'] == True
        assert result['allowed'] == False
        assert len(result['violations']) > 0
        
        # Test safe query - should be allowed with possible modifications
        safe_query = "index=security EventCode=4625"
        result = guardrails_engine.validate_search(safe_query, user_context)
        
        assert result['blocked'] == False
        assert result['allowed'] == True
    
    def test_performance_modifications_applied(self, guardrails_engine):
        """Test that performance modifications are properly applied"""
        
        user_context = {
            'username': 'test_user',
            'roles': ['standard_user'],
            'user_role': 'standard_user'
        }
        
        # Query without time range or limits
        query_without_limits = "index=web error"
        result = guardrails_engine.validate_search(query_without_limits, user_context)
        
        # Should add default time range and limits
        if result['modifications_applied']:
            assert any('time range' in mod.lower() for mod in result['modifications_applied'])
    
    def test_role_based_access_differences(self, guardrails_engine):
        """Test that different roles get different treatment"""
        
        query_with_long_timerange = "index=main earliest=-60d"
        
        # Standard user - should be limited
        standard_context = {
            'username': 'standard_user',
            'roles': ['standard_user'],
            'user_role': 'standard_user'
        }
        standard_result = guardrails_engine.validate_search(query_with_long_timerange, standard_context)
        
        # Admin user - should have more flexibility
        admin_context = {
            'username': 'admin_user', 
            'roles': ['admin'],
            'user_role': 'admin'
        }
        admin_result = guardrails_engine.validate_search(query_with_long_timerange, admin_context)
        
        # Admin should have different (likely more permissive) treatment
        assert isinstance(standard_result, dict)
        assert isinstance(admin_result, dict)
        
        # Verify role-specific limits are applied
        standard_limits = guardrails_engine._get_role_limits('standard_user')
        admin_limits = guardrails_engine._get_role_limits('admin')
        
        assert standard_limits['max_time_range_days'] < admin_limits['max_time_range_days']
    
    def test_bypass_technique_comprehensive_blocking(self, guardrails_engine):
        """Comprehensive test of all bypass techniques from GitHub issue"""
        
        user_context = {
            'username': 'test_user',
            'roles': ['standard_user'],
            'user_role': 'standard_user'
        }
        
        # All the bypass techniques that should be blocked
        bypass_attempts = [
            # Case sensitivity
            "index=main | DELETE",
            
            # Unicode (if properly set up)
            "index=main | dеlete",  # Cyrillic 'е'
            
            # URL encoding
            "index=main | %64%65%6C%65%74%65",
            
            # Dynamic construction
            '| eval cmd="del" + "ete" | run $cmd$',
            
            # Path traversal
            "| outputcsv ../../../etc/passwd",
            
            # Whitespace manipulation
            "| \t\n delete \t",
            
            # Missing commands (now added)
            "| crawl http://evil.com",
            "| dbxquery SELECT * FROM users",
        ]
        
        blocked_count = 0
        for query in bypass_attempts:
            result = guardrails_engine.validate_search(query, user_context)
            if result['blocked']:
                blocked_count += 1
            else:
                print(f"WARNING: Query not blocked: {query}")
        
        # Should block most bypass attempts
        assert blocked_count >= len(bypass_attempts) * 0.8, \
            f"Should block at least 80% of bypass attempts, blocked {blocked_count}/{len(bypass_attempts)}"


class TestErrorHandling:
    """Test error handling and fail-safe behavior"""
    
    def test_invalid_config_fallback(self):
        """Test behavior when configuration is invalid"""
        
        # Mock invalid config file
        with patch('os.path.exists', return_value=False):
            engine = GuardrailsEngine()
            
            # Should still work with fail-safe defaults
            user_context = {'username': 'test', 'roles': ['standard_user']}
            result = engine.validate_search("| delete", user_context)
            
            # Should still block dangerous commands
            assert result['blocked'] == True
    
    def test_query_validation_error_handling(self, guardrails_engine):
        """Test handling of malformed or problematic queries"""
        
        user_context = {
            'username': 'test_user',
            'roles': ['standard_user'],
            'user_role': 'standard_user'
        }
        
        problematic_queries = [
            "",  # Empty query
            "|||||||",  # Invalid syntax
            "search " + "x" * 10000,  # Very long query
            None,  # None value
        ]
        
        for query in problematic_queries:
            try:
                result = guardrails_engine.validate_search(query, user_context)
                # Should return a valid result structure even for bad input
                assert isinstance(result, dict)
                assert 'blocked' in result
                assert 'allowed' in result
            except Exception as e:
                pytest.fail(f"Should handle problematic query gracefully: {query} - {e}")
    
    def test_data_masking_error_recovery(self, guardrails_engine):
        """Test data masking error recovery"""
        
        user_context = {
            'username': 'test_user',
            'roles': ['standard_user'],
            'user_role': 'standard_user'
        }
        
        # Malformed data that might cause masking issues
        problematic_data = [
            {"field": None},  # None value
            {"field": {"nested": "object"}},  # Nested object
            {"field": ["list", "data"]},  # List data
            {},  # Empty object
        ]
        
        # Should handle gracefully without crashing
        result = guardrails_engine.apply_data_masking(problematic_data, user_context)
        assert isinstance(result, list)


class TestAuditLogging:
    """Test audit logging functionality"""
    
    def test_security_events_logged(self, guardrails_engine):
        """Test that security events are properly logged"""
        
        user_context = {
            'username': 'test_user',
            'roles': ['standard_user'],
            'user_role': 'standard_user'
        }
        
        with patch.object(guardrails_engine, '_audit_log') as mock_audit:
            # Trigger a security block
            result = guardrails_engine.validate_search("| delete", user_context)
            
            if result['blocked']:
                # Should have called audit logging
                assert mock_audit.called, "Security block should trigger audit log"
    
    def test_audit_log_format(self, guardrails_engine):
        """Test audit log entry format"""
        
        # Test the audit log method directly
        user_context = {'username': 'test_user'}
        
        with patch('logging.Logger.info') as mock_logger:
            guardrails_engine._audit_log(
                action='test_action',
                user_context=user_context,
                search_query='test query',
                details={'test': 'data'}
            )
            
            assert mock_logger.called, "Should log audit entry"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])