# Usage Examples

Here are some real scenarios we've tried with the pack. Results will vary depending on your data and setup, but these should give you ideas for what's possible.

> **Want to understand how the AI gets so smart?** Check out [Pack Architecture](architecture.md) to see how tools + transforms create the intelligent behavior you see in these examples.

## SOC Analyst Scenarios

### Finding Failed Authentication Events
```
You: "Show me failed authentication events in the last hour"

What the AI does:
1. Calls list_indexes → finds 'security', 'windows', 'auth'
2. Calls get_event_types → discovers 'failed_login', 'authentication_failure'
3. Constructs search → eventtype="failed_login" earliest=-1h
4. Calls execute_splunk_search with the constructed query
5. Analyzes results → groups by source IP, identifies patterns

What you might see:
"Found 23 failed login attempts in the last hour:
- 15 attempts from 192.168.1.50 targeting 'admin' account
- 5 attempts from 10.0.0.100 with various usernames
- 3 attempts from internal systems (likely legitimate retries)

The activity from 192.168.1.50 looks suspicious - consistent timing suggests automation."
```

### Investigating Unusual Network Traffic
```
You: "Any weird network activity in the firewall logs today?"

What happens:
1. Discovers network-related indexes
2. Finds relevant data models (Network_Traffic, etc.)
3. Constructs search using accelerated data
4. Looks for statistical outliers in connections, protocols, data volumes
5. Correlates with threat intelligence if available

Results depend on your data, but might find things like:
- Unusual outbound connections to external IPs
- Protocol anomalies (unexpected ports/services)
- Data exfiltration patterns
- Scan activity
```

## Threat Hunting

### PowerShell Analysis
```
You: "Look for suspicious PowerShell activity across endpoints"

AI workflow:
1. Finds endpoint/sysmon data sources
2. Discovers PowerShell-related event types or data models
3. Searches for PowerShell events with suspicious characteristics:
   - Encoded commands (base64, hex)
   - Network connections from PowerShell
   - Downloaded/executed content
   - Bypass techniques
4. Correlates across multiple endpoints
5. Builds timeline of related activities

Might identify:
- Encoded PowerShell commands
- Downloads from suspicious domains
- Lateral movement patterns
- Persistence mechanisms
```

### DNS Tunneling Detection
```
You: "Check if anyone's using DNS for data exfiltration"

The AI approach:
1. Locates DNS logs in your environment
2. Analyzes query patterns for anomalies:
   - Unusually long domain names
   - High volume of TXT queries
   - Entropy analysis of subdomain patterns
   - Frequency analysis
3. Correlates with endpoint activity
4. Identifies potential command and control

This is still experimental - we're learning what patterns work best.
```

## Incident Response

### User Activity Timeline
```
You: "Show me everything user john.doe did yesterday"

AI process:
1. Discovers authentication sources (AD, VPN, applications)
2. Finds relevant activity logs (email, file access, network, etc.)
3. Correlates events by username across data sources
4. Builds chronological timeline
5. Identifies unusual patterns or activities

Creates a comprehensive view:
- Login/logout times and locations
- File and system access
- Network connections
- Application usage
- Any security events involving that user
```

### Malware Investigation
```
You: "We found malware on host WIN-SERVER01, what else did it do?"

Investigation flow:
1. Searches for all activity from that host
2. Looks for indicators of compromise:
   - Process creation events
   - Network connections
   - File modifications
   - Registry changes
3. Identifies lateral movement attempts
4. Checks other hosts for similar activity
5. Builds attack timeline

Helps answer:
- How did it get there?
- What did it do?
- Where did it spread?
- What data was affected?
```

## Dashboard Creation

### Authentication Monitoring Dashboard
```
You: "Create a dashboard to monitor authentication failures"

AI builds dashboard with:
1. Failed login attempts over time
2. Top source IPs for failures
3. Most targeted accounts
4. Success vs failure ratios
5. Geographic distribution if GeoIP available

Provides both the searches and suggested visualization types.
```

### Network Security Overview
```
You: "I need a network security dashboard for management"

Results in dashboard showing:
- Top talkers and protocols
- Blocked vs allowed connections
- Threat indicators (if you have threat feeds)
- Bandwidth utilization
- Geographic traffic patterns

Tailored to what data sources you actually have available.
```

## System Administration

### Performance Monitoring
```
You: "Is our Splunk environment healthy?"

Health check includes:
1. Index sizes and growth rates
2. Search performance metrics
3. License usage
4. System resource utilization
5. Failed searches and errors

Identifies potential issues before they become problems.
```

### Data Quality Assessment
```
You: "Are we missing any expected log sources?"

Analysis approach:
1. Catalogs current data sources
2. Checks for gaps in expected logs
3. Identifies hosts that stopped sending data
4. Looks for data format changes
5. Suggests investigation priorities

Helps maintain visibility across your environment.
```

## What Works Well vs What's Tricky

### ✅ Usually Works Well
- Finding specific events by type or pattern
- Time-based analysis and trending
- Basic correlation across data sources
- System health and performance checks
- Building simple dashboards and searches

### 🤔 Sometimes Challenging
- Complex multi-step investigations
- Advanced statistical analysis
- Custom field extractions on the fly
- Very specific technical details
- Integration with external tools

### 🚧 Still Working On
- Advanced machine learning detection
- Complex behavioral analysis
- Multi-tenant environments
- Very large dataset analysis
- Custom app integrations

## Tips for Better Results

### Be Specific About Time Ranges
```
Good: "Show me failed logins in the last 2 hours"
Less good: "Show me failed logins" (AI has to guess time range)
```

### Mention Your Environment Context
```
Helpful: "Check our Windows domain controllers for authentication issues"
Less helpful: "Check for authentication issues" (AI has to discover what you have)
```

### Start Broad, Then Narrow Down
```
Effective approach:
1. "What security data do we have available?"
2. "Show me authentication events from the last day"
3. "Focus on the failed login attempts from external IPs"
4. "Investigate the activity from 192.168.1.50"
```

## Your Mileage May Vary

These examples assume:
- You have relevant data sources configured
- Your Splunk environment is set up with reasonable field extractions
- The AI has necessary permissions to search your data

Every environment is different, and we're still learning what works best in different setups. If you find patterns that work well (or don't work), please [share them with us](https://github.com/billebel/splunk-community-ai/discussions)!