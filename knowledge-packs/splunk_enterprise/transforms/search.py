"""
Search Transform - Clean data extraction from Splunk search results with guardrails
"""

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

def extract_search_results(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extract clean search results from Splunk oneshot search response with guardrails enforcement
    
    Args:
        data: Splunk oneshot search response
        variables: Search parameters (search_query, max_results, etc.)
        
    Returns:
        Clean, secured, and properly limited results for LLM analysis
    """
    try:
        variables = variables or {}
        guardrails = get_guardrails_engine()
        
        # Get user context for guardrails (would typically come from auth system)
        user_context = _extract_user_context(variables)
        
        # Validate search query before processing results
        search_query = variables.get('search_query', '')
        if search_query:
            validation_result = guardrails.validate_search(search_query, user_context)
            
            # If search was blocked, return the block information
            if validation_result['blocked']:
                return {
                    'success': False,
                    'blocked_by_guardrails': True,
                    'violations': validation_result['violations'],
                    'block_reason': validation_result.get('block_reason', 'Security violation'),
                    'user_role': validation_result.get('user_role', 'unknown'),
                    'events': [],
                    'count': 0,
                    'search_info': {
                        'original_query': validation_result['original_query'],
                        'enforcement_level': validation_result['enforcement_level']
                    }
                }
        
        # Extract results from Splunk response
        results = []
        if isinstance(data.get('results'), list):
            results = data['results']
        elif isinstance(data, list):
            results = data
        
        if not results:
            return {
                'success': True,
                'events': [],
                'count': 0,
                'message': 'No events found',
                'search_info': {
                    'query': search_query,
                    'time_range': f"{variables.get('earliest_time', '')} to {variables.get('latest_time', '')}",
                    'max_requested': variables.get('max_results', 100)
                },
                'guardrails_info': {
                    'data_masking_applied': False,
                    'user_role': user_context.get('user_role', 'unknown')
                }
            }
        
        # Clean events for LLM consumption - only essential fields
        cleaned_events = []
        essential_fields = ['_time', '_raw', 'index', 'sourcetype', 'source', 'host']
        
        for event in results:
            if isinstance(event, dict):
                cleaned_event = {}
                
                # Include only the essential fields
                for field in essential_fields:
                    if field in event:
                        # Rename _time to timestamp for clarity
                        if field == '_time':
                            cleaned_event['timestamp'] = event[field]
                        else:
                            cleaned_event[field] = event[field]
                
                # Add any other non-underscore fields (but not the verbose internal ones)
                for key, value in event.items():
                    if (not key.startswith('_') and 
                        key not in ['index', 'sourcetype', 'source', 'host'] and
                        key not in cleaned_event):
                        cleaned_event[key] = value
                
                cleaned_events.append(cleaned_event)
        
        # Apply data masking based on user role and guardrails config
        masked_events = guardrails.apply_data_masking(cleaned_events, user_context)
        
        # Prepare final result
        final_result = {
            'success': True,
            'events': masked_events,
            'count': len(masked_events),
            'search_info': {
                'query': search_query,
                'time_range': f"{variables.get('earliest_time', '')} to {variables.get('latest_time', '')}",
                'max_requested': variables.get('max_results', 100),
                'total_found': len(results),
                'total_returned': len(masked_events)
            },
            'field_summary': _generate_field_summary(masked_events[:5]) if masked_events else {},
            'guardrails_info': {
                'data_masking_applied': len(masked_events) != len(cleaned_events) or any(
                    '[MASKED]' in str(event) or '***' in str(event) for event in masked_events
                ),
                'user_role': user_context.get('user_role', 'unknown'),
                'enforcement_level': validation_result.get('enforcement_level', 'none') if search_query else 'none'
            }
        }
        
        # Add guardrails warnings if any
        if search_query and validation_result.get('warnings'):
            final_result['guardrails_warnings'] = validation_result['warnings']
        
        if search_query and validation_result.get('modifications_applied'):
            final_result['guardrails_modifications'] = validation_result['modifications_applied']
        
        return final_result
        
    except Exception as e:
        logger.error(f"Search result extraction failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'events': [],
            'count': 0,
            'search_info': {
                'query': variables.get('search_query', ''),
                'error_context': 'Failed to process search results'
            },
            'guardrails_info': {
                'error': 'Guardrails processing failed'
            }
        }

def _generate_field_summary(sample_events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a summary of fields found in sample events"""
    
    if not sample_events:
        return {}
    
    all_fields = set()
    field_types = {}
    
    for event in sample_events:
        for field, value in event.items():
            all_fields.add(field)
            
            # Determine field type
            if field not in field_types:
                if field in ['timestamp', '_time'] or 'time' in field.lower():
                    field_types[field] = 'timestamp'
                elif field.endswith('_ip') or field.endswith('IP') or 'ip' in field.lower():
                    field_types[field] = 'ip_address'
                elif field in ['user', 'username', 'account', 'User']:
                    field_types[field] = 'username'
                elif isinstance(value, (int, float)):
                    field_types[field] = 'numeric'
                else:
                    field_types[field] = 'text'
    
    return {
        'total_fields': len(all_fields),
        'common_fields': list(all_fields),
        'field_types': field_types
    }

def _extract_user_context(variables: Dict[str, Any]) -> Dict[str, Any]:
    """Extract user context from variables for guardrails"""
    # In a real implementation, this would come from authentication system
    # For now, use variables or defaults
    return {
        'username': variables.get('user', 'unknown'),
        'roles': variables.get('user_roles', ['standard_user']),  # Default to standard user
        'user_role': 'standard_user'  # Will be determined by guardrails engine
    }