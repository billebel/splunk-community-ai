"""Unified audit system integrating with all MCP components."""

import asyncio
import time
from typing import Dict, Any, Optional, List
from dataclasses import asdict
import logging

from .hec_logger import SplunkHECLogger

# Local definitions for audit compatibility
from dataclasses import dataclass

@dataclass
class ExecutionContext:
    """Execution context for audit logging."""
    tool_name: str
    arguments: Dict[str, Any]
    session_id: Optional[str] = None
    user_id: Optional[str] = None

@dataclass
class ToolResult:
    """Tool execution result for audit logging."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None

logger = logging.getLogger(__name__)


class AuditSystem:
    """Centralized audit system for MCP operations."""
    
    def __init__(self, hec_logger: Optional[SplunkHECLogger] = None):
        self.hec_logger = hec_logger
        self._session_start_times: Dict[str, float] = {}
        
    async def start(self) -> None:
        """Start audit system and HEC logger."""
        if self.hec_logger:
            await self.hec_logger.start()
            await self.log_system_event("audit_system_started")
    
    async def stop(self) -> None:
        """Stop audit system and flush logs."""
        if self.hec_logger:
            await self.log_system_event("audit_system_stopped")
            await self.hec_logger.stop()
    
    async def log_session_start(
        self, 
        context: ExecutionContext,
        client_info: Dict[str, Any],
        capabilities: List[str]
    ) -> None:
        """Log session initialization."""
        session_key = context.session_id or context.librechat_user_id or "anonymous"
        self._session_start_times[session_key] = time.time()
        
        if self.hec_logger:
            await self.hec_logger.log_session_activity(
                event_type="session_start",
                librechat_user_id=context.librechat_user_id,
                librechat_user_email=context.librechat_user_email,
                session_id=context.session_id,
                client_info=client_info.get("name"),
                client_version=client_info.get("version"),
                capabilities_granted=capabilities,
                service_account=context.user,
                client_ip=context.client_ip,
                user_agent=context.user_agent
            )
    
    async def log_tool_execution(
        self,
        tool_name: str,
        params: Dict[str, Any],
        result: ToolResult,
        context: ExecutionContext
    ) -> None:
        """Log tool execution with full context."""
        if not self.hec_logger:
            return
            
        # Extract safe parameter info (avoid sensitive data)
        safe_params = self._extract_safe_params(tool_name, params)
        
        await self.hec_logger.log_tool_execution(
            tool_name=tool_name,
            librechat_user_id=context.librechat_user_id,
            librechat_user_email=context.librechat_user_email,
            service_account=context.user,
            execution_time_ms=result.execution_time_ms or 0,
            status=result.status.value,
            result_count=self._extract_result_count(result),
            error_message=result.error if result.is_error else None,
            request_id=result.request_id,
            session_id=context.session_id,
            client_ip=context.client_ip,
            parameters=safe_params,
            metadata=result.metadata
        )
        
        # Log search queries separately for analysis
        if tool_name in ["search_splunk", "run_saved_search"] and "search_query" in params:
            await self._log_search_query(params, result, context)
    
    async def log_guardrail_violation(
        self,
        violation_type: str,
        tool_name: str,
        params: Dict[str, Any],
        context: ExecutionContext,
        violation_details: Dict[str, Any],
        blocked: bool = True
    ) -> None:
        """Log security guardrail violations."""
        if not self.hec_logger:
            return
            
        await self.hec_logger.log_guardrail_violation(
            violation_type=violation_type,
            tool_name=tool_name,
            librechat_user_id=context.librechat_user_id,
            librechat_user_email=context.librechat_user_email,
            violation_details=violation_details,
            blocked=blocked,
            session_id=context.session_id,
            service_account=context.user,
            client_ip=context.client_ip,
            parameters=self._extract_safe_params(tool_name, params)
        )
    
    async def log_authentication_event(
        self,
        event_type: str,
        service_account: str,
        success: bool,
        response_time_ms: Optional[float] = None,
        capabilities_count: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Log authentication and capability check events."""
        if not self.hec_logger:
            return
            
        await self.hec_logger.log_system_health(
            event_type=event_type,
            service_account=service_account,
            success=success,
            response_time_ms=response_time_ms,
            capabilities_count=capabilities_count,
            error_message=error_message
        )
    
    async def log_system_event(
        self,
        event_type: str,
        **kwargs
    ) -> None:
        """Log general system events."""
        if not self.hec_logger:
            return
            
        await self.hec_logger.log_system_health(
            event_type=event_type,
            **kwargs
        )
    
    async def log_session_end(
        self,
        context: ExecutionContext,
        reason: str = "normal_shutdown"
    ) -> None:
        """Log session termination."""
        if not self.hec_logger:
            return
            
        session_key = context.session_id or context.librechat_user_id or "anonymous"
        session_duration = None
        
        if session_key in self._session_start_times:
            session_duration = time.time() - self._session_start_times[session_key]
            del self._session_start_times[session_key]
        
        await self.hec_logger.log_session_activity(
            event_type="session_end",
            librechat_user_id=context.librechat_user_id,
            session_id=context.session_id,
            reason=reason,
            session_duration_seconds=session_duration
        )
    
    def _extract_safe_params(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract safe parameter info, filtering out sensitive data."""
        safe_params = {}
        
        # Tool-specific parameter extraction
        if tool_name in ["search_splunk", "run_saved_search"]:
            safe_params.update({
                "earliest_time": params.get("earliest_time"),
                "latest_time": params.get("latest_time"),
                "max_results": params.get("max_results"),
                "query_length": len(params.get("search_query", "")),
                "has_index_filter": "index=" in params.get("search_query", "")
            })
        elif tool_name in ["list_indexes", "get_index_details"]:
            safe_params.update({
                "count": params.get("count"),
                "index_name": params.get("index_name")
            })
        elif tool_name in ["list_saved_searches", "get_saved_search_details"]:
            safe_params.update({
                "count": params.get("count"),
                "app": params.get("app"),
                "owner": params.get("owner"),
                "search_name": params.get("search_name")
            })
        else:
            # Generic parameter info
            for key, value in params.items():
                if key.lower() in ["password", "token", "key", "secret", "auth"]:
                    safe_params[key] = "***"
                elif isinstance(value, str) and len(value) > 100:
                    safe_params[f"{key}_length"] = len(value)
                else:
                    safe_params[key] = value
        
        return safe_params
    
    def _extract_result_count(self, result: ToolResult) -> Optional[int]:
        """Extract result count from tool result."""
        if not result.data:
            return None
            
        if isinstance(result.data, list):
            return len(result.data)
        elif isinstance(result.data, dict):
            # Check common count fields
            for field in ["total", "count", "result_count", "entries"]:
                if field in result.data:
                    count = result.data[field]
                    if isinstance(count, int):
                        return count
            
            # Check if data contains a list
            for key, value in result.data.items():
                if isinstance(value, list) and key not in ["metadata", "links"]:
                    return len(value)
        
        return None
    
    async def _log_search_query(
        self,
        params: Dict[str, Any], 
        result: ToolResult,
        context: ExecutionContext
    ) -> None:
        """Log search query details separately for analysis."""
        query = params.get("search_query", "")
        if not query:
            return
            
        await self.hec_logger.log_search_query(
            query=query,
            earliest_time=params.get("earliest_time"),
            latest_time=params.get("latest_time"),
            librechat_user_id=context.librechat_user_id,
            result_count=self._extract_result_count(result),
            search_time_ms=result.execution_time_ms,
            index_filter=self._extract_index_filter(query),
            session_id=context.session_id,
            service_account=context.user
        )
    
    def _extract_index_filter(self, query: str) -> Optional[str]:
        """Extract index filter from search query."""
        import re
        match = re.search(r'index=(\w+)', query, re.IGNORECASE)
        return match.group(1) if match else None