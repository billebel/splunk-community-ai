"""
Tests for Schedule Management functionality
"""

import pytest
import sys
import os

# Add the transforms directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'transforms'))

from schedule_management import (
    create_scheduled_search,
    analyze_schedule_conflicts,
    update_search_schedule,
    delete_scheduled_search,
    validate_search_performance,
    optimize_search_schedules
)

class TestScheduledSearchCreation:
    """Test scheduled search creation functionality"""

    def test_create_scheduled_search_success(self):
        """Test successful scheduled search creation"""
        data = {
            'parameters': {
                'search_name': 'Test Security Monitor',
                'search_query': 'index=security action=failure | stats count by user',
                'schedule_requirement': 'every 15 minutes',
                'business_priority': 'Critical security monitoring',
                'data_freshness': '10 minutes',
                'app_context': 'security'
            }
        }

        result = create_scheduled_search(data)

        assert result['success'] == True
        assert result['operation'] == 'create_scheduled_search'
        assert result['search_name'] == 'Test Security Monitor'
        assert 'schedule' in result
        assert 'cron_expression' in result['schedule']
        assert result['complexity_analysis']['performance_impact'] in ['low', 'medium', 'high']

    def test_create_scheduled_search_missing_parameters(self):
        """Test scheduled search creation with missing parameters"""
        data = {
            'parameters': {
                'search_name': 'Test Search'
                # Missing required parameters
            }
        }

        result = create_scheduled_search(data)

        assert result['success'] == False
        assert 'Missing required parameters' in result['error']

    def test_create_scheduled_search_invalid_name(self):
        """Test scheduled search creation with invalid name"""
        data = {
            'parameters': {
                'search_name': '123invalid!@#',
                'search_query': 'index=test | stats count',
                'schedule_requirement': 'daily',
                'business_priority': 'Medium'
            }
        }

        result = create_scheduled_search(data)

        assert result['success'] == False
        assert 'name must start with letter' in result['error']

    def test_create_scheduled_search_dangerous_query(self):
        """Test scheduled search with dangerous SPL"""
        data = {
            'parameters': {
                'search_name': 'Dangerous Search',
                'search_query': 'index=test | delete',
                'schedule_requirement': 'hourly',
                'business_priority': 'Low'
            }
        }

        result = create_scheduled_search(data)

        assert result['success'] == False
        assert 'dangerous commands' in result['error']

class TestScheduleRequirementParsing:
    """Test schedule requirement parsing"""

    def test_parse_minute_intervals(self):
        """Test parsing minute-based schedules"""
        test_cases = [
            ('every 15 minutes', '*/15 * * * *'),
            ('every 30 minutes', '*/30 * * * *'),
            ('every 5 min', '*/5 * * * *'),
        ]

        from schedule_management import ScheduleManager
        manager = ScheduleManager()

        for requirement, expected_pattern in test_cases:
            result = manager._parse_schedule_requirement(requirement)
            assert result['success'] == True
            assert '15' in result['cron_expression'] or '30' in result['cron_expression'] or '5' in result['cron_expression']

    def test_parse_daily_schedules(self):
        """Test parsing daily schedules"""
        test_cases = [
            'daily at 8am',
            'daily at 2pm',
            'daily',
            'every day'
        ]

        from schedule_management import ScheduleManager
        manager = ScheduleManager()

        for requirement in test_cases:
            result = manager._parse_schedule_requirement(requirement)
            assert result['success'] == True
            # Should contain daily pattern
            assert '*' in result['cron_expression']

    def test_parse_invalid_schedule(self):
        """Test parsing invalid schedule requirements"""
        invalid_requirements = [
            'whenever I feel like it',
            'randomly',
            'maybe sometimes'
        ]

        from schedule_management import ScheduleManager
        manager = ScheduleManager()

        for requirement in invalid_requirements:
            result = manager._parse_schedule_requirement(requirement)
            assert result['success'] == False
            assert 'suggestions' in result

class TestScheduleConflictAnalysis:
    """Test schedule conflict analysis"""

    def test_analyze_schedule_conflicts_success(self):
        """Test successful conflict analysis"""
        data = {
            'parameters': {
                'analysis_scope': 'all',
                'conflict_threshold': 3
            }
        }

        result = analyze_schedule_conflicts(data)

        assert result['success'] == True
        assert 'conflict_summary' in result
        assert 'recommendations' in result
        assert 'optimal_time_slots' in result

    def test_analyze_conflicts_with_custom_threshold(self):
        """Test conflict analysis with custom threshold"""
        data = {
            'parameters': {
                'analysis_scope': 'business_hours',
                'conflict_threshold': 10
            }
        }

        result = analyze_schedule_conflicts(data)

        assert result['success'] == True
        assert result['conflict_summary']['conflict_threshold'] == 10

