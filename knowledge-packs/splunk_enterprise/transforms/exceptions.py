"""
Custom exception hierarchy for Splunk MCP platform

Provides specific exception types to replace broad Exception catching,
enabling better error handling, debugging, and operational monitoring.
"""

class SplunkMCPException(Exception):
    """Base exception for Splunk MCP platform
    
    All platform-specific exceptions inherit from this base class,
    making it easy to catch all platform errors while still allowing
    specific error handling where needed.
    """
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ConfigurationError(SplunkMCPException):
    """Configuration file or validation errors
    
    Raised when:
    - Configuration files cannot be loaded (missing, malformed YAML, permissions)
    - Configuration validation fails (invalid structure, missing required fields)
    - Environment variable configuration issues
    """
    pass


class SecurityViolation(SplunkMCPException):
    """Guardrails security policy violations
    
    Raised when:
    - Blocked commands are detected in queries
    - Blocked patterns match in search strings
    - Bypass attempts are detected (Unicode normalization, eval injection, etc.)
    - User role restrictions are violated
    """
    
    def __init__(self, message: str, violation_type: str = None, query: str = None, user_role: str = None):
        details = {}
        if violation_type:
            details['violation_type'] = violation_type
        if query:
            details['blocked_query'] = query[:100]  # Truncate for logging
        if user_role:
            details['user_role'] = user_role
            
        super().__init__(message, details)


class SplunkAPIError(SplunkMCPException):
    """Splunk API communication errors
    
    Raised when:
    - HTTP connection failures to Splunk
    - Authentication failures
    - API response parsing errors
    - Splunk server errors (500, 503, etc.)
    """
    
    def __init__(self, message: str, status_code: int = None, response_body: str = None):
        details = {}
        if status_code:
            details['status_code'] = status_code
        if response_body:
            details['response_preview'] = response_body[:200]  # Truncate for logging
            
        super().__init__(message, details)


class DataTransformError(SplunkMCPException):
    """Data processing and transformation errors
    
    Raised when:
    - Data parsing fails (JSON, XML, CSV)
    - Field extraction fails
    - Data validation fails
    - Transform function execution errors
    """
    
    def __init__(self, message: str, transform_name: str = None, data_sample: str = None):
        details = {}
        if transform_name:
            details['transform'] = transform_name
        if data_sample:
            details['data_sample'] = str(data_sample)[:100]  # Truncate for logging
            
        super().__init__(message, details)


class PerformanceError(SplunkMCPException):
    """Performance limit violations
    
    Raised when:
    - Time range limits are exceeded
    - Result count limits are exceeded
    - Query timeout limits are exceeded
    - Memory or resource limits are hit
    """
    
    def __init__(self, message: str, limit_type: str = None, limit_value: str = None, actual_value: str = None):
        details = {}
        if limit_type:
            details['limit_type'] = limit_type
        if limit_value:
            details['limit_value'] = limit_value
        if actual_value:
            details['actual_value'] = actual_value
            
        super().__init__(message, details)


class DataMaskingError(SplunkMCPException):
    """Data masking and privacy protection errors
    
    Raised when:
    - Data masking rules fail to apply
    - Privacy policy violations are detected
    - Role-based masking configuration errors
    """
    pass


# Convenience functions for common error patterns
def raise_config_error(operation: str, file_path: str = None, original_error: Exception = None):
    """Helper to raise consistent configuration errors"""
    details = {}
    if file_path:
        details['file_path'] = file_path
    if original_error:
        details['original_error'] = str(original_error)
        details['error_type'] = type(original_error).__name__
    
    raise ConfigurationError(f"Configuration {operation} failed", details)


def raise_security_violation(violation_type: str, query: str, user_role: str = None, reason: str = None):
    """Helper to raise consistent security violations"""
    message = f"Security violation: {violation_type}"
    if reason:
        message += f" - {reason}"
    
    raise SecurityViolation(message, violation_type, query, user_role)


def raise_api_error(operation: str, status_code: int = None, response_body: str = None, original_error: Exception = None):
    """Helper to raise consistent API errors"""
    message = f"Splunk API {operation} failed"
    if original_error:
        message += f": {str(original_error)}"
    
    raise SplunkAPIError(message, status_code, response_body)