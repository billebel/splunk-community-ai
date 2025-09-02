"""Factory for creating and managing different adapter types."""

import logging
from typing import Dict, Any, Union, List
from ..models import Pack, ConnectionConfig

from .api_adapter import APIAdapter
from .database_adapter import DatabaseAdapter
from .queue_adapter import MessageQueueAdapter
from .file_adapter import FileSystemAdapter
from .ssh_adapter import SSHAdapter

logger = logging.getLogger(__name__)


class AdapterFactory:
    """Factory for creating the appropriate adapter based on connection type."""
    
    @staticmethod
    def create_adapter(pack: Pack) -> Union[APIAdapter, DatabaseAdapter, MessageQueueAdapter, FileSystemAdapter, SSHAdapter]:
        """Create appropriate adapter based on pack connection type.
        
        Args:
            pack: Knowledge pack configuration
            
        Returns:
            Appropriate adapter instance
            
        Raises:
            ValueError: If connection type is not supported
        """
        connection_type = pack.connection.type.lower()
        
        if connection_type == 'rest' or connection_type == 'api':
            return APIAdapter(pack)
        elif connection_type == 'database':
            return DatabaseAdapter(pack)
        elif connection_type == 'message_queue' or connection_type == 'queue':
            return MessageQueueAdapter(pack)
        elif connection_type == 'filesystem' or connection_type == 'storage':
            return FileSystemAdapter(pack)
        elif connection_type == 'ssh' or connection_type == 'shell':
            return SSHAdapter(pack)
        else:
            raise ValueError(f"Unsupported connection type: {connection_type}")
    
    @staticmethod
    def get_supported_types() -> Dict[str, str]:
        """Get dictionary of supported connection types and their descriptions.
        
        Returns:
            Dictionary mapping connection type to description
        """
        return {
            'rest': 'REST API integration with HTTP/HTTPS endpoints',
            'database': 'Database integration (PostgreSQL, MySQL, MongoDB, Redis, etc.)',
            'message_queue': 'Message queue integration (RabbitMQ, Redis Pub/Sub, Kafka, etc.)',
            'filesystem': 'File system integration (Local, S3, GCS, Azure, FTP, etc.)',
            'ssh': 'SSH and shell command execution (Remote and local)'
        }
    
    @staticmethod
    def validate_pack_configuration(pack: Pack) -> List[str]:
        """Validate pack configuration for the specified connection type.
        
        Args:
            pack: Knowledge pack configuration
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        connection_type = pack.connection.type.lower()
        
        # Common validations
        if not pack.connection.type:
            errors.append("Connection type must be specified")
            return errors
        
        # Type-specific validations
        if connection_type == 'rest' or connection_type == 'api':
            if not pack.connection.base_url:
                errors.append("base_url is required for REST API connections")
        
        elif connection_type == 'database':
            if not pack.connection.engine:
                errors.append("Database engine must be specified")
            
            if pack.connection.engine.lower() not in ['sqlite', 'duckdb']:
                if not pack.connection.host:
                    errors.append("Database host must be specified for most engines")
                if not pack.connection.database:
                    errors.append("Database name must be specified")
        
        elif connection_type == 'message_queue' or connection_type == 'queue':
            if not pack.connection.engine:
                errors.append("Queue engine must be specified (rabbitmq, redis, kafka, etc.)")
            if not pack.connection.host:
                errors.append("Queue host must be specified")
        
        elif connection_type == 'filesystem' or connection_type == 'storage':
            if not pack.connection.engine:
                errors.append("Storage engine must be specified (local, s3, gcs, azure, ftp)")
            
            if pack.connection.engine.lower() == 'local':
                if not pack.connection.root_path:
                    errors.append("root_path is required for local file system")
            elif pack.connection.engine.lower() == 's3':
                if not pack.connection.bucket:
                    errors.append("bucket is required for S3 storage")
        
        elif connection_type == 'ssh' or connection_type == 'shell':
            if not pack.connection.engine:
                errors.append("Shell engine must be specified (ssh, local)")
            
            if pack.connection.engine.lower() == 'ssh':
                if not pack.connection.hostname:
                    errors.append("hostname is required for SSH connections")
                if not pack.connection.username:
                    errors.append("username is required for SSH connections")
        
        # Validate authentication configuration
        if pack.connection.auth:
            auth_errors = AdapterFactory._validate_auth_config(pack.connection.auth, connection_type)
            errors.extend(auth_errors)
        
        return errors
    
    @staticmethod
    def _validate_auth_config(auth_config, connection_type: str) -> List[str]:
        """Validate authentication configuration.
        
        Args:
            auth_config: Authentication configuration
            connection_type: Type of connection
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if not auth_config.method:
            errors.append("Authentication method must be specified")
            return errors
        
        method = auth_config.method
        config = auth_config.config or {}
        
        # Method-specific validations
        if method.value == 'basic':
            if connection_type in ['database', 'ssh']:
                if not config.get('username'):
                    errors.append("username is required for basic authentication")
                if not config.get('password'):
                    errors.append("password is required for basic authentication")
        
        elif method.value == 'api_key':
            if not config.get('key'):
                errors.append("key is required for API key authentication")
        
        elif method.value == 'bearer':
            if not config.get('token'):
                errors.append("token is required for bearer authentication")
        
        elif method.value == 'ssh_key':
            if connection_type == 'ssh':
                if not config.get('private_key_file'):
                    errors.append("private_key_file is required for SSH key authentication")
        
        elif method.value == 'oauth2':
            if not config.get('client_id'):
                errors.append("client_id is required for OAuth2 authentication")
            if not config.get('client_secret'):
                errors.append("client_secret is required for OAuth2 authentication")
        
        return errors
    
    @staticmethod
    def get_required_dependencies(connection_type: str) -> Dict[str, str]:
        """Get required Python dependencies for a connection type.
        
        Args:
            connection_type: Type of connection
            
        Returns:
            Dictionary mapping dependency name to pip install command
        """
        dependencies = {
            'rest': {},  # httpx is already included in base requirements
            'database': {
                'postgresql': 'pip install asyncpg',
                'mysql': 'pip install aiomysql',
                'sqlite': 'pip install aiosqlite',
                'mongodb': 'pip install motor',
                'redis': 'pip install redis',
                'elasticsearch': 'pip install elasticsearch'
            },
            'message_queue': {
                'rabbitmq': 'pip install aio-pika',
                'redis': 'pip install redis',
                'kafka': 'pip install aiokafka',
                'aws_sqs': 'pip install aioboto3'
            },
            'filesystem': {
                's3': 'pip install aioboto3',
                'gcs': 'pip install google-cloud-storage',
                'azure': 'pip install azure-storage-blob',
                'ftp': 'pip install aioftp',
                'sftp': 'pip install asyncssh'
            },
            'ssh': {
                'ssh': 'pip install asyncssh'
            }
        }
        
        return dependencies.get(connection_type, {})