"""
Discovery Transform - Extract Splunk environment information
"""

from typing import Dict, List, Any, Optional
import logging
import yaml
import os

logger = logging.getLogger(__name__)

def extract_indexes(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extract index information - SIMPLIFIED since API pre-filters data
    
    Args:
        data: Pre-filtered Splunk response (f=name&f=currentDBSizeMB&f=totalEventCount&f=disabled&f=datatype&f=minTime&f=maxTime)
        variables: Parameters (include_internal, etc.)
        
    Returns:
        Clean list of available indexes with minimal processing needed
    """
    try:
        variables = variables or {}
        include_internal = variables.get('include_internal', False)
        
        entries = data.get('entry', [])
        indexes = []
        
        for entry in entries:
            content = entry.get('content', {})
            index_name = entry.get('name', 'unknown')
            
            # Simple filter for internal indexes
            if not include_internal and index_name.startswith('_'):
                continue
            
            # Simple extraction - API already filtered for us
            index_info = {
                'name': index_name,
                'current_size_mb': _safe_int(content.get('currentDBSizeMB', 0)),
                'total_event_count': _safe_int(content.get('totalEventCount', 0)),
                'disabled': content.get('disabled', False),
                'data_type': content.get('datatype', 'event'),
                'earliest_time': content.get('minTime', ''),
                'latest_time': content.get('maxTime', ''),
                'is_internal': index_name.startswith('_')
            }
            
            indexes.append(index_info)
        
        # API already handles most filtering - simple sort by size
        indexes.sort(key=lambda x: (-x['current_size_mb'], x['name']))
        
        return {
            'success': True,
            'indexes': indexes,
            'count': len(indexes),
            'total_size_mb': sum(idx['current_size_mb'] for idx in indexes),
            'largest_indexes': [idx['name'] for idx in indexes[:5]],
            'usage_guidance': f"Found {len(indexes)} indexes. Largest: {indexes[0]['name'] if indexes else 'none'}"
        }
        
    except Exception as e:
        logger.error(f"Index extraction failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'indexes': [],
            'count': 0
        }

def _safe_int(value: Any) -> int:
    """Safely convert value to integer"""
    try:
        if isinstance(value, (int, float)):
            return int(value)
        elif isinstance(value, str):
            return int(float(value)) if value.replace('.', '').replace('-', '').isdigit() else 0
        else:
            return 0
    except (ValueError, TypeError):
        return 0

def find_data_sources(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Find data sources for common user requests - translates business terms to Splunk searches
    
    Args:
        data: Dummy server info (ignored)
        variables: search_term (user's request), category (broad category)
        
    Returns:
        Ready-to-use index/sourcetype info with example searches for the LLM
    """
    try:
        variables = variables or {}
        search_term = variables.get('search_term', '').lower()
        category = variables.get('category', '').lower()
        
        # Load the data source mappings file
        mappings_file = os.path.join(os.path.dirname(__file__), '..', 'data_source_mappings.yaml')
        
        if not os.path.exists(mappings_file):
            return {
                'success': False,
                'error': 'Data source mappings not available',
                'suggestion': 'Try using list_indexes or get_sourcetypes to discover data sources directly',
                'available_categories': ['authentication', 'network', 'security', 'web', 'system', 'application', 'database'],
                'example_usage': 'Use search_term like "login", "web", or "firewall" to find relevant data sources'
            }
        
        with open(mappings_file, 'r') as f:
            mappings = yaml.safe_load(f)
        
        result = {
            'success': True,
            'search_term': search_term,
            'category_filter': category
        }
        
        # If specific category requested, return just that
        if category and category in mappings:
            result['category_data'] = {
                category: mappings[category]
            }
            result['message'] = f"Data source mappings for category: {category}"
            return result
        
        # If search term provided, find relevant mappings
        if search_term:
            relevant_mappings = {}
            
            for cat_name, cat_data in mappings.items():
                if cat_name in ['common_field_aliases', 'time_range_recommendations']:
                    continue
                    
                # Check if search term matches category name or aliases
                if search_term in cat_name.lower():
                    relevant_mappings[cat_name] = cat_data
                    continue
                
                # Check aliases
                if 'aliases' in cat_data:
                    for alias in cat_data['aliases']:
                        if search_term in alias.lower():
                            relevant_mappings[cat_name] = cat_data
                            break
                
                # Check source descriptions
                if 'splunk_sources' in cat_data:
                    for source in cat_data['splunk_sources']:
                        if search_term in source.get('description', '').lower():
                            relevant_mappings[cat_name] = cat_data
                            break
            
            result['matching_categories'] = relevant_mappings
            result['matches_found'] = len(relevant_mappings)
            
            if len(relevant_mappings) > 0:
                result['message'] = f"Found {len(relevant_mappings)} data source categories for '{search_term}'"
                # Add quick usage summary
                quick_examples = []
                for cat_name, cat_data in relevant_mappings.items():
                    if 'splunk_sources' in cat_data and cat_data['splunk_sources']:
                        first_source = cat_data['splunk_sources'][0]
                        if 'example_searches' in first_source and first_source['example_searches']:
                            quick_examples.append(first_source['example_searches'][0])
                if quick_examples:
                    result['ready_to_use_searches'] = quick_examples[:3]  # Top 3 examples
            else:
                result['message'] = f"No data sources found for '{search_term}'"
                result['suggestions'] = [
                    "Try broader terms like 'web', 'security', 'network', 'database'",
                    "Use category parameter with: authentication, network, security, web, system, application, database",
                    "Or use list_indexes tool to see what data is available"
                ]
            
            # Add common field mappings if relevant
            if search_term in ['field', 'fields', 'column', 'columns']:
                result['common_field_aliases'] = mappings.get('common_field_aliases', {})
            
            return result
        
        # No specific search - return overview
        categories = []
        for cat_name, cat_data in mappings.items():
            if cat_name in ['common_field_aliases', 'time_range_recommendations']:
                continue
                
            categories.append({
                'name': cat_name,
                'aliases': cat_data.get('aliases', []),
                'source_count': len(cat_data.get('splunk_sources', [])),
                'description': f"Data sources for {cat_name}-related searches"
            })
        
        result['available_categories'] = categories
        result['total_categories'] = len(categories)
        result['message'] = "Here are all available data source categories. Use search_term for specific requests."
        
        # Include actionable usage examples
        result['how_to_use'] = {
            "for_user_requests": {
                "show_failed_logins": "search_term: 'authentication'",
                "web_server_errors": "search_term: 'web'", 
                "network_traffic": "search_term: 'network'",
                "database_issues": "search_term: 'database'"
            },
            "for_categories": "Use category parameter: authentication, network, security, web, system, application, database"
        }
        
        # Quick examples from each category
        quick_preview = {}
        for cat_name, cat_data in mappings.items():
            if cat_name in ['common_field_aliases', 'time_range_recommendations']:
                continue
            if 'splunk_sources' in cat_data and cat_data['splunk_sources']:
                first_source = cat_data['splunk_sources'][0]
                if 'example_searches' in first_source and first_source['example_searches']:
                    quick_preview[cat_name] = first_source['example_searches'][0]
        
        if quick_preview:
            result['sample_searches_by_category'] = quick_preview
        
        return result
        
    except Exception as e:
        logger.error(f"Data source lookup failed: {str(e)}")
        return {
            'success': False,
            'error': 'Could not load data source information',
            'what_to_do': 'Try using list_indexes or get_sourcetypes tools instead',
            'search_term': variables.get('search_term', ''),
            'available_categories': ['authentication', 'network', 'security', 'web', 'system', 'application', 'database'],
            'alternative_approach': 'Use list_indexes first, then get_sourcetypes to discover data sources'
        }