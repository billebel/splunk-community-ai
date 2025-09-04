# Testing Documentation

This document describes our testing approach for the Splunk Community MCP Pack. We're being transparent about what we've tested, what's working, and what still needs attention.

## Current Test Status

**What We Know**: We focused on security-critical components first, but this is still beta software.

- ✅ **15/15 Security Tests Passing** - Core security features appear to work correctly  
- ✅ **~80 Tests Passing** - Basic functionality seems solid
- ❌ **~35 Tests Failing** - Mostly format mismatches and integration issues
- 📊 **76% code coverage** - Reasonable coverage, but coverage != quality

## What's Working

### Transform Functions (The Good News)
- `discovery.py`: 73% coverage - index discovery and data source mapping
- `knowledge.py`: 98% coverage - data models, event types, search macros
- `search.py`: 78% coverage - search result processing
- `system.py`: 97% coverage - server info, apps, user context
- `guardrails.py`: 88% coverage - security validation (mostly working)

### Test Categories

1. **Security Tests** (`test_guardrails_security.py`) - 15 tests covering:
   - Query injection and bypass attempts
   - Data masking for sensitive information
   - Role-based access controls
   - Configuration validation

2. **Transform Tests** (`test_transforms_*.py`) - Testing data processing functions
3. **Integration Tests** (`test_integration.py`) - End-to-end workflow validation  
4. **Pack Validation** (`test_pack_validation.py`) - Configuration structure checks

## Security Testing

### What We've Addressed
We identified and worked on several security concerns:
- Unicode character substitution attempts (like Cyrillic look-alikes)
- Base64 encoding patterns that could bypass filters
- Dynamic query construction detection
- Sensitive field masking (usernames, passwords, etc.)

### Current Status
Our security tests are passing, which gives us confidence in the basic protections. However:
- **Tests don't cover every possible attack vector**
- **Real-world usage may reveal edge cases we haven't considered**
- **Security is an ongoing process, not a one-time achievement**

We encourage security-minded users to review our `guardrails.yaml` configuration and test against your specific use cases.

## What Still Needs Work

### Test Failures (~35 tests)
Many of our tests are failing, and we're being honest about why:
- **Format mismatches**: Tests expect different return formats than what functions actually provide
- **Mock limitations**: Our test mocks don't perfectly match real Splunk API responses  
- **Integration gaps**: Some end-to-end workflows have assumptions that don't hold in practice

### Known Issues
- MCP server startup shows warnings about transform paths
- Some tool configurations generate type warnings
- Authentication works but produces non-critical warnings in logs
- Error handling could be more graceful in edge cases

### What This Means
**The pack works for basic use cases**, but we haven't tested every scenario. There are likely edge cases and error conditions we haven't encountered yet. Use with appropriate caution and please report issues you find.

## Running Tests

### Security Tests
```bash
cd knowledge-packs/splunk_enterprise/tests

# Run security-focused tests
python -m pytest test_guardrails_security.py -v

# Include coverage information
python -m pytest test_guardrails_security.py --cov=../transforms/guardrails --cov-report=term-missing
```

### Full Test Suite
```bash
# Run everything (expect failures)
python -m pytest tests/ -v

# Get coverage overview
python -m pytest tests/ --cov=transforms --cov-report=term-missing

# Quick pass/fail summary
python -m pytest tests/ --tb=line -q
```

## Contributing

### Help Wanted
If you'd like to help improve our testing:
1. **Fix format mismatches** - Many tests just need expectations aligned with actual function outputs
2. **Improve mocking** - Better simulation of Splunk API responses would help integration tests
3. **Find edge cases** - Real-world usage often reveals scenarios we haven't tested
4. **Security review** - Additional eyes on our guardrails implementation

### Testing Philosophy
- **Be realistic** - Test against actual Splunk API responses when possible
- **Plan for failure** - Error scenarios are just as important as success cases
- **Stay honest** - Don't make tests pass by lowering expectations; fix the real issues
- **Document gaps** - If something can't be tested well, say so

## Where We Stand

### What We're Confident About
- Basic security protections are working (based on our test coverage)
- Core functionality handles typical use cases
- The pack integrates successfully with MCP clients

### What We're Less Sure About
- Edge cases and error conditions we haven't encountered
- Performance under high load or complex queries  
- Integration with unusual Splunk configurations
- Long-term stability and maintenance requirements

### Honest Assessment
This pack represents our best effort to create a useful, secure Splunk integration for AI assistants. We've focused on the security aspects because that's where the biggest risks lie. The testing validates our basic assumptions, but **real-world usage is the ultimate test**.

We're sharing this as a community contribution - use it, break it, and let us know what needs improvement. That's how open source software gets better.