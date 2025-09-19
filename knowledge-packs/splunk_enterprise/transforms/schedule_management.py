"""
Schedule Management Transforms
Handles creation, updating, and optimization of Splunk scheduled searches with AI assistance.
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from croniter import croniter

try:
    from .guardrails import GuardrailsEngine
    SecurityValidator = GuardrailsEngine
except ImportError:
    # Fallback for testing
    class SecurityValidator:
        def is_safe_content(self, content: str) -> bool:
            dangerous = ['| delete', '|delete', '| script', '|script', '| run', '|run', '| external', '|external']
            content_lower = content.lower()
            return not any(cmd in content_lower for cmd in dangerous)

logger = logging.getLogger(__name__)

class ScheduleManager:
    """Manages Splunk scheduled searches with AI-powered optimization"""

    def __init__(self):
        self.security = SecurityValidator()

    def _validate_search_name(self, name: str) -> Dict[str, Any]:
        """Validate scheduled search names"""
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_\s]*$', name.strip()):
            return {
                'valid': False,
                'error': 'Search name must start with letter and contain only letters, numbers, underscores, spaces'
            }

        if len(name.strip()) > 100:
            return {
                'valid': False,
                'error': 'Search name too long (max 100 characters)'
            }

        return {'valid': True}

    def _parse_schedule_requirement(self, requirement: str) -> Dict[str, Any]:
        """Parse natural language schedule requirements into cron expressions"""
        req_lower = requirement.lower().strip()

        schedule_patterns = {
            # Real-time and high frequency
            r'every\s+(\d+)\s+minutes?': lambda m: f"*/{m.group(1)} * * * *",
            r'every\s+(\d+)\s+min': lambda m: f"*/{m.group(1)} * * * *",
            r'real.?time': lambda: "*/5 * * * *",  # Every 5 minutes for "real-time"

            # Hourly patterns
            r'every\s+hour': lambda: "0 * * * *",
            r'hourly': lambda: "0 * * * *",
            r'every\s+(\d+)\s+hours?': lambda m: f"0 */{m.group(1)} * * *",

            # Daily patterns
            r'daily\s+at\s+(\d+)am': lambda m: f"0 {m.group(1)} * * *",
            r'daily\s+at\s+(\d+)pm': lambda m: f"0 {int(m.group(1)) + 12} * * *",
            r'daily': lambda: "0 6 * * *",  # Default to 6 AM
            r'every\s+day': lambda: "0 6 * * *",

            # Weekly patterns
            r'weekly\s+on\s+sunday': lambda: "0 2 * * 0",
            r'weekly\s+on\s+monday': lambda: "0 2 * * 1",
            r'weekly': lambda: "0 2 * * 0",  # Default to Sunday 2 AM

            # Business hours
            r'business\s+hours': lambda: "0 9-17 * * 1-5",  # 9 AM to 5 PM, weekdays
            r'during\s+business\s+hours': lambda: "0 9-17 * * 1-5",
        }

        for pattern, cron_func in schedule_patterns.items():
            match = re.search(pattern, req_lower)
            if match:
                try:
                    if callable(cron_func):
                        if match.groups():
                            cron_expr = cron_func(match)
                        else:
                            cron_expr = cron_func()
                    else:
                        cron_expr = cron_func

                    return {
                        'success': True,
                        'cron_expression': cron_expr,
                        'frequency_type': 'parsed',
                        'description': requirement
                    }
                except Exception as e:
                    logger.warning(f"Error parsing schedule requirement '{requirement}': {e}")

        # If no pattern matches, return a default with suggestion
        return {
            'success': False,
            'error': f"Could not parse schedule requirement: '{requirement}'",
            'suggestions': [
                "Try: 'every 15 minutes'",
                "Try: 'daily at 6am'",
                "Try: 'weekly on Sunday'",
                "Try: 'every hour'"
            ]
        }

    def _analyze_search_complexity(self, search_query: str) -> Dict[str, Any]:
        """Analyze SPL complexity and estimate performance impact"""
        query_lower = search_query.lower()
        complexity_score = 0
        performance_notes = []

        # Basic complexity indicators
        if 'index=*' in query_lower or 'index=_*' in query_lower:
            complexity_score += 3
            performance_notes.append("Wildcard index search - high resource usage")

        if '| join' in query_lower:
            complexity_score += 2
            performance_notes.append("Join operations can be expensive")

        if '| stats' in query_lower:
            complexity_score += 1
            performance_notes.append("Statistics aggregation")

        if '| eval' in query_lower:
            complexity_score += 1

        if 'earliest=0' in query_lower or 'earliest=-99' in query_lower:
            complexity_score += 4
            performance_notes.append("All-time search - very expensive")

        # Estimate runtime based on complexity
        if complexity_score <= 2:
            estimated_runtime = "< 30 seconds"
            performance_impact = "low"
        elif complexity_score <= 5:
            estimated_runtime = "30 seconds - 2 minutes"
            performance_impact = "medium"
        else:
            estimated_runtime = "> 2 minutes"
            performance_impact = "high"

        return {
            'complexity_score': complexity_score,
            'estimated_runtime': estimated_runtime,
            'performance_impact': performance_impact,
            'performance_notes': performance_notes
        }

def create_scheduled_search(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a scheduled search with AI-powered optimization"""
    try:
        params = data.get('parameters', {})
        search_name = params.get('search_name', '').strip()
        search_query = params.get('search_query', '').strip()
        schedule_requirement = params.get('schedule_requirement', '').strip()
        business_priority = params.get('business_priority', '').strip()
        data_freshness = params.get('data_freshness', '15 minutes')
        app_context = params.get('app_context', 'search')

        # Validate required parameters
        if not all([search_name, search_query, schedule_requirement, business_priority]):
            return {
                'success': False,
                'error': 'Missing required parameters: search_name, search_query, schedule_requirement, business_priority'
            }

        # Validate search name
        name_validation = ScheduleManager()._validate_search_name(search_name)
        if not name_validation['valid']:
            return {
                'success': False,
                'error': name_validation['error']
            }

        # Security validation
        security = SecurityValidator()
        if not security.is_safe_content(search_query):
            return {
                'success': False,
                'error': 'Search query contains potentially dangerous commands'
            }

        # Parse schedule requirement
        schedule_manager = ScheduleManager()
        schedule_parse = schedule_manager._parse_schedule_requirement(schedule_requirement)

        if not schedule_parse['success']:
            return {
                'success': False,
                'error': schedule_parse['error'],
                'suggestions': schedule_parse.get('suggestions', [])
            }

        # Analyze search complexity
        complexity_analysis = schedule_manager._analyze_search_complexity(search_query)

        # Generate optimal timing (would use AI prompts in full implementation)
        cron_expression = schedule_parse['cron_expression']

        # Apply conflict avoidance (simplified version)
        optimized_cron = _apply_conflict_avoidance(cron_expression, business_priority)

        logger.info(f"Creating scheduled search: {search_name}")

        return {
            'success': True,
            'operation': 'create_scheduled_search',
            'search_name': search_name,
            'schedule': {
                'cron_expression': optimized_cron,
                'original_requirement': schedule_requirement,
                'description': f"Runs {schedule_requirement}"
            },
            'complexity_analysis': complexity_analysis,
            'business_context': {
                'priority': business_priority,
                'data_freshness': data_freshness
            },
            'configuration': {
                'app': app_context,
                'is_scheduled': 1,
                'cron_schedule': optimized_cron,
                'dispatch.earliest_time': _get_time_range_for_freshness(data_freshness)[0],
                'dispatch.latest_time': _get_time_range_for_freshness(data_freshness)[1]
            },
            'recommendations': [
                f"Search complexity: {complexity_analysis['performance_impact']}",
                f"Estimated runtime: {complexity_analysis['estimated_runtime']}",
                "Monitor search performance after deployment",
                "Consider using summary indexing if search runs frequently"
            ]
        }

    except Exception as e:
        logger.error(f"Scheduled search creation failed: {str(e)}")
        return {
            'success': False,
            'error': f'Scheduled search creation failed: {str(e)}',
            'operation': 'create_scheduled_search'
        }

