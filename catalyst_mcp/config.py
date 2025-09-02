"""Simplified configuration management."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class MCPConfig:
    """MCP Server configuration."""
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8443
    log_level: str = "INFO"
    
    # Splunk connection
    splunk_url: str = "https://localhost:8089"
    splunk_user: str = "admin"
    splunk_password: str = ""
    splunk_verify_ssl: bool = False
    splunk_timeout: int = 30
    
    # Session settings
    session_timeout: int = 7200  # 2 hours for service account
    
    # Splunk HEC settings for audit logging
    splunk_hec_url: str = "http://localhost:8088"
    splunk_hec_token: str = ""
    splunk_hec_index: str = "main"
    enable_hec_logging: bool = True
    
    @classmethod
    def from_env(cls) -> 'MCPConfig':
        """Load configuration from environment variables."""
        return cls(
            host=os.getenv("MCP_HOST", "0.0.0.0"),
            port=int(os.getenv("MCP_PORT", "8443")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            
            splunk_url=os.getenv("SPLUNK_URL", "https://localhost:8089"),
            splunk_user=os.getenv("SPLUNK_SERVICE_USER", os.getenv("SPLUNK_USER", "admin")),
            splunk_password=os.getenv("SPLUNK_SERVICE_PASSWORD", os.getenv("SPLUNK_PASSWORD", "")),
            splunk_verify_ssl=os.getenv("SPLUNK_VERIFY_SSL", "false").lower() == "true",
            splunk_timeout=int(os.getenv("SPLUNK_TIMEOUT", "30")),
            
            session_timeout=int(os.getenv("SESSION_TIMEOUT", "7200")),
            
            # HEC settings
            splunk_hec_url=os.getenv("SPLUNK_HEC_URL", "http://localhost:8088"),
            splunk_hec_token=os.getenv("SPLUNK_HEC_TOKEN", ""),
            splunk_hec_index=os.getenv("SPLUNK_HEC_INDEX", "main"),
            enable_hec_logging=os.getenv("ENABLE_HEC_LOGGING", "true").lower() == "true"
        )
    
    def validate(self) -> None:
        """Validate required configuration."""
        if not self.splunk_url:
            raise ValueError("SPLUNK_URL is required")
        if not self.splunk_user:
            raise ValueError("SPLUNK_SERVICE_USER or SPLUNK_USER is required")
        if not self.splunk_password:
            raise ValueError("SPLUNK_SERVICE_PASSWORD or SPLUNK_PASSWORD is required")