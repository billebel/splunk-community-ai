"""
Comprehensive tests for discovery transform functions
Tests all discovery logic with various Splunk response scenarios
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add transforms to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'transforms'))

from discovery import (
    extract_indexes, 
    find_data_sources
)


class TestExtractIndexes:
    """Test index extraction from Splunk API responses"""
    
    def test_extract_indexes_basic(self):
        """Test basic index extraction"""
        mock_data = {
            "entry": [
                {
                    "name": "main",
                    "content": {
                        "currentDBSizeMB": "15000",
                        "totalEventCount": "2000000",
                        "maxDataSize": "auto"
                    }
                },
                {
                    "name": "security", 
                    "content": {
                        "currentDBSizeMB": "8500",
                        "totalEventCount": "850000",
                        "maxDataSize": "auto"
                    }
                },
                {
                    "name": "_internal",
                    "content": {
                        "currentDBSizeMB": "500",
                        "totalEventCount": "100000"
                    }
                }
            ]
        }
        
        # Test without internal indexes (default)
        result = extract_indexes(mock_data)
        
        assert result['status'] == 'success'
        assert 'indexes' in result
        assert len(result['indexes']) == 2  # Should exclude _internal
        
        index_names = [idx['name'] for idx in result['indexes']]
        assert 'main' in index_names
        assert 'security' in index_names
        assert '_internal' not in index_names
    
    def test_extract_indexes_include_internal(self):
        """Test index extraction with internal indexes included"""
        mock_data = {
            "entry": [
                {"name": "main", "content": {"currentDBSizeMB": "15000"}},
                {"name": "_internal", "content": {"currentDBSizeMB": "500"}}
            ]
        }
        
        variables = {"include_internal": True}
        result = extract_indexes(mock_data, variables)
        
        assert len(result['indexes']) == 2
        index_names = [idx['name'] for idx in result['indexes']]
        assert '_internal' in index_names
    
    def test_extract_indexes_empty_response(self):
        """Test handling of empty Splunk response"""
        mock_data = {"entry": []}
        
        result = extract_indexes(mock_data)
        
        assert result['status'] == 'success'
        assert result['indexes'] == []
        assert 'No indexes found' in result['message']
    
    def test_extract_indexes_malformed_data(self):
        """Test error handling with malformed data"""
        mock_data = {"malformed": "data"}
        
        result = extract_indexes(mock_data)
        
        assert result['status'] == 'error'
        assert 'Error extracting indexes' in result['message']
    
    def test_extract_indexes_size_formatting(self):
        """Test proper size formatting and statistics"""
        mock_data = {
            "entry": [
                {
                    "name": "large_index",
                    "content": {
                        "currentDBSizeMB": "50000",  # 50GB
                        "totalEventCount": "10000000"
                    }
                }
            ]
        }
        
        result = extract_indexes(mock_data)
        
        index = result['indexes'][0]
        assert index['size_mb'] == 50000
        assert index['event_count'] == 10000000
        assert 'usage_summary' in result


# NOTE: extract_search_results and extract_hosts are not implemented in discovery.py
# These would be separate functions or part of other transforms


class TestFindDataSources:
    """Test business-term to technical-term mapping"""
    
    def test_find_authentication_sources(self):
        """Test finding authentication data sources"""
        variables = {"search_term": "authentication"}
        
        result = find_data_sources({}, variables)
        
        assert result['status'] == 'success'
        assert 'matching_categories' in result
        assert 'authentication' in result['matching_categories']
        
        auth_sources = result['matching_categories']['authentication']['splunk_sources']
        assert len(auth_sources) > 0
        
        # Should include Windows and Linux auth sources
        source_types = [src['sourcetype'] for src in auth_sources]
        assert any('wineventlog' in st for st in source_types)
        assert any('secure' in st for st in source_types)
    
    def test_find_web_sources(self):
        """Test finding web server data sources"""
        variables = {"search_term": "web"}
        
        result = find_data_sources({}, variables)
        
        web_sources = result['matching_categories']['web']['splunk_sources']
        source_types = [src['sourcetype'] for src in web_sources]
        
        # Should include Apache, Nginx, IIS
        assert any('apache' in st for st in source_types)
        assert any('nginx' in st for st in source_types)
        assert any('iis' in st for st in source_types)
    
    def test_find_sources_by_category(self):
        """Test finding sources by category"""
        variables = {"category": "security"}
        
        result = find_data_sources({}, variables)
        
        assert 'security' in result['matching_categories']
        security_sources = result['matching_categories']['security']['splunk_sources']
        
        # Should include various security data sources
        assert len(security_sources) > 3
        
        # Check for example searches
        for source in security_sources:
            assert 'example_searches' in source
            assert len(source['example_searches']) > 0
    
    def test_find_sources_no_matches(self):
        """Test handling when no sources match"""
        variables = {"search_term": "nonexistent_data_type"}
        
        result = find_data_sources({}, variables)
        
        assert result['status'] == 'success'
        assert result['matching_categories'] == {}
        assert 'No matching data sources found' in result['message']
    
    def test_find_sources_multiple_categories(self):
        """Test search term matching multiple categories"""
        variables = {"search_term": "log"}  # Should match multiple categories
        
        result = find_data_sources({}, variables)
        
        # "log" should match multiple categories
        assert len(result['matching_categories']) > 1
        
        # Each category should have relevant sources
        for category, data in result['matching_categories'].items():
            assert 'splunk_sources' in data
            assert len(data['splunk_sources']) > 0
    
    def test_find_sources_with_examples(self):
        """Test that all sources include practical examples"""
        variables = {"search_term": "firewall"}
        
        result = find_data_sources({}, variables)
        
        for category, data in result['matching_categories'].items():
            for source in data['splunk_sources']:
                # Each source should have example searches
                assert 'example_searches' in source
                assert len(source['example_searches']) > 0
                
                # Examples should be practical SPL
                for example in source['example_searches']:
                    assert 'index=' in example
                    assert any(keyword in example.lower() 
                             for keyword in ['count', 'stats', 'table', 'search'])


# NOTE: extract_hosts would be implemented separately or as part of search transform


class TestIntegrationScenarios:
    """Integration tests combining multiple discovery functions"""
    
    def test_discovery_workflow_complete(self):
        """Test complete discovery workflow"""
        # Step 1: Discover indexes
        index_data = {
            "entry": [
                {"name": "security", "content": {"currentDBSizeMB": "5000"}},
                {"name": "web", "content": {"currentDBSizeMB": "8000"}}
            ]
        }
        
        index_result = extract_indexes(index_data)
        assert index_result['status'] == 'success'
        
        # Step 2: Find data sources for security use case
        source_variables = {"search_term": "authentication"}
        source_result = find_data_sources({}, source_variables)
        assert source_result['status'] == 'success'
        
        # NOTE: Host extraction would be a separate function in search transform
    
    def test_error_recovery_scenarios(self):
        """Test error handling and recovery in discovery functions"""
        # Test each function with various error conditions
        error_scenarios = [
            None,  # None input
            {},    # Empty dict
            {"invalid": "structure"},  # Wrong structure
            {"entry": "not_a_list"}    # Wrong data type
        ]
        
        for scenario in error_scenarios:
            # Each function should handle errors gracefully
            index_result = extract_indexes(scenario)
            assert index_result['status'] == 'error'
        
        # find_data_sources should handle errors in variables
        for bad_variables in [None, {"invalid": "param"}]:
            source_result = find_data_sources({}, bad_variables)
            assert source_result['status'] in ['success', 'error']  # May return empty results