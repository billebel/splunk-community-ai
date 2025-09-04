# Security Guardrails

We've tried to build in some safety controls to prevent the AI from doing anything too destructive or resource-intensive. Here's what we have so far and what we're still working on.

## What the Guardrails Try to Do

### 🚫 Prevent Destructive Operations
- Block queries with `delete`, `drop`, `truncate` 
- No write operations to indexes
- Read-only access to configuration
- Can't modify user permissions or settings

**How it works:** The `validate_search_query` tool analyzes queries before execution and blocks anything that could change data.

**What we're learning:** Some legitimate operations might get blocked. We're trying to find the right balance.

### ⏱️ Resource Protection
- Automatic time range limits (default: no searches older than 30 days without explicit time range)
- Result count limits (default: max 1000 events per search)
- Search complexity analysis (warns about expensive operations)
- Concurrent search limits

**How it works:** The pack automatically modifies queries to add safety limits and validates complexity before execution.

**What we're still figuring out:** Different environments have different capacity. We need better ways to adapt to your specific setup.

### 🔒 Privacy Controls
- Automatic field masking for common PII patterns
- Role-based data filtering (respects Splunk RBAC)
- Audit logging of all AI interactions
- No credential or token exposure in responses

**How it works:** The `test_data_masking` tool shows how data would be filtered. Actual filtering happens in the transform layer.

**Areas we're improving:** Better pattern detection, configurable masking rules, more granular controls.

## Current Safety Features

### Query Validation
```
Before: index=* | delete
Result: ❌ BLOCKED - Destructive operation detected

Before: search * earliest=0
Result: ⚠️ MODIFIED - Added time limit: earliest=-30d

Before: index=security EventCode=4625 earliest=-1h
Result: ✅ APPROVED - Safe query
```

### Data Masking
```
Original: {"username": "john.doe", "ssn": "123-45-6789", "ip": "192.168.1.100"}
Filtered: {"username": "j***", "ssn": "***-**-****", "ip": "192.168.1.100"}
```

### Resource Limits
- Maximum 1000 results per search
- Searches limited to last 30 days by default
- Complex regex patterns flagged for review
- Statistical operations monitored for resource usage

## Configuration Options

You can adjust some guardrails in your environment:

```bash
# In your .env file
SPLUNK_MAX_RESULTS=1000          # Maximum events per search
SPLUNK_DEFAULT_EARLIEST=-30d     # Default time range limit
SPLUNK_TIMEOUT=30               # Query timeout in seconds
ENABLE_DESTRUCTIVE_COMMANDS=false  # Keep this false!
```

## What's Protected vs What's Not

### ✅ Currently Protected
- Data deletion/modification
- Excessive resource usage
- Common PII exposure
- System configuration access
- User management operations

### ⚠️ Partially Protected
- Complex statistical operations (flagged but allowed)
- Large time range searches (modified with limits)
- Custom field extraction (validated but allowed)

### 🚧 Not Yet Protected
- Advanced data correlation that might be resource-intensive
- Custom macro execution (trusts existing Splunk macros)
- Some edge cases in query parsing

## Known Limitations

### False Positives
Sometimes safe queries get blocked:
- Legitimate uses of the word "delete" in search terms
- Complex but safe statistical operations
- Valid time ranges that seem excessive

### False Negatives  
Some potentially problematic things might slip through:
- Very complex regex that could be slow
- Correlation searches that join large datasets
- Custom commands we haven't seen before

### Environment Differences
- Different Splunk versions behave differently
- Your RBAC setup might be more/less restrictive
- Network policies might add additional constraints

## Testing Your Guardrails

Use the validation tools to test what's allowed:

```bash
# Test a query safely (doesn't execute)
validate_search_query: "index=security | delete"

# Check current guardrail settings
get_guardrails_config: {}

# Test data masking rules
test_data_masking: {"sample_data": "john.doe@company.com"}
```

## What We're Working On

### Better Detection
- Smarter analysis of query intent
- Context-aware validation (some operations OK for admins)
- Learning from false positives/negatives

### More Flexibility
- Per-user guardrail settings
- Environment-specific tuning
- Override mechanisms for trusted users

### Better Feedback
- Clearer explanations when queries are blocked
- Suggestions for how to make blocked queries safe
- Progressive permission models

## Reporting Issues

If the guardrails are:
- **Too restrictive:** Blocking things you need to do → [Tell us about it](https://github.com/your-org/splunk-community-mcp/issues)
- **Not restrictive enough:** Allowing dangerous operations → [Definitely tell us](https://github.com/your-org/splunk-community-mcp/issues)
- **Confusing:** Hard to understand what's blocked/allowed → [We want to know](https://github.com/your-org/splunk-community-mcp/issues)

Security is hard to get right, and we're learning as we go. Your feedback helps us improve the balance between safety and usability.