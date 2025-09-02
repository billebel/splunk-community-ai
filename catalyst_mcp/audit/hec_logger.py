"""Splunk HEC (HTTP Event Collector) logging for structured audit events."""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import httpx
import logging

logger = logging.getLogger(__name__)


class SourceType(Enum):
    """Splunk sourcetype definitions for MCP audit events."""
    TOOL_EXECUTION = "mcp:tool:execution"
    GUARDRAIL_VIOLATION = "mcp:guardrail:violation"  
    SESSION_ACTIVITY = "mcp:session:activity"
    SEARCH_QUERY = "mcp:search:query"
    SYSTEM_HEALTH = "mcp:system:health"


@dataclass
class HECEvent:
    """Structured HEC event with metadata."""
    time: float
    source: str
    sourcetype: str
    host: str
    index: str
    event: Dict[str, Any]
    
    def to_hec_format(self) -> Dict[str, Any]:
        """Convert to Splunk HEC JSON format."""
        return {
            "time": self.time,
            "source": self.source,
            "sourcetype": self.sourcetype,
            "host": self.host,
            "index": self.index,
            "event": self.event
        }


class SplunkHECLogger:
    """Async Splunk HEC logger for structured audit events."""
    
    def __init__(
        self,
        hec_url: str,
        hec_token: str,
        index: str = "main",
        source: str = "catalyst_mcp",
        host: str = "mcp-server",
        verify_ssl: bool = False,
        batch_size: int = 50,
        flush_interval: float = 5.0
    ):
        self.hec_url = hec_url.rstrip('/')
        self.hec_token = hec_token
        self.default_index = index
        self.default_source = source
        self.default_host = host
        self.verify_ssl = verify_ssl
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        # Event batching
        self._event_queue: List[HECEvent] = []
        self._flush_task: Optional[asyncio.Task] = None
        self._client: Optional[httpx.AsyncClient] = None
        self._running = False
        
    async def start(self) -> None:
        """Start the HEC logger and batching system."""
        if self._running:
            return
            
        self._client = httpx.AsyncClient(
            verify=self.verify_ssl,
            timeout=httpx.Timeout(30.0),
            headers={
                "Authorization": f"Splunk {self.hec_token}",
                "Content-Type": "application/json"
            }
        )
        
        self._running = True
        self._flush_task = asyncio.create_task(self._flush_loop())
        
        # Test HEC connectivity
        try:
            await self._test_connectivity()
            logger.info("Splunk HEC logger started successfully")
        except Exception as e:
            logger.warning(f"HEC connectivity test failed: {e}")
    
    async def stop(self) -> None:
        """Stop the HEC logger and flush remaining events."""
        if not self._running:
            return
            
        self._running = False
        
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining events
        await self._flush_events()
        
        if self._client:
            await self._client.aclose()
            
        logger.info("Splunk HEC logger stopped")
    
    async def log_tool_execution(
        self,
        tool_name: str,
        librechat_user_id: Optional[str],
        librechat_user_email: Optional[str],
        service_account: str,
        execution_time_ms: float,
        status: str,
        result_count: Optional[int] = None,
        error_message: Optional[str] = None,
        request_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """Log tool execution event."""
        event_data = {
            "event_type": "tool_execution",
            "tool_name": tool_name,
            "librechat_user_id": librechat_user_id,
            "librechat_user_email": librechat_user_email,
            "service_account": service_account,
            "execution_time_ms": execution_time_ms,
            "status": status,
            "request_id": request_id or str(uuid.uuid4()),
            **kwargs
        }
        
        if result_count is not None:
            event_data["result_count"] = result_count
            
        if error_message:
            event_data["error_message"] = error_message
            
        await self._queue_event(SourceType.TOOL_EXECUTION, event_data)
    
    async def log_guardrail_violation(
        self,
        violation_type: str,
        tool_name: str,
        librechat_user_id: Optional[str],
        violation_details: Dict[str, Any],
        blocked: bool = True,
        **kwargs
    ) -> None:
        """Log guardrail violation event."""
        event_data = {
            "event_type": "guardrail_violation",
            "violation_type": violation_type,
            "tool_name": tool_name,
            "librechat_user_id": librechat_user_id,
            "blocked": blocked,
            "violation_details": violation_details,
            "request_id": str(uuid.uuid4()),
            **kwargs
        }
        
        await self._queue_event(SourceType.GUARDRAIL_VIOLATION, event_data)
    
    async def log_session_activity(
        self,
        event_type: str,
        librechat_user_id: Optional[str],
        session_id: Optional[str] = None,
        client_info: Optional[str] = None,
        capabilities_granted: Optional[List[str]] = None,
        **kwargs
    ) -> None:
        """Log session activity event."""
        event_data = {
            "event_type": event_type,
            "librechat_user_id": librechat_user_id,
            "session_id": session_id,
            "client_info": client_info,
            **kwargs
        }
        
        if capabilities_granted:
            event_data["capabilities_granted"] = capabilities_granted
            event_data["capability_count"] = len(capabilities_granted)
            
        await self._queue_event(SourceType.SESSION_ACTIVITY, event_data)
    
    async def log_search_query(
        self,
        query: str,
        earliest_time: Optional[str],
        latest_time: Optional[str],
        librechat_user_id: Optional[str],
        result_count: Optional[int] = None,
        search_time_ms: Optional[float] = None,
        index_filter: Optional[str] = None,
        **kwargs
    ) -> None:
        """Log search query event with sanitized query."""
        # Sanitize query (remove potential sensitive data patterns)
        sanitized_query = self._sanitize_query(query)
        
        event_data = {
            "event_type": "search_query",
            "query": sanitized_query,
            "query_length": len(query),
            "earliest_time": earliest_time,
            "latest_time": latest_time,
            "librechat_user_id": librechat_user_id,
            "index_filter": index_filter,
            "request_id": str(uuid.uuid4()),
            **kwargs
        }
        
        if result_count is not None:
            event_data["result_count"] = result_count
            
        if search_time_ms is not None:
            event_data["search_time_ms"] = search_time_ms
            
        await self._queue_event(SourceType.SEARCH_QUERY, event_data)
    
    async def log_system_health(
        self,
        event_type: str,
        service_account: Optional[str] = None,
        response_time_ms: Optional[float] = None,
        error_message: Optional[str] = None,
        **kwargs
    ) -> None:
        """Log system health event."""
        event_data = {
            "event_type": event_type,
            "service_account": service_account,
            **kwargs
        }
        
        if response_time_ms is not None:
            event_data["response_time_ms"] = response_time_ms
            
        if error_message:
            event_data["error_message"] = error_message
            
        await self._queue_event(SourceType.SYSTEM_HEALTH, event_data)
    
    async def _queue_event(self, sourcetype: SourceType, event_data: Dict[str, Any]) -> None:
        """Queue an event for batch processing."""
        if not self._running:
            logger.warning("HEC logger not running, dropping event")
            return
            
        # Add common fields
        event_data.update({
            "timestamp": datetime.utcnow().isoformat(),
            "mcp_version": "1.0.0"
        })
        
        hec_event = HECEvent(
            time=time.time(),
            source=self.default_source,
            sourcetype=sourcetype.value,
            host=self.default_host,
            index=self.default_index,
            event=event_data
        )
        
        self._event_queue.append(hec_event)
        
        # Force flush if batch is full
        if len(self._event_queue) >= self.batch_size:
            await self._flush_events()
    
    async def _flush_loop(self) -> None:
        """Background task to flush events periodically."""
        while self._running:
            try:
                await asyncio.sleep(self.flush_interval)
                if self._event_queue:
                    await self._flush_events()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in HEC flush loop: {e}")
    
    async def _flush_events(self) -> None:
        """Flush queued events to Splunk HEC."""
        if not self._event_queue or not self._client:
            return
            
        events = self._event_queue.copy()
        self._event_queue.clear()
        
        try:
            # Send events individually to HEC collector endpoint
            # HEC doesn't support batch arrays, so we concatenate JSON objects
            payload_lines = [json.dumps(event.to_hec_format()) for event in events]
            payload = "\n".join(payload_lines)
            
            response = await self._client.post(
                f"{self.hec_url}/services/collector",
                content=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                logger.debug(f"Successfully sent {len(events)} events to Splunk HEC")
            else:
                logger.error(f"HEC send failed: {response.status_code} - {response.text}")
                # Re-queue events for retry (simple strategy)
                self._event_queue.extend(events[:10])  # Keep last 10 for retry
                
        except Exception as e:
            logger.error(f"Failed to send events to HEC: {str(e)} - URL: {self.hec_url}/services/collector")
            # Re-queue some events for retry
            self._event_queue.extend(events[:10])
    
    async def _test_connectivity(self) -> None:
        """Test HEC connectivity."""
        if not self._client:
            return
            
        test_event = {
            "time": time.time(),
            "source": self.default_source,
            "sourcetype": SourceType.SYSTEM_HEALTH.value,
            "host": self.default_host,
            "index": self.default_index,
            "event": {
                "event_type": "hec_connectivity_test",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        response = await self._client.post(
            f"{self.hec_url}/services/collector",
            json=test_event
        )
        
        if response.status_code != 200:
            raise Exception(f"HEC connectivity test failed: {response.status_code}")
    
    def _sanitize_query(self, query: str) -> str:
        """Sanitize search query to remove sensitive patterns."""
        if not query:
            return query
            
        # Basic sanitization - replace potential sensitive patterns
        import re
        
        # Replace potential passwords/tokens/keys
        query = re.sub(r'(password|token|key|secret)=\S+', r'\1=***', query, flags=re.IGNORECASE)
        
        # Replace potential IP addresses in certain contexts
        query = re.sub(r'(pwd|pass|auth)=[\d.]+', r'\1=***', query, flags=re.IGNORECASE)
        
        return query