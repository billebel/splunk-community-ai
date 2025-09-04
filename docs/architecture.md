# Pack Architecture - How It All Works Together

We're sharing what we've learned about building an AI assistant that actually knows how to work with Splunk, instead of just having access to Splunk APIs. Here's how the pieces fit together.

## The Core Problem We're Trying to Solve

**Naive approach:** Give AI a "run search" tool and hope it figures out what to do.
**Result:** Blind queries, inefficient searches, dangerous operations, poor results.

**Our approach:** We're trying to help AI discover, understand, and leverage your specific Splunk environment.
**Result:** Hopefully better queries that try to use existing knowledge and respect safety boundaries.

## The Architecture Layers

### 🔍 **Discovery Layer - Environment Intelligence**

**The challenge:** Every Splunk environment is different. You can't hardcode assumptions about what indexes, data types, or configurations exist.

**Our solution:** Discovery tools that help the AI understand your specific setup.

```
list_indexes → "What data repositories exist in this environment?"
get_sourcetypes → "What data formats are available in each index?"
get_hosts → "What systems are generating data here?"
find_data_sources → "Translate 'authentication logs' to actual index/sourcetype combinations"
```

**Why transforms matter here:** Raw Splunk API responses are XML/JSON designed for web interfaces, not AI analysis. The `discovery.py` transform:
- Cleans messy API responses into structured data
- Filters out internal/system indexes unless requested
- Adds usage examples and context the AI needs
- Provides ready-to-use search patterns

**Example:** User asks "show me web server errors"
1. AI calls `find_data_sources` with "web server errors"
2. Transform returns: `{"index": "web", "sourcetype": "apache_error", "example_search": "index=web sourcetype=apache_error status>=400"}`
3. AI uses this specific pattern instead of guessing

### 🧠 **Knowledge Layer - Leverage Existing Intelligence**

**The challenge:** Your Splunk environment already has tons of intelligence - data models, event types, search macros, field extractions. Most tools ignore this and make everything from scratch.

**Our solution:** Knowledge object tools that discover and leverage existing configurations.

```
get_data_models → "What accelerated structures exist for 100x faster queries?"
get_event_types → "What existing event categorizations can I reuse?"
get_search_macros → "What established search patterns already exist?"
get_field_extractions → "How is this data already structured?"
```

**Why transforms matter here:** The `knowledge.py` transform:
- Identifies which data models are accelerated (ready for tstats)
- Provides usage examples for each knowledge object
- Explains performance benefits (when to use tstats vs regular search)
- Shows field mappings and relationships

**Example:** User wants authentication statistics
1. AI calls `get_data_models` 
2. Transform identifies "Authentication" data model is accelerated
3. AI constructs fast tstats query instead of slow regular search
4. Result: 100x faster execution on large datasets

### 🛡️ **Safety Layer - Trying to Add Guardrails**

**The challenge:** AI assistants can accidentally run expensive or dangerous operations. Traditional approaches either block everything (too restrictive) or allow everything (too dangerous).

**Our solution:** We're experimenting with guardrails that try to understand intent and adapt to user expertise.

**What we're trying to do with the `guardrails.py` transform:**
- **Query analysis:** Detects destructive operations, expensive patterns, security risks
- **Dynamic limits:** Adjusts based on query type, time range, user role
- **Data privacy:** Applies masking rules based on field content and user permissions  
- **Performance protection:** Prevents resource-exhaustive operations
- **Audit compliance:** Logs all interactions for security review

**Example:** User asks for "all login events ever"
1. Guardrails detect overly broad time range
2. AI suggests: "That's a lot of data. How about the last 24 hours to start?"
3. If user confirms, guardrails add automatic result limits
4. Query executes safely with built-in boundaries

### 🎯 **Behavior Layer - Trying to Guide AI**

**The challenge:** Even with good tools, an AI needs to know HOW to use them effectively - what order, when to confirm vs execute, how to adapt to different request types.

**Our solution:** We're experimenting with system prompts that try to guide AI behavior.

