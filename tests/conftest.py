"""
Project-level test configuration

Provides common fixtures and configuration for all project-level tests.
These tests validate deployment, integration, and end-to-end functionality.
"""

import pytest
import subprocess
import os
import tempfile
import shutil
from pathlib import Path


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may require external services)"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (may take longer than 30 seconds)"
    )
    config.addinivalue_line(
        "markers", "docker: marks tests that require Docker to be available"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests (full user workflow)"
    )


@pytest.fixture(scope="session")
def project_root():
    """Get the project root directory"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def docker_available():
    """Check if Docker is available"""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


@pytest.fixture(scope="session")
def docker_compose_available():
    """Check if docker-compose is available"""
    try:
        result = subprocess.run(
            ["docker-compose", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


@pytest.fixture
def temp_project_copy(tmp_path, project_root):
    """Create a temporary copy of the project for testing"""
    temp_project = tmp_path / "test_project"
    
    # Copy key files needed for deployment tests
    key_files = [
        "docker-compose.yml",
        "docker-compose.mcp-only.yml", 
        "docker-compose.splunk.yml",
        ".env.example",
        "README.md"
    ]
    
    temp_project.mkdir()
    
    for file_name in key_files:
        src_file = project_root / file_name
        if src_file.exists():
            shutil.copy2(src_file, temp_project / file_name)
    
    return temp_project


@pytest.fixture
def test_env_file(tmp_path):
    """Create a test .env file with safe values"""
    env_content = """# Test environment configuration
SPLUNK_URL=https://test-splunk.example.com:8089
SPLUNK_USER=testuser
SPLUNK_PASSWORD=testpass123
ANTHROPIC_API_KEY=test-key-12345
"""
    env_file = tmp_path / ".env"
    env_file.write_text(env_content)
    return env_file


@pytest.fixture
def mock_splunk_env():
    """Mock Splunk environment variables for testing"""
    original_env = dict(os.environ)
    
    # Set test environment variables
    test_env = {
        "SPLUNK_URL": "https://mock-splunk:8089",
        "SPLUNK_USER": "testuser",
        "SPLUNK_PASSWORD": "testpass",
        "ANTHROPIC_API_KEY": "test-key"
    }
    
    os.environ.update(test_env)
    
    yield test_env
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location and name"""
    for item in items:
        # Add markers based on test path
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # Add markers based on test names
        if "docker" in item.name.lower():
            item.add_marker(pytest.mark.docker)
        
        if "slow" in item.name.lower() or "deployment" in item.name.lower():
            item.add_marker(pytest.mark.slow)


def pytest_runtest_setup(item):
    """Setup for individual tests"""
    # Skip Docker tests if Docker not available
    if item.get_closest_marker("docker"):
        if not docker_available():
            pytest.skip("Docker not available")
    
    # Skip integration tests in fast mode
    if item.get_closest_marker("integration"):
        if item.config.getoption("--fast", default=False):
            pytest.skip("Integration tests skipped in fast mode")


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--fast", 
        action="store_true", 
        default=False, 
        help="Run only fast tests, skip integration and slow tests"
    )
    
    parser.addoption(
        "--docker",
        action="store_true",
        default=False,
        help="Run tests that require Docker (may start containers)"
    )


# Helper functions for tests
def docker_available():
    """Check if Docker is available"""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def wait_for_port(host, port, timeout=30):
    """Wait for a port to become available"""
    import socket
    import time
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                return True
        except:
            pass
        time.sleep(1)
    return False