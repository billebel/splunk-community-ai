"""Universal adapters for different integration types."""

from .api_adapter import APIAdapter
from .database_adapter import DatabaseAdapter
from .queue_adapter import MessageQueueAdapter
from .file_adapter import FileSystemAdapter
from .ssh_adapter import SSHAdapter
from .adapter_factory import AdapterFactory

__all__ = [
    'APIAdapter',
    'DatabaseAdapter', 
    'MessageQueueAdapter',
    'FileSystemAdapter',
    'SSHAdapter',
    'AdapterFactory'
]