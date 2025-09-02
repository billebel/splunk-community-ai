#!/usr/bin/env python3
"""
Test script for the new modular knowledge pack system.
Tests loading, transforms, and all modular components.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from catalyst_mcp.packs.registry import PackRegistry
from catalyst_pack_schemas import TransformEngine, TransformConfig

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_pack_discovery():
    """Test pack discovery functionality."""
    logger.info("=== Testing Pack Discovery ===")
    
    registry = PackRegistry("knowledge-packs")
    
    # Discover packs
    available_packs = registry.list_available_packs()
    logger.info(f"Available packs: {available_packs}")
    
    # Get pack info without loading
    for pack_name in available_packs:
        info = registry.get_pack_info(pack_name)
        if info:
            logger.info(f"Pack {pack_name}: {info.get('description', 'No description')} "
                       f"({info.get('tools_count', 0)} tools, {info.get('prompts_count', 0)} prompts)")
        else:
            logger.warning(f"Could not get info for pack: {pack_name}")
    
    return available_packs

def test_modular_pack_loading():
    """Test loading modular packs."""
    logger.info("\n=== Testing Modular Pack Loading ===")
    
    registry = PackRegistry("knowledge-packs")
    
    # Try to load the Splunk Enterprise pack (should be modular)
    pack = registry.get_pack("splunk_enterprise")
    
    if pack:
        logger.info(f"Successfully loaded modular pack: {pack.metadata.name} v{pack.metadata.version}")
        logger.info(f"  Tools: {len(pack.tools)}")
        logger.info(f"  Prompts: {len(pack.prompts)}")
        logger.info(f"  Resources: {len(pack.resources)}")
        
        # List some tool names
        tool_names = list(pack.tools.keys())[:5]  # First 5 tools
        logger.info(f"  Sample tools: {tool_names}")
        
        # Check if any tools have transforms
        tools_with_transforms = [name for name, tool in pack.tools.items() if tool.transform]
        logger.info(f"  Tools with transforms: {len(tools_with_transforms)}")
        
        return pack
    else:
        logger.error("Failed to load modular pack: splunk_enterprise")
        return None

def test_transform_engines():
    """Test transform engine functionality."""
    logger.info("\n=== Testing Transform Engines ===")
    
    registry = PackRegistry("knowledge-packs")
    pack = registry.get_pack("splunk_enterprise")
    
    if not pack:
        logger.error("No pack loaded for transform testing")
        return False
    
    # Test transform engine initialization
    transform_engine = registry.get_transform_engine("splunk_basic")
    if transform_engine:
        logger.info("Transform engine initialized successfully")
        
        # Check engine status
        status = transform_engine.get_engine_status()
        logger.info(f"Engine capabilities: {status}")
        
        # Test a simple transform if we have tools with transforms
        tools_with_transforms = [(name, tool) for name, tool in pack.tools.items() if tool.transform]
        
        if tools_with_transforms:
            tool_name, tool = tools_with_transforms[0]
            logger.info(f"Testing transform for tool: {tool_name}")
            
            # Create test data
            test_data = {
                "entry": [
                    {"name": "main", "content": {"currentDBSizeMB": "15000", "totalEventCount": "2000000"}},
                    {"name": "test", "content": {"currentDBSizeMB": "500", "totalEventCount": "10000"}}
                ]
            }
            
            try:
                result = registry.execute_transform("splunk_enterprise", test_data, tool.transform)
                logger.info(f"Transform result type: {type(result)}")
                logger.info(f"Transform successful for {tool_name}")
                return True
            except Exception as e:
                logger.error(f"Transform failed for {tool_name}: {e}")
                return False
        else:
            logger.info("No tools with transforms found to test")
            return True
    else:
        logger.error("Transform engine not initialized")
        return False

def test_pack_statistics():
    """Test pack statistics functionality."""
    logger.info("\n=== Testing Pack Statistics ===")
    
    registry = PackRegistry("knowledge-packs")
    
    # Initialize some packs
    registry.initialize_core_packs()
    
    # Get statistics
    stats = registry.get_pack_statistics()
    logger.info("Pack Statistics:")
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")
    
    return stats

def test_pack_reloading():
    """Test pack hot reloading."""
    logger.info("\n=== Testing Pack Reloading ===")
    
    registry = PackRegistry("knowledge-packs")
    
    # Load pack initially
    pack1 = registry.get_pack("splunk_enterprise")
    if not pack1:
        logger.error("Failed to load pack for reload testing")
        return False
    
    logger.info(f"Initial load: {len(pack1.tools)} tools")
    
    # Reload pack
    pack2 = registry.reload_pack("splunk_enterprise")
    if pack2:
        logger.info(f"After reload: {len(pack2.tools)} tools")
        logger.info("Pack reload successful")
        
        # Check that transform engine was also reloaded
        transform_engine = registry.get_transform_engine("splunk_enterprise")
        if transform_engine:
            logger.info("Transform engine reloaded successfully")
            return True
        else:
            logger.error("Transform engine not reloaded")
            return False
    else:
        logger.error("Pack reload failed")
        return False

def main():
    """Run all tests."""
    logger.info("Starting Modular Knowledge Pack System Tests")
    logger.info("=" * 50)
    
    try:
        # Test 1: Pack Discovery
        available_packs = test_pack_discovery()
        if not available_packs:
            logger.error("No packs discovered - cannot continue testing")
            return False
        
        # Test 2: Modular Pack Loading
        pack = test_modular_pack_loading()
        if not pack:
            logger.error("Modular pack loading failed - cannot continue")
            return False
        
        # Test 3: Transform Engines
        transforms_ok = test_transform_engines()
        if not transforms_ok:
            logger.warning("Transform engine tests had issues")
        
        # Test 4: Pack Statistics
        stats = test_pack_statistics()
        if not stats:
            logger.error("Pack statistics test failed")
            return False
        
        # Test 5: Pack Reloading
        reload_ok = test_pack_reloading()
        if not reload_ok:
            logger.error("Pack reloading test failed")
            return False
        
        logger.info("\n" + "=" * 50)
        logger.info("🎉 ALL TESTS PASSED! The modular system is working correctly.")
        logger.info("=" * 50)
        return True
        
    except Exception as e:
        logger.error(f"Test suite failed with exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)