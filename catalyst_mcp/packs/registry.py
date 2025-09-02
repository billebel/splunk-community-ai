"""Global pack registry for managing loaded knowledge packs."""

import logging
from typing import Dict, List, Optional, Set
from catalyst_pack_schemas import Pack
from .loader import PackLoader
from .transforms import TransformEngine


logger = logging.getLogger(__name__)


class PackRegistry:
    """Global registry for managing loaded knowledge packs."""
    
    def __init__(self, packs_directory: str = "knowledge-packs"):
        """Initialize pack registry.
        
        Args:
            packs_directory: Directory containing knowledge packs
        """
        self.loader = PackLoader(packs_directory)
        self.loaded_packs: Dict[str, Pack] = {}
        self.core_packs: Set[str] = set()
        self.transform_engines: Dict[str, TransformEngine] = {}
        
    def set_core_packs(self, pack_names: List[str]) -> None:
        """Set which packs should be loaded at startup.
        
        Args:
            pack_names: List of pack names to treat as core packs
        """
        self.core_packs = set(pack_names)
        logger.info(f"Set core packs: {pack_names}")
    
    def initialize_core_packs(self) -> Dict[str, Pack]:
        """Load all core packs at startup.
        
        Returns:
            Dictionary of successfully loaded core packs
        """
        logger.info("Initializing core packs...")
        
        if not self.core_packs:
            # If no core packs specified, treat all discovered packs as core
            discovered = self.loader.discover_packs()
            logger.info(f"No core packs specified, loading all discovered: {discovered}")
            self.core_packs = set(discovered)
        
        loaded_core = {}
        for pack_name in self.core_packs:
            pack = self.loader.load_pack(pack_name)
            if pack:
                self.loaded_packs[pack_name] = pack
                loaded_core[pack_name] = pack
                # Initialize transform engine for this pack
                self._initialize_transform_engine(pack_name)
            else:
                logger.error(f"Failed to load core pack: {pack_name}")
        
        logger.info(f"Loaded {len(loaded_core)} core packs: {list(loaded_core.keys())}")
        return loaded_core
    
    def get_pack(self, pack_name: str, lazy_load: bool = True) -> Optional[Pack]:
        """Get a pack by name, loading if necessary.
        
        Args:
            pack_name: Name of pack to retrieve
            lazy_load: Whether to load pack if not already loaded
            
        Returns:
            Pack object or None if not found/failed to load
        """
        # Return cached pack if available
        if pack_name in self.loaded_packs:
            return self.loaded_packs[pack_name]
        
        # If lazy loading disabled, return None
        if not lazy_load:
            return None
        
        # Attempt lazy load
        logger.info(f"Lazy loading pack: {pack_name}")
        pack = self.loader.load_pack(pack_name)
        if pack:
            self.loaded_packs[pack_name] = pack
            # Initialize transform engine for this pack
            self._initialize_transform_engine(pack_name)
        
        return pack
    
    def list_loaded_packs(self) -> List[str]:
        """List names of currently loaded packs.
        
        Returns:
            List of loaded pack names
        """
        return list(self.loaded_packs.keys())
    
    def list_available_packs(self) -> List[str]:
        """List names of all available packs (loaded + discoverable).
        
        Returns:
            List of all available pack names
        """
        loaded = set(self.loaded_packs.keys())
        discoverable = set(self.loader.discover_packs())
        return list(loaded | discoverable)
    
    def get_pack_info(self, pack_name: str) -> Optional[Dict[str, any]]:
        """Get information about a pack without loading it.
        
        Args:
            pack_name: Name of pack to inspect
            
        Returns:
            Pack information dictionary or None if not found
        """
        return self.loader.get_pack_info(pack_name)
    
    def reload_pack(self, pack_name: str) -> Optional[Pack]:
        """Reload a specific pack from disk.
        
        Args:
            pack_name: Name of pack to reload
            
        Returns:
            Reloaded pack or None if failed
        """
        logger.info(f"Reloading pack: {pack_name}")
        
        # Remove from registry cache
        if pack_name in self.loaded_packs:
            del self.loaded_packs[pack_name]
        
        # Remove transform engine cache
        if pack_name in self.transform_engines:
            del self.transform_engines[pack_name]
        
        # Reload from disk
        pack = self.loader.reload_pack(pack_name)
        if pack:
            self.loaded_packs[pack_name] = pack
            # Reinitialize transform engine for reloaded pack
            self._initialize_transform_engine(pack_name)
        
        return pack
    
    def get_all_tools(self) -> Dict[str, str]:
        """Get mapping of all tool names to their pack names.
        
        Returns:
            Dictionary mapping tool names to pack names
        """
        tool_to_pack = {}
        
        for pack_name, pack in self.loaded_packs.items():
            for tool_name in pack.tools.keys():
                # Use pack-prefixed tool name to avoid collisions
                full_tool_name = f"{pack_name}_{tool_name}"
                tool_to_pack[full_tool_name] = pack_name
        
        return tool_to_pack
    
    def get_pack_for_tool(self, tool_name: str) -> Optional[Pack]:
        """Get the pack that contains a specific tool.
        
        Args:
            tool_name: Name of tool (may be pack-prefixed)
            
        Returns:
            Pack containing the tool or None if not found
        """
        # Handle pack-prefixed tool names (pack_name_tool_name)
        if '_' in tool_name:
            parts = tool_name.split('_', 1)
            if len(parts) >= 2:
                potential_pack_name = parts[0]
                potential_tool_name = parts[1]
                
                pack = self.get_pack(potential_pack_name)
                if pack and potential_tool_name in pack.tools:
                    return pack
        
        # If not pack-prefixed, search all loaded packs
        for pack in self.loaded_packs.values():
            if tool_name in pack.tools:
                return pack
        
        return None
    
    def get_pack_statistics(self) -> Dict[str, any]:
        """Get statistics about loaded packs.
        
        Returns:
            Dictionary with pack statistics
        """
        total_tools = sum(len(pack.tools) for pack in self.loaded_packs.values())
        total_prompts = sum(len(pack.prompts) for pack in self.loaded_packs.values())
        total_resources = sum(len(pack.resources) for pack in self.loaded_packs.values())
        
        domains = set()
        vendors = set()
        for pack in self.loaded_packs.values():
            domains.add(pack.metadata.domain)
            vendors.add(pack.metadata.vendor)
        
        return {
            "total_packs": len(self.loaded_packs),
            "core_packs": len(self.core_packs),
            "total_tools": total_tools,
            "total_prompts": total_prompts,
            "total_resources": total_resources,
            "unique_domains": len(domains),
            "unique_vendors": len(vendors),
            "loaded_pack_names": list(self.loaded_packs.keys())
        }
    
    def get_transform_engine(self, pack_name: str) -> Optional[TransformEngine]:
        """Get the transform engine for a specific pack.
        
        Args:
            pack_name: Name of the pack
            
        Returns:
            TransformEngine instance for the pack or None if not found
        """
        return self.transform_engines.get(pack_name)
    
    def _initialize_transform_engine(self, pack_name: str) -> None:
        """Initialize transform engine for a pack.
        
        Args:
            pack_name: Name of the pack to initialize transform engine for
        """
        if pack_name not in self.loaded_packs:
            logger.warning(f"Cannot initialize transform engine for unloaded pack: {pack_name}")
            return
        
        try:
            # Get pack directory path
            pack_dir = self.loader.packs_directory / pack_name
            
            # Create transform engine for this pack
            transform_engine = TransformEngine(str(pack_dir))
            self.transform_engines[pack_name] = transform_engine
            
            # Log engine capabilities
            engine_status = transform_engine.get_engine_status()
            logger.info(f"Initialized transform engine for {pack_name}: {engine_status}")
            
        except Exception as e:
            logger.error(f"Failed to initialize transform engine for {pack_name}: {e}")
    
    def execute_transform(self, pack_name: str, data: Dict[str, any], 
                         transform_config: any, variables: Dict[str, any] = None) -> any:
        """Execute a transform for a specific pack.
        
        Args:
            pack_name: Name of the pack containing the transform
            data: Data to transform
            transform_config: Transform configuration
            variables: Variables for transform context
            
        Returns:
            Transformed data or original data if transform fails
        """
        transform_engine = self.get_transform_engine(pack_name)
        if not transform_engine:
            logger.warning(f"No transform engine available for pack {pack_name}")
            return data
        
        return transform_engine.transform(data, transform_config, variables or {})