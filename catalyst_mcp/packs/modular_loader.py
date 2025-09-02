"""
Enhanced pack loader for modular knowledge pack structure.
Supports loading packs split across multiple YAML files.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
from catalyst_pack_schemas import Pack, PackMetadata, ToolDefinition, AuthConfig, ConnectionConfig, PackValidationError, ParameterDefinition, TransformConfig, TransformEngine, ExecutionStep, ToolType, PromptDefinition, ResourceDefinition


logger = logging.getLogger(__name__)


class ModularPackLoader:
    """Enhanced pack loader that supports modular file structures."""
    
    def __init__(self, packs_directory: str = "knowledge-packs"):
        """Initialize modular pack loader.
        
        Args:
            packs_directory: Directory containing pack subdirectories
        """
        self.packs_directory = Path(packs_directory)
        self.loaded_packs: Dict[str, Pack] = {}
        
    def discover_packs(self) -> List[str]:
        """Discover available pack names in the packs directory.
        
        Returns:
            List of pack names (directory names containing pack.yaml)
        """
        if not self.packs_directory.exists():
            logger.warning(f"Packs directory not found: {self.packs_directory}")
            return []
        
        pack_names = []
        for item in self.packs_directory.iterdir():
            if item.is_dir():
                # Skip .example directories
                if item.name.endswith('.example'):
                    logger.debug(f"Skipping example pack: {item.name}")
                    continue
                    
                pack_yaml = item / "pack.yaml"
                if pack_yaml.exists():
                    pack_names.append(item.name)
                else:
                    logger.debug(f"Directory {item.name} missing pack.yaml, skipping")
        
        logger.info(f"Discovered {len(pack_names)} packs: {pack_names}")
        return pack_names
    
    def load_pack(self, pack_name: str, force_reload: bool = False) -> Optional[Pack]:
        """Load a modular knowledge pack.
        
        Args:
            pack_name: Name of the pack to load
            force_reload: Force reload even if already cached
            
        Returns:
            Loaded Pack object or None if loading failed
        """
        if pack_name in self.loaded_packs and not force_reload:
            logger.debug(f"Returning cached pack: {pack_name}")
            return self.loaded_packs[pack_name]
        
        pack_dir = self.packs_directory / pack_name
        pack_yaml = pack_dir / "pack.yaml"
        
        if not pack_yaml.exists():
            logger.error(f"Pack YAML not found: {pack_yaml}")
            return None
            
        try:
            logger.info(f"Loading modular pack: {pack_name}")
            
            # Load the main pack configuration
            with open(pack_yaml, 'r', encoding='utf-8') as f:
                main_config = yaml.safe_load(f)
            
            # Load modular components
            pack = self._load_modular_pack(pack_dir, main_config)
            
            # Validate the loaded pack
            self._validate_pack(pack, pack_name)
            
            # Cache the loaded pack
            self.loaded_packs[pack_name] = pack
            
            tool_count = len(pack.tools)
            prompt_count = len(pack.prompts)
            resource_count = len(pack.resources)
            
            logger.info(f"Successfully loaded modular pack '{pack.metadata.name}' v{pack.metadata.version}")
            logger.info(f"  Tools: {tool_count}, Prompts: {prompt_count}, Resources: {resource_count}")
            
            return pack
            
        except Exception as e:
            logger.error(f"Failed to load modular pack {pack_name}: {e}")
            import traceback
            logger.debug(f"Stack trace: {traceback.format_exc()}")
            return None
    
    def _load_modular_pack(self, pack_dir: Path, main_config: Dict[str, Any]) -> Pack:
        """Load a pack from modular structure.
        
        Args:
            pack_dir: Pack directory path
            main_config: Main pack configuration from pack.yaml
            
        Returns:
            Complete Pack object
        """
        # Parse metadata and connection from main config
        pack = Pack.from_dict(main_config)
        
        # Load modular components based on structure definition
        structure = main_config.get('structure', {})
        
        # Load tools from multiple files
        if 'tools' in structure:
            for tool_file in structure['tools']:
                tool_path = pack_dir / tool_file
                if tool_path.exists():
                    tools = self._load_tools_file(tool_path)
                    pack.tools.update(tools)
                else:
                    logger.warning(f"Tool file not found: {tool_path}")
        
        # Load prompts from multiple files  
        if 'prompts' in structure:
            for prompt_file in structure['prompts']:
                prompt_path = pack_dir / prompt_file
                if prompt_path.exists():
                    prompts = self._load_prompts_file(prompt_path)
                    pack.prompts.update(prompts)
                else:
                    logger.warning(f"Prompt file not found: {prompt_path}")
        
        # Load resources from multiple files
        if 'resources' in structure:
            for resource_file in structure['resources']:
                resource_path = pack_dir / resource_file
                if resource_path.exists():
                    resources = self._load_resources_file(resource_path)
                    pack.resources.update(resources)
                else:
                    logger.warning(f"Resource file not found: {resource_path}")
        
        return pack
    
    def _load_tools_file(self, tool_file_path: Path) -> Dict[str, ToolDefinition]:
        """Load tools from a YAML file.
        
        Args:
            tool_file_path: Path to tools YAML file
            
        Returns:
            Dictionary of tool definitions
        """
        logger.debug(f"Loading tools from {tool_file_path}")
        
        with open(tool_file_path, 'r', encoding='utf-8') as f:
            tool_data = yaml.safe_load(f)
        
        if not tool_data or 'tools' not in tool_data:
            logger.warning(f"No tools found in {tool_file_path}")
            return {}
        
        tools = {}
        
        for tool_name, tool_dict in tool_data['tools'].items():
            try:
                # Parse parameters
                parameters = []
                for param_dict in tool_dict.get('parameters', []):
                    # ParameterDefinition now imported at top
                    param = ParameterDefinition(
                        name=param_dict['name'],
                        type=param_dict['type'],
                        required=param_dict.get('required', False),
                        default=param_dict.get('default'),
                        description=param_dict.get('description', ''),
                        enum=param_dict.get('enum', []),
                        min_value=param_dict.get('min_value'),
                        max_value=param_dict.get('max_value')
                    )
                    parameters.append(param)
                
                # Parse transform config with enhanced support
                transform = None
                if 'transform' in tool_dict:
                    transform_dict = tool_dict['transform']
                    # TransformConfig, TransformEngine now imported at top
                    transform = TransformConfig(
                        type=TransformEngine(transform_dict['type']),
                        expression=transform_dict.get('expression'),
                        code=transform_dict.get('code'),
                        template=transform_dict.get('template'),
                        file=transform_dict.get('file'),
                        function=transform_dict.get('function'),
                        timeout=transform_dict.get('timeout', 30),
                        sandbox=transform_dict.get('sandbox', True)
                    )
                
                # Parse execution steps
                execution_steps = []
                for step_dict in tool_dict.get('execution_steps', []):
                    # ExecutionStep now imported at top
                    step = ExecutionStep(
                        name=step_dict['name'],
                        method=step_dict['method'],
                        endpoint=step_dict['endpoint'],
                        query_params=step_dict.get('query_params', {}),
                        form_data=step_dict.get('form_data', {}),
                        response_key=step_dict.get('response_key')
                    )
                    execution_steps.append(step)
                
                # Create tool definition
                # ToolType now imported at top
                tool = ToolDefinition(
                    name=tool_name,
                    type=ToolType(tool_dict['type']),
                    description=tool_dict['description'],
                    endpoint=tool_dict['endpoint'],
                    method=tool_dict.get('method', 'GET'),
                    parameters=parameters,
                    query_params=tool_dict.get('query_params', {}),
                    form_data=tool_dict.get('form_data', {}),
                    headers=tool_dict.get('headers', {}),
                    transform=transform,
                    execution_steps=execution_steps
                )
                
                tools[tool_name] = tool
                logger.debug(f"Loaded tool: {tool_name}")
                
            except Exception as e:
                logger.error(f"Failed to parse tool {tool_name} from {tool_file_path}: {e}")
        
        return tools
    
    def _load_prompts_file(self, prompt_file_path: Path) -> Dict[str, Any]:
        """Load prompts from a YAML file.
        
        Args:
            prompt_file_path: Path to prompts YAML file
            
        Returns:
            Dictionary of prompt definitions
        """
        logger.debug(f"Loading prompts from {prompt_file_path}")
        
        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            prompt_data = yaml.safe_load(f)
        
        if not prompt_data or 'prompts' not in prompt_data:
            logger.warning(f"No prompts found in {prompt_file_path}")
            return {}
        
        prompts = {}
        
        for prompt_name, prompt_dict in prompt_data['prompts'].items():
            try:
                # PromptDefinition, ParameterDefinition now imported at top
                
                # Parse arguments
                arguments = []
                for arg_dict in prompt_dict.get('arguments', []):
                    arg = ParameterDefinition(
                        name=arg_dict['name'],
                        type=arg_dict['type'],
                        required=arg_dict.get('required', False),
                        default=arg_dict.get('default'),
                        description=arg_dict.get('description', ''),
                        enum=arg_dict.get('enum', [])
                    )
                    arguments.append(arg)
                
                prompt = PromptDefinition(
                    name=prompt_name,
                    description=prompt_dict['description'],
                    template=prompt_dict['template'],
                    suggested_tools=prompt_dict.get('suggested_tools', []),
                    arguments=arguments
                )
                
                prompts[prompt_name] = prompt
                logger.debug(f"Loaded prompt: {prompt_name}")
                
            except Exception as e:
                logger.error(f"Failed to parse prompt {prompt_name} from {prompt_file_path}: {e}")
        
        return prompts
    
    def _load_resources_file(self, resource_file_path: Path) -> Dict[str, Any]:
        """Load resources from a YAML file.
        
        Args:
            resource_file_path: Path to resources YAML file
            
        Returns:
            Dictionary of resource definitions
        """
        logger.debug(f"Loading resources from {resource_file_path}")
        
        with open(resource_file_path, 'r', encoding='utf-8') as f:
            resource_data = yaml.safe_load(f)
        
        if not resource_data:
            logger.warning(f"No resources found in {resource_file_path}")
            return {}
        
        resources = {}
        
        # Load standard resources
        if 'resources' in resource_data:
            for resource_name, resource_dict in resource_data['resources'].items():
                try:
                    # ResourceDefinition now imported at top
                    resource = ResourceDefinition(
                        name=resource_name,
                        type=resource_dict['type'],
                        url=resource_dict.get('url', ''),
                        description=resource_dict['description']
                    )
                    resources[resource_name] = resource
                    logger.debug(f"Loaded resource: {resource_name}")
                    
                except Exception as e:
                    logger.error(f"Failed to parse resource {resource_name}: {e}")
        
        # Load other resource types (quick_reference, help_topics, etc.)
        for section_name in ['quick_reference', 'help_topics']:
            if section_name in resource_data:
                resources[section_name] = resource_data[section_name]
                logger.debug(f"Loaded resource section: {section_name}")
        
        return resources
    
    def _validate_pack(self, pack: Pack, pack_name: str) -> None:
        """Validate a loaded modular pack.
        
        Args:
            pack: Pack object to validate
            pack_name: Pack name for error messages
            
        Raises:
            PackValidationError: If validation fails
        """
        # Basic metadata validation
        if not pack.metadata.name:
            raise PackValidationError(f"Pack {pack_name}: metadata.name is required")
            
        if not pack.metadata.version:
            raise PackValidationError(f"Pack {pack_name}: metadata.version is required")
        
        # Connection validation
        if not pack.connection:
            raise PackValidationError(f"Pack {pack_name}: connection config is required")
            
        if not pack.connection.base_url:
            raise PackValidationError(f"Pack {pack_name}: connection.base_url is required")
        
        # Tools validation
        if not pack.tools:
            logger.warning(f"Pack {pack_name}: no tools defined")
        else:
            logger.info(f"Pack {pack_name}: validated {len(pack.tools)} tools")
        
        # Validate transform file references
        pack_dir = self.packs_directory / pack_name
        for tool_name, tool in pack.tools.items():
            if tool.transform and tool.transform.file:
                transform_file = pack_dir / "transforms" / tool.transform.file
                if not transform_file.exists():
                    logger.warning(f"Transform file not found for tool {tool_name}: {transform_file}")
    
    def get_pack_info(self, pack_name: str) -> Optional[Dict[str, Any]]:
        """Get basic information about a modular pack without fully loading it.
        
        Args:
            pack_name: Name of pack to inspect
            
        Returns:
            Dictionary with pack metadata or None if pack not found
        """
        pack_yaml = self.packs_directory / pack_name / "pack.yaml"
        
        if not pack_yaml.exists():
            return None
            
        try:
            with open(pack_yaml, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            metadata = data.get('metadata', {})
            structure = data.get('structure', {})
            
            # Count tools, prompts, resources across files
            pack_dir = self.packs_directory / pack_name
            
            tools_count = 0
            if 'tools' in structure:
                for tool_file in structure['tools']:
                    tool_path = pack_dir / tool_file
                    if tool_path.exists():
                        with open(tool_path, 'r') as f:
                            tool_data = yaml.safe_load(f)
                            tools_count += len(tool_data.get('tools', {}))
            
            prompts_count = 0
            if 'prompts' in structure:
                for prompt_file in structure['prompts']:
                    prompt_path = pack_dir / prompt_file
                    if prompt_path.exists():
                        with open(prompt_path, 'r') as f:
                            prompt_data = yaml.safe_load(f)
                            prompts_count += len(prompt_data.get('prompts', {}))
            
            return {
                "name": metadata.get('name'),
                "version": metadata.get('version'),
                "description": metadata.get('description'),
                "vendor": metadata.get('vendor'),
                "domain": metadata.get('domain'),
                "tools_count": tools_count,
                "prompts_count": prompts_count,
                "pricing_tier": metadata.get('pricing_tier', 'free'),
                "is_modular": True,
                "structure": structure
            }
            
        except Exception as e:
            logger.error(f"Failed to read pack info for {pack_name}: {e}")
            return None