class TestSearchPerformanceValidation:
    """Test search performance validation"""

    def test_validate_simple_search(self):
        """Test validation of simple search"""
        data = {
            'parameters': {
                'search_query': 'index=security | stats count by user',
                'expected_frequency': 'every hour'
            }
        }

        result = validate_search_performance(data)

        assert result['success'] == True
        assert 'search_analysis' in result
        assert 'performance_score' in result
        assert result['search_analysis']['performance_impact'] in ['low', 'medium', 'high']

    def test_validate_complex_search(self):
        """Test validation of complex search"""
        data = {
            'parameters': {
                'search_query': 'index=* | join type=outer src_ip [search index=threat_intel] | stats count',
                'expected_frequency': 'every 5 minutes'
            }
        }

        result = validate_search_performance(data)

        assert result['success'] == True
        assert len(result['warnings']) > 0  # Should have warnings for complex search with high frequency
        assert len(result['recommendations']) > 0

    def test_validate_wildcard_index_search(self):
        """Test validation of wildcard index search"""
        data = {
            'parameters': {
                'search_query': 'index=* error | head 100',
                'expected_frequency': 'every 10 minutes'
            }
        }

        result = validate_search_performance(data)

        assert result['success'] == True
        assert any('wildcard' in warning.lower() for warning in result['warnings'])
        assert any('index' in rec.lower() for rec in result['recommendations'])

class TestScheduleUpdates:
    """Test schedule update functionality"""

    def test_update_search_schedule_success(self):
        """Test successful schedule update"""
        data = {
            'parameters': {
                'search_name': 'Existing Search',
                'new_schedule': 'every 30 minutes',
                'reason': 'Reduce resource usage'
            }
        }

        result = update_search_schedule(data)

        assert result['success'] == True
        assert result['operation'] == 'update_search_schedule'
        assert result['search_name'] == 'Existing Search'
        assert result['reason'] == 'Reduce resource usage'

    def test_update_search_schedule_missing_params(self):
        """Test schedule update with missing parameters"""
        data = {
            'parameters': {
                'search_name': 'Test Search'
                # Missing new_schedule and reason
            }
        }

        result = update_search_schedule(data)

        assert result['success'] == False
        assert 'Missing required parameters' in result['error']

class TestScheduleOptimization:
    """Test schedule optimization functionality"""

    def test_optimize_schedules_preview(self):
        """Test schedule optimization in preview mode"""
        data = {
            'parameters': {
                'optimization_strategy': 'balanced',
                'business_constraints': 'Executive reports must complete by 8am',
                'apply_changes': False
            }
        }

        result = optimize_search_schedules(data)

        assert result['success'] == True
        assert result['applied'] == False
        assert 'optimization_summary' in result
        assert 'optimizations' in result
        assert len(result['next_steps']) > 0

    def test_optimize_schedules_apply(self):
        """Test schedule optimization with application"""
        data = {
            'parameters': {
                'optimization_strategy': 'performance',
                'apply_changes': True
            }
        }

        result = optimize_search_schedules(data)

        assert result['success'] == True
        assert result['applied'] == True
        assert 'optimization_summary' in result

class TestScheduleDeletion:
    """Test scheduled search deletion"""

    def test_delete_scheduled_search_success(self):
        """Test successful deletion"""
        data = {
            'parameters': {
                'search_name': 'Test Search',
                'confirm_deletion': True,
                'check_dependencies': True
            }
        }

        result = delete_scheduled_search(data)

        assert result['success'] == True
        assert result['operation'] == 'delete_scheduled_search'
        assert result['search_name'] == 'Test Search'

    def test_delete_scheduled_search_not_confirmed(self):
        """Test deletion without confirmation"""
        data = {
            'parameters': {
                'search_name': 'Test Search',
                'confirm_deletion': False
            }
        }

        result = delete_scheduled_search(data)

        assert result['success'] == False
        assert 'not confirmed' in result['error']

class TestComplexityAnalysis:
    """Test search complexity analysis"""

    def test_analyze_simple_search_complexity(self):
        """Test complexity analysis of simple search"""
        from schedule_management import ScheduleManager
        manager = ScheduleManager()

        simple_query = "index=security action=failure | stats count by user"
        result = manager._analyze_search_complexity(simple_query)

        assert result['complexity_score'] >= 0
        assert result['performance_impact'] in ['low', 'medium', 'high']
        assert result['estimated_runtime'] is not None

    def test_analyze_complex_search_complexity(self):
        """Test complexity analysis of complex search"""
        from schedule_management import ScheduleManager
        manager = ScheduleManager()

        complex_query = "index=* | join type=outer src_ip [search index=* earliest=0] | stats count"
        result = manager._analyze_search_complexity(complex_query)

        assert result['complexity_score'] > 5  # Should be high due to wildcards and joins
        assert result['performance_impact'] == 'high'
        assert len(result['performance_notes']) > 0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])