**What we're trying to do with the prompts:**
- **Decision trees:** "For common requests → use find_data_sources first → get ready-made patterns"
- **Confirmation rules:** "Auto-execute if ≤4 hours and ≤100 results, otherwise confirm"
- **Performance guidance:** "Always use index filters, prefer tstats when available"
- **Ready-to-use SPL:** Embedded query patterns for immediate use

**Example workflow:**
```
User: "Show me failed SSH logins from external IPs"

AI system prompt logic:
1. This is authentication + network analysis → use find_data_sources
2. Get patterns for "ssh" and "external" 
3. Time range not specified → apply default 24h window
4. External IPs = performance consideration → confirm scope
5. Construct: index=security sourcetype=ssh action=failure NOT src=192.168.* NOT src=10.*
6. Execute with result limits applied
```

## How Advanced Logic Works

### **Pattern 1: Adaptive Discovery**
```python
# In discovery.py transform
def find_data_sources(search_term, user_context):
    # Match business terms to technical terms
    patterns = {
        "authentication": ["login", "auth", "ldap", "kerberos"],
        "network": ["firewall", "dns", "proxy", "vpn"],
        "web": ["apache", "nginx", "http", "ssl"]
    }
    
    # Return environment-specific mappings
    # Not hardcoded - discovers what actually exists
```

### **Pattern 2: Performance Optimization**
```python
# In knowledge.py transform  
def suggest_search_optimization(query, available_data_models):
    # If query matches accelerated data model pattern
    if "authentication" in query and "Authentication" in data_models:
        # Rewrite as tstats query for 100x speed improvement
        return convert_to_tstats(query, "Authentication")
```

### **Pattern 3: Context-Aware Safety**
```python
# In guardrails.py transform
def validate_query_safety(query, user_role, environment_context):
    # Adapt limits based on context
    if user_role == "admin" and environment_context["size"] == "small":
        return apply_relaxed_limits(query)
    elif "production" in environment_context["tags"]:
        return apply_strict_limits(query)
```

## Why This Architecture Matters

### **For Users:**
- **Smarter results:** AI uses your existing Splunk intelligence instead of starting from scratch
- **Safer operations:** Guardrails adapt to your environment and expertise level
- **Faster searches:** Automatically uses optimized data models and patterns
- **Learning system:** Discovers and leverages your specific configurations

### **For Developers:**
- **Extensible logic:** Add new discovery patterns, safety rules, optimization logic
- **Environment adaptation:** Transforms can detect and adapt to different Splunk setups
- **Layered intelligence:** Separate concerns (discovery, safety, optimization, behavior)
- **Testable components:** Each transform can be tested and validated independently

## What We're Still Figuring Out

### **Discovery Intelligence**
- Better pattern matching for business terms → technical terms
- Automatic detection of data quality and completeness
- Learning from user corrections and preferences

### **Safety Adaptation**  
- How to balance safety with user expertise levels
- Environment-specific risk assessment
- Adaptive confirmation thresholds

### **Performance Intelligence**
- Automatic query optimization recommendations
- Resource usage prediction and management
- Intelligent caching and result reuse

## Extending the Architecture

Want to add advanced logic? Here's how:

### **Add Discovery Intelligence**
```python
# In transforms/discovery.py
def find_data_sources(search_term, variables):
    # Your custom logic here
    # - Machine learning pattern matching
    # - Integration with CMDB/asset management
    # - Custom business term mappings
```

### **Add Safety Rules**
```python
# In transforms/guardrails.py  
def validate_search_query(query, user_context):
    # Your custom validation logic
    # - Integration with identity management
    # - Environment-specific policies
    # - Compliance requirements
```

### **Add Optimization Logic**
```python
# In transforms/knowledge.py
def optimize_search_performance(query, environment):
    # Your custom optimization
    # - Automatic index selection
    # - Query rewriting for performance
    # - Resource allocation management
```

The architecture is designed to grow with your needs. Each layer can be extended independently, and the AI will automatically use your new intelligence.

We'd love to see what advanced logic you build with this foundation!