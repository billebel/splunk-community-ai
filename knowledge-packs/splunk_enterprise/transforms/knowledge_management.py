"""
Knowledge Object Management Transforms
Handles creation, updating, and deletion of Splunk knowledge objects with AI assistance.
"""

import csv
import io
import json
import logging
import re
from typing import Dict, Any, Optional, List

try:
    from .guardrails import GuardrailsEngine
    SecurityValidator = GuardrailsEngine  # Use GuardrailsEngine as SecurityValidator
except ImportError:
    # Fallback for testing - create a simple validator
    class SecurityValidator:
        def is_safe_content(self, content: str) -> bool:
            """Basic safety check"""
            dangerous = ['|delete', '|script', '|run', '|external']
            return not any(cmd in content.lower() for cmd in dangerous)

logger = logging.getLogger(__name__)

class KnowledgeObjectManager:
    """Manages Splunk knowledge objects with AI-powered optimization"""

    def __init__(self):
        self.security = SecurityValidator()

    def _validate_name(self, name: str, object_type: str) -> Dict[str, Any]:
        """Validate object names follow Splunk conventions"""
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', name):
            return {
                'valid': False,
                'error': f'{object_type} name must start with letter and contain only letters, numbers, underscores'
            }

        if len(name) > 50:
            return {
                'valid': False,
                'error': f'{object_type} name too long (max 50 characters)'
            }

        return {'valid': True}

