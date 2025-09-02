"""Message queue adapter for pub/sub and messaging operations."""

import asyncio
import logging
import time
import json
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass

from ..models import Pack, ToolDefinition, AuthMethod
from .api_adapter import VariableSubstitutor

logger = logging.getLogger(__name__)


@dataclass
class QueueResponse:
    """Response from message queue operation."""
    success: bool
    data: Union[Dict[str, Any], List[Dict[str, Any]], None]
    message_count: Optional[int]
    execution_time: float
    error: Optional[str] = None


class MessageQueueAdapter:
    """Universal message queue adapter supporting multiple queue systems."""
    
    def __init__(self, pack: Pack):
        """Initialize message queue adapter.
        
        Args:
            pack: Knowledge pack configuration
        """
        self.pack = pack
        self.connections = {}
        
        # Validate configuration
        if not pack.connection.engine:
            raise ValueError("Queue engine must be specified (rabbitmq, redis, kafka, etc.)")
    
    async def execute_tool(
        self,
        tool_def: ToolDefinition,
        parameters: Dict[str, Any]
    ) -> QueueResponse:
        """Execute message queue tool.
        
        Args:
            tool_def: Tool definition
            parameters: Tool parameters
            
        Returns:
            QueueResponse with results
        """
        start_time = time.time()
        
        try:
            # Get queue connection
            connection = await self._get_connection()
            
            # Execute based on tool type
            if tool_def.type.value == "execute":
                if tool_def.config.get('operation') == 'publish':
                    result = await self._publish_message(tool_def, parameters, connection)
                elif tool_def.config.get('operation') == 'consume':
                    result = await self._consume_messages(tool_def, parameters, connection)
                elif tool_def.config.get('operation') == 'create_queue':
                    result = await self._create_queue(tool_def, parameters, connection)
                else:
                    raise ValueError(f"Unknown queue operation: {tool_def.config.get('operation')}")
            elif tool_def.type.value == "list":
                result = await self._list_queues(tool_def, parameters, connection)
            elif tool_def.type.value == "details":
                result = await self._get_queue_details(tool_def, parameters, connection)
            else:
                raise ValueError(f"Unsupported queue tool type: {tool_def.type}")
                
            execution_time = time.time() - start_time
            
            return QueueResponse(
                success=True,
                data=result.get('data'),
                message_count=result.get('message_count'),
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Queue operation failed: {e}")
            
            return QueueResponse(
                success=False,
                data=None,
                message_count=None,
                execution_time=execution_time,
                error=str(e)
            )
    
    async def _get_connection(self):
        """Get message queue connection based on engine type."""
        engine = self.pack.connection.engine.lower()
        
        if engine == 'rabbitmq':
            return await self._get_rabbitmq_connection()
        elif engine == 'redis':
            return await self._get_redis_connection()
        elif engine == 'kafka':
            return await self._get_kafka_connection()
        elif engine == 'aws_sqs':
            return await self._get_sqs_connection()
        else:
            raise ValueError(f"Unsupported queue engine: {engine}")
    
    async def _get_rabbitmq_connection(self):
        """Get RabbitMQ connection."""
        try:
            import aio_pika
        except ImportError:
            raise ImportError("aio-pika is required for RabbitMQ support. Install with: pip install aio-pika")
        
        connection_key = f"rabbitmq_{self.pack.connection.host}"
        
        if connection_key not in self.connections:
            # Build connection URL
            auth_config = self.pack.connection.auth.config if self.pack.connection.auth else {}
            username = VariableSubstitutor.substitute(auth_config.get('username', 'guest'), {})
            password = VariableSubstitutor.substitute(auth_config.get('password', 'guest'), {})
            
            url = f"amqp://{username}:{password}@{self.pack.connection.host}:{self.pack.connection.port or 5672}/"
            
            # Create connection
            self.connections[connection_key] = await aio_pika.connect_robust(
                url,
                timeout=self.pack.connection.timeout
            )
        
        return self.connections[connection_key]
    
    async def _get_redis_connection(self):
        """Get Redis connection for pub/sub."""
        try:
            import redis.asyncio as redis
        except ImportError:
            raise ImportError("redis is required for Redis support. Install with: pip install redis")
        
        connection_key = f"redis_{self.pack.connection.host}"
        
        if connection_key not in self.connections:
            # Build connection
            auth_config = self.pack.connection.auth.config if self.pack.connection.auth else {}
            password = VariableSubstitutor.substitute(auth_config.get('password', ''), {})
            
            self.connections[connection_key] = redis.Redis(
                host=self.pack.connection.host,
                port=self.pack.connection.port or 6379,
                password=password if password else None,
                decode_responses=True,
                socket_timeout=self.pack.connection.timeout
            )
        
        return self.connections[connection_key]
    
    async def _get_kafka_connection(self):
        """Get Kafka connection."""
        try:
            from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
        except ImportError:
            raise ImportError("aiokafka is required for Kafka support. Install with: pip install aiokafka")
        
        # Implementation for Kafka
        raise NotImplementedError("Kafka adapter implementation pending")
    
    async def _get_sqs_connection(self):
        """Get AWS SQS connection."""
        try:
            import aioboto3
        except ImportError:
            raise ImportError("aioboto3 is required for AWS SQS support. Install with: pip install aioboto3")
        
        # Implementation for SQS
        raise NotImplementedError("AWS SQS adapter implementation pending")
    
    async def _publish_message(
        self,
        tool_def: ToolDefinition,
        parameters: Dict[str, Any],
        connection
    ) -> Dict[str, Any]:
        """Publish message to queue."""
        if self.pack.connection.engine.lower() == 'rabbitmq':
            import aio_pika
            
            # Get queue name and exchange
            queue_name = VariableSubstitutor.substitute(
                tool_def.queue or parameters.get('queue_name', ''), parameters
            )
            exchange_name = VariableSubstitutor.substitute(
                tool_def.exchange_name or parameters.get('exchange_name', ''), parameters
            )
            
            # Get message data
            message_data = parameters.get('message', {})
            if isinstance(message_data, dict):
                message_body = json.dumps(message_data)
            else:
                message_body = str(message_data)
            
            # Create channel and publish
            channel = await connection.channel()
            
            if exchange_name:
                exchange = await channel.get_exchange(exchange_name)
                await exchange.publish(
                    aio_pika.Message(message_body.encode()),
                    routing_key=queue_name
                )
            else:
                queue = await channel.declare_queue(queue_name, durable=True)
                await channel.default_exchange.publish(
                    aio_pika.Message(message_body.encode()),
                    routing_key=queue_name
                )
            
            await channel.close()
            
            return {
                'data': {
                    'queue': queue_name,
                    'exchange': exchange_name,
                    'message_published': True,
                    'message_size': len(message_body)
                },
                'message_count': 1
            }
            
        elif self.pack.connection.engine.lower() == 'redis':
            # Redis pub/sub
            channel = VariableSubstitutor.substitute(
                tool_def.queue or parameters.get('channel', ''), parameters
            )
            message_data = parameters.get('message', {})
            
            if isinstance(message_data, dict):
                message_body = json.dumps(message_data)
            else:
                message_body = str(message_data)
            
            result = await connection.publish(channel, message_body)
            
            return {
                'data': {
                    'channel': channel,
                    'subscribers_reached': result,
                    'message_published': True
                },
                'message_count': 1
            }
        else:
            raise NotImplementedError(f"Publish for {self.pack.connection.engine} not implemented")
    
    async def _consume_messages(
        self,
        tool_def: ToolDefinition,
        parameters: Dict[str, Any],
        connection
    ) -> Dict[str, Any]:
        """Consume messages from queue."""
        if self.pack.connection.engine.lower() == 'rabbitmq':
            import aio_pika
            
            queue_name = VariableSubstitutor.substitute(
                tool_def.queue or parameters.get('queue_name', ''), parameters
            )
            max_messages = parameters.get('max_messages', 10)
            timeout = parameters.get('timeout', 5)
            
            channel = await connection.channel()
            queue = await channel.declare_queue(queue_name, durable=True)
            
            messages = []
            try:
                # Consume messages with timeout
                async with asyncio.timeout(timeout):
                    for _ in range(max_messages):
                        message = await queue.get(timeout=1)
                        if message is None:
                            break
                        
                        try:
                            # Try to parse as JSON
                            message_data = json.loads(message.body.decode())
                        except json.JSONDecodeError:
                            message_data = message.body.decode()
                        
                        messages.append({
                            'data': message_data,
                            'delivery_tag': message.delivery_tag,
                            'timestamp': message.timestamp,
                            'headers': dict(message.headers or {})
                        })
                        
                        await message.ack()
                        
            except asyncio.TimeoutError:
                pass
            
            await channel.close()
            
            return {
                'data': messages,
                'message_count': len(messages)
            }
        else:
            raise NotImplementedError(f"Consume for {self.pack.connection.engine} not implemented")
    
    async def _create_queue(
        self,
        tool_def: ToolDefinition,
        parameters: Dict[str, Any],
        connection
    ) -> Dict[str, Any]:
        """Create a new queue."""
        if self.pack.connection.engine.lower() == 'rabbitmq':
            queue_name = VariableSubstitutor.substitute(
                tool_def.queue or parameters.get('queue_name', ''), parameters
            )
            durable = parameters.get('durable', True)
            
            channel = await connection.channel()
            queue = await channel.declare_queue(queue_name, durable=durable)
            await channel.close()
            
            return {
                'data': {
                    'queue_name': queue_name,
                    'durable': durable,
                    'created': True
                },
                'message_count': 0
            }
        else:
            raise NotImplementedError(f"Create queue for {self.pack.connection.engine} not implemented")
    
    async def _list_queues(
        self,
        tool_def: ToolDefinition,
        parameters: Dict[str, Any],
        connection
    ) -> Dict[str, Any]:
        """List available queues."""
        # This would typically require management API access
        # Implementation depends on the specific queue system
        raise NotImplementedError("List queues not implemented - requires management API access")
    
    async def _get_queue_details(
        self,
        tool_def: ToolDefinition,
        parameters: Dict[str, Any],
        connection
    ) -> Dict[str, Any]:
        """Get details about a specific queue."""
        # This would typically require management API access
        # Implementation depends on the specific queue system
        raise NotImplementedError("Queue details not implemented - requires management API access")
    
    async def close(self):
        """Close all queue connections."""
        for connection in self.connections.values():
            try:
                await connection.close()
            except Exception as e:
                logger.warning(f"Error closing queue connection: {e}")
        
        self.connections.clear()