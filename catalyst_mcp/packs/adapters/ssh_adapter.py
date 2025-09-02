"""SSH and shell command adapter for remote execution."""

import asyncio
import logging
import time
import os
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
import shlex

from ..models import Pack, ToolDefinition, AuthMethod
from .api_adapter import VariableSubstitutor

logger = logging.getLogger(__name__)


@dataclass
class SSHResponse:
    """Response from SSH/shell operation."""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    error: Optional[str] = None


class SSHAdapter:
    """Universal SSH and shell command adapter."""
    
    def __init__(self, pack: Pack):
        """Initialize SSH adapter.
        
        Args:
            pack: Knowledge pack configuration
        """
        self.pack = pack
        self.connections = {}
        
        # Validate configuration
        if not pack.connection.engine:
            raise ValueError("Shell engine must be specified (ssh, local)")
            
        if pack.connection.engine == 'ssh' and not pack.connection.hostname:
            raise ValueError("SSH hostname must be specified")
    
    async def execute_tool(
        self,
        tool_def: ToolDefinition,
        parameters: Dict[str, Any]
    ) -> SSHResponse:
        """Execute SSH/shell tool.
        
        Args:
            tool_def: Tool definition
            parameters: Tool parameters
            
        Returns:
            SSHResponse with results
        """
        start_time = time.time()
        
        try:
            # Get shell connection
            connection = await self._get_connection()
            
            # Execute command
            result = await self._execute_command(tool_def, parameters, connection)
            
            execution_time = time.time() - start_time
            
            return SSHResponse(
                success=result['exit_code'] == 0,
                stdout=result['stdout'],
                stderr=result['stderr'],
                exit_code=result['exit_code'],
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"SSH/shell operation failed: {e}")
            
            return SSHResponse(
                success=False,
                stdout="",
                stderr="",
                exit_code=-1,
                execution_time=execution_time,
                error=str(e)
            )
    
    async def _get_connection(self):
        """Get shell connection based on engine type."""
        engine = self.pack.connection.engine.lower()
        
        if engine == 'ssh':
            return await self._get_ssh_connection()
        elif engine == 'local':
            return await self._get_local_connection()
        else:
            raise ValueError(f"Unsupported shell engine: {engine}")
    
    async def _get_ssh_connection(self):
        """Get SSH connection."""
        try:
            import asyncssh
        except ImportError:
            raise ImportError("asyncssh is required for SSH support. Install with: pip install asyncssh")
        
        connection_key = f"ssh_{self.pack.connection.hostname}_{self.pack.connection.username}"
        
        if connection_key not in self.connections:
            # Build connection parameters
            auth_config = self.pack.connection.auth.config if self.pack.connection.auth else {}
            
            conn_params = {
                'host': self.pack.connection.hostname,
                'port': self.pack.connection.port or 22,
                'username': self.pack.connection.username,
                'connect_timeout': self.pack.connection.timeout,
                'known_hosts': None  # For development - should be configured for production
            }
            
            # Handle different auth methods
            if self.pack.connection.auth:
                if self.pack.connection.auth.method == AuthMethod.BASIC:
                    # Password authentication
                    password = VariableSubstitutor.substitute(auth_config.get('password', ''), {})
                    conn_params['password'] = password
                    
                elif self.pack.connection.auth.method == AuthMethod.SSH_KEY:
                    # SSH key authentication
                    key_file = VariableSubstitutor.substitute(
                        auth_config.get('private_key_file', self.pack.connection.key_file or ''), {}
                    )
                    if key_file:
                        conn_params['client_keys'] = [key_file]
                    
                    passphrase = VariableSubstitutor.substitute(auth_config.get('passphrase', ''), {})
                    if passphrase:
                        conn_params['passphrase'] = passphrase
            
            # Create SSH connection
            self.connections[connection_key] = await asyncssh.connect(**conn_params)
        
        return self.connections[connection_key]
    
    async def _get_local_connection(self):
        """Get local shell connection."""
        # For local shell, we don't need a persistent connection
        return {
            'type': 'local',
            'shell': self.pack.connection.extra_config.get('shell', '/bin/bash')
        }
    
    async def _execute_command(
        self,
        tool_def: ToolDefinition,
        parameters: Dict[str, Any],
        connection
    ) -> Dict[str, Any]:
        """Execute shell command."""
        # Build command
        command = VariableSubstitutor.substitute(
            tool_def.command or parameters.get('command', ''), parameters
        )
        
        if not command:
            raise ValueError("No command specified")
        
        # Get working directory
        working_dir = VariableSubstitutor.substitute(
            tool_def.working_directory or parameters.get('working_directory', ''), parameters
        )
        
        # Get environment variables
        env_vars = parameters.get('environment', {})
        
        if self.pack.connection.engine.lower() == 'ssh':
            # SSH execution
            return await self._execute_ssh_command(command, working_dir, env_vars, connection)
        else:
            # Local execution
            return await self._execute_local_command(command, working_dir, env_vars, connection)
    
    async def _execute_ssh_command(
        self,
        command: str,
        working_dir: str,
        env_vars: Dict[str, str],
        connection
    ) -> Dict[str, Any]:
        """Execute command over SSH."""
        # Build full command with environment and working directory
        full_command = []
        
        # Add environment variables
        if env_vars:
            env_string = ' '.join([f"{k}={shlex.quote(str(v))}" for k, v in env_vars.items()])
            full_command.append(f"env {env_string}")
        
        # Add working directory change
        if working_dir:
            full_command.append(f"cd {shlex.quote(working_dir)} &&")
        
        # Add the actual command
        full_command.append(command)
        
        final_command = ' '.join(full_command)
        
        # Execute command
        result = await connection.run(final_command, check=False)
        
        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'exit_code': result.exit_status
        }
    
    async def _execute_local_command(
        self,
        command: str,
        working_dir: str,
        env_vars: Dict[str, str],
        connection
    ) -> Dict[str, Any]:
        """Execute command locally."""
        # Prepare environment
        env = os.environ.copy()
        if env_vars:
            env.update({k: str(v) for k, v in env_vars.items()})
        
        # Determine shell
        shell = connection.get('shell', '/bin/bash')
        if os.name == 'nt':  # Windows
            shell = connection.get('shell', 'cmd.exe')
            # For Windows, we might want to use PowerShell
            if 'powershell' in shell.lower():
                command_args = [shell, '-Command', command]
            else:
                command_args = [shell, '/c', command]
        else:
            # Unix-like systems
            command_args = [shell, '-c', command]
        
        # Execute command
        process = await asyncio.create_subprocess_exec(
            *command_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=working_dir if working_dir else None
        )
        
        stdout, stderr = await process.communicate()
        
        return {
            'stdout': stdout.decode('utf-8', errors='replace'),
            'stderr': stderr.decode('utf-8', errors='replace'),
            'exit_code': process.returncode or 0
        }
    
    async def close(self):
        """Close all SSH connections."""
        for connection in self.connections.values():
            try:
                if hasattr(connection, 'close'):
                    connection.close()
                    await connection.wait_closed()
            except Exception as e:
                logger.warning(f"Error closing SSH connection: {e}")
        
        self.connections.clear()