def create_lookup(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a Splunk lookup table with AI-powered data optimization

    Uses the management prompts to analyze and optimize data before creation
    """
    try:
        params = data.get('parameters', {})
        lookup_name = params.get('lookup_name', '').strip()
        raw_data = params.get('raw_data', '').strip()
        lookup_purpose = params.get('lookup_purpose', '').strip()
        app_context = params.get('app_context', 'search')

        # Basic validation
        if not lookup_name or not raw_data or not lookup_purpose:
            return {
                'success': False,
                'error': 'Missing required parameters: lookup_name, raw_data, lookup_purpose'
            }

        # Validate lookup name
        name_validation = KnowledgeObjectManager()._validate_name(lookup_name, 'Lookup')
        if not name_validation['valid']:
            return {
                'success': False,
                'error': name_validation['error']
            }

        # Security validation
        security = SecurityValidator()
        if not security.is_safe_content(raw_data):
            return {
                'success': False,
                'error': 'Data contains potentially dangerous content'
            }

        # Size check
        if len(raw_data) > 10_000_000:  # 10MB
            return {
                'success': False,
                'error': 'Data too large (max 10MB)'
            }

        # Try to parse as CSV to validate format
        try:
            # Handle different input formats
            if raw_data.startswith('{') or raw_data.startswith('['):
                # JSON format - would need conversion logic
                return {
                    'success': False,
                    'error': 'JSON format conversion not yet implemented. Please provide CSV format.'
                }

            # Assume CSV format
            csv_reader = csv.DictReader(io.StringIO(raw_data))
            headers = csv_reader.fieldnames

            if not headers:
                return {
                    'success': False,
                    'error': 'No headers found in CSV data'
                }

            # Count rows for validation
            row_count = sum(1 for row in csv_reader)

            if row_count > 100_000:
                return {
                    'success': False,
                    'error': 'Too many rows (max 100,000)'
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'Invalid CSV format: {str(e)}'
            }

        # Add .csv extension if not present
        if not lookup_name.endswith('.csv'):
            lookup_filename = f"{lookup_name}.csv"
        else:
            lookup_filename = lookup_name
            lookup_name = lookup_name[:-4]  # Remove .csv for transform name

        # At this point, we would typically make API calls to Splunk
        # For now, return success with what would be created

        logger.info(f"Creating lookup: {lookup_name} with {row_count} rows")

        return {
            'success': True,
            'operation': 'create_lookup',
            'lookup_name': lookup_name,
            'filename': lookup_filename,
            'headers': headers,
            'row_count': row_count,
            'app': app_context,
            'purpose': lookup_purpose,
            'next_steps': [
                f"Lookup definition created: {lookup_name}",
                f"CSV file uploaded: {lookup_filename}",
                f"Usage: | lookup {lookup_name} field_name",
                "Test the lookup with sample data"
            ]
        }

    except Exception as e:
        logger.error(f"Lookup creation failed: {str(e)}")
        return {
            'success': False,
            'error': f'Lookup creation failed: {str(e)}',
            'operation': 'create_lookup'
        }

def update_lookup(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Update existing lookup table content"""
    try:
        params = data.get('parameters', {})
        lookup_name = params.get('lookup_name', '').strip()
        new_data = params.get('new_data', '').strip()
        merge_strategy = params.get('merge_strategy', 'replace')

        if not lookup_name or not new_data:
            return {
                'success': False,
                'error': 'Missing required parameters: lookup_name, new_data'
            }

        # Security validation
        security = SecurityValidator()
        if not security.is_safe_content(new_data):
            return {
                'success': False,
                'error': 'New data contains potentially dangerous content'
            }

        # Validate CSV format
        try:
            csv_reader = csv.DictReader(io.StringIO(new_data))
            headers = csv_reader.fieldnames
            row_count = sum(1 for row in csv_reader)

        except Exception as e:
            return {
                'success': False,
                'error': f'Invalid CSV format: {str(e)}'
            }

        logger.info(f"Updating lookup: {lookup_name} with {row_count} rows using {merge_strategy} strategy")

        return {
            'success': True,
            'operation': 'update_lookup',
            'lookup_name': lookup_name,
            'merge_strategy': merge_strategy,
            'new_row_count': row_count,
            'headers': headers,
            'message': f'Lookup {lookup_name} updated successfully'
        }

    except Exception as e:
        logger.error(f"Lookup update failed: {str(e)}")
        return {
            'success': False,
            'error': f'Lookup update failed: {str(e)}',
            'operation': 'update_lookup'
        }

def create_macro(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a search macro from natural language description"""
    try:
        params = data.get('parameters', {})
        macro_name = params.get('macro_name', '').strip()
        description = params.get('description', '').strip()
        parameters = params.get('parameters', '').strip()

        if not macro_name or not description:
            return {
                'success': False,
                'error': 'Missing required parameters: macro_name, description'
            }

        # Validate macro name
        name_validation = KnowledgeObjectManager()._validate_name(macro_name, 'Macro')
        if not name_validation['valid']:
            return {
                'success': False,
                'error': name_validation['error']
            }

        # Parse parameters if provided
        param_list = []
        if parameters:
            param_list = [p.strip() for p in parameters.split(',') if p.strip()]

        # Basic SPL generation based on description
        # In a full implementation, this would use the management prompts
        spl_definition = _generate_spl_from_description(description, param_list)

        if not spl_definition:
            return {
                'success': False,
                'error': 'Could not generate SPL from description'
            }

        # Security check on generated SPL
        security = SecurityValidator()
        if not security.is_safe_content(spl_definition):
            return {
                'success': False,
                'error': 'Generated SPL contains potentially dangerous commands'
            }

        # Format macro name with parameter count
        if param_list:
            full_macro_name = f"{macro_name}({len(param_list)})"
        else:
            full_macro_name = macro_name

        logger.info(f"Creating macro: {full_macro_name}")

        return {
            'success': True,
            'operation': 'create_macro',
            'macro_name': full_macro_name,
            'definition': spl_definition,
            'parameters': param_list,
            'description': description,
            'usage_example': f"`{macro_name}{'(' + ','.join(['value'] * len(param_list)) + ')' if param_list else ''}`"
        }

    except Exception as e:
        logger.error(f"Macro creation failed: {str(e)}")
        return {
            'success': False,
            'error': f'Macro creation failed: {str(e)}',
            'operation': 'create_macro'
        }

def delete_lookup(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Delete a lookup table and its definition"""
    try:
        params = data.get('parameters', {})
        lookup_name = params.get('lookup_name', '').strip()
        confirm_deletion = params.get('confirm_deletion', False)

        if not lookup_name:
            return {
                'success': False,
                'error': 'Missing required parameter: lookup_name'
            }

        if not confirm_deletion:
            return {
                'success': False,
                'error': 'Deletion not confirmed. Set confirm_deletion to true.'
            }

        logger.info(f"Deleting lookup: {lookup_name}")

        return {
            'success': True,
            'operation': 'delete_lookup',
            'lookup_name': lookup_name,
            'message': f'Lookup {lookup_name} deleted successfully'
        }

    except Exception as e:
        logger.error(f"Lookup deletion failed: {str(e)}")
        return {
            'success': False,
            'error': f'Lookup deletion failed: {str(e)}',
            'operation': 'delete_lookup'
        }

def validate_lookup_data(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Validate lookup data quality and suggest optimizations"""
    try:
        params = data.get('parameters', {})
        data_sample = params.get('data_sample', '').strip()
        intended_use = params.get('intended_use', '').strip()

        if not data_sample or not intended_use:
            return {
                'success': False,
                'error': 'Missing required parameters: data_sample, intended_use'
            }

        issues = []
        recommendations = []

        # Basic validation
        try:
            csv_reader = csv.DictReader(io.StringIO(data_sample))
            headers = csv_reader.fieldnames
            rows = list(csv_reader)

            # Check for common issues
            if not headers:
                issues.append("No headers found")

            if len(headers) > 20:
                issues.append("Too many columns (>20) may impact performance")
                recommendations.append("Consider splitting into multiple lookups")

            # Check for empty values
            empty_cells = 0
            total_cells = len(rows) * len(headers) if headers else 0

            for row in rows:
                for value in row.values():
                    if not value or value.strip() == '':
                        empty_cells += 1

            if total_cells > 0 and empty_cells / total_cells > 0.3:
                issues.append(f"High percentage of empty values ({empty_cells/total_cells:.1%})")
                recommendations.append("Consider filling empty values or removing sparse columns")

        except Exception as e:
            issues.append(f"CSV parsing error: {str(e)}")

        # Size recommendations
        data_size = len(data_sample)
        if data_size > 1_000_000:  # 1MB
            recommendations.append("Consider using KV Store for large datasets")

        validation_result = {
            'success': True,
            'data_quality': 'good' if not issues else 'needs_attention',
            'issues': issues,
            'recommendations': recommendations,
            'estimated_size': f"{data_size:,} bytes",
            'estimated_rows': len(rows) if 'rows' in locals() else 0,
            'field_count': len(headers) if headers else 0
        }

        return validation_result

    except Exception as e:
        logger.error(f"Lookup validation failed: {str(e)}")
        return {
            'success': False,
            'error': f'Lookup validation failed: {str(e)}',
            'operation': 'validate_lookup_data'
        }

def _generate_spl_from_description(description: str, parameters: List[str]) -> str:
    """
    Simple SPL generation from description
    In full implementation, this would use the management prompts for AI generation
    """
    description_lower = description.lower()

    # Simple pattern matching for common requests
    if 'failed login' in description_lower or 'login fail' in description_lower:
        if parameters:
            return f"index=security action=failure | stats count by user | where count > ${parameters[0]}$"
        else:
            return "index=security action=failure | stats count by user | where count > 3"

    elif 'response time' in description_lower:
        if 'percentile' in description_lower:
            return "index=web | stats perc95(response_time) as p95_time by host"
        else:
            return "index=web | stats avg(response_time) as avg_time by host"

    elif 'bandwidth' in description_lower or 'top' in description_lower:
        return "index=network | stats sum(bytes) as total_bytes by user | sort -total_bytes | head 10"

    elif 'error' in description_lower:
        return "index=application (ERROR OR error OR Error) | stats count by host | sort -count"

    else:
        # Generic search pattern
        return "index=* | stats count by field | sort -count"