#!/usr/bin/env python3
"""Universal Catalyst MCP Server - Knowledge Pack Architecture."""

import asyncio
import os
import sys
import logging
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dotenv import load_dotenv

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

# Import existing components
from .config import MCPConfig
from .audit.audit_system import AuditSystem, ExecutionContext
from .audit.hec_logger import SplunkHECLogger

# Import universal pack system
from .packs import PackRegistry, UniversalToolFactory

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("Catalyst MCP Server - Universal")

# Health check endpoint for Docker container monitoring
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint for Docker container monitoring."""
    return JSONResponse({"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()})

# Global pack system components
pack_registry: Optional[PackRegistry] = None
tool_factory: Optional[UniversalToolFactory] = None
config: Optional[MCPConfig] = None


def initialize_pack_system() -> bool:
    """Initialize the universal knowledge pack system.
    
    Returns:
        True if initialization succeeded, False otherwise
    """
    global pack_registry, tool_factory
    
    try:
        logger.info("Initializing Universal Knowledge Pack System...")
        
        # Create pack registry
        pack_registry = PackRegistry("knowledge-packs")
        
        # Auto-discover and load all valid packs (excluding .example)
        # No need to specify core packs - will auto-discover from knowledge-packs/
        
        # Create universal tool factory
        tool_factory = UniversalToolFactory(mcp)
        
        # Load and register core packs
        core_packs = pack_registry.initialize_core_packs()
        
        total_tools = 0
        for pack_name, pack in core_packs.items():
            registered_tools = tool_factory.register_pack_tools(pack_name, pack)
            total_tools += len(registered_tools)
            logger.info(f"Pack '{pack_name}': {len(registered_tools)} tools registered")
        
        # Log pack system statistics
        stats = pack_registry.get_pack_statistics()
        logger.info(f"Pack System Initialized: {stats['total_packs']} packs, {total_tools} tools")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize pack system: {e}")
        return False


@mcp.tool
async def list_knowledge_packs() -> Dict[str, Any]:
    """List all available knowledge packs and their status."""
    if not pack_registry:
        return {"error": "Pack system not initialized"}
    
    try:
        available_packs = pack_registry.list_available_packs()
        loaded_packs = pack_registry.list_loaded_packs()
        
        pack_info = []
        for pack_name in available_packs:
            info = pack_registry.get_pack_info(pack_name)
            if info:
                info["loaded"] = pack_name in loaded_packs
                pack_info.append(info)
        
        stats = pack_registry.get_pack_statistics()
        
        return {
            "available_packs": len(available_packs),
            "loaded_packs": len(loaded_packs),
            "total_tools": stats["total_tools"],
            "packs": pack_info,
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to list knowledge packs: {e}")
        return {"error": str(e)}


@mcp.tool  
async def reload_knowledge_pack(pack_name: str) -> Dict[str, Any]:
    """Reload a specific knowledge pack from disk.
    
    Args:
        pack_name: Name of pack to reload
    """
    if not pack_registry or not tool_factory:
        return {"error": "Pack system not initialized"}
    
    try:
        logger.info(f"Reloading knowledge pack: {pack_name}")
        
        # Unregister existing tools
        unregistered = tool_factory.unregister_pack_tools(pack_name)
        logger.info(f"Unregistered {len(unregistered)} tools from {pack_name}")
        
        # Reload pack
        pack = pack_registry.reload_pack(pack_name)
        if not pack:
            return {"error": f"Failed to reload pack '{pack_name}'"}
        
        # Re-register tools
        registered = tool_factory.register_pack_tools(pack_name, pack)
        logger.info(f"Registered {len(registered)} tools for {pack_name}")
        
        return {
            "success": True,
            "pack_name": pack_name,
            "pack_version": pack.metadata.version,
            "tools_registered": len(registered),
            "tools": registered
        }
        
    except Exception as e:
        logger.error(f"Failed to reload pack {pack_name}: {e}")
        return {"error": str(e)}


@mcp.tool
async def get_pack_status() -> Dict[str, Any]:
    """Get detailed status of the knowledge pack system."""
    if not pack_registry or not tool_factory:
        return {"error": "Pack system not initialized"}
    
    try:
        stats = pack_registry.get_pack_statistics()
        tool_counts = tool_factory.get_tool_count_by_pack()
        
        loaded_packs = []
        for pack_name in pack_registry.list_loaded_packs():
            pack = pack_registry.get_pack(pack_name, lazy_load=False)
            if pack:
                loaded_packs.append({
                    "name": pack.metadata.name,
                    "pack_id": pack_name,
                    "version": pack.metadata.version,
                    "vendor": pack.metadata.vendor,
                    "domain": pack.metadata.domain,
                    "tools_count": tool_counts.get(pack_name, 0),
                    "pricing_tier": pack.metadata.pricing_tier
                })
        
        return {
            "system_status": "operational",
            "statistics": stats,
            "loaded_packs": loaded_packs,
            "tool_distribution": tool_counts
        }
        
    except Exception as e:
        logger.error(f"Failed to get pack status: {e}")
        return {"error": str(e)}


# Legacy Splunk tools for compatibility during migration
@mcp.tool
async def current_user() -> Dict[str, Any]:
    """Get current Splunk user information - Legacy compatibility tool."""
    # This is a legacy tool that will eventually be replaced by the pack system
    # For now, we'll implement a simple version
    
    try:
        config = MCPConfig.from_env()
        return {
            "username": config.splunk_user,
            "splunk_url": config.splunk_url,
            "note": "This is a legacy compatibility tool. Use knowledge packs for new implementations."
        }
    except Exception as e:
        return {"error": str(e)}


async def startup_sequence():
    """Run server startup sequence."""
    global config
    
    logger.info("Starting Catalyst MCP Server - Universal Knowledge Pack Edition")
    
    # Load configuration
    try:
        config = MCPConfig.from_env()
        config.validate()
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        return False
    
    # Initialize pack system
    if not initialize_pack_system():
        logger.error("Pack system initialization failed - server cannot start")
        return False
    
    # Initialize audit system if HEC is enabled
    if config.enable_hec_logging and config.splunk_hec_token:
        try:
            hec_logger = SplunkHECLogger(
                hec_url=config.splunk_hec_url,
                hec_token=config.splunk_hec_token,
                index=config.splunk_hec_index,
                source="catalyst_universal"
            )
            await hec_logger.start()
            logger.info("HEC audit logging enabled")
        except Exception as e:
            logger.warning(f"HEC audit logging failed to initialize: {e}")
    
    logger.info("Catalyst MCP Server startup complete")
    return True


async def startup_and_run():
    """Run startup sequence and start server."""
    # Run startup sequence
    if not await startup_sequence():
        sys.exit(1)
    
    # Return control - mcp.run will handle the server
    return True

def sync_main():
    """Synchronous entry point for the server."""
    try:
        # Run async startup
        startup_result = asyncio.run(startup_and_run())
        if not startup_result:
            sys.exit(1)
        
        # Start the FastMCP server (handles its own event loop)
        port = config.port if config else 8443
        logger.info(f"Starting server on port {port}")
        mcp.run(transport="http", port=port, host="0.0.0.0")
        
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    sync_main()