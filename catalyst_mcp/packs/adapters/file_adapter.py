"""File system adapter for local and cloud storage operations."""

import asyncio
import logging
import time
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
import mimetypes

from ..models import Pack, ToolDefinition, AuthMethod
from .api_adapter import VariableSubstitutor

logger = logging.getLogger(__name__)


@dataclass
class FileResponse:
    """Response from file system operation."""
    success: bool
    data: Union[Dict[str, Any], List[Dict[str, Any]], str, bytes, None]
    file_count: Optional[int]
    total_size: Optional[int]
    execution_time: float
    error: Optional[str] = None


class FileSystemAdapter:
    """Universal file system adapter supporting local and cloud storage."""
    
    def __init__(self, pack: Pack):
        """Initialize file system adapter.
        
        Args:
            pack: Knowledge pack configuration
        """
        self.pack = pack
        self.clients = {}
        
        # Validate configuration
        if not pack.connection.engine:
            raise ValueError("Storage engine must be specified (local, s3, gcs, azure, ftp)")
    
    async def execute_tool(
        self,
        tool_def: ToolDefinition,
        parameters: Dict[str, Any]
    ) -> FileResponse:
        """Execute file system tool.
        
        Args:
            tool_def: Tool definition
            parameters: Tool parameters
            
        Returns:
            FileResponse with results
        """
        start_time = time.time()
        
        try:
            # Get storage client
            client = await self._get_client()
            
            # Execute based on operation
            operation = tool_def.operation or tool_def.config.get('operation', 'read')
            
            if operation == 'read':
                result = await self._read_file(tool_def, parameters, client)
            elif operation == 'write':
                result = await self._write_file(tool_def, parameters, client)
            elif operation == 'list':
                result = await self._list_files(tool_def, parameters, client)
            elif operation == 'delete':
                result = await self._delete_file(tool_def, parameters, client)
            elif operation == 'copy':
                result = await self._copy_file(tool_def, parameters, client)
            elif operation == 'move':
                result = await self._move_file(tool_def, parameters, client)
            elif operation == 'info':
                result = await self._get_file_info(tool_def, parameters, client)
            elif operation == 'upload':
                result = await self._upload_file(tool_def, parameters, client)
            elif operation == 'download':
                result = await self._download_file(tool_def, parameters, client)
            else:
                raise ValueError(f"Unknown file operation: {operation}")
                
            execution_time = time.time() - start_time
            
            return FileResponse(
                success=True,
                data=result.get('data'),
                file_count=result.get('file_count'),
                total_size=result.get('total_size'),
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"File operation failed: {e}")
            
            return FileResponse(
                success=False,
                data=None,
                file_count=None,
                total_size=None,
                execution_time=execution_time,
                error=str(e)
            )
    
    async def _get_client(self):
        """Get storage client based on engine type."""
        engine = self.pack.connection.engine.lower()
        
        if engine == 'local':
            return await self._get_local_client()
        elif engine == 's3':
            return await self._get_s3_client()
        elif engine == 'gcs':
            return await self._get_gcs_client()
        elif engine == 'azure':
            return await self._get_azure_client()
        elif engine == 'ftp':
            return await self._get_ftp_client()
        elif engine == 'sftp':
            return await self._get_sftp_client()
        else:
            raise ValueError(f"Unsupported storage engine: {engine}")
    
    async def _get_local_client(self):
        """Get local file system client."""
        # For local file system, we don't need a client
        # Just return the root path
        return {
            'type': 'local',
            'root_path': self.pack.connection.root_path or '/'
        }
    
    async def _get_s3_client(self):
        """Get AWS S3 client."""
        try:
            import aioboto3
        except ImportError:
            raise ImportError("aioboto3 is required for S3 support. Install with: pip install aioboto3")
        
        if 's3' not in self.clients:
            # Create S3 client
            session = aioboto3.Session()
            
            auth_config = self.pack.connection.auth.config if self.pack.connection.auth else {}
            aws_access_key = VariableSubstitutor.substitute(auth_config.get('access_key', ''), {})
            aws_secret_key = VariableSubstitutor.substitute(auth_config.get('secret_key', ''), {})
            region = auth_config.get('region', 'us-east-1')
            
            self.clients['s3'] = session.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=region
            )
        
        return self.clients['s3']
    
    async def _get_gcs_client(self):
        """Get Google Cloud Storage client."""
        try:
            from google.cloud import storage
        except ImportError:
            raise ImportError("google-cloud-storage is required for GCS support. Install with: pip install google-cloud-storage")
        
        # Implementation for GCS
        raise NotImplementedError("GCS adapter implementation pending")
    
    async def _get_azure_client(self):
        """Get Azure Blob Storage client."""
        try:
            from azure.storage.blob.aio import BlobServiceClient
        except ImportError:
            raise ImportError("azure-storage-blob is required for Azure support. Install with: pip install azure-storage-blob")
        
        # Implementation for Azure
        raise NotImplementedError("Azure adapter implementation pending")
    
    async def _get_ftp_client(self):
        """Get FTP client."""
        try:
            import aioftp
        except ImportError:
            raise ImportError("aioftp is required for FTP support. Install with: pip install aioftp")
        
        # Implementation for FTP
        raise NotImplementedError("FTP adapter implementation pending")
    
    async def _get_sftp_client(self):
        """Get SFTP client."""
        try:
            import asyncssh
        except ImportError:
            raise ImportError("asyncssh is required for SFTP support. Install with: pip install asyncssh")
        
        # Implementation for SFTP
        raise NotImplementedError("SFTP adapter implementation pending")
    
    async def _read_file(
        self,
        tool_def: ToolDefinition,
        parameters: Dict[str, Any],
        client
    ) -> Dict[str, Any]:
        """Read file content."""
        file_path = VariableSubstitutor.substitute(
            tool_def.path or parameters.get('file_path', ''), parameters
        )
        
        if client.get('type') == 'local':
            # Local file system
            full_path = Path(client['root_path']) / file_path.lstrip('/')
            
            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Check if it's a text or binary file
            mime_type, _ = mimetypes.guess_type(str(full_path))
            is_text = mime_type and mime_type.startswith('text/')
            
            if is_text or parameters.get('mode', 'text') == 'text':
                # Read as text
                content = full_path.read_text(encoding=parameters.get('encoding', 'utf-8'))
            else:
                # Read as binary
                content = full_path.read_bytes()
                # Encode binary data as base64 for JSON serialization
                import base64
                content = base64.b64encode(content).decode('ascii')
            
            return {
                'data': {
                    'path': file_path,
                    'content': content,
                    'size': full_path.stat().st_size,
                    'mime_type': mime_type,
                    'is_binary': not is_text and parameters.get('mode', 'text') != 'text'
                },
                'file_count': 1,
                'total_size': full_path.stat().st_size
            }
        else:
            raise NotImplementedError(f"Read operation for {self.pack.connection.engine} not implemented")
    
    async def _write_file(
        self,
        tool_def: ToolDefinition,
        parameters: Dict[str, Any],
        client
    ) -> Dict[str, Any]:
        """Write file content."""
        file_path = VariableSubstitutor.substitute(
            tool_def.path or parameters.get('file_path', ''), parameters
        )
        content = parameters.get('content', '')
        mode = parameters.get('mode', 'text')
        
        if client.get('type') == 'local':
            # Local file system
            full_path = Path(client['root_path']) / file_path.lstrip('/')
            
            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            if mode == 'binary':
                # Decode base64 content for binary files
                import base64
                binary_content = base64.b64decode(content)
                full_path.write_bytes(binary_content)
                size = len(binary_content)
            else:
                # Write as text
                full_path.write_text(content, encoding=parameters.get('encoding', 'utf-8'))
                size = len(content.encode('utf-8'))
            
            return {
                'data': {
                    'path': file_path,
                    'size': size,
                    'mode': mode,
                    'written': True
                },
                'file_count': 1,
                'total_size': size
            }
        else:
            raise NotImplementedError(f"Write operation for {self.pack.connection.engine} not implemented")
    
    async def _list_files(
        self,
        tool_def: ToolDefinition,
        parameters: Dict[str, Any],
        client
    ) -> Dict[str, Any]:
        """List files in directory."""
        dir_path = VariableSubstitutor.substitute(
            tool_def.path or parameters.get('directory', ''), parameters
        )
        recursive = parameters.get('recursive', False)
        pattern = parameters.get('pattern', '*')
        
        if client.get('type') == 'local':
            # Local file system
            full_path = Path(client['root_path']) / dir_path.lstrip('/')
            
            if not full_path.exists():
                raise FileNotFoundError(f"Directory not found: {dir_path}")
            
            if not full_path.is_dir():
                raise NotADirectoryError(f"Path is not a directory: {dir_path}")
            
            files = []
            total_size = 0
            
            if recursive:
                glob_pattern = f"**/{pattern}"
                paths = full_path.rglob(pattern)
            else:
                paths = full_path.glob(pattern)
            
            for path in paths:
                if path.is_file():
                    stat = path.stat()
                    relative_path = path.relative_to(Path(client['root_path']))
                    
                    files.append({
                        'path': str(relative_path),
                        'name': path.name,
                        'size': stat.st_size,
                        'modified': stat.st_mtime,
                        'is_directory': False,
                        'mime_type': mimetypes.guess_type(str(path))[0]
                    })
                    total_size += stat.st_size
                elif path.is_dir() and parameters.get('include_directories', True):
                    relative_path = path.relative_to(Path(client['root_path']))
                    files.append({
                        'path': str(relative_path),
                        'name': path.name,
                        'size': 0,
                        'modified': path.stat().st_mtime,
                        'is_directory': True,
                        'mime_type': None
                    })
            
            return {
                'data': files,
                'file_count': len(files),
                'total_size': total_size
            }
        else:
            raise NotImplementedError(f"List operation for {self.pack.connection.engine} not implemented")
    
    async def _delete_file(
        self,
        tool_def: ToolDefinition,
        parameters: Dict[str, Any],
        client
    ) -> Dict[str, Any]:
        """Delete file or directory."""
        file_path = VariableSubstitutor.substitute(
            tool_def.path or parameters.get('file_path', ''), parameters
        )
        
        if client.get('type') == 'local':
            # Local file system
            full_path = Path(client['root_path']) / file_path.lstrip('/')
            
            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if full_path.is_file():
                size = full_path.stat().st_size
                full_path.unlink()
                return {
                    'data': {
                        'path': file_path,
                        'deleted': True,
                        'type': 'file',
                        'size': size
                    },
                    'file_count': 1,
                    'total_size': size
                }
            elif full_path.is_dir():
                import shutil
                shutil.rmtree(full_path)
                return {
                    'data': {
                        'path': file_path,
                        'deleted': True,
                        'type': 'directory'
                    },
                    'file_count': 1,
                    'total_size': 0
                }
        else:
            raise NotImplementedError(f"Delete operation for {self.pack.connection.engine} not implemented")
    
    async def _copy_file(
        self,
        tool_def: ToolDefinition,
        parameters: Dict[str, Any],
        client
    ) -> Dict[str, Any]:
        """Copy file."""
        source_path = VariableSubstitutor.substitute(parameters.get('source_path', ''), parameters)
        dest_path = VariableSubstitutor.substitute(parameters.get('dest_path', ''), parameters)
        
        if client.get('type') == 'local':
            import shutil
            
            source_full = Path(client['root_path']) / source_path.lstrip('/')
            dest_full = Path(client['root_path']) / dest_path.lstrip('/')
            
            if not source_full.exists():
                raise FileNotFoundError(f"Source file not found: {source_path}")
            
            # Create destination directory if needed
            dest_full.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(source_full, dest_full)
            size = dest_full.stat().st_size
            
            return {
                'data': {
                    'source_path': source_path,
                    'dest_path': dest_path,
                    'copied': True,
                    'size': size
                },
                'file_count': 1,
                'total_size': size
            }
        else:
            raise NotImplementedError(f"Copy operation for {self.pack.connection.engine} not implemented")
    
    async def _move_file(
        self,
        tool_def: ToolDefinition,
        parameters: Dict[str, Any],
        client
    ) -> Dict[str, Any]:
        """Move/rename file."""
        source_path = VariableSubstitutor.substitute(parameters.get('source_path', ''), parameters)
        dest_path = VariableSubstitutor.substitute(parameters.get('dest_path', ''), parameters)
        
        if client.get('type') == 'local':
            source_full = Path(client['root_path']) / source_path.lstrip('/')
            dest_full = Path(client['root_path']) / dest_path.lstrip('/')
            
            if not source_full.exists():
                raise FileNotFoundError(f"Source file not found: {source_path}")
            
            # Create destination directory if needed
            dest_full.parent.mkdir(parents=True, exist_ok=True)
            
            size = source_full.stat().st_size if source_full.is_file() else 0
            source_full.rename(dest_full)
            
            return {
                'data': {
                    'source_path': source_path,
                    'dest_path': dest_path,
                    'moved': True,
                    'size': size
                },
                'file_count': 1,
                'total_size': size
            }
        else:
            raise NotImplementedError(f"Move operation for {self.pack.connection.engine} not implemented")
    
    async def _get_file_info(
        self,
        tool_def: ToolDefinition,
        parameters: Dict[str, Any],
        client
    ) -> Dict[str, Any]:
        """Get file information."""
        file_path = VariableSubstitutor.substitute(
            tool_def.path or parameters.get('file_path', ''), parameters
        )
        
        if client.get('type') == 'local':
            full_path = Path(client['root_path']) / file_path.lstrip('/')
            
            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            stat = full_path.stat()
            
            return {
                'data': {
                    'path': file_path,
                    'name': full_path.name,
                    'size': stat.st_size,
                    'created': stat.st_ctime,
                    'modified': stat.st_mtime,
                    'accessed': stat.st_atime,
                    'is_directory': full_path.is_dir(),
                    'is_file': full_path.is_file(),
                    'mime_type': mimetypes.guess_type(str(full_path))[0],
                    'permissions': oct(stat.st_mode)[-3:]
                },
                'file_count': 1,
                'total_size': stat.st_size
            }
        else:
            raise NotImplementedError(f"Info operation for {self.pack.connection.engine} not implemented")
    
    async def _upload_file(
        self,
        tool_def: ToolDefinition,
        parameters: Dict[str, Any],
        client
    ) -> Dict[str, Any]:
        """Upload file to cloud storage."""
        # This would be implemented for cloud storage engines
        raise NotImplementedError("Upload operation not implemented for local storage")
    
    async def _download_file(
        self,
        tool_def: ToolDefinition,
        parameters: Dict[str, Any],
        client
    ) -> Dict[str, Any]:
        """Download file from cloud storage."""
        # This would be implemented for cloud storage engines
        raise NotImplementedError("Download operation not implemented for local storage")
    
    async def close(self):
        """Close all storage clients."""
        for client in self.clients.values():
            try:
                await client.close()
            except Exception as e:
                logger.warning(f"Error closing storage client: {e}")
        
        self.clients.clear()