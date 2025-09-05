# Project-Level Tests

These tests validate the entire Splunk AI Integration Platform deployment and user experience, ensuring the platform works as advertised in the README.

## Test Categories

### 🐳 **Deployment Tests** (`tests/deployment/`)
Validate that all deployment options work correctly:
- Docker Compose configurations
- Environment variable handling
- Service startup and health checks
- Port accessibility and routing

### 🔧 **Integration Tests** (`tests/integration/`)
Test cross-service functionality:
- MCP server communication
- Splunk connectivity
- AI provider integration
- Authentication workflows

### 🚀 **End-to-End Tests** (`tests/e2e/`)
Validate complete user workflows:
- Quick start guide accuracy
- Example queries work correctly
- Documentation examples function
- User experience flows

## Purpose

These tests address the biggest adoption barrier: **"Does it actually work?"**

When someone follows our README instructions, these tests ensure:
- Docker commands succeed
- Configuration examples work
- Promised functionality exists
- No deployment surprises

## Running Tests

```bash
# All deployment validation tests
pytest tests/deployment/ -v

# Quick start verification
pytest tests/e2e/test_quick_start.py -v

# Full platform validation
pytest tests/ -v
```

## Test Philosophy

**These tests validate promises made in documentation.** Every claim in the README should have a corresponding test that proves it works in a fresh environment.

**Focus on first-time user experience.** If someone can't get it working in 10 minutes, they won't adopt it.

**Test real deployment scenarios.** Use actual Docker commands, real configuration files, and realistic Splunk connections.