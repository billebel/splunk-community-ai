"""API adapters for executing knowledge pack tools."""

import os
import re
import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
import httpx
from ..models import Pack, ToolDefinition, AuthMethod, ConnectionConfig


logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """Response from API call."""
    status_code: int
    data: Dict[str, Any]
    headers: Dict[str, str]
    execution_time: float


class VariableSubstitutor:
    """Handles variable substitution in pack configurations."""
    
    @staticmethod
    def substitute(template: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in template string.
        
        Args:
            template: Template string with {VARIABLE} patterns
            variables: Dictionary of variable values
            
        Returns:
            String with variables substituted
        """
        if not template:
            return template
            
        # Handle environment variables
        def replace_env_var(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))  # Return original if not found
        
        # First substitute environment variables
        result = re.sub(r'\{([A-Z_][A-Z0-9_]*)\}', replace_env_var, template)
        
        # Then substitute provided variables
        for key, value in variables.items():
            pattern = f"{{{key}}}"
            result = result.replace(pattern, str(value) if value is not None else "")
        
        return result
    
    @staticmethod 
    def substitute_dict(template_dict: Dict[str, str], variables: Dict[str, Any]) -> Dict[str, str]:
        """Substitute variables in dictionary values.
        
        Args:
            template_dict: Dictionary with template strings as values
            variables: Variables for substitution
            
        Returns:
            Dictionary with substituted values, excluding empty values
        """
        result = {}
        for key, template in template_dict.items():
            if isinstance(template, str):
                substituted = VariableSubstitutor.substitute(template, variables)
                # Only include parameter if it has a value and doesn't contain unresolved variables
                if substituted and not ('{' in substituted and '}' in substituted):
                    result[key] = substituted
            else:
                result[key] = template
        return result


class AuthenticationHandler:
    """Handles different authentication methods."""
    
    @staticmethod
    def prepare_auth(connection: ConnectionConfig) -> Dict[str, Any]:
        """Prepare authentication for HTTP client.
        
        Args:
            connection: Connection configuration
            
        Returns:
            Dictionary with auth parameters for httpx
        """
        if not connection.auth:
            return {}
        
        auth_method = connection.auth.method
        auth_config = connection.auth.config
        
        # Debug: Log the actual auth method type and value (using warning to ensure visibility)
        logger.warning(f"DEBUG: Auth method type: {type(auth_method)}, value: {auth_method}, repr: {repr(auth_method)}")
        
        # Handle both string and enum values for auth method
        if auth_method == AuthMethod.BASIC or auth_method == "basic":
            username = VariableSubstitutor.substitute(auth_config.get('username', ''), {})
            password = VariableSubstitutor.substitute(auth_config.get('password', ''), {})
            logger.debug(f"Preparing basic auth with username: {username[:3]}*** and password: {'*' * len(password) if password else 'EMPTY'}")
            return {'auth': (username, password)}
        
        elif auth_method == AuthMethod.BEARER or auth_method == "bearer":
            token = VariableSubstitutor.substitute(auth_config.get('token', ''), {})
            return {'headers': {'Authorization': f'Bearer {token}'}}
        
        elif auth_method == AuthMethod.API_KEY or auth_method == "api_key":
            key = VariableSubstitutor.substitute(auth_config.get('key', ''), {})
            header = auth_config.get('header', 'X-API-Key')
            return {'headers': {header: key}}
        
        else:
            logger.warning(f"Unsupported auth method: {auth_method} (type: {type(auth_method)}, repr: {repr(auth_method)})")
            # Try a fallback for basic auth if method name contains 'basic'
            if str(auth_method).lower() == 'basic' or 'basic' in str(auth_method).lower():
                username = VariableSubstitutor.substitute(auth_config.get('username', ''), {})
                password = VariableSubstitutor.substitute(auth_config.get('password', ''), {})
                logger.warning(f"Fallback: Using basic auth with username: {username[:3]}*** and password: {'*' * len(password) if password else 'EMPTY'}")
                return {'auth': (username, password)}
            return {}


class ResponseTransformer:
    """Handles response transformation using different engines."""
    
    def __init__(self):
        self._jq_available = self._check_jq_available()
    
    def _check_jq_available(self) -> bool:
        """Check if jq transformation is available."""
        try:
            import jq
            return True
        except ImportError:
            logger.warning("jq library not available, jq transforms will be disabled")
            return False
    
    def transform(self, data: Dict[str, Any], transform_config, variables: Dict[str, Any] = None) -> Any:
        """Transform response data using specified engine.
        
        Args:
            data: Raw response data
            transform_config: Transform configuration
            variables: Variables for substitution in transform
            
        Returns:
            Transformed data
        """
        if not transform_config:
            return data
        
        variables = variables or {}
        
        if transform_config.type.value == "jq":
            return self._transform_jq(data, transform_config.expression, variables)
        elif transform_config.type.value == "template":
            return self._transform_template(data, transform_config.expression, variables)
        else:
            logger.warning(f"Unsupported transform engine: {transform_config.type}")
            return data
    
    def _transform_jq(self, data: Dict[str, Any], expression: str, variables: Dict[str, Any]) -> Any:
        """Transform using jq expression."""
        if not self._jq_available:
            logger.warning("jq transform requested but jq not available, returning raw data")
            return data
        
        try:
            import jq
            
            # Substitute variables in jq expression
            expression = VariableSubstitutor.substitute(expression, variables)
            
            # Compile and apply jq expression
            compiled = jq.compile(expression)
            result = compiled.input(data).all()
            
            # Return single result if only one item
            if isinstance(result, list) and len(result) == 1:
                return result[0]
            
            return result
            
        except Exception as e:
            logger.error(f"jq transform failed: {e}")
            return data
    
    def _transform_template(self, data: Dict[str, Any], template: str, variables: Dict[str, Any]) -> str:
        """Transform using template substitution."""
        try:
            from jinja2 import Template
            
            # Combine data and variables for template context
            context = {**data, **variables}
            
            template_obj = Template(template)
            return template_obj.render(**context)
            
        except Exception as e:
            logger.error(f"Template transform failed: {e}")
            return str(data)


class APIAdapter:
    """Universal API adapter for executing pack tools."""
    
    def __init__(self, pack: Pack):
        """Initialize adapter for a specific pack.
        
        Args:
            pack: Pack configuration
        """
        self.pack = pack
        self.connection = pack.connection
        self.transformer = ResponseTransformer()
        self._auth_retry_used = False  # Track if we've already retried auth
        
        # Prepare base URL with variable substitution
        self.base_url = VariableSubstitutor.substitute(self.connection.base_url, {})
        
        # Prepare authentication
        self.auth_params = AuthenticationHandler.prepare_auth(self.connection)
    
    def _reload_auth(self) -> None:
        """Reload authentication parameters from fresh environment variables."""
        logger.info("Reloading authentication parameters due to potential stale environment variables")
        
        # Log current auth params before reload
        logger.debug(f"Current auth params before reload: {self.auth_params}")
        
        # Force re-reading of environment variables by recreating the connection auth
        old_auth = self.auth_params
        self.auth_params = AuthenticationHandler.prepare_auth(self.connection)
        
        # Log new auth params after reload
        logger.debug(f"New auth params after reload: {self.auth_params}")
        logger.info(f"Auth params changed: {old_auth != self.auth_params}")
    
    async def execute_tool(self, tool: ToolDefinition, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with given parameters.
        
        Args:
            tool: Tool definition
            parameters: Tool parameters
            
        Returns:
            Tool execution result
        """
        try:
            # Handle multi-step execution if defined
            if tool.execution_steps:
                result = await self._execute_multi_step(tool, parameters)
            else:
                result = await self._execute_single_step(tool, parameters)
            
            # Debug logging for result
            logger.debug(f"Tool {tool.name} execution result: error={result.get('error')}, status_code={result.get('status_code')}, auth_retry_used={self._auth_retry_used}")
            
            # Check for authentication errors and retry once with fresh auth
            if (result.get("error") and 
                result.get("status_code") == 401 and 
                not self._auth_retry_used):
                
                logger.warning(f"Authentication failed for {tool.name}, retrying with fresh credentials...")
                self._auth_retry_used = True
                self._reload_auth()
                
                # Retry the execution
                logger.info(f"Retrying {tool.name} execution after auth reload...")
                if tool.execution_steps:
                    result = await self._execute_multi_step(tool, parameters)
                else:
                    result = await self._execute_single_step(tool, parameters)
                
                if not result.get("error"):
                    logger.info(f"Authentication retry successful for {tool.name}")
                else:
                    logger.warning(f"Authentication retry failed for {tool.name}: {result.get('message')}")
            
            # Reset retry flag on successful execution for future requests
            if not result.get("error"):
                self._auth_retry_used = False
            
            return result
                
        except Exception as e:
            logger.error(f"Tool execution failed for {tool.name}: {e}")
            return {
                "error": True,
                "message": str(e),
                "tool": tool.name
            }
    
    async def _execute_single_step(self, tool: ToolDefinition, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single-step tool.
        
        Args:
            tool: Tool definition
            parameters: Tool parameters
            
        Returns:
            Execution result
        """
        # Prepare request components
        url = self.base_url + VariableSubstitutor.substitute(tool.endpoint, parameters)
        
        query_params = VariableSubstitutor.substitute_dict(tool.query_params, parameters)
        form_data = VariableSubstitutor.substitute_dict(tool.form_data, parameters)
        headers = VariableSubstitutor.substitute_dict(tool.headers, parameters)
        
        # Make HTTP request
        response = await self._make_request(
            method=tool.method,
            url=url,
            params=query_params,
            data=form_data if form_data else None,
            headers=headers
        )
        
        # Handle API errors
        if response.status_code >= 400:
            error_message = self._get_error_message(response.status_code, response.data)
            return {
                "error": True,
                "status_code": response.status_code,
                "message": error_message,
                "tool": tool.name
            }
        
        # Transform response if configured
        result_data = response.data
        if tool.transform:
            result_data = self.transformer.transform(result_data, tool.transform, parameters)
        
        return {
            "error": False,
            "data": result_data,
            "execution_time": response.execution_time,
            "tool": tool.name
        }
    
    async def _execute_multi_step(self, tool: ToolDefinition, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a multi-step tool.
        
        Args:
            tool: Tool definition with execution steps
            parameters: Tool parameters
            
        Returns:
            Execution result
        """
        context = parameters.copy()
        step_results = []
        
        for step in tool.execution_steps:
            # Prepare step request
            url = self.base_url + VariableSubstitutor.substitute(step.endpoint, context)
            query_params = VariableSubstitutor.substitute_dict(step.query_params, context)
            form_data = VariableSubstitutor.substitute_dict(step.form_data, context)
            
            # Execute step
            response = await self._make_request(
                method=step.method,
                url=url,
                params=query_params,
                data=form_data if form_data else None
            )
            
            if response.status_code >= 400:
                error_message = self._get_error_message(response.status_code, response.data)
                return {
                    "error": True,
                    "status_code": response.status_code,
                    "message": f"Step '{step.name}' failed: {error_message}",
                    "tool": tool.name,
                    "failed_step": step.name
                }
            
            step_results.append(response.data)
            
            # Add response data to context for next step
            if step.response_key and step.response_key in response.data:
                context[step.response_key] = response.data[step.response_key]
            
            # Small delay between steps
            await asyncio.sleep(0.1)
        
        # Use last step result for transformation
        final_data = step_results[-1] if step_results else {}
        
        # Transform final result if configured
        if tool.transform:
            final_data = self.transformer.transform(final_data, tool.transform, parameters)
        
        return {
            "error": False,
            "data": final_data,
            "steps": len(step_results),
            "tool": tool.name
        }
    
    async def _make_request(self, method: str, url: str, params: Dict = None, 
                           data: Dict = None, headers: Dict = None) -> APIResponse:
        """Make HTTP request with authentication and error handling.
        
        Args:
            method: HTTP method
            url: Request URL
            params: Query parameters
            data: Request body data
            headers: Additional headers
            
        Returns:
            APIResponse object
        """
        import time
        start_time = time.time()
        
        # Prepare request parameters
        request_params = {
            "method": method.upper(),
            "url": url,
            "timeout": self.connection.timeout
        }
        
        if params:
            request_params["params"] = params
        
        if data:
            if method.upper() == "POST":
                request_params["data"] = data
        
        # Add authentication
        if "auth" in self.auth_params:
            request_params["auth"] = self.auth_params["auth"]
        
        # Merge headers
        request_headers = {}
        if "headers" in self.auth_params:
            request_headers.update(self.auth_params["headers"])
        if headers:
            request_headers.update(headers)
        if request_headers:
            request_params["headers"] = request_headers
        
        # Handle SSL verification
        if isinstance(self.connection.verify_ssl, str):
            verify_ssl = self.connection.verify_ssl.lower() == "true"
        else:
            verify_ssl = bool(self.connection.verify_ssl)
        
        # Make request with retry logic
        async with httpx.AsyncClient(verify=verify_ssl) as client:
            try:
                response = await client.request(**request_params)
                execution_time = time.time() - start_time
                
                # Try to parse JSON response
                try:
                    data = response.json()
                except:
                    data = {"raw_response": response.text}
                
                return APIResponse(
                    status_code=response.status_code,
                    data=data,
                    headers=dict(response.headers),
                    execution_time=execution_time
                )
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"HTTP request failed: {e}")
                
                return APIResponse(
                    status_code=500,
                    data={"error": f"Request failed: {str(e)}"},
                    headers={},
                    execution_time=execution_time
                )
    
    def _get_error_message(self, status_code: int, response_data: Dict[str, Any]) -> str:
        """Get user-friendly error message.
        
        Args:
            status_code: HTTP status code
            response_data: Response data
            
        Returns:
            Error message string
        """
        # Check pack-specific error mapping
        status_str = str(status_code)
        if status_str in self.pack.error_mapping:
            return self.pack.error_mapping[status_str]
        
        # Extract error from response
        if isinstance(response_data, dict):
            if "error" in response_data:
                return str(response_data["error"])
            elif "message" in response_data:
                return str(response_data["message"])
        
        # Default error messages
        default_errors = {
            400: "Bad request - check parameters",
            401: "Authentication failed",
            403: "Access forbidden - insufficient permissions", 
            404: "Resource not found",
            429: "Rate limit exceeded",
            500: "Internal server error",
            502: "Bad gateway",
            503: "Service unavailable"
        }
        
        return default_errors.get(status_code, f"HTTP error {status_code}")