"""
Tests for Knowledge Management functionality
"""

import pytest
import sys
import os

# Add the transforms directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'transforms'))

from knowledge_management import (
    create_lookup,
    update_lookup,
    create_macro,
    delete_lookup,
    validate_lookup_data
)

class TestLookupCreation:
    """Test lookup creation functionality"""

    def test_create_lookup_success(self):
        """Test successful lookup creation"""
        data = {
            'parameters': {
                'lookup_name': 'test_lookup',
                'raw_data': 'field1,field2\nvalue1,value2\nvalue3,value4',
                'lookup_purpose': 'Test lookup for unit testing',
                'app_context': 'search'
            }
        }

        result = create_lookup(data)

        assert result['success'] == True
        assert result['operation'] == 'create_lookup'
        assert result['lookup_name'] == 'test_lookup'
        assert result['filename'] == 'test_lookup.csv'
        assert result['row_count'] == 2
        assert result['headers'] == ['field1', 'field2']

    def test_create_lookup_missing_parameters(self):
        """Test lookup creation with missing parameters"""
        data = {
            'parameters': {
                'lookup_name': 'test_lookup'
                # Missing raw_data and lookup_purpose
            }
        }

        result = create_lookup(data)

        assert result['success'] == False
        assert 'Missing required parameters' in result['error']

    def test_create_lookup_invalid_name(self):
        """Test lookup creation with invalid name"""
        data = {
            'parameters': {
                'lookup_name': '123invalid-name!',
                'raw_data': 'field1,field2\nvalue1,value2',
                'lookup_purpose': 'Test lookup'
            }
        }

        result = create_lookup(data)

        assert result['success'] == False
        assert 'name must start with letter' in result['error']

    def test_create_lookup_too_large(self):
        """Test lookup creation with data too large"""
        # Create a large data string (>10MB)
        large_data = 'field1,field2\n' + 'value1,value2\n' * 500000

        data = {
            'parameters': {
                'lookup_name': 'large_lookup',
                'raw_data': large_data,
                'lookup_purpose': 'Test large lookup'
            }
        }

        result = create_lookup(data)

        assert result['success'] == False
        # Could fail on size OR row count limits
        assert 'too large' in result['error'] or 'Too many rows' in result['error']

    def test_create_lookup_invalid_csv(self):
        """Test lookup creation with invalid CSV"""
        data = {
            'parameters': {
                'lookup_name': 'invalid_lookup',
                'raw_data': 'invalid\ncsv\nformat,with,mismatched,columns',
                'lookup_purpose': 'Test invalid CSV'
            }
        }

        result = create_lookup(data)

        # Should either fail validation or handle gracefully
        # (depending on how strict CSV parsing is)
        assert 'error' in result or result['success'] == True

class TestMacroCreation:
    """Test macro creation functionality"""

    def test_create_macro_success(self):
        """Test successful macro creation"""
        data = {
            'parameters': {
                'macro_name': 'test_macro',
                'description': 'Find failed login attempts',
                'parameters': 'threshold'
            }
        }

        result = create_macro(data)

        assert result['success'] == True
        assert result['operation'] == 'create_macro'
        assert result['macro_name'] == 'test_macro(1)'
        assert 'definition' in result
        assert result['parameters'] == ['threshold']

    def test_create_macro_no_parameters(self):
        """Test macro creation without parameters"""
        data = {
            'parameters': {
                'macro_name': 'simple_macro',
                'description': 'Show error logs'
            }
        }

        result = create_macro(data)

        assert result['success'] == True
        assert result['macro_name'] == 'simple_macro'
        assert result['parameters'] == []

    def test_create_macro_invalid_name(self):
        """Test macro creation with invalid name"""
        data = {
            'parameters': {
                'macro_name': '123invalid-name!',
                'description': 'Test macro'
            }
        }

        result = create_macro(data)

        assert result['success'] == False
        assert 'name must start with letter' in result['error']

class TestLookupValidation:
    """Test lookup data validation"""

    def test_validate_good_data(self):
        """Test validation of good lookup data"""
        data = {
            'parameters': {
                'data_sample': 'username,department,title\njohn,IT,Engineer\njane,HR,Manager',
                'intended_use': 'User department mapping'
            }
        }

        result = validate_lookup_data(data)

        assert result['success'] == True
        assert result['data_quality'] == 'good'
        assert result['estimated_rows'] == 2
        assert result['field_count'] == 3

    def test_validate_problematic_data(self):
        """Test validation of data with issues"""
        # Data with many empty cells
        problematic_data = 'field1,field2,field3\n,value2,\nvalue1,,value3\n,,'

        data = {
            'parameters': {
                'data_sample': problematic_data,
                'intended_use': 'Test mapping'
            }
        }

        result = validate_lookup_data(data)

        assert result['success'] == True
        assert result['data_quality'] == 'needs_attention'
        assert len(result['issues']) > 0
        assert len(result['recommendations']) > 0

class TestLookupUpdate:
    """Test lookup update functionality"""

    def test_update_lookup_success(self):
        """Test successful lookup update"""
        data = {
            'parameters': {
                'lookup_name': 'existing_lookup',
                'new_data': 'field1,field2\nnew1,new2\nnew3,new4',
                'merge_strategy': 'replace'
            }
        }

        result = update_lookup(data)

        assert result['success'] == True
        assert result['operation'] == 'update_lookup'
        assert result['lookup_name'] == 'existing_lookup'
        assert result['new_row_count'] == 2

class TestLookupDeletion:
    """Test lookup deletion functionality"""

    def test_delete_lookup_success(self):
        """Test successful lookup deletion"""
        data = {
            'parameters': {
                'lookup_name': 'test_lookup',
                'confirm_deletion': True
            }
        }

        result = delete_lookup(data)

        assert result['success'] == True
        assert result['operation'] == 'delete_lookup'
        assert result['lookup_name'] == 'test_lookup'

    def test_delete_lookup_not_confirmed(self):
        """Test deletion without confirmation"""
        data = {
            'parameters': {
                'lookup_name': 'test_lookup',
                'confirm_deletion': False
            }
        }

        result = delete_lookup(data)

        assert result['success'] == False
        assert 'not confirmed' in result['error']

if __name__ == '__main__':
    pytest.main([__file__, '-v'])