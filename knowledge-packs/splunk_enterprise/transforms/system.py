"""
System Transform - Extract Splunk system and deployment information
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

def extract_server_info(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extract Splunk server configuration and status
    
    Args:
        data: Splunk /services/server/info response
        variables: Tool parameters
        
    Returns:
        Clean server configuration and status information
    """
    try:
        entry = data.get('entry', [{}])[0]
        content = entry.get('content', {})
        
        server_info = {
            'splunk_version': content.get('version', 'unknown'),
            'build_number': content.get('build', 'unknown'),
            'server_name': content.get('serverName', 'unknown'),
            'license_state': content.get('licenseState', 'unknown'),
            'server_roles': content.get('server_roles', []),
            'cluster_mode': content.get('cluster_mode', 'standalone'),
            'system_info': {
                'cpu_arch': content.get('cpu_arch', 'unknown'),
                'number_of_cores': _safe_int(content.get('numberOfCores', 0)),
                'os_name': content.get('os_name', 'unknown'),
                'os_version': content.get('os_version', 'unknown')
            },
            'memory_info': {
                'physical_memory_mb': _safe_int(content.get('physicalMemoryMB', 0)),
                'free_memory_mb': _safe_int(content.get('freeMemoryMB', 0))
            }
        }
        
        # Calculate memory usage if available
        total_mem = server_info['memory_info']['physical_memory_mb']
        free_mem = server_info['memory_info']['free_memory_mb']
        
        if total_mem > 0 and free_mem >= 0:
            used_mem = total_mem - free_mem
            memory_usage_pct = round((used_mem / total_mem) * 100, 1)
            server_info['memory_info']['memory_usage_percent'] = memory_usage_pct
            server_info['memory_info']['memory_status'] = (
                'high' if memory_usage_pct > 85 else
                'moderate' if memory_usage_pct > 70 else
                'normal'
            )
        
        # System health assessment
        health_indicators = []
        if server_info['license_state'].lower() != 'ok':
            health_indicators.append('license_issue')
        if server_info['memory_info'].get('memory_usage_percent', 0) > 85:
            health_indicators.append('high_memory_usage')
        
        return {
            'success': True,
            'server_info': server_info,
            'health_status': 'healthy' if not health_indicators else 'attention_needed',
            'health_indicators': health_indicators,
            'system_summary': f"Splunk {server_info['splunk_version']} on {server_info['server_name']} "
                            f"({server_info['system_info']['number_of_cores']} cores, "
                            f"{server_info['memory_info']['physical_memory_mb']}MB RAM)"
        }
        
    except Exception as e:
        logger.error(f"Server info extraction failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'server_info': {}
        }

def extract_apps(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extract installed Splunk applications
    
    Args:
        data: Splunk /services/apps/local response
        variables: Tool parameters
        
    Returns:
        List of installed Splunk applications
    """
    try:
        entries = data.get('entry', [])
        apps = []
        
        for entry in entries:
            if not isinstance(entry, dict):
                continue
                
            content = entry.get('content', {})
            
            app_info = {
                'name': entry.get('name', 'unknown'),
                'label': content.get('label', entry.get('name', 'unknown')),
                'version': content.get('version', 'unknown'),
                'author': content.get('author', 'unknown'),
                'description': content.get('description', '')[:200] + '...' if len(content.get('description', '')) > 200 else content.get('description', ''),
                'disabled': content.get('disabled', False),
                'visible': content.get('visible', True),
                'configured': content.get('configured', False)
            }
            
            apps.append(app_info)
        
        # Sort by visibility and name
        apps.sort(key=lambda x: (x['disabled'], not x['visible'], x['name']))
        
        return {
            'success': True,
            'apps': apps,
            'count': len(apps),
            'summary': {
                'total_apps': len(apps),
                'enabled_apps': [app['name'] for app in apps if not app['disabled']],
                'disabled_apps': [app['name'] for app in apps if app['disabled']],
                'visible_apps': [app['name'] for app in apps if app['visible'] and not app['disabled']]
            },
            'key_apps': {
                'security_apps': [app['name'] for app in apps if any(term in app['name'].lower() for term in ['security', 'enterprise_security', 'es', 'fraud'])],
                'it_ops_apps': [app['name'] for app in apps if any(term in app['name'].lower() for term in ['itsi', 'monitoring', 'infrastructure', 'unix', 'windows'])],
                'data_apps': [app['name'] for app in apps if any(term in app['name'].lower() for term in ['db_connect', 'hadoop', 'aws', 'cloud'])]
            }
        }
        
    except Exception as e:
        logger.error(f"Apps extraction failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'apps': [],
            'count': 0
        }

def extract_user_info(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extract current user context and permissions
    
    Args:
        data: Splunk /services/authentication/current-context response
        variables: Tool parameters
        
    Returns:
        Current user role and permission information
    """
    try:
        entry = data.get('entry', [{}])[0]
        content = entry.get('content', {})
        
        user_info = {
            'username': content.get('username', 'unknown'),
            'real_name': content.get('realname', ''),
            'email': content.get('email', ''),
            'roles': content.get('roles', []),
            'default_app': content.get('defaultApp', 'search'),
            'timezone': content.get('tz', 'UTC')
        }
        
        # Determine user experience level and capabilities based on roles
        roles = user_info.get('roles', [])
        user_capabilities = {
            'is_admin': 'admin' in roles,
            'is_power_user': 'power' in roles or 'sc_admin' in roles,
            'can_search_all_indexes': 'admin' in roles or 'power' in roles,
            'can_create_knowledge_objects': 'power' in roles or 'admin' in roles,
            'can_install_apps': 'admin' in roles,
            'can_manage_users': 'admin' in roles
        }
        
        # Determine appropriate explanation depth
        if user_capabilities['is_admin']:
            user_type = 'administrator'
            explanation_depth = 'concise'
        elif user_capabilities['is_power_user']:
            user_type = 'power_user'
            explanation_depth = 'balanced'
        else:
            user_type = 'standard_user'
            explanation_depth = 'detailed'
        
        return {
            'success': True,
            'user_info': user_info,
            'user_type': user_type,
            'capabilities': user_capabilities,
            'recommended_explanation_depth': explanation_depth,
            'role_summary': f"{user_info['username']} ({user_type}) with roles: {', '.join(roles)}"
        }
        
    except Exception as e:
        logger.error(f"User info extraction failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'user_info': {},
            'fallback_user_type': 'standard_user',
            'fallback_explanation_depth': 'balanced'
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