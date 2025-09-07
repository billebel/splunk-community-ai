"""
Enhanced Knowledge Objects Transform - LLM-optimized with smart API filtering and context awareness
"""

from typing import Dict, List, Any, Optional
import logging
import json
import os
import sys
import importlib.util

# Add transforms directory to path for imports
transforms_dir = os.path.dirname(__file__)
if transforms_dir not in sys.path:
    sys.path.insert(0, transforms_dir)

# Import LLM context manager
try:
    from llm_context_manager import get_context_manager, detect_and_configure, LLMProfile, QueryStrategy, ContextSize
except ImportError:
    # Fallback implementation
    from dataclasses import dataclass
    from enum import Enum
    
    class ContextSize(Enum):
        SMALL = "small_context"
        MEDIUM = "medium_context" 
        LARGE = "large_context"
    
    @dataclass
    class LLMProfile:
        name: str = "default"
        context_window: int = 8192
        chars_per_token: int = 4
        context_class: ContextSize = ContextSize.SMALL
    
    def detect_and_configure(request_context):
        return LLMProfile(), {"fallback": "using basic configuration"}

logger = logging.getLogger(__name__)

# Context-aware limits for different knowledge objects
KNOWLEDGE_LIMITS = {
    ContextSize.SMALL: {
        'data_models': 10,
        'search_macros': 20,
        'event_types': 30,
        'lookup_tables': 15,
        'fields_per_object': 5,
        'objects_per_model': 3
    },
    ContextSize.MEDIUM: {
        'data_models': 25,
        'search_macros': 50,
        'event_types': 75,
        'lookup_tables': 40,
        'fields_per_object': 10,
        'objects_per_model': 5
    },
    ContextSize.LARGE: {
        'data_models': 50,
        'search_macros': 100,
        'event_types': 150,
        'lookup_tables': 75,
        'fields_per_object': 20,
        'objects_per_model': 10
    }
}

