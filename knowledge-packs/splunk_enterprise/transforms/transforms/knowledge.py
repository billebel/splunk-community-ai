"""
Ultra-Simplified Knowledge Objects Transform - Minimal processing since API pre-filters
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

def _extract_basic(entries: List[Dict], item_type: str) -> List[Dict]:
    """Extract basic info from any knowledge object type"""
    items = []
    for entry in entries:
        content = entry.get('content', {})
        item = {
            'name': entry.get('name', 'unknown'),
            'app': content.get('eai:appName', 'unknown')
        }
        items.append(item)
    return items

def extract_data_models(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Extract data models - ULTRA SIMPLIFIED"""
    try:
        entries = data.get('entry', [])
        models = []
        accelerated_count = 0
        
        for entry in entries:
            content = entry.get('content', {})
            is_accelerated = 'enabled\":true' in content.get('acceleration', '')
            
            model = {
                'name': entry.get('name', 'unknown'),
                'app': content.get('eai:appName', 'unknown'),
                'accelerated': is_accelerated
            }
            
            if is_accelerated:
                model['tstats_example'] = f"| tstats count from datamodel={model['name']}"
                accelerated_count += 1
            
            models.append(model)
        
        return {
            'success': True,
            'data_models': models,
            'count': len(models),
            'accelerated_count': accelerated_count
        }
    except Exception as e:
        logger.error(f"Data models extraction failed: {str(e)}")
        return {'success': False, 'error': str(e), 'data_models': [], 'count': 0}

def extract_search_macros(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Extract search macros - ULTRA SIMPLIFIED"""
    try:
        entries = data.get('entry', [])
        macros = []
        
        for entry in entries:
            content = entry.get('content', {})
            name = entry.get('name', 'unknown')
            args = content.get('args', '')
            
            macro = {
                'name': name,
                'app': content.get('eai:appName', 'unknown'),
                'has_args': bool(args),
                'usage': f'`{name}({args})`' if args else f'`{name}`'
            }
            macros.append(macro)
        
        return {
            'success': True,
            'search_macros': macros,
            'count': len(macros)
        }
    except Exception as e:
        logger.error(f"Search macros extraction failed: {str(e)}")
        return {'success': False, 'error': str(e), 'search_macros': [], 'count': 0}

def extract_event_types(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Extract event types - ULTRA SIMPLIFIED"""
    try:
        items = _extract_basic(data.get('entry', []), 'eventtype')
        for item in items:
            item['usage'] = f'eventtype="{item["name"]}"'
        
        return {
            'success': True,
            'event_types': items,
            'count': len(items)
        }
    except Exception as e:
        logger.error(f"Event types extraction failed: {str(e)}")
        return {'success': False, 'error': str(e), 'event_types': [], 'count': 0}

def extract_lookup_tables(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Extract lookup tables - ULTRA SIMPLIFIED"""
    try:
        items = _extract_basic(data.get('entry', []), 'lookup')
        for item in items:
            item['usage'] = f'| lookup {item["name"]} field_in OUTPUT field_out'
        
        return {
            'success': True,
            'lookup_tables': items,
            'count': len(items)
        }
    except Exception as e:
        logger.error(f"Lookup tables extraction failed: {str(e)}")
        return {'success': False, 'error': str(e), 'lookup_tables': [], 'count': 0}

def extract_field_extractions(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Extract field extractions - ULTRA SIMPLIFIED"""
    try:
        entries = data.get('entry', [])
        extractions = {}
        
        for entry in entries:
            sourcetype = entry.get('name', 'unknown')
            if sourcetype not in extractions:
                extractions[sourcetype] = {
                    'sourcetype': sourcetype,
                    'app': entry.get('content', {}).get('eai:appName', 'unknown')
                }
        
        return {
            'success': True,
            'field_extractions': extractions,
            'count': len(extractions)
        }
    except Exception as e:
        logger.error(f"Field extractions extraction failed: {str(e)}")
        return {'success': False, 'error': str(e), 'field_extractions': {}, 'count': 0}