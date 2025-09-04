"""
Test configuration and fixtures for Splunk Enterprise v2 pack
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch

# Add the transforms directory to Python path
pack_root = os.path.dirname(os.path.dirname(__file__))
transforms_path = os.path.join(pack_root, 'transforms')
sys.path.insert(0, transforms_path)


@pytest.fixture(scope="session")
def test_config():
    """Test configuration for guardrails"""
    return {
        'guardrails': {
            'enabled': True,
            'fail_safe_mode': True,
            'audit_logging': True
        },
        'security': {
            'blocked_commands': [
                '|delete', '|script', '|outputcsv', '|outputlookup',
                '|external', '|sendemail', '|run', '|crawl', '|dbxquery'
            ],
            'blocked_patterns': [
                r'(?i)eval.*system\s*\(',
                r'(?i)\.\./',
                r'(?i)c:\\windows',
                r'(?i)base64\s*\(',
                r'(?i)eval.*\+.*[\'"]'
            ],
            'warning_patterns': [
                r'\|\s*stats\s+.*by\s+.*,.*,.*',
                r'\|\s*transaction',
                r'\|\s*join'
            ]
        },
        'performance': {
            'time_limits': {
                'max_time_range_days': 30,
                'default_time_range': '-1h'
            },
            'result_limits': {
                'max_results_per_search': 1000,
                'default_result_limit': 100
            },
            'execution_limits': {
                'search_timeout_seconds': 300,
                'max_concurrent_searches': 5
            }
        },
        'privacy': {
            'data_masking': {
                'enabled': True
            },
            'sensitive_fields': [
                'password', 'passwd', 'secret', 'token', 'api_key',
                'ssn', 'social_security', 'credit_card', 'account_number',
                'email', 'phone', 'address'
            ],
            'masking_patterns': {
                'email': '****@****.***',
                'phone': '***-***-****',
                'ssn': '***-**-****',
                'credit_card': '****-****-****-****',
                'default': '[MASKED]'
            },
            'filtered_fields': ['_raw', 'punct']
        },
        'user_roles': {
            'admin': {
                'bypass_command_blocks': False,
                'bypass_time_limits': False,
                'max_time_range_days': 90,
                'max_results_per_search': 10000,
                'max_concurrent_searches': 10,
                'search_timeout_seconds': 600,
                'data_masking_enabled': False
            },
            'power_user': {
                'bypass_command_blocks': False,
                'bypass_time_limits': False,
                'max_time_range_days': 60,
                'max_results_per_search': 5000,
                'max_concurrent_searches': 7,
                'search_timeout_seconds': 450,
                'data_masking_enabled': True
            },
            'standard_user': {
                'bypass_command_blocks': False,
                'bypass_time_limits': False,
                'max_time_range_days': 7,
                'max_results_per_search': 1000,
                'max_concurrent_searches': 3,
                'search_timeout_seconds': 300,
                'data_masking_enabled': True
            },
            'readonly_user': {
                'bypass_command_blocks': False,
                'bypass_time_limits': False,
                'max_time_range_days': 1,
                'max_results_per_search': 100,
                'max_concurrent_searches': 2,
                'search_timeout_seconds': 120,
                'data_masking_enabled': True
            }
        }
    }


@pytest.fixture
def guardrails_engine(test_config):
    """Create a guardrails engine with test configuration"""
    with patch('guardrails.GuardrailsEngine._load_config', return_value=test_config):
        from guardrails import GuardrailsEngine
        yield GuardrailsEngine()


@pytest.fixture
def mock_guardrails_config(test_config):
    """Mock the guardrails configuration loading"""
    with patch('guardrails.GuardrailsEngine._load_config', return_value=test_config):
        yield test_config


@pytest.fixture
def sample_search_results():
    """Sample search results for testing data masking"""
    return [
        {
            '_time': '2024-01-15T10:30:00Z',
            'host': 'web-server-01',
            'source': '/var/log/auth.log',
            'sourcetype': 'linux_secure',
            'username': 'john.doe@company.com',
            'password': 'secretpassword123',
            'ssn': '123-45-6789',
            'ip_address': '192.168.1.100',
            'action': 'login_attempt',
            'result': 'success'
        },
        {
            '_time': '2024-01-15T10:31:00Z',
            'host': 'web-server-02',
            'source': '/var/log/auth.log',
            'sourcetype': 'linux_secure',
            'username': 'admin',
            'email': 'admin@company.com',
            'credit_card': '4532-1234-5678-9012',
            'phone': '555-123-4567',
            'action': 'admin_access',
            'result': 'granted'
        }
    ]


@pytest.fixture(autouse=True)
def setup_logging():
    """Set up logging for tests"""
    import logging
    logging.basicConfig(level=logging.DEBUG)
    yield
    # Cleanup after tests
    logging.getLogger().handlers.clear()