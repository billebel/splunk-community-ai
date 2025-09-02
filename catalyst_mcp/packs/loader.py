"""Knowledge pack loader and validator."""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
import yaml
from catalyst_pack_schemas import Pack, PackValidationError
from .modular_loader import ModularPackLoader


logger = logging.getLogger(__name__)


class PackLoader:
    """Loads and validates knowledge packs from YAML files."""
    
    def __init__(self, packs_directory: str = "knowledge-packs"):
        """Initialize pack loader.
        
        Args:
            packs_directory: Directory containing pack subdirectories
        """
        self.packs_directory = Path(packs_directory)
        self.loaded_packs: Dict[str, Pack] = {}
        self.modular_loader = ModularPackLoader(packs_directory)
        
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
        """Load a specific knowledge pack.
        
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
            logger.info(f"Loading pack: {pack_name}")
            
            # Detect if this is a modular pack
            if self._is_modular_pack(pack_yaml):
                logger.debug(f"Detected modular pack structure for {pack_name}")
                pack = self.modular_loader.load_pack(pack_name, force_reload)
            else:
                logger.debug(f"Using legacy monolithic loader for {pack_name}")
                pack = Pack.from_yaml_file(str(pack_yaml))
            
            if not pack:
                logger.error(f"Failed to load pack {pack_name}")
                return None
                
            # Validate the loaded pack
            self._validate_pack(pack, pack_name)
            
            # Cache the loaded pack
            self.loaded_packs[pack_name] = pack
            
            tool_count = len(pack.tools)
            prompt_count = len(pack.prompts)
            resource_count = len(pack.resources)
            
            logger.info(f"Successfully loaded pack '{pack.metadata.name}' v{pack.metadata.version}")
            logger.info(f"  Tools: {tool_count}, Prompts: {prompt_count}, Resources: {resource_count}")
            return pack
            
        except Exception as e:
            logger.error(f"Failed to load pack {pack_name}: {e}")
            import traceback
            logger.debug(f"Stack trace: {traceback.format_exc()}")
            return None
    
    def load_all_packs(self) -> Dict[str, Pack]:
        """Load all discovered packs.
        
        Returns:
            Dictionary mapping pack names to Pack objects
        """
        pack_names = self.discover_packs()
        loaded_packs = {}
        
        for pack_name in pack_names:
            pack = self.load_pack(pack_name)
            if pack:
                loaded_packs[pack_name] = pack
        
        logger.info(f"Loaded {len(loaded_packs)} out of {len(pack_names)} discovered packs")
        return loaded_packs
    
    def reload_pack(self, pack_name: str) -> Optional[Pack]:
        """Reload a specific pack, clearing cache first.
        
        Args:
            pack_name: Name of pack to reload
            
        Returns:
            Reloaded Pack object or None if failed
        """
        logger.info(f"Reloading pack: {pack_name}")
        
        # Remove from cache if exists
        if pack_name in self.loaded_packs:
            del self.loaded_packs[pack_name]
        
        return self.load_pack(pack_name, force_reload=True)
    
    def _validate_pack(self, pack: Pack, pack_name: str) -> None:
        """Validate a loaded pack for correctness.
        
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
        
        for tool_name, tool in pack.tools.items():
            self._validate_tool(tool, f"{pack_name}.{tool_name}")
    
    def _validate_tool(self, tool, tool_identifier: str) -> None:
        """Validate a tool definition.
        
        Args:
            tool: ToolDefinition to validate
            tool_identifier: Tool identifier for error messages
            
        Raises:
            PackValidationError: If validation fails
        """
        if not tool.description:
            raise PackValidationError(f"Tool {tool_identifier}: description is required")
            
        if not tool.endpoint:
            raise PackValidationError(f"Tool {tool_identifier}: endpoint is required")
        
        # Validate parameter types
        valid_types = {"string", "integer", "number", "boolean", "array", "object"}
        for param in tool.parameters:
            if param.type not in valid_types:
                raise PackValidationError(f"Tool {tool_identifier}: invalid parameter type '{param.type}'")
        
        # If multi-step execution, validate steps
        if tool.execution_steps:
            for i, step in enumerate(tool.execution_steps):
                if not step.endpoint:
                    raise PackValidationError(f"Tool {tool_identifier}: execution step {i} missing endpoint")
    
    def get_pack_info(self, pack_name: str) -> Optional[Dict[str, any]]:
        """Get basic information about a pack without fully loading it.
        
        Args:
            pack_name: Name of pack to inspect
            
        Returns:
            Dictionary with pack metadata or None if pack not found
        """
        pack_yaml = self.packs_directory / pack_name / "pack.yaml"
        
        if not pack_yaml.exists():
            return None
            
        try:
            # Check if modular and delegate to modular loader for accurate counts
            if self._is_modular_pack(pack_yaml):
                return self.modular_loader.get_pack_info(pack_name)
            
            # Legacy monolithic pack info
            with open(pack_yaml, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            metadata = data.get('metadata', {})
            tools_count = len(data.get('tools', {}))
            prompts_count = len(data.get('prompts', {}))
            
            return {
                "name": metadata.get('name'),
                "version": metadata.get('version'),
                "description": metadata.get('description'),
                "vendor": metadata.get('vendor'),
                "domain": metadata.get('domain'),
                "tools_count": tools_count,
                "prompts_count": prompts_count,
                "pricing_tier": metadata.get('pricing_tier', 'free'),
                "is_modular": False
            }
            
        except Exception as e:
            logger.error(f"Failed to read pack info for {pack_name}: {e}")
            return None
    
    def _is_modular_pack(self, pack_yaml_path: Path) -> bool:
        """Check if a pack uses modular structure.
        
        Args:
            pack_yaml_path: Path to pack.yaml file
            
        Returns:
            True if pack has modular structure definition
        """
        try:
            with open(pack_yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Check for structure definition indicating modular pack
            return 'structure' in data and isinstance(data['structure'], dict)
            
        except Exception:
            return False