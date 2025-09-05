"""
Main Deployment Validation Tests

Tests that validate the deployment system works correctly across platforms.
This is the main entry point for deployment validation in the test suite.
"""

import pytest
import platform
from pathlib import Path


# Import all script test classes
try:
    from .deployment.test_scripts import (
        TestScriptExistence,
        TestScriptSyntax, 
        TestScriptConfiguration,
        TestScriptFunctionality,
        TestScriptIntegration,
        TestScriptExecution
    )

    from .e2e.test_deployment_scripts import (
        TestDeploymentScriptGuidance,
        TestScriptErrorHandling,
        TestScriptConfigurationValidation,
        TestScriptUsabilityFeatures,
        TestScriptWorkflow
    )
except ImportError:
    # If running from different directory, try absolute imports
    import sys
    from pathlib import Path
    tests_dir = Path(__file__).parent
    sys.path.insert(0, str(tests_dir))
    
    from deployment.test_scripts import (
        TestScriptExistence,
        TestScriptSyntax, 
        TestScriptConfiguration,
        TestScriptFunctionality,
        TestScriptIntegration,
        TestScriptExecution
    )

    from e2e.test_deployment_scripts import (
        TestDeploymentScriptGuidance,
        TestScriptErrorHandling,
        TestScriptConfigurationValidation,
        TestScriptUsabilityFeatures,
        TestScriptWorkflow
    )


class TestDeploymentSystemIntegrity:
    """High-level deployment system validation"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent
    
    def test_deployment_files_present(self, project_root):
        """Test that all deployment files are present"""
        required_files = [
            "docker-compose.yml",
            "docker-compose.mcp-only.yml", 
            "docker-compose.splunk.yml",
            ".env.example",
            "scripts/deploy.bat",
            "scripts/deploy.sh",
            "scripts/start-dev.bat",
            "scripts/start-dev.sh",
            "scripts/stop-dev.sh",
            "scripts/test-mcp.bat",
            "scripts/test-mcp.sh",
            "scripts/build-chat.bat"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        assert not missing_files, f"Missing deployment files: {missing_files}"
    
    def test_deployment_system_completeness(self, project_root):
        """Test that deployment system provides all necessary components"""
        # Should have scripts for all major platforms
        scripts_dir = project_root / "scripts"
        
        # Windows scripts
        windows_scripts = list(scripts_dir.glob("*.bat"))
        assert len(windows_scripts) >= 4, "Should have Windows deployment scripts"
        
        # Unix scripts  
        unix_scripts = list(scripts_dir.glob("*.sh"))
        assert len(unix_scripts) >= 4, "Should have Unix deployment scripts"
        
        # Each Windows script should have Unix equivalent
        for windows_script in windows_scripts:
            unix_equivalent = scripts_dir / f"{windows_script.stem}.sh"
            if windows_script.name not in ["build-chat.bat"]:  # build-chat is Windows-only
                assert unix_equivalent.exists(), \
                    f"Windows script {windows_script.name} missing Unix equivalent"


@pytest.mark.integration
class TestCrossPlatformDeployment:
    """Cross-platform deployment validation"""
    
    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent
    
    def test_platform_specific_scripts_work(self, project_root):
        """Test that platform-specific scripts are properly configured"""
        scripts_dir = project_root / "scripts"
        
        if platform.system() == "Windows":
            # Test Windows scripts
            required_windows_scripts = [
                "deploy.bat", "start-dev.bat", "stop-dev.bat", 
                "test-mcp.bat", "build-chat.bat"
            ]
            
            for script_name in required_windows_scripts:
                script_path = scripts_dir / script_name
                assert script_path.exists(), f"Windows script {script_name} missing"
                
                # Read and verify content
                with open(script_path, encoding='utf-8') as f:
                    content = f.read()
                
                # Should be proper batch file
                assert content.startswith("@echo off") or content.startswith("REM"), \
                    f"Script {script_name} should be proper batch file"
        
        else:
            # Test Unix scripts
            required_unix_scripts = [
                "deploy.sh", "start-dev.sh", "stop-dev.sh", "test-mcp.sh"
            ]
            
            for script_name in required_unix_scripts:
                script_path = scripts_dir / script_name
                assert script_path.exists(), f"Unix script {script_name} missing"
                
                # Read and verify content
                with open(script_path, encoding='utf-8') as f:
                    content = f.read()
                
                # Should be proper shell script
                assert content.startswith("#!/bin/bash"), \
                    f"Script {script_name} should be proper shell script"


# Re-export all test classes for discovery
__all__ = [
    'TestDeploymentSystemIntegrity',
    'TestCrossPlatformDeployment',
    'TestScriptExistence',
    'TestScriptSyntax',
    'TestScriptConfiguration', 
    'TestScriptFunctionality',
    'TestScriptIntegration',
    'TestScriptExecution',
    'TestDeploymentScriptGuidance',
    'TestScriptErrorHandling', 
    'TestScriptConfigurationValidation',
    'TestScriptUsabilityFeatures',
    'TestScriptWorkflow'
]