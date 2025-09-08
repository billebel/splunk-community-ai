"""
Guardrails Engine - Comprehensive safety, security, and privacy controls
"""

import re
import yaml
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import hashlib
import unicodedata
import urllib.parse

try:
    from .exceptions import (
        ConfigurationError, SecurityViolation, DataMaskingError,
        raise_config_error, raise_security_violation
    )
except ImportError:
    # Handle case when imported directly (not as package)
    try:
        from exceptions import (
            ConfigurationError, SecurityViolation, DataMaskingError,
            raise_config_error, raise_security_violation
        )
    except ImportError:
        # Fallback to built-in exceptions if custom ones aren't available
        class ConfigurationError(Exception):
            pass
        class SecurityViolation(Exception):
            pass
        class DataMaskingError(Exception):
            pass
        def raise_config_error(op, path=None, err=None):
            raise ConfigurationError(f"Config {op} failed")
        def raise_security_violation(vtype, query, role=None, reason=None):
            raise SecurityViolation(f"Security violation: {vtype}")

logger = logging.getLogger(__name__)

class GuardrailsEngine:
    """Main guardrails enforcement engine"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._find_config_path()
        self.config = self._load_config()
        self.audit_log = []
        
    def _find_config_path(self) -> str:
        """Find guardrails.yaml config file"""
        # Look in current directory and parent directories
        current_dir = os.path.dirname(__file__)
        for _ in range(3):  # Look up 3 levels
            config_file = os.path.join(current_dir, 'guardrails.yaml')
            if os.path.exists(config_file):
                return config_file
            current_dir = os.path.dirname(current_dir)
        
        # Fallback to strict defaults if no config found
        logger.warning("No guardrails.yaml found, using fail-safe defaults")
        return None
    
    def _load_config(self) -> Dict[str, Any]:
        """Load guardrails configuration with fail-safe defaults"""
        if not self.config_path or not os.path.exists(self.config_path):
            return self._get_fail_safe_config()
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            # Validate config structure
            if not self._validate_config(config):
                logger.error("Invalid guardrails config, using fail-safe defaults")
                return self._get_fail_safe_config()
                
            return config
            
        except FileNotFoundError:
            logger.warning(f"Guardrails config file not found: {self.config_path}")
            return self._get_fail_safe_config()
        except PermissionError:
            logger.error(f"Permission denied reading guardrails config: {self.config_path}")
            raise_config_error("load", self.config_path, PermissionError("Permission denied"))
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in guardrails config: {e}")
            raise_config_error("parse", self.config_path, e)
        except OSError as e:
            logger.error(f"IO error reading guardrails config: {e}")
            return self._get_fail_safe_config()
    
    def _get_fail_safe_config(self) -> Dict[str, Any]:
        """Load externalized ultra-restrictive fail-safe configuration"""
        fail_safe_path = os.path.join(
            os.path.dirname(__file__), '..', 'config', 'fail_safe_defaults.yaml'
        )
        
        try:
            with open(fail_safe_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.critical("FAIL-SAFE MODE ACTIVE: Using emergency security defaults from external config")
            return config
        except FileNotFoundError:
            logger.critical(f"Fail-safe config file missing: {fail_safe_path}")
            return self._get_minimal_hardcoded_config()
        except yaml.YAMLError as e:
            logger.critical(f"Fail-safe config YAML error: {e}")
            return self._get_minimal_hardcoded_config()
        except Exception as e:
            logger.critical(f"Fail-safe config load failed: {e}")
            return self._get_minimal_hardcoded_config()
    
    def _get_minimal_hardcoded_config(self) -> Dict[str, Any]:
        """Absolute minimal hardcoded config when even fail-safe file fails"""
        logger.critical("EMERGENCY LOCKDOWN: Using minimal hardcoded defaults - ALL QUERIES BLOCKED")
        return {
            'guardrails': {'enabled': True, 'fail_safe_mode': True, 'emergency_lockdown': True},
            'security': {
                'blocked_commands': ['*'],  # Block everything
                'blocked_patterns': [{'pattern': '.*', 'reason': 'Emergency lockdown mode'}]
            },
            'performance': {
                'time_limits': {'max_time_range_days': 0},
                'result_limits': {'max_results_per_search': 0},
                'execution_limits': {'search_timeout_seconds': 1}
            },
            'privacy': {
                'data_masking': {'enabled': True, 'mask_all': True},
                'sensitive_fields': ['*']  # Mask everything
            },
            'emergency': {
                'message': 'System in emergency lockdown. Contact administrator immediately.',
                'contact_required': True
            }
        }
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate guardrails configuration structure"""
        required_sections = ['security', 'performance', 'privacy']
        return all(section in config for section in required_sections)
    
    def validate_search(self, search_query: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive search validation before execution
        
        Args:
            search_query: SPL search query to validate
            user_context: User role and context information
            
        Returns:
            Validation result with allowed/blocked status and modifications
        """
        try:
            user_role = self._determine_user_role(user_context.get('roles', []))
            role_limits = self._get_role_limits(user_role)
            
            validation_result = {
                'allowed': True,
                'blocked': False,
                'warnings': [],
                'violations': [],
                'modifications_applied': [],
                'original_query': search_query,
                'modified_query': search_query,
                'user_role': user_role,
                'enforcement_level': 'none'
            }
            
            # 1. Security validation - Check for dangerous commands and patterns
            security_result = self._validate_security(search_query, role_limits)
            if security_result['blocked']:
                validation_result.update({
                    'allowed': False,
                    'blocked': True,
                    'violations': security_result['violations'],
                    'enforcement_level': 'blocked',
                    'block_reason': 'Security violation'
                })
                self._audit_log('security_block', user_context, search_query, security_result)
                return validation_result
            
            validation_result['warnings'].extend(security_result['warnings'])
            
            # 2. Performance validation - Time ranges, result limits, etc.
            performance_result = self._validate_performance(search_query, role_limits)
            if performance_result['modifications']:
                validation_result['modified_query'] = performance_result['modified_query']
                validation_result['modifications_applied'].extend(performance_result['modifications'])
                validation_result['enforcement_level'] = 'modified'
            
            validation_result['warnings'].extend(performance_result['warnings'])
            
            # 3. Add guardrails metadata to query
            validation_result['execution_metadata'] = {
                'max_results': role_limits.get('max_results_per_search', 1000),
                'timeout_seconds': role_limits.get('search_timeout_seconds', 300),
                'data_masking_enabled': role_limits.get('data_masking_enabled', True)
            }
            
            # Log validation result
            if validation_result['warnings'] or validation_result['modifications_applied']:
                self._audit_log('validation_warning', user_context, search_query, validation_result)
            
            return validation_result
            
        except (ConfigurationError, SecurityViolation) as e:
            # Re-raise our own exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error during search validation: {str(e)}")
            # Fail-safe: Block the search if validation fails unexpectedly
            return {
                'allowed': False,
                'blocked': True,
                'violations': [f"System error during validation: {type(e).__name__}"],
                'enforcement_level': 'blocked',
                'block_reason': 'System error'
            }
    
    def _normalize_query(self, search_query: str) -> str:
        """
        Normalize search query to prevent bypass techniques
        Addresses Unicode, encoding, and whitespace manipulation
        """
        try:
            # 1. Unicode normalization - convert to canonical form
            normalized = unicodedata.normalize('NFKD', search_query)
            
            # 2. Handle confusable characters (Cyrillic/Latin lookalikes)
            normalized = self._replace_confusable_characters(normalized)
            
            # 3. URL decode any encoded characters
            normalized = urllib.parse.unquote(normalized)
            normalized = urllib.parse.unquote_plus(normalized)  # Handle + as space
            
            # 4. Normalize whitespace - convert all whitespace to single spaces
            normalized = ' '.join(normalized.split())
            
            # 5. Convert to lowercase for consistent comparison
            normalized = normalized.lower()
            
            return normalized
            
        except Exception as e:
            logger.warning(f"Query normalization failed: {e}, using original query")
            return search_query.lower()
    
    def _replace_confusable_characters(self, text: str) -> str:
        """
        Replace visually similar characters that could be used for bypasses
        Handles common Cyrillic/Latin, Greek/Latin confusables
        """
        # Common confusable character mappings (Cyrillic -> Latin)
        confusable_map = {
            'а': 'a', 'А': 'A',  # Cyrillic a
            'е': 'e', 'Е': 'E',  # Cyrillic e  
            'о': 'o', 'О': 'O',  # Cyrillic o
            'р': 'p', 'Р': 'P',  # Cyrillic p
            'с': 'c', 'С': 'C',  # Cyrillic c
            'х': 'x', 'Х': 'X',  # Cyrillic x
            'у': 'y', 'У': 'Y',  # Cyrillic y
            'і': 'i', 'І': 'I',  # Cyrillic i
            'ѕ': 's', 'Ѕ': 'S',  # Cyrillic s
            
            # Greek confusables
            'α': 'a', 'Α': 'A',  # Greek alpha
            'ο': 'o', 'Ο': 'O',  # Greek omicron
            'ρ': 'p', 'Ρ': 'P',  # Greek rho
            
            # Additional Unicode tricks
            '\u2010': '-',  # Hyphen
            '\u2011': '-',  # Non-breaking hyphen
            '\u2012': '-',  # Figure dash
            '\u2013': '-',  # En dash
            '\u2014': '-',  # Em dash
        }
        
        # Replace confusable characters
        for confusable, replacement in confusable_map.items():
            text = text.replace(confusable, replacement)
            
        return text
    
    def _validate_security(self, search_query: str, role_limits: Dict[str, Any]) -> Dict[str, Any]:
        """Validate search for security violations with bypass protection"""
        result = {'blocked': False, 'violations': [], 'warnings': []}
        
        # Normalize query to prevent bypass techniques
        normalized_query = self._normalize_query(search_query)
        security_config = self.config.get('security', {})
        
        # Check for blocked commands with improved detection (unless user has bypass)
        if not role_limits.get('bypass_command_blocks', False):
            for blocked_cmd in security_config.get('blocked_commands', []):
                # Remove pipe symbol and normalize for comparison
                cmd_normalized = blocked_cmd.replace('|', '').strip().lower()
                
                # Multiple detection methods to prevent bypass
                # 1. Simple substring check
                if f"|{cmd_normalized}" in normalized_query or f"| {cmd_normalized}" in normalized_query:
                    result['blocked'] = True
                    result['violations'].append(f"Blocked command detected: {blocked_cmd}")
                    continue
                
                # 2. Regex pattern for robust detection
                cmd_pattern = rf'\|\s*{re.escape(cmd_normalized)}\b'
                if re.search(cmd_pattern, normalized_query, re.IGNORECASE):
                    result['blocked'] = True
                    result['violations'].append(f"Blocked command detected: {blocked_cmd}")
                    continue
                
                # 3. Check for dynamic construction patterns
                if self._detect_dynamic_construction(cmd_normalized, normalized_query):
                    result['blocked'] = True
                    result['violations'].append(f"Dynamic construction of blocked command detected: {blocked_cmd}")
        
        # Check for blocked patterns with normalized input
        for pattern in security_config.get('blocked_patterns', []):
            # Test pattern against both original and normalized query
            if re.search(pattern, search_query, re.IGNORECASE | re.MULTILINE) or \
               re.search(pattern, normalized_query, re.IGNORECASE | re.MULTILINE):
                result['blocked'] = True
                result['violations'].append(f"Blocked pattern detected: {pattern}")
        
        # Check for warning patterns
        for pattern in security_config.get('warning_patterns', []):
            if re.search(pattern, search_query, re.IGNORECASE | re.MULTILINE) or \
               re.search(pattern, normalized_query, re.IGNORECASE | re.MULTILINE):
                result['warnings'].append(f"Performance warning pattern: {pattern}")
        
        return result
    
    def _detect_dynamic_construction(self, command: str, normalized_query: str) -> bool:
        """
        Detect dynamic construction of blocked commands
        Looks for patterns like: eval cmd="del" + "ete" | run $cmd$
        """
        try:
            # Only check for very specific dynamic construction patterns
            # that are likely to be malicious
            
            # 1. String concatenation (+ operator)
            if '+' in normalized_query and 'eval' in normalized_query:
                # Look for patterns like: eval cmd="del" + "ete"
                concat_patterns = [
                    r'eval.*["\'][^"\']*["\']\s*\+\s*["\'][^"\']*["\']',  # String concatenation in eval
                    r'eval.*\+.*["\']\s*\|\s*run',  # Concatenation followed by run
                ]
                
                for pattern in concat_patterns:
                    if re.search(pattern, normalized_query, re.IGNORECASE):
                        return True
            
            # 2. Variable substitution ($ symbols)
            if re.search(r'\$\w+\$', normalized_query):
                return True
            
            # 3. Check if the command parts actually appear in suspicious contexts
            # Only check for partial matches if there are other suspicious indicators
            command_clean = command.replace('|', '').strip()
            if len(command_clean) >= 4:  # Only check meaningful commands
                # Look for partial command strings in suspicious contexts
                for i in range(2, len(command_clean)):
                    part = command_clean[:i]
                    # Only flag if the partial appears in eval AND there's concatenation
                    if (len(part) >= 3 and part in normalized_query and 
                        'eval' in normalized_query and 
                        ('+' in normalized_query or '$' in normalized_query)):
                        try:
                            part_pattern = rf'["\'][^"\']*{re.escape(part)}[^"\']*["\'].*\+.*["\']'
                            if re.search(part_pattern, normalized_query, re.IGNORECASE):
                                return True
                        except Exception:
                            continue  # Skip this part if regex fails
            
            return False
            
        except Exception as e:
            logger.warning(f"Dynamic construction detection failed: {e}")
            return False
    
    def _validate_performance(self, search_query: str, role_limits: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and modify search for performance constraints"""
        result = {
            'modifications': [],
            'warnings': [],
            'modified_query': search_query
        }
        
        modified_query = search_query
        
        # 1. Time range validation and enforcement
        time_result = self._enforce_time_limits(modified_query, role_limits)
        if time_result['modified']:
            modified_query = time_result['modified_query']
            result['modifications'].extend(time_result['modifications'])
        result['warnings'].extend(time_result['warnings'])
        
        # 2. Result limit enforcement
        limit_result = self._enforce_result_limits(modified_query, role_limits)
        if limit_result['modified']:
            modified_query = limit_result['modified_query']
            result['modifications'].extend(limit_result['modifications'])
        
        result['modified_query'] = modified_query
        return result
    
    def _enforce_time_limits(self, search_query: str, role_limits: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce time range limitations"""
        result = {'modified': False, 'modified_query': search_query, 'modifications': [], 'warnings': []}
        
        max_days = role_limits.get('max_time_range_days', 7)
        
        # Extract time range from query
        earliest_match = re.search(r'earliest\s*=\s*([^\s]+)', search_query, re.IGNORECASE)
        
        if earliest_match:
            earliest_value = earliest_match.group(1).strip('"\'')
            
            # Parse time range and check if it exceeds limits
            if self._time_range_exceeds_limit(earliest_value, max_days):
                # Replace with maximum allowed range
                max_range = f"-{max_days}d"
                modified_query = re.sub(
                    r'earliest\s*=\s*[^\s]+', 
                    f'earliest={max_range}', 
                    search_query, 
                    flags=re.IGNORECASE
                )
                result.update({
                    'modified': True,
                    'modified_query': modified_query,
                    'modifications': [f'Time range limited to maximum {max_days} days']
                })
        else:
            # No time range specified, add default safe range
            default_range = self.config.get('performance', {}).get('time_limits', {}).get('default_time_range', '-1h')
            modified_query = f'{search_query} earliest={default_range}'
            result.update({
                'modified': True,
                'modified_query': modified_query,
                'modifications': [f'Added default time range: {default_range}']
            })
        
        return result
    
    def _enforce_result_limits(self, search_query: str, role_limits: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce result count limitations"""
        result = {'modified': False, 'modified_query': search_query, 'modifications': []}
        
        max_results = role_limits.get('max_results_per_search', 1000)
        
        # Check if query already has a head/tail command
        if not re.search(r'\|\s*(head|tail)\s+\d+', search_query, re.IGNORECASE):
            # Add head command to limit results
            modified_query = f'{search_query} | head {max_results}'
            result.update({
                'modified': True,
                'modified_query': modified_query,
                'modifications': [f'Added result limit: {max_results} events']
            })
        
        return result
    
    def _time_range_exceeds_limit(self, time_value: str, max_days: int) -> bool:
        """Check if time range exceeds allowed limits"""
        try:
            # Parse common time formats
            if time_value == '0' or time_value == '@0':
                return True  # All-time search
            
            # Extract number and unit from formats like "-30d", "-24h", etc.
            match = re.match(r'-(\d+)([smhd])', time_value.lower())
            if match:
                number, unit = int(match.group(1)), match.group(2)
                
                # Convert to days
                if unit == 's':
                    days = number / (60 * 60 * 24)
                elif unit == 'm':
                    days = number / (60 * 24)
                elif unit == 'h':
                    days = number / 24
                elif unit == 'd':
                    days = number
                else:
                    return False  # Unknown unit, allow it
                
                return days > max_days
            
            return False  # Couldn't parse, assume it's safe
            
        except Exception:
            return False  # Error parsing, assume it's safe
    
    def apply_data_masking(self, results: List[Dict[str, Any]], user_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply data masking to search results"""
        try:
            user_role = self._determine_user_role(user_context.get('roles', []))
            role_limits = self._get_role_limits(user_role)
            
            # Check if masking is enabled for this user role
            if not role_limits.get('data_masking_enabled', True):
                return results
            
            privacy_config = self.config.get('privacy', {})
            masking_config = privacy_config.get('data_masking', {})
            
            if not masking_config.get('enabled', True):
                return results
            
            sensitive_fields = privacy_config.get('sensitive_fields', [])
            masking_patterns = privacy_config.get('masking_patterns', {})
            filtered_fields = privacy_config.get('filtered_fields', [])
            
            masked_results = []
            masking_applied = False
            
            for event in results:
                masked_event = {}
                
                for field, value in event.items():
                    # Remove filtered fields completely
                    if field.lower() in [f.lower() for f in filtered_fields]:
                        continue
                    
                    # Check if field is sensitive
                    if self._is_sensitive_field(field, sensitive_fields):
                        masked_event[field] = self._mask_value(value, field, masking_patterns)
                        masking_applied = True
                    else:
                        masked_event[field] = value
                
                masked_results.append(masked_event)
            
            if masking_applied:
                self._audit_log('data_masking', user_context, f"Masked {len(results)} events", {})
            
            return masked_results
            
        except Exception as e:
            logger.error(f"Data masking failed: {str(e)}")
            # Fail-safe: Return empty results if masking fails
            return []
    
    def _is_sensitive_field(self, field_name: str, sensitive_fields: List[str]) -> bool:
        """Check if a field name matches sensitive field patterns"""
        field_lower = field_name.lower()
        
        for sensitive_pattern in sensitive_fields:
            if sensitive_pattern.lower() in field_lower:
                return True
            
        # Additional pattern-based detection
        if re.search(r'(pass|pwd|secret|token|key|ssn|credit|card)', field_lower):
            return True
            
        return False
    
    def _mask_value(self, value: str, field_name: str, masking_patterns: Dict[str, str]) -> str:
        """Apply appropriate masking pattern to a value"""
        if not isinstance(value, str):
            value = str(value)
        
        field_lower = field_name.lower()
        
        # Apply specific patterns based on field type
        if 'email' in field_lower:
            return masking_patterns.get('email', '****@****.***')
        elif any(term in field_lower for term in ['phone', 'mobile']):
            return masking_patterns.get('phone', '***-***-****')
        elif any(term in field_lower for term in ['ssn', 'social']):
            return masking_patterns.get('ssn', '***-**-****')
        elif any(term in field_lower for term in ['credit', 'card']):
            return masking_patterns.get('credit_card', '****-****-****-****')
        elif 'ip' in field_lower:
            return masking_patterns.get('ip_address', 'xxx.xxx.xxx.xxx')
        else:
            return masking_patterns.get('default', '[MASKED]')
    
    def _determine_user_role(self, user_roles: List[str]) -> str:
        """Determine the most appropriate user role from a list"""
        if not user_roles:
            return 'readonly_user'
        
        # Priority order (most permissive first)
        role_priority = ['admin', 'power_user', 'power', 'standard_user', 'user']
        
        for role in role_priority:
            if role in user_roles:
                return role
        
        # Default to most restrictive
        return 'readonly_user'
    
    def _get_role_limits(self, user_role: str) -> Dict[str, Any]:
        """Get role-specific limits and permissions"""
        user_roles_config = self.config.get('user_roles', {})
        
        # Map common role names to our config structure
        role_mapping = {
            'power': 'power_user',
            'user': 'standard_user'
        }
        
        mapped_role = role_mapping.get(user_role, user_role)
        role_config = user_roles_config.get(mapped_role)
        
        if not role_config:
            # Fallback to most restrictive role
            role_config = user_roles_config.get('readonly_user', {
                'max_time_range_days': 1,
                'max_results_per_search': 100,
                'search_timeout_seconds': 60,
                'data_masking_enabled': True
            })
        
        return role_config
    
    def _audit_log(self, action: str, user_context: Dict[str, Any], search_query: str, details: Dict[str, Any]):
        """Log guardrails actions for audit purposes"""
        try:
            audit_entry = {
                'timestamp': datetime.now().isoformat(),
                'action': action,
                'user': user_context.get('username', 'unknown'),
                'user_roles': user_context.get('roles', []),
                'search_query_hash': hashlib.sha256(search_query.encode()).hexdigest()[:16],  # Hash for privacy
                'search_length': len(search_query),
                'details': details,
                'config_version': self.config.get('guardrails', {}).get('version', 'unknown')
            }
            
            self.audit_log.append(audit_entry)
            
            # Also log to standard logger
            logger.info(f"Guardrails {action}: user={audit_entry['user']}, "
                       f"hash={audit_entry['search_query_hash']}")
            
        except Exception as e:
            logger.error(f"Audit logging failed: {str(e)}")

# DEPRECATED: Global instance replaced with dependency injection
# Import services module for backwards compatibility

def get_guardrails_engine() -> GuardrailsEngine:
    """Get guardrails engine instance via dependency injection
    
    DEPRECATED: This function is maintained for backwards compatibility.
    New code should use services.get_guardrails_engine() instead.
    """
    # Import here to avoid circular imports
    from .services import ensure_services_configured, get_guardrails_engine as get_service
    
    ensure_services_configured()
    return get_service()