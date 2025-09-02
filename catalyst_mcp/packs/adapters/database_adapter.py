"""Database adapter for executing SQL and NoSQL operations."""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
import json

from ..models import Pack, ToolDefinition, AuthMethod
from .api_adapter import VariableSubstitutor

logger = logging.getLogger(__name__)


@dataclass
class DatabaseResponse:
    """Response from database operation."""
    success: bool
    data: Union[List[Dict[str, Any]], Dict[str, Any], None]
    rows_affected: Optional[int]
    execution_time: float
    error: Optional[str] = None


class DatabaseAdapter:
    """Universal database adapter supporting SQL and NoSQL operations."""
    
    def __init__(self, pack: Pack):
        """Initialize database adapter.
        
        Args:
            pack: Knowledge pack configuration
        """
        self.pack = pack
        self.connection = None
        self._connection_pools = {}
        
        # Validate database configuration
        if not pack.connection.engine:
            raise ValueError("Database engine must be specified")
            
        if not pack.connection.host and pack.connection.engine not in ['sqlite', 'duckdb']:
            raise ValueError("Database host must be specified for most engines")
    
    async def execute_tool(
        self, 
        tool_def: ToolDefinition, 
        parameters: Dict[str, Any]
    ) -> DatabaseResponse:
        """Execute database tool.
        
        Args:
            tool_def: Tool definition
            parameters: Tool parameters
            
        Returns:
            DatabaseResponse with results
        """
        start_time = time.time()
        
        try:
            # Get database connection
            connection = await self._get_connection()
            
            # Execute based on tool type
            if tool_def.type.value == "query":
                result = await self._execute_query(tool_def, parameters, connection)
            elif tool_def.type.value == "execute":
                result = await self._execute_command(tool_def, parameters, connection)
            elif tool_def.type.value == "transaction":
                result = await self._execute_transaction(tool_def, parameters, connection)
            else:
                raise ValueError(f"Unsupported database tool type: {tool_def.type}")
                
            execution_time = time.time() - start_time
            
            return DatabaseResponse(
                success=True,
                data=result.get('data'),
                rows_affected=result.get('rows_affected'),
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Database operation failed: {e}")
            
            return DatabaseResponse(
                success=False,
                data=None,
                rows_affected=None,
                execution_time=execution_time,
                error=str(e)
            )
    
    async def _get_connection(self):
        """Get database connection based on engine type."""
        engine = self.pack.connection.engine.lower()
        
        if engine == 'postgresql':
            return await self._get_postgresql_connection()
        elif engine == 'mysql':
            return await self._get_mysql_connection()
        elif engine == 'sqlite':
            return await self._get_sqlite_connection()
        elif engine == 'mongodb':
            return await self._get_mongodb_connection()
        elif engine == 'redis':
            return await self._get_redis_connection()
        elif engine == 'elasticsearch':
            return await self._get_elasticsearch_connection()
        else:
            raise ValueError(f"Unsupported database engine: {engine}")
    
    async def _get_postgresql_connection(self):
        """Get PostgreSQL connection."""
        try:
            import asyncpg
        except ImportError:
            raise ImportError("asyncpg is required for PostgreSQL support. Install with: pip install asyncpg")
        
        connection_key = f"postgresql_{self.pack.connection.host}_{self.pack.connection.database}"
        
        if connection_key not in self._connection_pools:
            # Build connection string
            auth_config = self.pack.connection.auth.config if self.pack.connection.auth else {}
            username = VariableSubstitutor.substitute(auth_config.get('username', 'postgres'), {})
            password = VariableSubstitutor.substitute(auth_config.get('password', ''), {})
            
            dsn = f"postgresql://{username}:{password}@{self.pack.connection.host}:{self.pack.connection.port or 5432}/{self.pack.connection.database}"
            
            # Create connection pool
            self._connection_pools[connection_key] = await asyncpg.create_pool(
                dsn,
                min_size=1,
                max_size=self.pack.connection.pool_size,
                command_timeout=self.pack.connection.timeout
            )
        
        return self._connection_pools[connection_key]
    
    async def _get_mysql_connection(self):
        """Get MySQL connection."""
        try:
            import aiomysql
        except ImportError:
            raise ImportError("aiomysql is required for MySQL support. Install with: pip install aiomysql")
        
        # Implementation for MySQL
        raise NotImplementedError("MySQL adapter implementation pending")
    
    async def _get_sqlite_connection(self):
        """Get SQLite connection."""
        try:
            import aiosqlite
        except ImportError:
            raise ImportError("aiosqlite is required for SQLite support. Install with: pip install aiosqlite")
        
        # Implementation for SQLite
        raise NotImplementedError("SQLite adapter implementation pending")
    
    async def _get_mongodb_connection(self):
        """Get MongoDB connection."""
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
        except ImportError:
            raise ImportError("motor is required for MongoDB support. Install with: pip install motor")
        
        # Implementation for MongoDB
        raise NotImplementedError("MongoDB adapter implementation pending")
    
    async def _get_redis_connection(self):
        """Get Redis connection."""
        try:
            import redis.asyncio as redis
        except ImportError:
            raise ImportError("redis is required for Redis support. Install with: pip install redis")
        
        # Implementation for Redis
        raise NotImplementedError("Redis adapter implementation pending")
    
    async def _get_elasticsearch_connection(self):
        """Get Elasticsearch connection."""
        try:
            from elasticsearch import AsyncElasticsearch
        except ImportError:
            raise ImportError("elasticsearch is required for Elasticsearch support. Install with: pip install elasticsearch")
        
        # Implementation for Elasticsearch
        raise NotImplementedError("Elasticsearch adapter implementation pending")
    
    async def _execute_query(
        self, 
        tool_def: ToolDefinition, 
        parameters: Dict[str, Any], 
        connection
    ) -> Dict[str, Any]:
        """Execute SQL query."""
        # Substitute parameters in SQL
        sql = VariableSubstitutor.substitute(tool_def.sql, parameters)
        
        if self.pack.connection.engine.lower() == 'postgresql':
            async with connection.acquire() as conn:
                # Execute query
                rows = await conn.fetch(sql)
                
                # Convert to list of dictionaries
                result = []
                for row in rows:
                    result.append(dict(row))
                
                return {
                    'data': result,
                    'rows_affected': len(result)
                }
        else:
            raise NotImplementedError(f"Query execution for {self.pack.connection.engine} not implemented")
    
    async def _execute_command(
        self,
        tool_def: ToolDefinition,
        parameters: Dict[str, Any],
        connection
    ) -> Dict[str, Any]:
        """Execute database command (INSERT, UPDATE, DELETE)."""
        sql = VariableSubstitutor.substitute(tool_def.sql, parameters)
        
        if self.pack.connection.engine.lower() == 'postgresql':
            async with connection.acquire() as conn:
                # Execute command
                result = await conn.execute(sql)
                
                # Extract rows affected from result
                # PostgreSQL returns something like "INSERT 0 5" or "UPDATE 3"
                rows_affected = 0
                if result:
                    parts = result.split()
                    if len(parts) >= 2:
                        try:
                            rows_affected = int(parts[-1])
                        except ValueError:
                            pass
                
                return {
                    'data': {'result': result},
                    'rows_affected': rows_affected
                }
        else:
            raise NotImplementedError(f"Command execution for {self.pack.connection.engine} not implemented")
    
    async def _execute_transaction(
        self,
        tool_def: ToolDefinition,
        parameters: Dict[str, Any],
        connection
    ) -> Dict[str, Any]:
        """Execute multiple commands in a transaction."""
        if self.pack.connection.engine.lower() == 'postgresql':
            async with connection.acquire() as conn:
                async with conn.transaction():
                    results = []
                    total_rows_affected = 0
                    
                    # Execute each step in the execution_steps
                    for step in tool_def.execution_steps:
                        sql = VariableSubstitutor.substitute(step.query_params.get('sql', ''), parameters)
                        
                        if sql:
                            if step.method.upper() == 'SELECT':
                                rows = await conn.fetch(sql)
                                step_result = [dict(row) for row in rows]
                                results.append({
                                    'step': step.name,
                                    'data': step_result,
                                    'rows_affected': len(step_result)
                                })
                            else:
                                result = await conn.execute(sql)
                                rows_affected = 0
                                if result:
                                    parts = result.split()
                                    if len(parts) >= 2:
                                        try:
                                            rows_affected = int(parts[-1])
                                        except ValueError:
                                            pass
                                
                                total_rows_affected += rows_affected
                                results.append({
                                    'step': step.name,
                                    'result': result,
                                    'rows_affected': rows_affected
                                })
                    
                    return {
                        'data': results,
                        'rows_affected': total_rows_affected
                    }
        else:
            raise NotImplementedError(f"Transaction execution for {self.pack.connection.engine} not implemented")
    
    async def close(self):
        """Close all database connections."""
        for pool in self._connection_pools.values():
            try:
                await pool.close()
            except Exception as e:
                logger.warning(f"Error closing connection pool: {e}")
        
        self._connection_pools.clear()