"""
Comprehensive tests for knowledge object transform functions
Tests data models, event types, search macros, field extractions, and lookup tables
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add transforms to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'transforms'))

from knowledge import (
    extract_data_models,
    extract_data_model_structure, 
    extract_event_types,
    extract_search_macros,
    extract_field_extractions,
    extract_lookup_tables
)


class TestExtractDataModels:
    """Test data model extraction for tstats optimization"""
    
    @pytest.fixture
    def sample_data_models_response(self):
        """Sample Splunk data models API response"""
        return {
            "entry": [
                {
                    "name": "Authentication",
                    "title": "Authentication Data Model",
                    "published": "2024-01-01T00:00:00Z",
                    "updated": "2024-01-15T10:00:00Z",
                    "content": {
                        "description": "Authentication events across all sources",
                        "acceleration": True,
                        "objects": [
                            {"objectName": "Authentication", "fields": []}
                        ]
                    },
                    "acl": {
                        "app": "Splunk_SA_CIM"
                    }
                },
                {
                    "name": "Web",
                    "title": "Web Data Model", 
                    "content": {
                        "description": "Web server logs and events",
                        "acceleration": False,
                        "objects": []
                    },
                    "acl": {
                        "app": "search"
                    }
                }
            ]
        }
    
    def test_extract_data_models_success(self, sample_data_models_response):
        """Test successful data model extraction"""
        result = extract_data_models(sample_data_models_response)
        
        assert result['success'] is True
        assert len(result['data_models']) == 2
        
        # Check accelerated model is first (sorted by acceleration)
        auth_model = result['data_models'][0]
        assert auth_model['name'] == 'Authentication'
        assert auth_model['accelerated'] is True
        assert auth_model['acceleration_status'] == 'ready_for_tstats'
        assert 'tstats_example' in auth_model
        
        # Check optimization summary
        assert result['optimization_summary']['total_models'] == 2
        assert result['optimization_summary']['tstats_ready_count'] == 1
        assert 'Authentication' in result['optimization_summary']['accelerated_models']
        assert 'Web' in result['optimization_summary']['non_accelerated_models']
    
    def test_extract_data_models_empty_response(self):
        """Test handling of empty response"""
        empty_response = {"entry": []}
        
        result = extract_data_models(empty_response)
        
        assert result['success'] is True
        assert result['data_models'] == []
        assert result['count'] == 0
        assert result['optimization_summary']['total_models'] == 0
    
    def test_extract_data_models_malformed_data(self):
        """Test error handling with malformed data"""
        malformed_data = {"invalid": "structure"}
        
        result = extract_data_models(malformed_data)
        
        assert result['success'] is False
        assert 'error' in result
        assert result['data_models'] == []
        assert result['count'] == 0
    
    def test_extract_data_models_mixed_data_types(self):
        """Test handling of mixed valid/invalid entries"""
        mixed_data = {
            "entry": [
                {
                    "name": "Valid_Model",
                    "content": {"acceleration": True}
                },
                "invalid_entry",  # Not a dict
                None,  # Null entry
                {
                    "name": "Another_Valid",
                    "content": {"acceleration": False}
                }
            ]
        }
        
        result = extract_data_models(mixed_data)
        
        assert result['success'] is True
        assert len(result['data_models']) == 2  # Only valid entries processed
        assert result['data_models'][0]['name'] == 'Valid_Model'  # Accelerated first


class TestExtractDataModelStructure:
    """Test detailed data model structure extraction"""
    
    @pytest.fixture
    def sample_data_model_detail(self):
        """Sample detailed data model response"""
        return {
            "entry": [{
                "content": {
                    "description": "Authentication data model with user events",
                    "acceleration": True,
                    "objects": [
                        {
                            "objectName": "Authentication",
                            "displayName": "Authentication Events",
                            "parentName": "",
                            "fields": [
                                {"fieldName": "user"},
                                {"fieldName": "src"},
                                {"fieldName": "dest"},
                                {"fieldName": "action"}
                            ]
                        },
                        {
                            "objectName": "Failed_Authentication", 
                            "displayName": "Failed Logins",
                            "parentName": "Authentication",
                            "fields": [
                                {"fieldName": "failure_reason"},
                                {"fieldName": "user"}
                            ]
                        }
                    ]
                }
            }]
        }
    
    def test_extract_data_model_structure_success(self, sample_data_model_detail):
        """Test successful data model structure extraction"""
        variables = {"model_name": "Authentication"}
        result = extract_data_model_structure(sample_data_model_detail, variables)
        
        assert result['success'] is True
        
        structure = result['model_structure']
        assert structure['name'] == 'Authentication'
        assert structure['acceleration_enabled'] is True
        assert structure['total_objects'] == 2
        
        # Check objects
        auth_obj = structure['objects'][0]
        assert auth_obj['name'] == 'Authentication'
        assert 'user' in auth_obj['available_fields']
        assert auth_obj['field_count'] == 4
        
        # Check all available fields
        assert 'user' in structure['all_available_fields']
        assert 'failure_reason' in structure['all_available_fields']
        
        # Check tstats examples
        assert len(result['tstats_examples']) > 0
        assert any('tstats count from datamodel=Authentication' in example for example in result['tstats_examples'])
    
    def test_extract_data_model_structure_not_accelerated(self):
        """Test structure extraction for non-accelerated model"""
        non_accelerated = {
            "entry": [{
                "content": {
                    "description": "Non-accelerated model",
                    "acceleration": False,
                    "objects": []
                }
            }]
        }
        
        variables = {"model_name": "TestModel"}
        result = extract_data_model_structure(non_accelerated, variables)
        
        assert result['success'] is True
        assert result['model_structure']['acceleration_enabled'] is False
        assert result['tstats_examples'] == []
        assert 'tstats not available' in result['usage_note']
    
    def test_extract_data_model_structure_error_handling(self):
        """Test error handling in structure extraction"""
        result = extract_data_model_structure({})
        
        assert result['success'] is False
        assert 'error' in result
        assert result['model_structure'] == {}


class TestExtractEventTypes:
    """Test event type extraction for search patterns"""
    
    @pytest.fixture
    def sample_event_types_response(self):
        """Sample event types API response"""
        return {
            "entry": [
                {
                    "name": "authentication_success",
                    "content": {
                        "description": "Successful authentication events",
                        "search": "tag=authentication action=success",
                        "tags": "authentication,success,login",
                        "disabled": False
                    },
                    "acl": {"app": "search"}
                },
                {
                    "name": "web_error", 
                    "content": {
                        "description": "Web server errors",
                        "search": "sourcetype=access_combined status>=400",
                        "tags": "web,error",
                        "disabled": False
                    },
                    "acl": {"app": "search"}
                },
                {
                    "name": "disabled_eventtype",
                    "content": {
                        "search": "some search",
                        "disabled": True
                    },
                    "acl": {"app": "search"}
                }
            ]
        }
    
    def test_extract_event_types_success(self, sample_event_types_response):
        """Test successful event type extraction"""
        result = extract_event_types(sample_event_types_response)
        
        assert result['success'] is True
        assert len(result['event_types']) == 2  # Disabled one excluded
        
        auth_et = next(et for et in result['event_types'] if et['name'] == 'authentication_success')
        assert auth_et['search_pattern'] == 'tag=authentication action=success'
        assert 'authentication' in auth_et['tags']
        assert auth_et['usage_example'] == 'eventtype="authentication_success"'
        
        # Verify disabled event type is excluded
        disabled_names = [et['name'] for et in result['event_types']]
        assert 'disabled_eventtype' not in disabled_names
    
    def test_extract_event_types_empty_tags(self):
        """Test event types with empty or missing tags"""
        response_no_tags = {
            "entry": [{
                "name": "no_tags_eventtype",
                "content": {
                    "search": "index=test",
                    "tags": "",  # Empty tags
                    "disabled": False
                }
            }]
        }
        
        result = extract_event_types(response_no_tags)
        
        assert result['success'] is True
        assert result['event_types'][0]['tags'] == []
    
    def test_extract_event_types_error_handling(self):
        """Test error handling"""
        result = extract_event_types({})
        
        assert result['success'] is False
        assert result['event_types'] == []
        assert result['count'] == 0


class TestExtractSearchMacros:
    """Test search macro extraction for reusable logic"""
    
    @pytest.fixture
    def sample_macros_response(self):
        """Sample search macros API response"""
        return {
            "entry": [
                {
                    "name": "get_windows_events",
                    "content": {
                        "definition": "index=windows sourcetype=WinEventLog*",
                        "description": "Base search for Windows events", 
                        "args": "",
                        "isPrivate": False
                    },
                    "acl": {"app": "search"}
                },
                {
                    "name": "timerange(2)",
                    "content": {
                        "definition": "earliest=$earliest$ latest=$latest$",
                        "description": "Dynamic time range macro",
                        "args": "earliest,latest",
                        "isPrivate": False
                    },
                    "acl": {"app": "search"}
                },
                {
                    "name": "private_macro",
                    "content": {
                        "definition": "private search logic",
                        "isPrivate": True
                    },
                    "acl": {"app": "custom_app"}
                }
            ]
        }
    
    def test_extract_search_macros_success(self, sample_macros_response):
        """Test successful macro extraction"""
        result = extract_search_macros(sample_macros_response)
        
        assert result['success'] is True
        assert len(result['search_macros']) == 2  # Private macro excluded
        
        # Test simple macro (no args)
        simple_macro = next(m for m in result['search_macros'] if m['name'] == 'get_windows_events')
        assert simple_macro['definition'] == 'index=windows sourcetype=WinEventLog*'
        assert simple_macro['usage_example'] == '`get_windows_events`'
        
        # Test macro with arguments
        arg_macro = next(m for m in result['search_macros'] if 'timerange' in m['name'])
        assert 'earliest,latest' in arg_macro['args']
        assert 'arg1, arg2' in arg_macro['usage_example']
    
    def test_extract_search_macros_private_handling(self):
        """Test handling of private macros"""
        private_in_search = {
            "entry": [{
                "name": "private_in_search_app",
                "content": {
                    "definition": "search logic",
                    "isPrivate": True
                },
                "acl": {"app": "search"}  # Should be included
            }]
        }
        
        result = extract_search_macros(private_in_search)
        
        assert result['success'] is True
        assert len(result['search_macros']) == 1  # Private macro in search app included
    
    def test_extract_search_macros_error_handling(self):
        """Test error handling"""
        result = extract_search_macros({"invalid": "data"})
        
        assert result['success'] is False
        assert result['search_macros'] == []
        assert result['count'] == 0


class TestExtractFieldExtractions:
    """Test field extraction rules for understanding data structure"""
    
    @pytest.fixture
    def sample_field_extractions_response(self):
        """Sample field extractions response"""
        return {
            "entry": [
                {
                    "name": "access_combined",
                    "content": {
                        "type": "regex", 
                        "field_names": "clientip,status,bytes,referer,useragent",
                        "regex": r'^(?P<clientip>\S+) \S+ \S+ \[(?P<timestamp>[^\]]+)\] "(?P<method>\S+) (?P<uri>\S+) (?P<protocol>[^"]+)" (?P<status>\d+) (?P<bytes>\d+|-) "(?P<referer>[^"]*)" "(?P<useragent>[^"]*)"'
                    },
                    "acl": {"app": "search"}
                },
                {
                    "name": "syslog",
                    "content": {
                        "type": "delimited",
                        "field_names": "timestamp,host,process,message"
                    },
                    "acl": {"app": "unix"}
                }
            ]
        }
    
    def test_extract_field_extractions_success(self, sample_field_extractions_response):
        """Test successful field extraction parsing"""
        result = extract_field_extractions(sample_field_extractions_response)
        
        assert result['success'] is True
        assert result['total_extractions'] == 2
        
        # Check sourcetype grouping
        assert 'access_combined' in result['field_extractions_by_sourcetype']
        assert 'syslog' in result['field_extractions_by_sourcetype']
        
        # Check access_combined extraction
        access_ext = result['field_extractions_by_sourcetype']['access_combined'][0]
        assert access_ext['extraction_type'] == 'regex'
        assert 'clientip' in access_ext['field_names']
        assert 'status' in access_ext['field_names']
        
        # Check regex truncation (for very long patterns)
        assert len(access_ext['regex_pattern']) <= 103  # 100 + '...'
    
    def test_extract_field_extractions_long_regex_truncation(self):
        """Test truncation of very long regex patterns"""
        long_regex_response = {
            "entry": [{
                "name": "test_sourcetype",
                "content": {
                    "type": "regex",
                    "regex": "a" * 200  # Very long regex
                },
                "acl": {"app": "search"}
            }]
        }
        
        result = extract_field_extractions(long_regex_response)
        
        assert result['success'] is True
        extraction = result['field_extractions_by_sourcetype']['test_sourcetype'][0]
        assert extraction['regex_pattern'].endswith('...')
        assert len(extraction['regex_pattern']) == 103  # 100 chars + '...'
    
    def test_extract_field_extractions_error_handling(self):
        """Test error handling"""
        result = extract_field_extractions({})
        
        assert result['success'] is False
        assert result['field_extractions_by_sourcetype'] == {}
        assert result['total_extractions'] == 0


class TestExtractLookupTables:
    """Test lookup table extraction for enrichment opportunities"""
    
    @pytest.fixture
    def sample_lookup_tables_response(self):
        """Sample lookup tables response"""
        return {
            "entry": [
                {
                    "name": "ip_to_location.csv",
                    "content": {
                        "filename": "ip_to_location.csv",
                        "size": 2048576,  # ~2MB
                        "updated": "2024-01-15T10:00:00Z"
                    },
                    "acl": {"app": "search"}
                },
                {
                    "name": "small_lookup.csv",
                    "content": {
                        "filename": "small_lookup.csv", 
                        "size": 1024  # 1KB
                    },
                    "acl": {"app": "security"}
                }
            ]
        }
    
    def test_extract_lookup_tables_success(self, sample_lookup_tables_response):
        """Test successful lookup table extraction"""
        result = extract_lookup_tables(sample_lookup_tables_response)
        
        assert result['success'] is True
        assert result['count'] == 2
        assert result['total_size_bytes'] == 2048576 + 1024
        
        # Should be sorted by size (largest first)
        assert result['lookup_tables'][0]['name'] == 'ip_to_location.csv'
        assert result['lookup_tables'][0]['size_bytes'] == 2048576
        
        # Check usage examples
        for lookup in result['lookup_tables']:
            assert lookup['usage_example'].startswith('| lookup')
    
    def test_extract_lookup_tables_empty_response(self):
        """Test empty lookup tables response"""
        result = extract_lookup_tables({"entry": []})
        
        assert result['success'] is True
        assert result['lookup_tables'] == []
        assert result['count'] == 0
        assert result['total_size_bytes'] == 0
    
    def test_extract_lookup_tables_error_handling(self):
        """Test error handling"""
        result = extract_lookup_tables({"invalid": "structure"})
        
        assert result['success'] is False
        assert result['lookup_tables'] == []
        assert result['count'] == 0


class TestKnowledgeIntegrationScenarios:
    """Integration tests for knowledge object functions"""
    
    def test_complete_knowledge_discovery_workflow(self):
        """Test complete knowledge discovery workflow"""
        # Mock responses for each knowledge object type
        data_models_response = {"entry": [{"name": "Authentication", "content": {"acceleration": True}}]}
        event_types_response = {"entry": [{"name": "auth_success", "content": {"search": "tag=authentication", "disabled": False}}]}
        macros_response = {"entry": [{"name": "get_auth_events", "content": {"definition": "index=security", "isPrivate": False}}]}
        
        # Test each extraction function
        dm_result = extract_data_models(data_models_response)
        et_result = extract_event_types(event_types_response)
        macro_result = extract_search_macros(macros_response)
        
        # All should succeed
        assert dm_result['success'] is True
        assert et_result['success'] is True
        assert macro_result['success'] is True
        
        # Should provide complementary information for search optimization
        assert dm_result['optimization_summary']['tstats_ready_count'] > 0
        assert len(et_result['event_types']) > 0
        assert len(macro_result['search_macros']) > 0
    
    def test_error_recovery_scenarios(self):
        """Test error handling across knowledge functions"""
        error_scenarios = [
            None,  # None input
            {},    # Empty dict
            {"invalid": "structure"},  # Wrong structure
            {"entry": "not_a_list"}    # Wrong data type
        ]
        
        knowledge_functions = [
            extract_data_models,
            extract_event_types, 
            extract_search_macros,
            extract_field_extractions,
            extract_lookup_tables
        ]
        
        for scenario in error_scenarios:
            for func in knowledge_functions:
                result = func(scenario)
                # All functions should handle errors gracefully
                assert 'success' in result
                if not result['success']:
                    assert 'error' in result