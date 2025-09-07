"""
Guardrails Testing Transform - Test and validate guardrails functionality
"""

import json
from typing import Dict, List, Any, Optional
import logging
# Import guardrails engine
import os
import sys
import importlib.util

# Add transforms directory to path for imports
transforms_dir = os.path.dirname(__file__)
if transforms_dir not in sys.path:
    sys.path.insert(0, transforms_dir)

# Import guardrails
try:
    from guardrails import get_guardrails_engine
except ImportError:
    # Fallback: direct file import
    guardrails_path = os.path.join(transforms_dir, 'guardrails.py')
    if os.path.exists(guardrails_path):
        spec = importlib.util.spec_from_file_location("guardrails", guardrails_path)
        guardrails_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guardrails_module)
        get_guardrails_engine = guardrails_module.get_guardrails_engine
    else:
        # Mock guardrails if not available
        def get_guardrails_engine():
            class MockGuardrails:
                def validate_search(self, query, user_context):
                    return {'blocked': False, 'violations': [], 'warnings': []}
                def apply_data_masking(self, events, user_context):
                    return events
            return MockGuardrails()
        logger.warning("Guardrails module not found, using mock implementation")

logger = logging.getLogger(__name__)

def validate_search_query(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Validate a search query against guardrails without executing it
    
    Args:
        data: Dummy search response (ignored)
        variables: Contains test_query, user_role, show_modifications
        
    Returns:
        Validation results with safety assessment and recommendations
    """
    try:
        variables = variables or {}
        test_query = variables.get('test_query', '')
        user_role = variables.get('user_role', 'standard_user')
        show_modifications = variables.get('show_modifications', True)
        
        if not test_query.strip():
            return {
                'success': False,
                'error': 'test_query parameter is required',
                'example_queries': [
                    'index=security EventCode=4625',
                    'index=web status>=400 | stats count by status',
                    'search * | head 1000'
                ]
            }
        
        # Create user context for testing
        user_context = {
            'username': 'test_user',
            'roles': [user_role],
            'user_role': user_role
        }
        
        # Get guardrails engine and validate
        guardrails = get_guardrails_engine()
        validation_result = guardrails.validate_search(test_query, user_context)
        
        # Prepare response
        result = {
            'success': True,
            'test_query': test_query,
            'user_role': user_role,
            'validation_results': {
                'allowed': validation_result['allowed'],
                'blocked': validation_result['blocked'],
                'enforcement_level': validation_result['enforcement_level']
            }
        }
        
        # Add violations if blocked
        if validation_result['blocked']:
            result['security_violations'] = validation_result['violations']
            result['block_reason'] = validation_result.get('block_reason', 'Security violation')
            result['recommendation'] = "Modify your search to avoid blocked commands and patterns"
        
        # Add warnings if any
        if validation_result['warnings']:
            result['performance_warnings'] = validation_result['warnings']
            result['recommendation'] = result.get('recommendation', '') + " Consider optimizing for better performance"
        
        # Show modifications if enabled and query would be modified
        if show_modifications and validation_result.get('modifications_applied'):
            result['query_modifications'] = {
                'original_query': validation_result['original_query'],
                'modified_query': validation_result['modified_query'],
                'modifications_applied': validation_result['modifications_applied']
            }
        
        # Add role-specific limits information
        role_limits = guardrails._get_role_limits(user_role)
        result['role_limits'] = {
            'max_time_range_days': role_limits.get('max_time_range_days', 'unknown'),
            'max_results_per_search': role_limits.get('max_results_per_search', 'unknown'),
            'search_timeout_seconds': role_limits.get('search_timeout_seconds', 'unknown'),
            'data_masking_enabled': role_limits.get('data_masking_enabled', True)
        }
        
        # Provide actionable recommendations
        recommendations = []
        if validation_result['blocked']:
            recommendations.extend([
                "Remove blocked commands like |delete, |outputlookup, |script",
                "Avoid wildcard searches like 'search *' or 'index=*'",
                "Specify time ranges instead of searching all historical data"
            ])
        
        if validation_result['warnings']:
            recommendations.extend([
                "Consider adding 'index=' to limit search scope",
                "Add time bounds with 'earliest=' and 'latest='",
                "Use '| head N' to limit result count"
            ])
        
        if not validation_result['blocked'] and not validation_result['warnings']:
            recommendations.append("Query passed all guardrails checks and is safe to execute")
        
        result['recommendations'] = recommendations
        
        return result
        
    except Exception as e:
        logger.error(f"Search validation failed: {str(e)}")
        return {
            'success': False,
            'error': f"Validation failed: {str(e)}",
            'test_query': variables.get('test_query', ''),
            'user_role': variables.get('user_role', 'unknown')
        }

def get_guardrails_config(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get current guardrails configuration and role limits
    
    Args:
        data: Server info response (ignored for config display)
        variables: Contains user_role, include_patterns
        
    Returns:
        Current guardrails configuration and role-specific limits
    """
    try:
        variables = variables or {}
        user_role = variables.get('user_role', 'standard_user')
        include_patterns = variables.get('include_patterns', False)
        
        guardrails = get_guardrails_engine()
        config = guardrails.config
        
        # Build configuration summary
        result = {
            'success': True,
            'guardrails_status': {
                'enabled': config.get('guardrails', {}).get('enabled', False),
                'version': config.get('guardrails', {}).get('version', 'unknown'),
                'fail_safe_mode': config.get('guardrails', {}).get('fail_safe_mode', True),
                'config_source': guardrails.config_path or 'fail-safe defaults'
            },
            'user_role_requested': user_role
        }
        
        # Get role-specific limits
        role_limits = guardrails._get_role_limits(user_role)
        result['role_limits'] = {
            'time_restrictions': {
                'max_time_range_days': role_limits.get('max_time_range_days', 'unknown'),
                'bypass_time_limits': role_limits.get('bypass_time_limits', False)
            },
            'result_restrictions': {
                'max_results_per_search': role_limits.get('max_results_per_search', 'unknown'),
                'max_concurrent_searches': role_limits.get('max_concurrent_searches', 'unknown'),
                'search_timeout_seconds': role_limits.get('search_timeout_seconds', 'unknown')
            },
            'security_permissions': {
                'bypass_command_blocks': role_limits.get('bypass_command_blocks', False),
                'data_masking_enabled': role_limits.get('data_masking_enabled', True)
            },
            'rate_limits': {
                'searches_per_minute': role_limits.get('rate_limit_searches_per_minute', 'unknown')
            }
        }
        
        # Security configuration summary (without sensitive patterns unless requested)
        security_config = config.get('security', {})
        result['security_controls'] = {
            'blocked_commands_count': len(security_config.get('blocked_commands', [])),
            'blocked_patterns_count': len(security_config.get('blocked_patterns', [])),
            'warning_patterns_count': len(security_config.get('warning_patterns', []))
        }
        
        # Include actual patterns if requested (admin use case)
        if include_patterns:
            result['security_patterns'] = {
                'blocked_commands': security_config.get('blocked_commands', []),
                'blocked_patterns': security_config.get('blocked_patterns', []),
                'warning_patterns': security_config.get('warning_patterns', [])
            }
        
        # Privacy controls summary
        privacy_config = config.get('privacy', {})
        result['privacy_controls'] = {
            'data_masking_enabled': privacy_config.get('data_masking', {}).get('enabled', False),
            'sensitive_fields_count': len(privacy_config.get('sensitive_fields', [])),
            'masking_patterns_count': len(privacy_config.get('masking_patterns', {})),
            'filtered_fields_count': len(privacy_config.get('filtered_fields', []))
        }
        
        # Available user roles
        user_roles_config = config.get('user_roles', {})
        result['available_roles'] = list(user_roles_config.keys())
        
        # Performance limits summary
        performance_config = config.get('performance', {})
        result['performance_limits'] = {
            'global_max_time_range_days': performance_config.get('time_limits', {}).get('max_time_range_days', 'unknown'),
            'global_max_results': performance_config.get('result_limits', {}).get('max_results_per_search', 'unknown'),
            'default_timeout_seconds': performance_config.get('execution_limits', {}).get('search_timeout_seconds', 'unknown')
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Guardrails config retrieval failed: {str(e)}")
        return {
            'success': False,
            'error': f"Config retrieval failed: {str(e)}",
            'user_role_requested': variables.get('user_role', 'unknown')
        }

def test_data_masking(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Test data masking rules on sample data
    
    Args:
        data: Dummy search response (ignored)
        variables: Contains sample_data, user_role
        
    Returns:
        Masked data examples showing privacy controls in action
    """
    try:
        variables = variables or {}
        sample_data_str = variables.get('sample_data', '')
        user_role = variables.get('user_role', 'standard_user')
        
        if not sample_data_str.strip():
            # Provide default test data if none given
            sample_data = [
                {
                    "username": "john.doe@company.com",
                    "password": "secretpassword123",
                    "ssn": "123-45-6789",
                    "credit_card": "4532-1234-5678-9012",
                    "phone": "555-123-4567",
                    "ip_address": "192.168.1.100",
                    "host": "web-server-01",
                    "timestamp": "2024-01-15T10:30:00Z"
                },
                {
                    "user": "admin",
                    "api_key": "sk-1234567890abcdef",
                    "account_number": "ACC-987654321",
                    "email": "admin@company.com",
                    "action": "login_attempt",
                    "result": "success"
                }
            ]
            sample_data_source = "default_test_data"
        else:
            try:
                sample_data = json.loads(sample_data_str)
                if not isinstance(sample_data, list):
                    sample_data = [sample_data]  # Wrap single object in list
                sample_data_source = "user_provided"
            except json.JSONDecodeError as e:
                return {
                    'success': False,
                    'error': f"Invalid JSON in sample_data: {str(e)}",
                    'example_format': '{"username": "test@example.com", "password": "secret123"}'
                }
        
        # Create user context for testing
        user_context = {
            'username': 'test_user',
            'roles': [user_role],
            'user_role': user_role
        }
        
        # Apply data masking
        guardrails = get_guardrails_engine()
        
        # Get role limits to show if masking would be applied
        role_limits = guardrails._get_role_limits(user_role)
        masking_enabled = role_limits.get('data_masking_enabled', True)
        
        if masking_enabled:
            masked_data = guardrails.apply_data_masking(sample_data, user_context)
        else:
            masked_data = sample_data  # No masking for this role
        
        # Prepare comparison result
        result = {
            'success': True,
            'user_role': user_role,
            'masking_enabled_for_role': masking_enabled,
            'sample_data_source': sample_data_source,
            'data_comparison': {
                'original_data': sample_data,
                'masked_data': masked_data,
                'masking_applied': masked_data != sample_data
            }
        }
        
        # Analyze what was masked
        if masking_enabled and masked_data != sample_data:
            masked_fields = set()
            for orig, masked in zip(sample_data, masked_data):
                for field in orig.keys():
                    if orig.get(field) != masked.get(field):
                        masked_fields.add(field)
            
            result['masking_analysis'] = {
                'fields_masked': list(masked_fields),
                'total_fields_masked': len(masked_fields),
                'masking_effective': len(masked_fields) > 0
            }
        else:
            result['masking_analysis'] = {
                'fields_masked': [],
                'total_fields_masked': 0,
                'masking_effective': False,
                'reason': 'No masking applied for this role' if not masking_enabled else 'No sensitive fields detected'
            }
        
        # Get configuration info for context
        privacy_config = guardrails.config.get('privacy', {})
        result['privacy_configuration'] = {
            'sensitive_field_patterns': privacy_config.get('sensitive_fields', [])[:10],  # Show first 10
            'total_sensitive_patterns': len(privacy_config.get('sensitive_fields', [])),
            'masking_patterns_available': list(privacy_config.get('masking_patterns', {}).keys())
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Data masking test failed: {str(e)}")
        return {
            'success': False,
            'error': f"Masking test failed: {str(e)}",
            'user_role': variables.get('user_role', 'unknown')
        }