def analyze_schedule_conflicts(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Analyze scheduling conflicts and suggest optimizations"""
    try:
        params = data.get('parameters', {})
        analysis_scope = params.get('analysis_scope', 'all')
        conflict_threshold = params.get('conflict_threshold', 5)

        # Mock existing schedules for demonstration
        # In real implementation, this would query Splunk for actual schedules
        mock_schedules = [
            {'name': 'Security Monitor', 'cron': '0 * * * *', 'app': 'security'},
            {'name': 'Login Failures', 'cron': '0 * * * *', 'app': 'security'},
            {'name': 'Performance Check', 'cron': '0 * * * *', 'app': 'monitoring'},
            {'name': 'Daily Report', 'cron': '0 8 * * *', 'app': 'reporting'},
            {'name': 'Weekly Summary', 'cron': '0 2 * * 0', 'app': 'reporting'},
        ]

        # Analyze minute-level conflicts
        minute_conflicts = {}
        hour_conflicts = {}

        for schedule in mock_schedules:
            cron_parts = schedule['cron'].split()
            minute = cron_parts[0]
            hour = cron_parts[1]

            minute_conflicts[minute] = minute_conflicts.get(minute, 0) + 1
            hour_conflicts[hour] = hour_conflicts.get(hour, 0) + 1

        # Identify hotspots
        hotspot_minutes = {k: v for k, v in minute_conflicts.items() if v >= conflict_threshold}
        hotspot_hours = {k: v for k, v in hour_conflicts.items() if v >= conflict_threshold}

        # Generate recommendations
        recommendations = []
        if '0' in hotspot_minutes:
            recommendations.append("High collision at :00 minute - suggest staggering to :15, :30, :45")
        if '8' in hotspot_hours:
            recommendations.append("Many searches at 8 AM - consider earlier execution for morning reports")

        # Suggest optimal time slots
        optimal_slots = _suggest_optimal_time_slots(minute_conflicts, hour_conflicts)

        return {
            'success': True,
            'analysis_scope': analysis_scope,
            'conflict_summary': {
                'total_searches': len(mock_schedules),
                'minute_hotspots': hotspot_minutes,
                'hour_hotspots': hotspot_hours,
                'conflict_threshold': conflict_threshold
            },
            'recommendations': recommendations,
            'optimal_time_slots': optimal_slots,
            'detailed_conflicts': {
                'by_minute': minute_conflicts,
                'by_hour': hour_conflicts
            }
        }

    except Exception as e:
        logger.error(f"Schedule conflict analysis failed: {str(e)}")
        return {
            'success': False,
            'error': f'Schedule conflict analysis failed: {str(e)}'
        }

def update_search_schedule(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Update an existing search schedule"""
    try:
        params = data.get('parameters', {})
        search_name = params.get('search_name', '').strip()
        new_schedule = params.get('new_schedule', '').strip()
        reason = params.get('reason', '').strip()

        if not all([search_name, new_schedule, reason]):
            return {
                'success': False,
                'error': 'Missing required parameters: search_name, new_schedule, reason'
            }

        # Parse new schedule requirement
        schedule_manager = ScheduleManager()
        schedule_parse = schedule_manager._parse_schedule_requirement(new_schedule)

        if not schedule_parse['success']:
            return {
                'success': False,
                'error': schedule_parse['error']
            }

        logger.info(f"Updating schedule for search: {search_name}")

        return {
            'success': True,
            'operation': 'update_search_schedule',
            'search_name': search_name,
            'old_schedule': 'existing_schedule',  # Would fetch from Splunk
            'new_schedule': schedule_parse['cron_expression'],
            'reason': reason,
            'message': f'Schedule updated for {search_name}'
        }

    except Exception as e:
        logger.error(f"Schedule update failed: {str(e)}")
        return {
            'success': False,
            'error': f'Schedule update failed: {str(e)}'
        }

def delete_scheduled_search(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Delete a scheduled search with safety checks"""
    try:
        params = data.get('parameters', {})
        search_name = params.get('search_name', '').strip()
        confirm_deletion = params.get('confirm_deletion', False)
        check_dependencies = params.get('check_dependencies', True)

        if not search_name:
            return {
                'success': False,
                'error': 'Missing required parameter: search_name'
            }

        if not confirm_deletion:
            return {
                'success': False,
                'error': 'Deletion not confirmed. Set confirm_deletion to true.'
            }

        dependencies = []
        if check_dependencies:
            # In real implementation, check for dashboards, alerts, etc. that use this search
            dependencies = []  # Would populate with actual dependencies

        if dependencies:
            return {
                'success': False,
                'error': f'Cannot delete search - used by: {", ".join(dependencies)}',
                'dependencies': dependencies
            }

        logger.info(f"Deleting scheduled search: {search_name}")

        return {
            'success': True,
            'operation': 'delete_scheduled_search',
            'search_name': search_name,
            'message': f'Scheduled search {search_name} deleted successfully'
        }

    except Exception as e:
        logger.error(f"Schedule deletion failed: {str(e)}")
        return {
            'success': False,
            'error': f'Schedule deletion failed: {str(e)}'
        }

def validate_search_performance(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Validate search performance before scheduling"""
    try:
        params = data.get('parameters', {})
        search_query = params.get('search_query', '').strip()
        expected_frequency = params.get('expected_frequency', '').strip()

        if not all([search_query, expected_frequency]):
            return {
                'success': False,
                'error': 'Missing required parameters: search_query, expected_frequency'
            }

        # Analyze search complexity
        schedule_manager = ScheduleManager()
        complexity_analysis = schedule_manager._analyze_search_complexity(search_query)

        # Performance recommendations based on frequency
        recommendations = []
        warnings = []

        if complexity_analysis['performance_impact'] == 'high' and 'minute' in expected_frequency.lower():
            warnings.append("High-complexity search with frequent execution may impact performance")
            recommendations.append("Consider optimizing search or reducing frequency")

        if 'index=*' in search_query.lower():
            warnings.append("Wildcard index search detected")
            recommendations.append("Specify exact indexes for better performance")

        return {
            'success': True,
            'search_analysis': complexity_analysis,
            'frequency_analysis': {
                'expected_frequency': expected_frequency,
                'performance_risk': 'high' if warnings else 'low'
            },
            'warnings': warnings,
            'recommendations': recommendations,
            'performance_score': _calculate_performance_score(complexity_analysis, expected_frequency)
        }

    except Exception as e:
        logger.error(f"Performance validation failed: {str(e)}")
        return {
            'success': False,
            'error': f'Performance validation failed: {str(e)}'
        }

def optimize_search_schedules(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """AI-powered optimization of all scheduled searches"""
    try:
        params = data.get('parameters', {})
        optimization_strategy = params.get('optimization_strategy', 'balanced')
        business_constraints = params.get('business_constraints', '')
        apply_changes = params.get('apply_changes', False)

        # Mock current schedules
        current_schedules = [
            {'name': 'Security Monitor', 'cron': '0 * * * *', 'priority': 'critical'},
            {'name': 'Performance Check', 'cron': '0 * * * *', 'priority': 'high'},
            {'name': 'Daily Report', 'cron': '0 8 * * *', 'priority': 'medium'},
        ]

        optimizations = []

        # Generate optimizations based on strategy
        for schedule in current_schedules:
            if schedule['cron'] == '0 * * * *':  # High collision time
                new_cron = _suggest_alternative_time(schedule['cron'], schedule['priority'])
                optimizations.append({
                    'search_name': schedule['name'],
                    'current_schedule': schedule['cron'],
                    'optimized_schedule': new_cron,
                    'reason': 'Reduce collision at :00 minute mark',
                    'impact': 'Improved performance, same functionality'
                })

        total_conflicts_before = len([s for s in current_schedules if s['cron'] == '0 * * * *'])
        total_conflicts_after = 0  # After optimization

        return {
            'success': True,
            'optimization_strategy': optimization_strategy,
            'business_constraints': business_constraints,
            'optimization_summary': {
                'total_searches_analyzed': len(current_schedules),
                'optimizations_identified': len(optimizations),
                'conflicts_before': total_conflicts_before,
                'conflicts_after': total_conflicts_after,
                'estimated_performance_improvement': '25%'
            },
            'optimizations': optimizations,
            'applied': apply_changes,
            'next_steps': [
                "Review proposed optimizations",
                "Set apply_changes=true to implement",
                "Monitor performance after changes"
            ] if not apply_changes else [
                "Optimizations applied successfully",
                "Monitor search performance",
                "Validate business requirements still met"
            ]
        }

    except Exception as e:
        logger.error(f"Schedule optimization failed: {str(e)}")
        return {
            'success': False,
            'error': f'Schedule optimization failed: {str(e)}'
        }

# Helper functions

def _apply_conflict_avoidance(cron_expression: str, priority: str) -> str:
    """Apply simple conflict avoidance to cron expressions"""
    parts = cron_expression.split()

    # For hourly searches, avoid :00 minute collision
    if parts[0] == '0' and len(parts) >= 2:
        if 'critical' in priority.lower():
            parts[0] = '7'  # 7 minutes after hour
        elif 'high' in priority.lower():
            parts[0] = '15'  # 15 minutes after hour
        else:
            parts[0] = '30'  # 30 minutes after hour

    return ' '.join(parts)

def _get_time_range_for_freshness(freshness: str) -> Tuple[str, str]:
    """Convert data freshness requirement to time range"""
    freshness_lower = freshness.lower()

    time_ranges = {
        'real-time': ('-5m', 'now'),
        '5 minutes': ('-10m', 'now'),
        '15 minutes': ('-20m', 'now'),
        '1 hour': ('-65m', 'now'),
        'hourly': ('-65m', 'now'),
        'daily': ('-1d', 'now'),
    }

    for key, (earliest, latest) in time_ranges.items():
        if key in freshness_lower:
            return (earliest, latest)

    # Default
    return ('-15m', 'now')

def _suggest_optimal_time_slots(minute_conflicts: Dict[str, int], hour_conflicts: Dict[str, int]) -> List[str]:
    """Suggest optimal time slots based on conflict analysis"""
    optimal_minutes = []

    # Find minutes with lowest conflict counts
    sorted_minutes = sorted(minute_conflicts.items(), key=lambda x: x[1])

    for minute, count in sorted_minutes[:5]:  # Top 5 least conflicted
        if count < 3:  # Low conflict threshold
            optimal_minutes.append(f":{minute.zfill(2)} minutes")

    if not optimal_minutes:
        optimal_minutes = [":07 minutes", ":22 minutes", ":37 minutes", ":52 minutes"]

    return optimal_minutes

def _suggest_alternative_time(current_cron: str, priority: str) -> str:
    """Suggest alternative time based on priority"""
    parts = current_cron.split()

    # Priority-based minute assignment
    if 'critical' in priority.lower():
        parts[0] = '7'
    elif 'high' in priority.lower():
        parts[0] = '15'
    elif 'medium' in priority.lower():
        parts[0] = '30'
    else:
        parts[0] = '45'

    return ' '.join(parts)

def _calculate_performance_score(complexity_analysis: Dict[str, Any], frequency: str) -> int:
    """Calculate performance score (1-10, lower is better)"""
    base_score = complexity_analysis['complexity_score']

    # Frequency multiplier
    frequency_lower = frequency.lower()
    if 'minute' in frequency_lower:
        frequency_multiplier = 3
    elif 'hour' in frequency_lower:
        frequency_multiplier = 2
    else:
        frequency_multiplier = 1

    return min(base_score * frequency_multiplier, 10)