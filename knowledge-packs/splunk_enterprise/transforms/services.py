"""
Service Configuration and Factory Functions

Replaces global singletons with proper dependency injection.
Provides factory functions and service configuration for the platform.
"""

from typing import Optional, Dict, Any
import logging
from .container import get_container, ServiceContainer
from .guardrails import GuardrailsEngine
from .transforms.llm_context_manager import LLMContextManager

logger = logging.getLogger(__name__)


def configure_services(
    guardrails_config_path: Optional[str] = None,
    context_config_path: Optional[str] = None,
    container: Optional[ServiceContainer] = None
) -> None:
    """Configure all platform services with dependency injection
    
    Args:
        guardrails_config_path: Path to guardrails configuration file
        context_config_path: Path to LLM context configuration file  
        container: Service container to use (defaults to global container)
    """
    if container is None:
        container = get_container()
    
    logger.info("Configuring platform services with dependency injection")
    
    # Register GuardrailsEngine factory
    def create_guardrails_engine() -> GuardrailsEngine:
        logger.debug("Creating GuardrailsEngine instance")
        return GuardrailsEngine(config_path=guardrails_config_path)
    
    container.register_factory('guardrails_engine', create_guardrails_engine, singleton=True)
    
    # Register LLMContextManager factory
    def create_context_manager() -> LLMContextManager:
        logger.debug("Creating LLMContextManager instance")
        return LLMContextManager(config_path=context_config_path)
    
    container.register_factory('context_manager', create_context_manager, singleton=True)
    
    logger.info("Service configuration completed")


def get_guardrails_engine(container: Optional[ServiceContainer] = None) -> GuardrailsEngine:
    """Get guardrails engine via dependency injection
    
    Args:
        container: Service container to use (defaults to global container)
        
    Returns:
        GuardrailsEngine instance
        
    Raises:
        ConfigurationError: If guardrails engine is not configured
    """
    if container is None:
        container = get_container()
    
    return container.get('guardrails_engine')


def get_context_manager(container: Optional[ServiceContainer] = None) -> LLMContextManager:
    """Get LLM context manager via dependency injection
    
    Args:
        container: Service container to use (defaults to global container)
        
    Returns:
        LLMContextManager instance
        
    Raises:
        ConfigurationError: If context manager is not configured
    """
    if container is None:
        container = get_container()
        
    return container.get('context_manager')


def ensure_services_configured(
    guardrails_config_path: Optional[str] = None,
    context_config_path: Optional[str] = None,
    container: Optional[ServiceContainer] = None
) -> None:
    """Ensure services are configured, configure them if not
    
    Args:
        guardrails_config_path: Path to guardrails configuration file
        context_config_path: Path to LLM context configuration file
        container: Service container to use (defaults to global container)
    """
    if container is None:
        container = get_container()
    
    # Check if services are already configured
    if not container.is_registered('guardrails_engine') or not container.is_registered('context_manager'):
        logger.info("Services not configured, configuring now")
        configure_services(guardrails_config_path, context_config_path, container)
    else:
        logger.debug("Services already configured")


# Backwards compatibility functions with deprecation warnings
def get_guardrails_engine_legacy() -> GuardrailsEngine:
    """Legacy function for backwards compatibility
    
    DEPRECATED: Use get_guardrails_engine() instead
    """
    import warnings
    warnings.warn(
        "get_guardrails_engine_legacy() is deprecated, use get_guardrails_engine() instead",
        DeprecationWarning,
        stacklevel=2
    )
    
    ensure_services_configured()
    return get_guardrails_engine()


def get_context_manager_legacy() -> LLMContextManager:
    """Legacy function for backwards compatibility
    
    DEPRECATED: Use get_context_manager() instead  
    """
    import warnings
    warnings.warn(
        "get_context_manager_legacy() is deprecated, use get_context_manager() instead",
        DeprecationWarning,
        stacklevel=2
    )
    
    ensure_services_configured()
    return get_context_manager()


# Service health check
def check_service_health(container: Optional[ServiceContainer] = None) -> Dict[str, Any]:
    """Check health status of all configured services
    
    Args:
        container: Service container to use (defaults to global container)
        
    Returns:
        Dictionary with service health information
    """
    if container is None:
        container = get_container()
    
    health_status = {
        'services_registered': container.list_services(),
        'healthy_services': [],
        'unhealthy_services': [],
        'missing_services': []
    }
    
    # Check required services
    required_services = ['guardrails_engine', 'context_manager']
    
    for service_name in required_services:
        try:
            service = container.get_optional(service_name)
            if service is not None:
                # Try to call a simple method to verify health
                if hasattr(service, '__dict__'):  # Basic health check
                    health_status['healthy_services'].append(service_name)
                else:
                    health_status['unhealthy_services'].append(service_name)
            else:
                health_status['missing_services'].append(service_name)
        except Exception as e:
            health_status['unhealthy_services'].append({
                'service': service_name,
                'error': str(e)
            })
    
    health_status['overall_healthy'] = (
        len(health_status['unhealthy_services']) == 0 and
        len(health_status['missing_services']) == 0
    )
    
    return health_status