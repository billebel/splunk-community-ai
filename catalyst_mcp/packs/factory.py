"""Universal tool factory that creates FastMCP tools from YAML configurations."""

import logging
import inspect
from typing import Dict, Any, Callable, Optional, List, Union
from fastmcp import FastMCP
from catalyst_pack_schemas import Pack, ToolDefinition, ParameterDefinition
from .adapters import AdapterFactory
from .adapters.api_adapter import APIAdapter
from .adapters.database_adapter import DatabaseAdapter
from .adapters.queue_adapter import MessageQueueAdapter
from .adapters.file_adapter import FileSystemAdapter
from .adapters.ssh_adapter import SSHAdapter


logger = logging.getLogger(__name__)


class UniversalToolFactory:
    """Factory for creating FastMCP tools from knowledge pack configurations."""
    
    def __init__(self, mcp_instance: FastMCP):
        """Initialize tool factory.
        
        Args:
            mcp_instance: FastMCP server instance to register tools with
        """
        self.mcp = mcp_instance
        self.registered_tools: Dict[str, str] = {}  # tool_name -> pack_name
        self.pack_adapters: Dict[str, Union[APIAdapter, DatabaseAdapter, MessageQueueAdapter, FileSystemAdapter, SSHAdapter]] = {}  # pack_name -> adapter
    
    def register_pack_tools(self, pack_name: str, pack: Pack) -> List[str]:
        """Register all tools from a knowledge pack.
        
        Args:
            pack_name: Name of the pack
            pack: Pack configuration
            
        Returns:
            List of registered tool names
        """
        logger.info(f"Registering tools from pack '{pack_name}' (connection type: {pack.connection.type})")
        
        # Create appropriate adapter for this pack
        adapter = AdapterFactory.create_adapter(pack)
        self.pack_adapters[pack_name] = adapter
        
        registered = []
        
        # Register tools
        for tool_name, tool_def in pack.tools.items():
            full_tool_name = f"{pack_name}_{tool_name}"
            
            try:
                # Create FastMCP tool function
                tool_func = self._create_tool_function(tool_def, adapter, pack_name)
                
                # Register with FastMCP
                self.mcp.tool(name=full_tool_name, description=tool_def.description)(tool_func)
                
                # Track registration
                self.registered_tools[full_tool_name] = pack_name
                registered.append(full_tool_name)
                
                logger.debug(f"Registered tool: {full_tool_name}")
                
            except Exception as e:
                logger.error(f"Failed to register tool {full_tool_name}: {e}")
                import traceback
                logger.error(f"Stack trace: {traceback.format_exc()}")
        
        # Register prompts as tools
        for prompt_name, prompt_def in pack.prompts.items():
            full_prompt_name = f"{pack_name}_{prompt_name}"
            
            try:
                # Create FastMCP prompt tool function
                prompt_func = self._create_prompt_function(prompt_def, pack_name)
                
                # Register with FastMCP
                self.mcp.tool(name=full_prompt_name, description=prompt_def.description)(prompt_func)
                
                # Track registration
                self.registered_tools[full_prompt_name] = pack_name
                registered.append(full_prompt_name)
                
                logger.debug(f"Registered prompt tool: {full_prompt_name}")
                
            except Exception as e:
                logger.error(f"Failed to register prompt {full_prompt_name}: {e}")
                import traceback
                logger.error(f"Stack trace: {traceback.format_exc()}")
        
        logger.info(f"Successfully registered {len(registered)} tools from pack '{pack_name}'")
        return registered
    
    def unregister_pack_tools(self, pack_name: str) -> List[str]:
        """Unregister all tools from a specific pack.
        
        Args:
            pack_name: Name of pack whose tools to unregister
            
        Returns:
            List of unregistered tool names
        """
        logger.info(f"Unregistering tools from pack '{pack_name}'")
        
        unregistered = []
        tools_to_remove = []
        
        # Find all tools from this pack
        for tool_name, tool_pack in self.registered_tools.items():
            if tool_pack == pack_name:
                tools_to_remove.append(tool_name)
        
        # Remove tools
        for tool_name in tools_to_remove:
            try:
                # FastMCP doesn't have direct unregister, but we can track it
                del self.registered_tools[tool_name]
                unregistered.append(tool_name)
                logger.debug(f"Unregistered tool: {tool_name}")
            except Exception as e:
                logger.error(f"Failed to unregister tool {tool_name}: {e}")
        
        # Remove adapter
        if pack_name in self.pack_adapters:
            del self.pack_adapters[pack_name]
        
        logger.info(f"Unregistered {len(unregistered)} tools from pack '{pack_name}'")
        return unregistered
    
    def _create_tool_function(self, tool_def: ToolDefinition, adapter: Union[APIAdapter, DatabaseAdapter, MessageQueueAdapter, FileSystemAdapter, SSHAdapter], pack_name: str) -> Callable:
        """Create a FastMCP tool function from tool definition.
        
        Args:
            tool_def: Tool definition from YAML
            adapter: API adapter for executing the tool
            pack_name: Name of the pack (for logging)
            
        Returns:
            Async function compatible with FastMCP
        """
        # Create a simpler function that accepts all parameters as optional keyword args
        # This avoids the complex dynamic signature generation that's causing issues
        
        # Build parameter documentation string
        param_docs = []
        for param in tool_def.parameters:
            required_str = " (required)" if param.required else " (optional)"
            param_docs.append(f"    {param.name}: {param.description}{required_str}")
        
        param_doc_string = "\n".join(param_docs) if param_docs else "    No parameters"
        
        # Create the actual tool function with explicit parameters
        # Build parameter list for function signature
        param_list = []
        for param in tool_def.parameters:
            if param.required:
                param_list.append(f"{param.name}: str")
            else:
                param_list.append(f"{param.name}: str = None")
        
        # Create function signature string
        if param_list:
            signature = f"async def universal_tool({', '.join(param_list)}) -> Dict[str, Any]:"
        else:
            signature = "async def universal_tool() -> Dict[str, Any]:"
        
        # Create function body
        docstring = f'''"""Universal tool function that executes YAML-defined tools.
            
Parameters:
{param_doc_string}
"""'''
        
        function_code = f'''
{signature}
    {docstring}
    
    # Collect all parameters into kwargs
    kwargs = {{}}
{chr(10).join([f'    if {param.name} is not None: kwargs["{param.name}"] = {param.name}' for param in tool_def.parameters])}
    
    try:
        logger.debug(f"Executing tool {{tool_def.name}} from pack {{pack_name}} with params: {{kwargs}}")
        
        # Filter out None values and validate parameters
        clean_params = self._validate_and_clean_parameters(kwargs, tool_def.parameters)
        
        # Execute tool via adapter
        result = await adapter.execute_tool(tool_def, clean_params)
        
        # Log execution result
        if result.get("error"):
            logger.warning(f"Tool {{tool_def.name}} execution failed: {{result.get('message')}}")
        else:
            logger.debug(f"Tool {{tool_def.name}} executed successfully in {{result.get('execution_time', 0):.2f}}s")
        
        return result
        
    except Exception as e:
        logger.error(f"Tool {{tool_def.name}} execution exception: {{e}}")
        return {{
            "error": True,
            "message": f"Tool execution failed: {{str(e)}}",
            "tool": tool_def.name
        }}
'''
        
        # Execute the dynamic function creation with proper variable references
        global_vars = {
            'Dict': Dict, 
            'Any': Any,
            'logger': logger,
            'tool_def': tool_def,
            'pack_name': pack_name,
            'adapter': adapter,
            'self': self
        }
        local_vars = {}
        
        try:
            exec(function_code, global_vars, local_vars)
            universal_tool = local_vars['universal_tool']
            
            # Set function metadata for FastMCP
            universal_tool.__name__ = tool_def.name
            universal_tool.__doc__ = f"{tool_def.description}\n\nParameters:\n{param_doc_string}"
            
        except Exception as e:
            logger.error(f"Failed to create dynamic function for {tool_def.name}: {e}")
            logger.error(f"Generated code:\n{function_code}")
            raise
        
        return universal_tool
    
    def _create_prompt_function(self, prompt_def, pack_name: str) -> Callable:
        """Create a FastMCP tool function from prompt definition.
        
        Args:
            prompt_def: Prompt definition from YAML
            pack_name: Name of the pack (for logging)
            
        Returns:
            Async function compatible with FastMCP
        """
        # Build parameter documentation string
        param_docs = []
        for param in getattr(prompt_def, 'arguments', []):
            required_str = " (required)" if getattr(param, 'required', False) else " (optional)"
            param_docs.append(f"    {param.name}: {getattr(param, 'description', 'No description')}{required_str}")
        
        param_doc_string = "\n".join(param_docs) if param_docs else "    No parameters"
        
        # Build parameter list for function signature
        param_list = []
        for param in getattr(prompt_def, 'arguments', []):
            if getattr(param, 'required', False):
                param_list.append(f"{param.name}: str")
            else:
                param_list.append(f"{param.name}: str = None")
        
        # Create function signature string
        if param_list:
            signature = f"async def prompt_tool({', '.join(param_list)}) -> Dict[str, Any]:"
        else:
            signature = "async def prompt_tool() -> Dict[str, Any]:"
        
        # Create function body
        docstring = f'''"""Prompt tool function that generates contextualized prompts.
            
Parameters:
{param_doc_string}
"""'''
        
        function_code = f'''
{signature}
    {docstring}
    
    # Collect all parameters into kwargs
    kwargs = {{}}
{chr(10).join([f'    if {param.name} is not None: kwargs["{param.name}"] = {param.name}' for param in getattr(prompt_def, 'arguments', [])])}
    
    try:
        logger.debug(f"Executing prompt {{prompt_def.name}} from pack {{pack_name}} with params: {{kwargs}}")
        
        # Substitute variables in the template
        template = prompt_def.template
        for key, value in kwargs.items():
            placeholder = "{{" + key + "}}"
            template = template.replace(placeholder, str(value) if value is not None else "")
        
        # Return the rendered prompt with metadata
        return {{
            "error": False,
            "prompt_name": prompt_def.name,
            "rendered_template": template,
            "suggested_tools": getattr(prompt_def, 'suggested_tools', []),
            "description": prompt_def.description,
            "parameters_used": kwargs
        }}
        
    except Exception as e:
        logger.error(f"Prompt {{prompt_def.name}} execution exception: {{e}}")
        return {{
            "error": True,
            "message": f"Prompt execution failed: {{str(e)}}",
            "prompt_name": prompt_def.name
        }}
'''
        
        # Execute the dynamic function creation
        global_vars = {
            'Dict': Dict, 
            'Any': Any,
            'logger': logger,
            'prompt_def': prompt_def,
            'pack_name': pack_name,
            'getattr': getattr
        }
        local_vars = {}
        
        try:
            exec(function_code, global_vars, local_vars)
            prompt_tool = local_vars['prompt_tool']
            
            # Set function metadata for FastMCP
            prompt_tool.__name__ = prompt_def.name
            prompt_tool.__doc__ = f"{prompt_def.description}\n\nParameters:\n{param_doc_string}"
            
        except Exception as e:
            logger.error(f"Failed to create dynamic prompt function for {prompt_def.name}: {e}")
            logger.error(f"Generated code:\n{function_code}")
            raise
        
        return prompt_tool
    
    def _build_function_parameters(self, parameters: List[ParameterDefinition]) -> Dict[str, Any]:
        """Build function parameter defaults from parameter definitions.
        
        Args:
            parameters: List of parameter definitions
            
        Returns:
            Dictionary mapping parameter names to default values
        """
        params = {}
        for param in parameters:
            if param.default is not None:
                params[param.name] = param.default
            elif not param.required:
                # Set sensible defaults based on type
                if param.type == "boolean":
                    params[param.name] = False
                elif param.type == "integer":
                    params[param.name] = 0
                elif param.type == "number":
                    params[param.name] = 0.0
                else:
                    params[param.name] = None
        
        return params
    
    def _set_function_signature(self, func: Callable, parameters: List[ParameterDefinition]) -> None:
        """Dynamically set function signature for FastMCP compatibility.
        
        Args:
            func: Function to modify
            parameters: Parameter definitions
        """
        try:
            # Build parameter list for signature
            sig_params = []
            
            for param in parameters:
                # Convert YAML types to Python types
                param_type = self._yaml_type_to_python(param.type)
                
                # Create parameter with proper default
                if param.required:
                    sig_param = inspect.Parameter(
                        name=param.name,
                        kind=inspect.Parameter.KEYWORD_ONLY,
                        annotation=param_type
                    )
                else:
                    default_val = param.default
                    if default_val is None:
                        if param.type == "boolean":
                            default_val = False
                        elif param.type == "integer":
                            default_val = 0
                        elif param.type == "number":
                            default_val = 0.0
                        else:
                            default_val = None
                    
                    sig_param = inspect.Parameter(
                        name=param.name,
                        kind=inspect.Parameter.KEYWORD_ONLY,
                        annotation=param_type,
                        default=default_val
                    )
                
                sig_params.append(sig_param)
            
            # Add return type annotation
            return_annotation = Dict[str, Any]
            
            # Create new signature
            new_signature = inspect.Signature(
                parameters=sig_params,
                return_annotation=return_annotation
            )
            
            # Set signature on function
            func.__signature__ = new_signature
            
        except Exception as e:
            logger.warning(f"Failed to set dynamic function signature: {e}")
            # Create a simple fallback signature that accepts **kwargs
            fallback_signature = inspect.Signature(
                parameters=[inspect.Parameter(
                    name="kwargs", 
                    kind=inspect.Parameter.VAR_KEYWORD
                )],
                return_annotation=Dict[str, Any]
            )
            func.__signature__ = fallback_signature
    
    def _yaml_type_to_python(self, yaml_type: str) -> type:
        """Convert YAML parameter type to Python type.
        
        Args:
            yaml_type: YAML type string
            
        Returns:
            Python type
        """
        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        return type_mapping.get(yaml_type, str)
    
    def _validate_and_clean_parameters(self, params: Dict[str, Any], 
                                     param_defs: List[ParameterDefinition]) -> Dict[str, Any]:
        """Validate and clean input parameters.
        
        Args:
            params: Input parameters
            param_defs: Parameter definitions for validation
            
        Returns:
            Cleaned and validated parameters
        """
        clean_params = {}
        param_map = {p.name: p for p in param_defs}
        
        for name, value in params.items():
            if name not in param_map:
                continue  # Skip unknown parameters
            
            param_def = param_map[name]
            
            # Skip None values for optional parameters
            if value is None and not param_def.required:
                continue
            
            # Validate required parameters
            if param_def.required and (value is None or value == ""):
                raise ValueError(f"Required parameter '{name}' is missing or empty")
            
            # Type conversion and validation
            if value is not None:
                try:
                    if param_def.type == "integer":
                        value = int(value)
                        if param_def.min_value is not None and value < param_def.min_value:
                            raise ValueError(f"Parameter '{name}' below minimum value {param_def.min_value}")
                        if param_def.max_value is not None and value > param_def.max_value:
                            raise ValueError(f"Parameter '{name}' above maximum value {param_def.max_value}")
                    
                    elif param_def.type == "number":
                        value = float(value)
                        if param_def.min_value is not None and value < param_def.min_value:
                            raise ValueError(f"Parameter '{name}' below minimum value {param_def.min_value}")
                        if param_def.max_value is not None and value > param_def.max_value:
                            raise ValueError(f"Parameter '{name}' above maximum value {param_def.max_value}")
                    
                    elif param_def.type == "boolean":
                        if isinstance(value, str):
                            value = value.lower() in ("true", "1", "yes", "on")
                        else:
                            value = bool(value)
                    
                    elif param_def.type == "string":
                        value = str(value)
                        if param_def.enum and value not in param_def.enum:
                            raise ValueError(f"Parameter '{name}' must be one of: {param_def.enum}")
                    
                    clean_params[name] = value
                    
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Invalid value for parameter '{name}': {e}")
        
        return clean_params
    
    def get_registered_tools(self) -> Dict[str, str]:
        """Get mapping of registered tool names to pack names.
        
        Returns:
            Dictionary mapping tool names to pack names
        """
        return self.registered_tools.copy()
    
    def get_tool_count_by_pack(self) -> Dict[str, int]:
        """Get count of registered tools by pack.
        
        Returns:
            Dictionary mapping pack names to tool counts
        """
        pack_counts = {}
        for pack_name in self.registered_tools.values():
            pack_counts[pack_name] = pack_counts.get(pack_name, 0) + 1
        return pack_counts