"""
Knowledge Objects Transform - Extract Splunk configuration and knowledge objects
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

def extract_data_models(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extract data model information for tstats optimization discovery
    
    Args:
        data: Splunk /services/datamodel/model response
        variables: Tool parameters
        
    Returns:
        List of data models with acceleration status for LLM tstats optimization
    """
    try:
        entries = data.get('entry', [])
        data_models = []
        
        for entry in entries:
            if not isinstance(entry, dict):
                continue
                
            content = entry.get('content', {})
            acl = entry.get('acl', {})
            
            model_info = {
                'name': entry.get('name', 'unknown'),
                'title': entry.get('title', entry.get('name', 'unknown')),
                'description': content.get('description', ''),
                'app': acl.get('app', 'unknown'),
                'accelerated': content.get('acceleration', False),
                'acceleration_status': 'ready_for_tstats' if content.get('acceleration', False) else 'not_accelerated',
                'object_count': len(content.get('objects', [])),
                'created': entry.get('published', ''),
                'updated': entry.get('updated', '')
            }
            
            # Add tstats usage guidance
            if model_info['accelerated']:
                model_info['tstats_example'] = f"| tstats count from datamodel={model_info['name']}"
            
            data_models.append(model_info)
        
        # Sort by acceleration status first, then by name
        data_models.sort(key=lambda x: (-int(x['accelerated']), x['name']))
        
        return {
            'success': True,
            'data_models': data_models,
            'count': len(data_models),
            'optimization_summary': {
                'total_models': len(data_models),
                'accelerated_models': [dm['name'] for dm in data_models if dm['accelerated']],
                'non_accelerated_models': [dm['name'] for dm in data_models if not dm['accelerated']],
                'tstats_ready_count': sum(1 for dm in data_models if dm['accelerated'])
            },
            'usage_guidance': "Use accelerated data models with tstats for high-performance searches. Accelerated models provide 10-100x performance improvement over regular searches."
        }
        
    except Exception as e:
        logger.error(f"Data models extraction failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'data_models': [],
            'count': 0
        }