def extract_data_models(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Enhanced data model extraction with LLM-optimized field information and smart filtering
    
    Args:
        data: Splunk /services/datamodel/model response (should be filtered with f=name&f=acceleration&f=eai:appName)
        variables: Tool parameters including LLM context
        
    Returns:
        LLM-optimized data models with field information and tstats examples
    """
    try:
        variables = variables or {}
        
        # Detect LLM context for appropriate limits
        request_context = _extract_request_context(variables)
        llm_profile, llm_config = detect_and_configure(request_context)
        limits = KNOWLEDGE_LIMITS[llm_profile.context_class]
        
        entries = data.get('entry', [])
        data_models = []
        
        for entry in entries[:limits['data_models']]:
            if not isinstance(entry, dict):
                continue
                
            content = entry.get('content', {})
            acl = entry.get('acl', {})
            
            # Basic model info
            model_info = {
                'name': entry.get('name', 'unknown'),
                'app': content.get('eai:appName', acl.get('app', 'unknown')),
                'accelerated': _is_accelerated(content.get('acceleration', '')),
                'acceleration_status': 'ready_for_tstats' if _is_accelerated(content.get('acceleration', '')) else 'not_accelerated'
            }
            
            # Parse model structure from description if available
            description = content.get('description', '')
            if description:
                try:
                    desc_json = json.loads(description)
                    model_info.update(_extract_model_structure(desc_json, limits))
                except (json.JSONDecodeError, KeyError):
                    # If description isn't parseable, provide basic info
                    model_info['objects'] = []
                    model_info['total_fields'] = 0
            
            # Add tstats usage examples
            if model_info['accelerated'] and model_info.get('sample_fields'):
                model_info['tstats_examples'] = _generate_tstats_examples(
                    model_info['name'], 
                    model_info['sample_fields']
                )
            
            data_models.append(model_info)
        
        # Sort by acceleration status first (accelerated models more useful), then by name
        data_models.sort(key=lambda x: (-int(x['accelerated']), x['name']))
        
        return {
            'success': True,
            'data_models': data_models,
            'count': len(data_models),
            'llm_optimization': {
                'detected_llm': llm_profile.name,
                'context_class': llm_profile.context_class.value,
                'limits_applied': limits,
                'total_available': len(entries)
            },
            'optimization_summary': {
                'accelerated_models': [dm['name'] for dm in data_models if dm['accelerated']],
                'non_accelerated_models': [dm['name'] for dm in data_models if not dm['accelerated']],
                'tstats_ready_count': sum(1 for dm in data_models if dm['accelerated'])
            },
            'usage_guidance': f"Found {sum(1 for dm in data_models if dm['accelerated'])} accelerated data models ready for high-performance tstats queries. Use accelerated models for 10-100x performance improvement."
        }
        
    except Exception as e:
        logger.error(f"Enhanced data models extraction failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'data_models': [],
            'count': 0
        }

def extract_search_macros(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Enhanced search macros extraction with LLM-optimized filtering and smart categorization
    
    Args:
        data: Splunk /services/admin/macros response (should be filtered with f=name&f=definition&f=args&f=eai:appName)
        variables: Tool parameters including LLM context
        
    Returns:
        LLM-optimized search macros with usage examples and smart categorization
    """
    try:
        variables = variables or {}
        
        # Detect LLM context for appropriate limits
        request_context = _extract_request_context(variables)
        llm_profile, llm_config = detect_and_configure(request_context)
        limits = KNOWLEDGE_LIMITS[llm_profile.context_class]
        
        entries = data.get('entry', [])
        macros = []
        
        for entry in entries[:limits['search_macros']]:
            if not isinstance(entry, dict):
                continue
                
            content = entry.get('content', {})
            acl = entry.get('acl', {})
            
            macro_name = entry.get('name', 'unknown')
            definition = content.get('definition', '')
            args = content.get('args', '')
            
            # Skip system/internal macros that aren't useful for users
            if _is_system_macro(macro_name, content.get('eai:appName', '')):
                continue
            
            macro_info = {
                'name': macro_name,
                'definition': _truncate_for_llm(definition, 200),  # Truncate long definitions
                'args': args,
                'app': content.get('eai:appName', acl.get('app', 'unknown')),
                'category': _categorize_macro(macro_name, definition),
                'complexity': _assess_macro_complexity(definition)
            }
            
            # Generate usage example
            macro_info['usage_example'] = _generate_macro_usage(macro_name, args)
            
            # Add description based on pattern recognition
            macro_info['description'] = _generate_macro_description(macro_name, definition)
            
            macros.append(macro_info)
        
        # Sort by usefulness - user-defined first, then by complexity (simpler first)
        macros.sort(key=lambda x: (
            x['app'] == 'search',  # System macros last
            x['complexity'],       # Simpler first
            x['name']             # Alphabetical
        ))
        
        return {
            'success': True,
            'search_macros': macros,
            'count': len(macros),
            'llm_optimization': {
                'detected_llm': llm_profile.name,
                'context_class': llm_profile.context_class.value,
                'limits_applied': limits,
                'total_available': len(entries)
            },
            'categorization': {
                category: [m['name'] for m in macros if m['category'] == category]
                for category in set(m['category'] for m in macros)
            },
            'usage_guidance': "Use `macro_name` in searches to leverage reusable search logic. Macros with arguments use syntax `macro_name(arg1, arg2)`."
        }
        
    except Exception as e:
        logger.error(f"Enhanced search macros extraction failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'search_macros': [],
            'count': 0
        }

def extract_event_types(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Enhanced event types extraction with LLM-optimized categorization and usage examples
    
    Args:
        data: Splunk /services/saved/eventtypes response (should be filtered with f=name&f=search&f=tags&f=eai:appName)
        variables: Tool parameters including LLM context
        
    Returns:
        LLM-optimized event types with smart categorization and usage guidance
    """
    try:
        variables = variables or {}
        
        # Detect LLM context for appropriate limits
        request_context = _extract_request_context(variables)
        llm_profile, llm_config = detect_and_configure(request_context)
        limits = KNOWLEDGE_LIMITS[llm_profile.context_class]
        
        entries = data.get('entry', [])
        event_types = []
        
        for entry in entries[:limits['event_types']]:
            if not isinstance(entry, dict):
                continue
                
            content = entry.get('content', {})
            acl = entry.get('acl', {})
            
            # Skip disabled event types
            if content.get('disabled', False):
                continue
            
            eventtype_name = entry.get('name', 'unknown')
            search_pattern = content.get('search', '')
            tags = content.get('tags', '').split(',') if content.get('tags') else []
            
            eventtype_info = {
                'name': eventtype_name,
                'search_pattern': _truncate_for_llm(search_pattern, 150),
                'tags': [tag.strip() for tag in tags if tag.strip()],
                'app': content.get('eai:appName', acl.get('app', 'unknown')),
                'category': _categorize_eventtype(eventtype_name, search_pattern, tags),
                'usage_example': f'eventtype="{eventtype_name}"'
            }
            
            # Add description based on pattern analysis
            eventtype_info['description'] = _generate_eventtype_description(
                eventtype_name, search_pattern, tags
            )
            
            event_types.append(eventtype_info)
        
        # Sort by category relevance and usefulness
        event_types.sort(key=lambda x: (
            x['category'] == 'other',     # Known categories first
            len(x['tags']) == 0,          # Tagged events first
            x['name']                     # Alphabetical
        ))
        
        return {
            'success': True,
            'event_types': event_types,
            'count': len(event_types),
            'llm_optimization': {
                'detected_llm': llm_profile.name,
                'context_class': llm_profile.context_class.value,
                'limits_applied': limits,
                'total_available': len(entries)
            },
            'categorization': {
                category: [et['name'] for et in event_types if et['category'] == category]
                for category in set(et['category'] for et in event_types)
            },
            'usage_guidance': "Use eventtype=\"name\" in searches to leverage pre-defined event patterns. This ensures consistency with existing analysis and improves search performance."
        }
        
    except Exception as e:
        logger.error(f"Enhanced event types extraction failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'event_types': [],
            'count': 0
        }

def extract_lookup_tables(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Enhanced lookup tables extraction with LLM-optimized metadata and usage examples
    
    Args:
        data: Splunk /services/data/transforms/lookups response (should be filtered)
        variables: Tool parameters including LLM context
        
    Returns:
        LLM-optimized lookup tables with usage examples and smart categorization
    """
    try:
        variables = variables or {}
        
        # Detect LLM context for appropriate limits
        request_context = _extract_request_context(variables)
        llm_profile, llm_config = detect_and_configure(request_context)
        limits = KNOWLEDGE_LIMITS[llm_profile.context_class]
        
        entries = data.get('entry', [])
        lookup_tables = []
        
        for entry in entries[:limits['lookup_tables']]:
            if not isinstance(entry, dict):
                continue
                
            content = entry.get('content', {})
            acl = entry.get('acl', {})
            
            lookup_name = entry.get('name', 'unknown')
            filename = content.get('filename', '')
            
            lookup_info = {
                'name': lookup_name,
                'filename': filename,
                'app': content.get('eai:appName', acl.get('app', 'unknown')),
                'type': _determine_lookup_type(filename, content),
                'size_estimate': _estimate_lookup_size(content),
                'category': _categorize_lookup(lookup_name, filename)
            }
            
            # Generate usage examples
            lookup_info['usage_examples'] = _generate_lookup_usage_examples(lookup_name)
            
            # Add description based on name analysis
            lookup_info['description'] = _generate_lookup_description(lookup_name, filename)
            
            lookup_tables.append(lookup_info)
        
        # Sort by usefulness - smaller, more commonly named lookups first
        lookup_tables.sort(key=lambda x: (
            x['size_estimate'] == 'unknown',  # Known sizes first
            x['category'] == 'other',          # Categorized first
            x['size_estimate'] == 'very_large', # Smaller first
            x['name']                          # Alphabetical
        ))
        
        return {
            'success': True,
            'lookup_tables': lookup_tables,
            'count': len(lookup_tables),
            'llm_optimization': {
                'detected_llm': llm_profile.name,
                'context_class': llm_profile.context_class.value,
                'limits_applied': limits,
                'total_available': len(entries)
            },
            'categorization': {
                category: [lt['name'] for lt in lookup_tables if lt['category'] == category]
                for category in set(lt['category'] for lt in lookup_tables)
            },
            'usage_guidance': "Use lookup tables to enrich search results with additional context. Syntax: | lookup table_name input_field OUTPUT enrichment_field"
        }
        
    except Exception as e:
        logger.error(f"Enhanced lookup tables extraction failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'lookup_tables': [],
            'count': 0
        }

# Helper functions for data model processing
def _extract_model_structure(desc_json: Dict, limits: Dict) -> Dict[str, Any]:
    """Extract and optimize data model structure from description JSON"""
    
    objects = desc_json.get('objects', [])
    all_fields = []
    optimized_objects = []
    
    for obj in objects[:limits['objects_per_model']]:
        obj_name = obj.get('objectName', 'unknown')
        fields = obj.get('fields', [])
        
        # Extract field names and types
        field_info = []
        for field in fields[:limits['fields_per_object']]:
            if isinstance(field, dict):
                field_name = field.get('fieldName', 'unknown')
                field_type = field.get('type', 'string')
                field_info.append({'name': field_name, 'type': field_type})
                all_fields.append(field_name)
        
        optimized_objects.append({
            'name': obj_name,
            'fields': field_info,
            'field_count': len(fields)  # Total count, not just shown
        })
    
    return {
        'displayName': desc_json.get('displayName', ''),
        'objects': optimized_objects,
        'total_objects': len(objects),
        'total_fields': len(set(all_fields)),
        'sample_fields': all_fields[:10]  # For tstats examples
    }

def _generate_tstats_examples(model_name: str, sample_fields: List[str]) -> List[str]:
    """Generate practical tstats usage examples"""
    examples = [
        f"| tstats count from datamodel={model_name}",
        f"| tstats count from datamodel={model_name} by _time span=1h"
    ]
    
    if sample_fields:
        # Add field-specific examples
        examples.append(f"| tstats count from datamodel={model_name} by {sample_fields[0]}")
        if len(sample_fields) > 1:
            examples.append(f"| tstats values({sample_fields[1]}) from datamodel={model_name} by {sample_fields[0]}")
    
    return examples

def _is_accelerated(acceleration_config: str) -> bool:
    """Check if data model is accelerated"""
    return 'enabled":true' in acceleration_config

# Helper functions for macros
def _is_system_macro(name: str, app: str) -> bool:
    """Identify system macros that aren't useful for users"""
    system_patterns = ['_', 'internal', 'splunk', 'default']
    return any(pattern in name.lower() for pattern in system_patterns) or app in ['splunk_httpinput', 'splunk_monitoring_console']

def _categorize_macro(name: str, definition: str) -> str:
    """Categorize macro by function"""
    name_lower = name.lower()
    def_lower = definition.lower()
    
    if any(term in name_lower for term in ['time', 'date', 'hour', 'day']):
        return 'time_analysis'
    elif any(term in name_lower for term in ['security', 'auth', 'user', 'login']):
        return 'security'
    elif any(term in name_lower for term in ['network', 'ip', 'dns', 'tcp', 'udp']):
        return 'network'
    elif any(term in name_lower for term in ['error', 'exception', 'fail', 'alert']):
        return 'error_handling'
    elif any(term in def_lower for term in ['stats', 'chart', 'timechart']):
        return 'analytics'
    else:
        return 'general'

def _assess_macro_complexity(definition: str) -> int:
    """Assess macro complexity (0=simple, 2=complex)"""
    if len(definition) < 50:
        return 0  # Simple
    elif len(definition) < 200:
        return 1  # Medium
    else:
        return 2  # Complex

def _generate_macro_usage(name: str, args: str) -> str:
    """Generate macro usage example"""
    if args:
        arg_count = len(args.split(',')) if args else 0
        arg_placeholders = ', '.join([f'arg{i+1}' for i in range(arg_count)])
        return f'`{name}({arg_placeholders})`'
    else:
        return f'`{name}`'

def _generate_macro_description(name: str, definition: str) -> str:
    """Generate helpful description based on macro analysis"""
    if 'stats' in definition.lower():
        return f"Statistical analysis macro - {name}"
    elif 'search' in definition.lower():
        return f"Search optimization macro - {name}"
    elif 'eval' in definition.lower():
        return f"Field calculation macro - {name}"
    else:
        return f"Utility macro - {name}"

# Helper functions for event types
def _categorize_eventtype(name: str, search: str, tags: List[str]) -> str:
    """Categorize event type by function"""
    name_lower = name.lower()
    search_lower = search.lower()
    all_tags = ' '.join(tags).lower()
    
    security_terms = ['security', 'auth', 'login', 'fail', 'attack', 'malware', 'intrusion']
    network_terms = ['network', 'traffic', 'connection', 'firewall', 'dns', 'proxy']
    system_terms = ['system', 'error', 'warning', 'performance', 'cpu', 'memory']
    web_terms = ['web', 'http', 'apache', 'nginx', 'access', 'request']
    
    text_to_check = f"{name_lower} {search_lower} {all_tags}"
    
    if any(term in text_to_check for term in security_terms):
        return 'security'
    elif any(term in text_to_check for term in network_terms):
        return 'network'
    elif any(term in text_to_check for term in system_terms):
        return 'system'
    elif any(term in text_to_check for term in web_terms):
        return 'web'
    else:
        return 'other'

def _generate_eventtype_description(name: str, search: str, tags: List[str]) -> str:
    """Generate helpful description for event type"""
    if tags:
        return f"Event type for {', '.join(tags[:3])} events"
    elif 'error' in search.lower():
        return f"Error event detection - {name}"
    elif 'success' in search.lower():
        return f"Success event detection - {name}"
    else:
        return f"Custom event pattern - {name}"

# Helper functions for lookups
def _determine_lookup_type(filename: str, content: Dict) -> str:
    """Determine lookup table type"""
    if filename.endswith('.csv'):
        return 'csv_file'
    elif filename.endswith('.txt'):
        return 'text_file'
    elif 'external_cmd' in content:
        return 'scripted'
    elif 'collection' in content:
        return 'kv_store'
    else:
        return 'unknown'

def _estimate_lookup_size(content: Dict) -> str:
    """Estimate lookup table size category"""
    size = content.get('size', 0)
    if isinstance(size, (int, str)):
        try:
            size_bytes = int(size)
            if size_bytes < 1024:
                return 'small'
            elif size_bytes < 1024 * 1024:  # 1MB
                return 'medium'
            elif size_bytes < 10 * 1024 * 1024:  # 10MB
                return 'large'
            else:
                return 'very_large'
        except ValueError:
            pass
    return 'unknown'

def _categorize_lookup(name: str, filename: str) -> str:
    """Categorize lookup by purpose"""
    text = f"{name} {filename}".lower()
    
    geo_terms = ['geo', 'location', 'country', 'city', 'ip', 'asn']
    user_terms = ['user', 'employee', 'person', 'identity', 'ldap', 'ad']
    asset_terms = ['asset', 'inventory', 'host', 'server', 'device', 'cmdb']
    threat_terms = ['threat', 'malware', 'ioc', 'intel', 'blacklist', 'reputation']
    
    if any(term in text for term in geo_terms):
        return 'geolocation'
    elif any(term in text for term in user_terms):
        return 'identity'
    elif any(term in text for term in asset_terms):
        return 'asset_management'
    elif any(term in text for term in threat_terms):
        return 'threat_intelligence'
    else:
        return 'other'

def _generate_lookup_usage_examples(name: str) -> List[str]:
    """Generate practical lookup usage examples"""
    return [
        f"| lookup {name} input_field",
        f"| lookup {name} input_field OUTPUT output_field",
        f"| lookup {name} input_field as field_alias OUTPUT output_field"
    ]

def _generate_lookup_description(name: str, filename: str) -> str:
    """Generate helpful description for lookup"""
    if 'geo' in name.lower() or 'location' in name.lower():
        return f"Geographic enrichment lookup - {name}"
    elif 'user' in name.lower() or 'identity' in name.lower():
        return f"User/identity enrichment lookup - {name}"
    elif 'asset' in name.lower() or 'inventory' in name.lower():
        return f"Asset information lookup - {name}"
    else:
        return f"Data enrichment lookup - {name}"

# Utility functions
def _extract_request_context(variables: Dict[str, Any]) -> Dict[str, Any]:
    """Extract context clues for LLM detection"""
    return {
        'user_agent': variables.get('user_agent', ''),
        'api_endpoint': variables.get('api_endpoint', ''),
        'model': variables.get('model', variables.get('llm_model', '')),
        'client_info': variables.get('client_info', {}),
        'query_intent': variables.get('query_intent', 'discovery')
    }

def _truncate_for_llm(text: str, max_length: int) -> str:
    """Truncate text for LLM consumption"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."