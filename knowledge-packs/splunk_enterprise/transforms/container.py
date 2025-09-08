"""
Dependency Injection Container

Thread-safe service container for managing dependencies and eliminating global singletons.
Supports both singleton instances and factory functions for better testability and modularity.
"""

from typing import Dict, Any, Optional, Callable, TypeVar, Type
import threading
import logging
from .exceptions import ConfigurationError

T = TypeVar('T')

logger = logging.getLogger(__name__)


class ServiceContainer:
    """Thread-safe dependency injection container"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, bool] = {}
        self._lock = threading.RLock()
        self._initialized = False
    
    def register_singleton(self, name: str, instance: Any) -> None:
        """Register a singleton instance
        
        Args:
            name: Service name identifier
            instance: Pre-created instance to register
        """
        with self._lock:
            self._services[name] = instance
            self._singletons[name] = True
            logger.debug(f"Registered singleton service: {name}")
    
    def register_factory(self, name: str, factory: Callable[[], T], singleton: bool = True) -> None:
        """Register a factory function
        
        Args:
            name: Service name identifier  
            factory: Factory function that creates the service instance
            singleton: If True, cache the first created instance
        """
        with self._lock:
            self._factories[name] = factory
            self._singletons[name] = singleton
            logger.debug(f"Registered {'singleton' if singleton else 'transient'} factory: {name}")
    
    def register_type(self, name: str, service_type: Type[T], *args, singleton: bool = True, **kwargs) -> None:
        """Register a service type with constructor arguments
        
        Args:
            name: Service name identifier
            service_type: Class type to instantiate
            *args: Constructor positional arguments
            singleton: If True, cache the first created instance  
            **kwargs: Constructor keyword arguments
        """
        factory = lambda: service_type(*args, **kwargs)
        self.register_factory(name, factory, singleton)
    
    def get(self, name: str) -> Any:
        """Get service instance
        
        Args:
            name: Service name identifier
            
        Returns:
            Service instance
            
        Raises:
            ConfigurationError: If service is not registered or creation fails
        """
        with self._lock:
            # Return existing singleton instance
            if name in self._services:
                return self._services[name]
            
            # Create from factory
            if name in self._factories:
                try:
                    instance = self._factories[name]()
                    
                    # Cache if singleton
                    if self._singletons.get(name, True):
                        self._services[name] = instance
                        
                    logger.debug(f"Created service instance: {name}")
                    return instance
                except Exception as e:
                    logger.error(f"Failed to create service '{name}': {e}")
                    raise ConfigurationError(f"Service creation failed: {name}", {'error': str(e)})
            
            raise ConfigurationError(f"Service '{name}' not registered")
    
    def get_optional(self, name: str) -> Optional[Any]:
        """Get service instance if registered, None otherwise
        
        Args:
            name: Service name identifier
            
        Returns:
            Service instance or None
        """
        try:
            return self.get(name)
        except ConfigurationError:
            return None
    
    def is_registered(self, name: str) -> bool:
        """Check if service is registered
        
        Args:
            name: Service name identifier
            
        Returns:
            True if service is registered
        """
        with self._lock:
            return name in self._services or name in self._factories
    
    def unregister(self, name: str) -> bool:
        """Unregister a service
        
        Args:
            name: Service name identifier
            
        Returns:
            True if service was registered and removed
        """
        with self._lock:
            removed = False
            if name in self._services:
                del self._services[name]
                removed = True
            if name in self._factories:
                del self._factories[name]
                removed = True  
            if name in self._singletons:
                del self._singletons[name]
            
            if removed:
                logger.debug(f"Unregistered service: {name}")
            return removed
    
    def clear(self) -> None:
        """Clear all registered services - useful for testing"""
        with self._lock:
            self._services.clear()
            self._factories.clear()
            self._singletons.clear()
            logger.debug("Cleared all registered services")
    
    def list_services(self) -> Dict[str, str]:
        """List all registered services and their types
        
        Returns:
            Dictionary mapping service names to their registration type
        """
        with self._lock:
            services = {}
            for name in self._services:
                services[name] = 'singleton_instance'
            for name in self._factories:
                if name not in services:  # Don't overwrite singleton instances
                    services[name] = 'singleton_factory' if self._singletons.get(name, True) else 'transient_factory'
            return services


# Global container instance (properly managed)
_container = ServiceContainer()


def get_container() -> ServiceContainer:
    """Get the global service container
    
    Returns:
        Global ServiceContainer instance
    """
    return _container


def reset_container() -> None:
    """Reset the global container - primarily for testing"""
    global _container
    _container.clear()
    logger.debug("Reset global service container")


# Context manager for testing
class ContainerContext:
    """Context manager for temporary container state during testing"""
    
    def __init__(self):
        self._original_services = {}
        self._original_factories = {}
        self._original_singletons = {}
    
    def __enter__(self) -> ServiceContainer:
        container = get_container()
        with container._lock:
            # Backup current state
            self._original_services = container._services.copy()
            self._original_factories = container._factories.copy()
            self._original_singletons = container._singletons.copy()
        return container
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        container = get_container()
        with container._lock:
            # Restore original state
            container._services = self._original_services
            container._factories = self._original_factories
            container._singletons = self._original_singletons


def with_container_context():
    """Decorator for test functions that need isolated container state"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with ContainerContext():
                return func(*args, **kwargs)
        return wrapper
    return decorator