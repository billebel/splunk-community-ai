# Claude Code Configuration for Splunk Community MCP Pack

## Mission Statement

**"Enable productive AI-human collaboration on complex Splunk projects by providing the context, constraints, and cultural understanding that AI agents need to contribute meaningfully - combining deep Splunk expertise with innovative approaches while maintaining humility about what we're still learning together."**

## Project Overview

This is a **security-focused MCP (Model Context Protocol) knowledge pack** for integrating AI assistants with Splunk Enterprise. The pack emphasizes **defensive security practices** and **robust guardrails** to safely enable AI-driven Splunk analysis.

Built by practitioners with **25+ years of cybersecurity experience**, this pack represents our attempt to **innovate responsibly** - exploring how AI can enhance Splunk analysis while respecting the security and operational realities of production environments. We approach this work with **humility**, knowing that real-world usage will teach us things our testing hasn't revealed.

## Key Architecture Components

### 🛡️ Security-First Design
- **Guardrails Engine** (`transforms/guardrails.py`) - Core security validation and data protection
- **Security Configuration** (`guardrails.yaml`) - Centralized security policies and controls
- **Comprehensive Testing** - 15+ security tests covering bypass protection and data masking

### 📦 Knowledge Pack Structure
```
knowledge-packs/splunk_enterprise/
├── tools/           # MCP tool definitions (17 specialized tools)
├── transforms/      # Python data processing functions
├── prompts/         # AI behavior guidance (5 strategic prompts)
├── tests/           # Comprehensive test suite
└── guardrails.yaml  # Security configuration
```

### 🔧 Transform Functions (Core Logic)
- `discovery.py` - Data source discovery and mapping
- `knowledge.py` - Knowledge objects (data models, macros, lookups)
- `search.py` - Search execution and result processing
- `system.py` - System information and diagnostics
- `guardrails.py` - **CRITICAL**: Security validation and data protection

## Development Guidelines

### 🚨 Security Requirements (NON-NEGOTIABLE)
1. **NEVER modify security controls without comprehensive testing**
2. **ALL security tests must pass** before any commit (`pytest test_guardrails_security.py`)
3. **Review guardrails.yaml changes carefully** - impacts all queries
4. **Test bypass protection** when adding new security patterns
5. **Data masking must work** for sensitive fields (usernames, passwords, etc.)

### 🧪 Testing Commands
```bash
# REQUIRED: Security validation (must pass 15/15 tests)
cd knowledge-packs/splunk_enterprise/tests
python -m pytest test_guardrails_security.py -v

# Full test suite (expect ~35 non-critical format failures)
python -m pytest tests/ -v

# Coverage analysis
python -m pytest tests/ --cov=transforms --cov-report=term-missing

# Quick validation
python -m pytest test_guardrails_security.py -q
```

### 📁 Key Files to Understand

#### Critical Security Files
- `guardrails.yaml` - **Main security configuration** - blocked commands, patterns, role limits
- `transforms/guardrails.py` - **Security engine** - query validation, bypass detection, data masking
- `tests/test_guardrails_security.py` - **Security test suite** - validates all protection mechanisms

#### Core Functionality
- `tools/` directory - MCP tool definitions (what AI assistants can call)
- `prompts/` directory - AI behavior guidance (how AI should use tools strategically)
- `transforms/` directory - Data processing logic (what happens when tools are called)

### 🎯 AI Behavior Prompts (Unique Feature)
We include 5 strategic prompts that guide AI behavior:
- `search-prompts.yaml` - Smart query orchestration
- `dashboard-prompts.yaml` - Performance & security analysis
- `scheduled-search-prompts.yaml` - Optimization strategies
- `knowledge-objects-prompts.yaml` - Leverage existing assets
- `system-diagnostics-prompts.yaml` - Health monitoring

## Development Workflow

### 🔍 Before Making Changes
1. **Understand the security model** - Review `guardrails.yaml` and security tests
2. **Run security tests** - Ensure baseline security is working
3. **Check existing patterns** - Follow established code conventions
4. **Review AI prompts** - Understand how changes affect AI guidance

### ✅ Testing & Validation
1. **Security first**: `pytest test_guardrails_security.py -v` (must be 15/15 passing)
2. **Core functionality**: Run relevant transform tests
3. **Integration check**: Test with actual MCP client if possible
4. **Coverage analysis**: Maintain good test coverage on security components

### 🚀 Deployment Considerations
- **MCP-only deployment**: `docker-compose.mcp-only.yml` (lightweight)
- **Full web experience**: `docker-compose.yml` (includes LibreChat UI)
- **Development setup**: `docker-compose.splunk.yml` (includes test Splunk)

## Common Pitfalls to Avoid

### 🚫 Security Anti-Patterns
- **Don't bypass security checks** - even for "convenience" during development
- **Don't add commands to blocked_commands list without testing** - ensure legitimate queries still work
- **Don't modify data masking without validating privacy protection**
- **Don't assume Unicode normalization catches everything** - test with actual bypass attempts

### 🐛 Technical Gotchas
- **Transform path resolution** - MCP server looks for transforms in specific locations
- **Mock configurations** - Test mocks should match real Splunk API responses
- **Error handling** - Graceful failure is critical for production use
- **Format expectations** - Many failing tests are just format mismatches (not functional issues)

## Current State (Be Honest)

### ✅ What's Working Well
- **Security guardrails**: 15/15 tests passing, bypass protection implemented
- **Core functionality**: Basic Splunk integration works reliably  
- **AI guidance**: Strategic prompts help AI make better decisions
- **Docker deployment**: Multiple deployment options available

### 🔧 What Needs Work
- **~35 test failures**: Mostly format expectation mismatches (non-critical)
- **Error handling**: Could be more graceful in edge cases
- **Performance testing**: Limited validation under high load
- **Edge case coverage**: Real-world usage may reveal untested scenarios

### 🤝 Community Contribution Priorities
1. **Security review**: Additional eyes on guardrails implementation
2. **Real-world testing**: Try with your Splunk environment and report issues
3. **Test alignment**: Fix format mismatches in transform tests
4. **Documentation**: Help improve clarity and completeness

## Philosophy

This pack embodies a **security-first, community-driven approach** to AI-Splunk integration. We prioritize:
- **Safety over convenience** - Better to block a legitimate query than allow a dangerous one
- **Transparency over perfection** - Honest about limitations and areas needing work  
- **Community over closed development** - Share early, improve together
- **Reality over theory** - Test with real Splunk data and real AI interactions

## Getting Help

- **Security questions**: Review `docs/security-guardrails.md` and test suite
- **Architecture questions**: Check `docs/architecture.md` 
- **Testing questions**: See `docs/testing.md`
- **Usage examples**: Look at `docs/examples.md`

---

**Remember**: This is beta software shared with the community. It works for basic use cases with good security foundations, but expect some rough edges. Use it, test it, break it, and help us make it better!