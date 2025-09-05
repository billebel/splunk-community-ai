"""
Comprehensive tests for search transform functions
Tests search result processing, data masking, and guardrails integration
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add transforms to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'transforms'))

from search import extract_search_results


class TestExtractSearchResults:
    """Test search result extraction and processing"""
    
    @pytest.fixture
    def sample_splunk_response(self):
        """Sample Splunk oneshot search response"""
        return {
            "results": [
                {
                    "_time": "2024-01-15T10:30:00Z",
                    "host": "web-server-01",
                    "source": "/var/log/auth.log",
                    "sourcetype": "linux_secure",
                    "username": "john.doe@company.com",
                    "password": "secretpassword123",
                    "ssn": "123-45-6789",
                    "ip_address": "192.168.1.100",
                    "action": "login_attempt",
                    "result": "success",
                    "_raw": "Jan 15 10:30:00 web-server-01 sshd[12345]: Accepted publickey for john.doe from 192.168.1.100"
                },
                {
                    "_time": "2024-01-15T10:31:00Z", 
                    "host": "web-server-02",
                    "source": "/var/log/auth.log",
                    "sourcetype": "linux_secure", 
                    "username": "admin",
                    "email": "admin@company.com",
                    "credit_card": "4532-1234-5678-9012",
                    "phone": "555-123-4567",
                    "action": "admin_access",
                    "result": "granted"
                }
            ]
        }
    
    def test_extract_search_results_basic(self, sample_splunk_response):
        """Test basic search result extraction"""
        variables = {
            "search_query": "index=security EventCode=4625",
            "max_results": 1000
        }
        
        result = extract_search_results(sample_splunk_response, variables)
        
        assert result['success'] == True
        assert 'events' in result
        assert len(result['events']) == 2
        assert 'field_summary' in result
    
    def test_extract_search_results_with_masking(self, sample_splunk_response):
        """Test search results with data masking applied"""
        variables = {
            "search_query": "index=security",
            "apply_data_masking": True,
            "user_role": "standard_user"
        }
        
        with patch('search.get_guardrails_engine') as mock_guardrails:
            # Mock the guardrails engine to apply masking
            mock_engine = Mock()
            mock_engine.apply_data_masking.return_value = [
                {
                    "_time": "2024-01-15T10:30:00Z",
                    "host": "web-server-01",
                    "username": "j***@***.***",
                    "password": "[MASKED]",
                    "ssn": "***-**-****",
                    "ip_address": "192.168.1.100",
                    "action": "login_attempt"
                }
            ]
            mock_guardrails.return_value = mock_engine
            
            result = extract_search_results(sample_splunk_response, variables)
            
            assert result['success'] == True
            event = result['events'][0]
            assert event['username'] == "j***@***.***"
            assert event['password'] == "[MASKED]"
            assert event['ssn'] == "***-**-****"
    
    def test_extract_search_results_limit_enforcement(self, sample_splunk_response):
        """Test automatic result limiting"""
        variables = {
            "search_query": "index=*",
            "max_results": 1  # Limit to 1 result
        }
        
        result = extract_search_results(sample_splunk_response, variables)
        
        assert result['success'] == True
        assert len(result['events']) == 1
        assert 'limited_results' in result
        assert result['limited_results'] is True
    
    def test_extract_search_results_field_filtering(self, sample_splunk_response):
        """Test filtering of sensitive fields"""
        variables = {
            "search_query": "index=security",
            "filter_sensitive_fields": True
        }
        
        result = extract_search_results(sample_splunk_response, variables)
        
        # Should remove _raw and other sensitive fields
        for event in result['events']:
            assert '_raw' not in event  # Should be filtered out
            # Other fields should remain
            assert 'host' in event
            assert 'action' in event
    
    def test_extract_search_results_with_guardrails_validation(self, sample_splunk_response):
        """Test integration with guardrails validation"""
        variables = {
            "search_query": "index=security | delete",  # Dangerous query
            "validate_query": True
        }
        
        with patch('search.get_guardrails_engine') as mock_guardrails:
            mock_engine = Mock()
            mock_engine.validate_search.return_value = {
                'blocked': True,
                'violations': ['Blocked command detected: |delete'],
                'allowed': False
            }
            mock_guardrails.return_value = mock_engine
            
            result = extract_search_results(sample_splunk_response, variables)
            
            assert result['status'] == 'blocked'
            assert 'Query blocked by security guardrails' in result['message']
            assert 'violations' in result
    
    def test_extract_search_results_performance_metadata(self, sample_splunk_response):
        """Test inclusion of performance metadata"""
        variables = {
            "search_query": "index=web | stats count by status",
            "include_performance": True
        }
        
        result = extract_search_results(sample_splunk_response, variables)
        
        assert 'performance' in result
        assert 'event_count' in result['performance']
        assert 'processing_time' in result['performance']
    
    def test_extract_search_results_empty_response(self):
        """Test handling of empty search results"""
        empty_response = {"results": []}
        
        result = extract_search_results(empty_response)
        
        assert result['success'] == True
        assert result['events'] == []
        assert 'No events found' in result['message']
    
    def test_extract_search_results_malformed_response(self):
        """Test error handling with malformed response"""
        malformed_response = {"error": "Search timeout"}
        
        result = extract_search_results(malformed_response)
        
        assert result['success'] == False
        assert 'Error processing search results' in result['message']
    
    def test_extract_search_results_large_dataset_handling(self):
        """Test handling of large result sets"""
        # Create large dataset
        large_response = {
            "results": [
                {
                    "_time": f"2024-01-15T10:{i:02d}:00Z",
                    "host": f"server-{i:03d}",
                    "event_id": i,
                    "data": f"event_{i}_data"
                }
                for i in range(2000)  # 2000 events
            ]
        }
        
        variables = {
            "search_query": "index=large_data",
            "max_results": 1000  # Should limit to 1000
        }
        
        result = extract_search_results(large_response, variables)
        
        assert result['success'] == True
        assert len(result['events']) == 1000  # Should be limited
        assert result['limited_results'] is True
        assert result['total_available'] == 2000
    
    def test_extract_search_results_error_recovery(self):
        """Test error recovery scenarios"""
        error_scenarios = [
            None,  # None input
            {},    # Empty dict
            {"invalid": "structure"},  # Wrong structure
            {"results": "not_a_list"}  # Wrong data type
        ]
        
        for scenario in error_scenarios:
            result = extract_search_results(scenario)
            assert result['success'] == False
            assert 'message' in result


class TestSearchResultProcessing:
    """Test specific search result processing logic"""
    
    def test_field_type_detection(self):
        """Test automatic field type detection"""
        test_event = {
            "timestamp": "2024-01-15T10:30:00Z",
            "count": "123",
            "percentage": "45.67",
            "status": "success",
            "enabled": "true",
            "ip": "192.168.1.1"
        }
        
        # This would be part of the processing logic
        result = extract_search_results({"results": [test_event]})
        
        processed_event = result['events'][0]
        
        # Should detect and convert types appropriately
        assert isinstance(processed_event['count'], int)
        assert isinstance(processed_event['percentage'], float)
        assert isinstance(processed_event['enabled'], bool)
    
    def test_timestamp_normalization(self):
        """Test timestamp format normalization"""
        test_events = [
            {"_time": "2024-01-15T10:30:00Z"},          # ISO format
            {"_time": "1705315800"},                     # Unix timestamp
            {"_time": "Jan 15 10:30:00"},               # Splunk format
        ]
        
        result = extract_search_results({"results": test_events})
        
        # All timestamps should be normalized to consistent format
        for event in result['events']:
            assert '_time' in event
            # Should be in ISO format or epoch time
    
    def test_nested_field_handling(self):
        """Test handling of nested field structures"""
        test_event = {
            "user": {
                "name": "john.doe",
                "dept": "engineering",
                "permissions": ["read", "write"]
            },
            "system": {
                "host": "server-01",
                "process": {"pid": 1234, "name": "httpd"}
            }
        }
        
        result = extract_search_results({"results": [test_event]})
        
        # Should handle nested structures appropriately
        event = result['events'][0]
        assert 'user' in event
        assert 'system' in event


class TestDataMaskingIntegration:
    """Test data masking integration with search results"""
    
    def test_pii_detection_and_masking(self):
        """Test automatic PII detection and masking"""
        test_event = {
            "email": "user@company.com",
            "ssn": "123-45-6789",
            "credit_card": "4532-1234-5678-9012",
            "phone": "555-123-4567",
            "normal_field": "safe_data"
        }
        
        variables = {
            "apply_data_masking": True,
            "user_role": "standard_user"
        }
        
        with patch('search.get_guardrails_engine') as mock_guardrails:
            mock_engine = Mock()
            mock_engine.apply_data_masking.return_value = [{
                "email": "****@****.***",
                "ssn": "***-**-****", 
                "credit_card": "****-****-****-****",
                "phone": "***-***-****",
                "normal_field": "safe_data"
            }]
            mock_guardrails.return_value = mock_engine
            
            result = extract_search_results({"results": [test_event]}, variables)
            
            event = result['events'][0]
            assert "***" in event['email']
            assert "***" in event['ssn']
            assert "***" in event['credit_card']
            assert "***" in event['phone']
            assert event['normal_field'] == "safe_data"  # Unchanged
    
    def test_role_based_masking(self):
        """Test different masking levels based on user role"""
        test_event = {"sensitive_data": "secret_info"}
        
        # Admin role - no masking
        admin_variables = {
            "apply_data_masking": True,
            "user_role": "admin"
        }
        
        with patch('search.get_guardrails_engine') as mock_guardrails:
            mock_engine = Mock()
            mock_engine.apply_data_masking.return_value = [test_event]  # No masking for admin
            mock_guardrails.return_value = mock_engine
            
            result = extract_search_results({"results": [test_event]}, admin_variables)
            assert result['events'][0]['sensitive_data'] == "secret_info"
        
        # Standard user - with masking
        user_variables = {
            "apply_data_masking": True,
            "user_role": "standard_user"
        }
        
        with patch('search.get_guardrails_engine') as mock_guardrails:
            mock_engine = Mock()
            mock_engine.apply_data_masking.return_value = [{"sensitive_data": "[MASKED]"}]
            mock_guardrails.return_value = mock_engine
            
            result = extract_search_results({"results": [test_event]}, user_variables)
            assert result['events'][0]['sensitive_data'] == "[MASKED]"


class TestPerformanceOptimization:
    """Test performance optimization features"""
    
    def test_memory_efficient_processing(self):
        """Test memory-efficient processing of large datasets"""
        # Simulate processing of large result set
        large_dataset = {
            "results": [{"id": i, "data": "x" * 100} for i in range(5000)]
        }
        
        variables = {
            "search_query": "index=large",
            "max_results": 100,
            "memory_efficient": True
        }
        
        result = extract_search_results(large_dataset, variables)
        
        # Should limit memory usage
        assert len(result['events']) == 100
        assert result['success'] == True
    
    def test_streaming_result_processing(self):
        """Test streaming processing for very large results"""
        # This would test streaming/chunked processing
        # Implementation depends on actual streaming logic
        pass


class TestErrorHandling:
    """Test comprehensive error handling"""
    
    def test_guardrails_engine_failure(self):
        """Test handling when guardrails engine fails"""
        test_data = {"results": [{"test": "data"}]}
        variables = {"apply_data_masking": True}
        
        with patch('search.get_guardrails_engine', side_effect=Exception("Engine failed")):
            result = extract_search_results(test_data, variables)
            
            # Should fall back gracefully
            assert result['status'] in ['success', 'warning']
            assert 'events' in result
    
    def test_partial_data_corruption(self):
        """Test handling of partially corrupted data"""
        mixed_data = {
            "results": [
                {"valid": "event", "_time": "2024-01-15T10:30:00Z"},
                "invalid_event",  # This is not a dict
                {"another": "valid_event"},
                None,  # This is null
                {"final": "valid_event"}
            ]
        }
        
        result = extract_search_results(mixed_data)
        
        # Should process valid events and skip invalid ones
        assert result['success'] == True
        assert len(result['events']) == 3  # Only valid events
        assert 'warnings' in result
    
    def test_timeout_handling(self):
        """Test handling of processing timeouts"""
        # This would test timeout scenarios
        # Implementation depends on actual timeout logic
        pass