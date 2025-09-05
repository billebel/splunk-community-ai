"""
Deployment test configuration and fixtures

Provides common utilities for deployment validation tests
"""

import pytest
import subprocess
import time
import requests
import os
from pathlib import Path


@pytest.fixture(scope="session")
def docker_available():
    """Check if Docker is available and running"""
    try:
        result = subprocess.run(
            ["docker", "--version"], 
            capture_output=True, 
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            pytest.skip("Docker not available")
            
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True, 
            timeout=10
        )
        if result.returncode != 0:
            pytest.skip("Docker daemon not running")
            
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pytest.skip("Docker not available or not responding")


@pytest.fixture(scope="session") 
def docker_compose_available():
    """Check if docker-compose is available"""
    try:
        result = subprocess.run(
            ["docker-compose", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            pytest.skip("docker-compose not available")
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pytest.skip("docker-compose not available")


def wait_for_service(url, timeout=30, check_interval=2):
    """
    Wait for a service to become available
    
    Args:
        url: Service URL to check
        timeout: Maximum time to wait in seconds
        check_interval: Time between checks in seconds
        
    Returns:
        bool: True if service becomes available, False if timeout
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            # Any HTTP response means service is running
            return True
        except (requests.ConnectionError, requests.exceptions.ReadTimeout):
            time.sleep(check_interval)
    
    return False


def cleanup_docker_compose(project_root, compose_file):
    """
    Clean up Docker Compose deployment
    
    Args:
        project_root: Path to project root
        compose_file: Docker compose file name
    """
    try:
        subprocess.run([
            "docker-compose", "-f", compose_file, "down", "-v", "--remove-orphans"
        ], cwd=project_root, timeout=60)
    except subprocess.TimeoutExpired:
        # Force cleanup if normal cleanup hangs
        subprocess.run([
            "docker-compose", "-f", compose_file, "kill"
        ], cwd=project_root)
        subprocess.run([
            "docker-compose", "-f", compose_file, "rm", "-f"
        ], cwd=project_root)


@pytest.fixture
def temp_env_file(tmp_path):
    """Create a temporary .env file for testing"""
    env_content = """# Test environment configuration
SPLUNK_URL=https://test-splunk:8089
SPLUNK_USER=testuser
SPLUNK_PASSWORD=testpass
ANTHROPIC_API_KEY=test_key_123
"""
    env_file = tmp_path / ".env"
    env_file.write_text(env_content)
    return env_file


@pytest.fixture
def mock_splunk_config():
    """Mock Splunk configuration for testing"""
    return {
        "url": "https://mock-splunk:8089",
        "username": "testuser", 
        "password": "testpass",
        "verify": False
    }