def extract_data_model_structure(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extract detailed data model structure for tstats query construction
    
    Args:
        data: Splunk /services/datamodel/model/{name} response
        variables: Parameters (model_name)
        
    Returns:
        Detailed data model structure for LLM tstats construction
    """
    try:
        variables = variables or {}
        model_name = variables.get('model_name', 'unknown')
        
        entry = data.get('entry', [{}])[0]
        content = entry.get('content', {})
        
        # Extract objects and fields
        objects = content.get('objects', [])
        processed_objects = []
        
        for obj in objects:
            if isinstance(obj, dict):
                fields = obj.get('fields', [])
                field_names = [f.get('fieldName', '') for f in fields if isinstance(f, dict)]
                
                obj_info = {
                    'name': obj.get('objectName', 'unknown'),
                    'display_name': obj.get('displayName', ''),
                    'parent': obj.get('parentName', ''),
                    'available_fields': field_names,
                    'field_count': len(field_names)
                }
                processed_objects.append(obj_info)
        
        model_structure = {
            'name': model_name,
            'description': content.get('description', ''),
            'acceleration_enabled': content.get('acceleration', False),
            'objects': processed_objects,
            'total_objects': len(processed_objects),
            'all_available_fields': []
        }
        
        # Collect all unique fields across objects
        all_fields = set()
        for obj in processed_objects:
            all_fields.update(obj['available_fields'])
        model_structure['all_available_fields'] = sorted(list(all_fields))
        
        # Generate tstats examples if accelerated
        examples = []
        if model_structure['acceleration_enabled']:
            examples = [
                f"| tstats count from datamodel={model_name}",
                f"| tstats count from datamodel={model_name} by _time span=1h",
            ]
            
            # Add field-specific examples if we have fields
            if model_structure['all_available_fields']:
                first_field = model_structure['all_available_fields'][0]
                examples.append(f"| tstats count from datamodel={model_name} by {first_field}")
        
        return {
            'success': True,
            'model_structure': model_structure,
            'tstats_examples': examples,
            'usage_note': "Use these field names in tstats queries for optimal performance" if model_structure['acceleration_enabled'] else "Data model not accelerated - tstats not available"
        }
        
    except Exception as e:
        logger.error(f"Data model structure extraction failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'model_structure': {}
        }

def extract_event_types(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extract event type definitions for search pattern reuse
    
    Args:
        data: Splunk /services/saved/eventtypes response
        variables: Tool parameters
        
    Returns:
        List of event types with search patterns for LLM reuse
    """
    try:
        entries = data.get('entry', [])
        event_types = []
        
        for entry in entries:
            if not isinstance(entry, dict):
                continue
                
            content = entry.get('content', {})
            acl = entry.get('acl', {})
            
            eventtype_info = {
                'name': entry.get('name', 'unknown'),
                'description': content.get('description', ''),
                'search_pattern': content.get('search', ''),
                'tags': content.get('tags', '').split(',') if content.get('tags') else [],
                'app': acl.get('app', 'unknown'),
                'disabled': content.get('disabled', False),
                'usage_example': f'eventtype="{entry.get("name", "unknown")}"'
            }
            
            # Only include enabled event types
            if not eventtype_info['disabled']:
                event_types.append(eventtype_info)
        
        return {
            'success': True,
            'event_types': event_types,
            'count': len(event_types),
            'usage_guidance': "Use eventtype=\"name\" in searches to leverage pre-defined event patterns. This ensures consistency with existing analysis."
        }
        
    except Exception as e:
        logger.error(f"Event types extraction failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'event_types': [],
            'count': 0
        }

def extract_search_macros(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extract search macro definitions for reusable search logic
    
    Args:
        data: Splunk /services/admin/macros response
        variables: Tool parameters
        
    Returns:
        List of search macros for LLM reuse in search construction
    """
    try:
        entries = data.get('entry', [])
        macros = []
        
        for entry in entries:
            if not isinstance(entry, dict):
                continue
                
            content = entry.get('content', {})
            acl = entry.get('acl', {})
            
            macro_info = {
                'name': entry.get('name', 'unknown'),
                'definition': content.get('definition', ''),
                'description': content.get('description', ''),
                'args': content.get('args', ''),
                'app': acl.get('app', 'unknown'),
                'is_private': content.get('isPrivate', False)
            }
            
            # Generate usage example
            if macro_info['args']:
                # Macro has arguments
                arg_count = len(macro_info['args'].split(',')) if macro_info['args'] else 0
                arg_placeholders = ', '.join([f'arg{i+1}' for i in range(arg_count)])
                macro_info['usage_example'] = f'`{macro_info["name"]}({arg_placeholders})`'
            else:
                # Simple macro without arguments
                macro_info['usage_example'] = f'`{macro_info["name"]}`'
            
            # Only include public macros or private ones from search app
            if not macro_info['is_private'] or macro_info['app'] == 'search':
                macros.append(macro_info)
        
        return {
            'success': True,
            'search_macros': macros,
            'count': len(macros),
            'usage_guidance': "Use `macro_name` in searches to leverage reusable search logic. Macros with arguments use syntax `macro_name(arg1, arg2)`."
        }
        
    except Exception as e:
        logger.error(f"Search macros extraction failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'search_macros': [],
            'count': 0
        }

def extract_field_extractions(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extract field extraction rules to understand data structure
    
    Args:
        data: Splunk /services/data/props/extractions response
        variables: Tool parameters
        
    Returns:
        Field extraction information for understanding data structure
    """
    try:
        entries = data.get('entry', [])
        extractions = []
        
        for entry in entries:
            if not isinstance(entry, dict):
                continue
                
            content = entry.get('content', {})
            acl = entry.get('acl', {})
            
            extraction_info = {
                'sourcetype': entry.get('name', 'unknown'),
                'app': acl.get('app', 'unknown'),
                'extraction_type': content.get('type', 'unknown'),
                'field_names': content.get('field_names', '').split(',') if content.get('field_names') else [],
                'regex_pattern': content.get('regex', '')[:100] + '...' if len(content.get('regex', '')) > 100 else content.get('regex', '')  # Truncate long regex
            }
            
            extractions.append(extraction_info)
        
        # Group by sourcetype for better organization
        sourcetype_extractions = {}
        for ext in extractions:
            st = ext['sourcetype']
            if st not in sourcetype_extractions:
                sourcetype_extractions[st] = []
            sourcetype_extractions[st].append(ext)
        
        return {
            'success': True,
            'field_extractions_by_sourcetype': sourcetype_extractions,
            'total_extractions': len(extractions),
            'sourcetypes_with_extractions': list(sourcetype_extractions.keys()),
            'usage_guidance': "These field extractions show what fields are available for each sourcetype. Use this information to construct searches with correct field names."
        }
        
    except Exception as e:
        logger.error(f"Field extractions extraction failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'field_extractions_by_sourcetype': {},
            'total_extractions': 0
        }

def extract_lookup_tables(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extract lookup table information for enrichment opportunities
    
    Args:
        data: Splunk /services/data/lookup-table-files response
        variables: Tool parameters
        
    Returns:
        Available lookup tables for data enrichment
    """
    try:
        entries = data.get('entry', [])
        lookup_tables = []
        
        for entry in entries:
            if not isinstance(entry, dict):
                continue
                
            content = entry.get('content', {})
            acl = entry.get('acl', {})
            
            lookup_info = {
                'name': entry.get('name', 'unknown'),
                'filename': content.get('filename', ''),
                'app': acl.get('app', 'unknown'),
                'size_bytes': content.get('size', 0),
                'updated': entry.get('updated', ''),
                'usage_example': f'| lookup {entry.get("name", "unknown")} field_name'
            }
            
            lookup_tables.append(lookup_info)
        
        # Sort by size (largest first) to show most comprehensive lookups
        lookup_tables.sort(key=lambda x: -x['size_bytes'])
        
        return {
            'success': True,
            'lookup_tables': lookup_tables,
            'count': len(lookup_tables),
            'total_size_bytes': sum(lt['size_bytes'] for lt in lookup_tables),
            'usage_guidance': "Use lookup tables to enrich search results with additional context. Syntax: | lookup table_name input_field OUTPUT enrichment_field"
        }
        
    except Exception as e:
        logger.error(f"Lookup tables extraction failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'lookup_tables': [],
            'count': 0
        }