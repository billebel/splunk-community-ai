"""
Tests for Dashboard Management functionality
"""

import pytest
import sys
import os
import json

# Add the transforms directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'transforms'))

from dashboard_management import (
    create_dashboard,
    add_dashboard_panel,
    optimize_dashboard,
    validate_dashboard,
    clone_dashboard,
    delete_dashboard,
    recommend_visualizations,
    export_dashboard,
    DashboardManager
)


class TestDashboardCreation:
    """Test dashboard creation functionality"""

    def test_create_dashboard_success(self):
        """Test successful dashboard creation"""
        data = {
            'parameters': {
                'dashboard_name': 'Security Monitoring Dashboard',
                'business_purpose': 'Monitor security threats and failed authentication attempts',
                'target_audience': 'Security analysts',
                'data_sources': 'index=security, index=authentication',
                'dashboard_type': 'studio',
                'refresh_frequency': '5 minutes'
            }
        }

        result = create_dashboard(data)

        assert result['success'] == True
        assert result['operation'] == 'create_dashboard'
        assert result['dashboard_name'] == 'Security Monitoring Dashboard'
        assert result['dashboard_type'] == 'studio'
        assert 'data_analysis' in result
        assert 'layout_optimization' in result
        assert 'dashboard_definition' in result
        assert len(result['recommendations']) > 0

    def test_create_dashboard_missing_parameters(self):
        """Test dashboard creation with missing parameters"""
        data = {
            'parameters': {
                'dashboard_name': 'Test Dashboard'
                # Missing required parameters
            }
        }

        result = create_dashboard(data)

        assert result['success'] == False
        assert 'Missing required parameters' in result['error']
        assert 'required_parameters' in result

    def test_create_dashboard_invalid_name(self):
        """Test dashboard creation with invalid name"""
        data = {
            'parameters': {
                'dashboard_name': '123invalid!@#',
                'business_purpose': 'Test purpose',
                'target_audience': 'Test audience',
                'data_sources': 'index=test'
            }
        }

        result = create_dashboard(data)

        assert result['success'] == False
        assert 'name must start with letter' in result['error']

    def test_create_dashboard_with_classic_type(self):
        """Test dashboard creation with classic type"""
        data = {
            'parameters': {
                'dashboard_name': 'Classic Dashboard',
                'business_purpose': 'Monitor operations',
                'target_audience': 'Operations team',
                'data_sources': 'index=infrastructure',
                'dashboard_type': 'classic'
            }
        }

        result = create_dashboard(data)

        assert result['success'] == True
        assert result['dashboard_type'] == 'classic'
        assert 'dashboard_definition' in result


class TestPanelAddition:
    """Test dashboard panel addition functionality"""

    def test_add_dashboard_panel_success(self):
        """Test successful panel addition"""
        data = {
            'parameters': {
                'dashboard_name': 'Existing Dashboard',
                'panel_purpose': 'Show failed login attempts over time',
                'search_query': 'index=security action=failure | timechart count by user',
                'panel_position': 'top-left'
            }
        }

        result = add_dashboard_panel(data)

        assert result['success'] == True
        assert result['operation'] == 'add_dashboard_panel'
        assert result['dashboard_name'] == 'Existing Dashboard'
        assert 'panel_config' in result
        assert 'visualization_options' in result['panel_config']
        assert len(result['recommendations']) > 0

    def test_add_dashboard_panel_missing_parameters(self):
        """Test panel addition with missing parameters"""
        data = {
            'parameters': {
                'dashboard_name': 'Test Dashboard'
                # Missing required parameters
            }
        }

        result = add_dashboard_panel(data)

        assert result['success'] == False
        assert 'Missing required parameters' in result['error']

    def test_add_dashboard_panel_complex_search(self):
        """Test panel addition with complex search"""
        data = {
            'parameters': {
                'dashboard_name': 'Performance Dashboard',
                'panel_purpose': 'Monitor response times with complex analysis',
                'search_query': 'index=* | join type=outer src_ip [search index=threat_intel] | stats avg(response_time)'
            }
        }

        result = add_dashboard_panel(data)

        assert result['success'] == True
        assert result['panel_config']['performance_analysis']['performance_impact'] == 'high'
        assert len(result['warnings']) > 0


class TestDashboardOptimization:
    """Test dashboard optimization functionality"""

    def test_optimize_dashboard_preview(self):
        """Test dashboard optimization in preview mode"""
        data = {
            'parameters': {
                'dashboard_name': 'Heavy Dashboard',
                'optimization_focus': 'performance',
                'apply_optimizations': False
            }
        }

        result = optimize_dashboard(data)

        assert result['success'] == True
        assert result['operation'] == 'optimize_dashboard'
        assert result['applied'] == False
        assert 'optimizations' in result
        assert 'performance_improvement' in result
        assert len(result['optimizations']) > 0

    def test_optimize_dashboard_balanced_focus(self):
        """Test dashboard optimization with balanced focus"""
        data = {
            'parameters': {
                'dashboard_name': 'Executive Dashboard',
                'optimization_focus': 'balanced'
            }
        }

        result = optimize_dashboard(data)

        assert result['success'] == True
        assert result['optimization_focus'] == 'balanced'
        assert 'optimization_summary' in result

    def test_optimize_dashboard_apply_changes(self):
        """Test dashboard optimization with applied changes"""
        data = {
            'parameters': {
                'dashboard_name': 'Test Dashboard',
                'optimization_focus': 'usability',
                'apply_optimizations': True
            }
        }

        result = optimize_dashboard(data)

        assert result['success'] == True
        assert result['applied'] == True
        assert 'application_results' in result

    def test_optimize_dashboard_missing_name(self):
        """Test dashboard optimization without dashboard name"""
        data = {
            'parameters': {
                'optimization_focus': 'performance'
            }
        }

        result = optimize_dashboard(data)

        assert result['success'] == False
        assert 'Missing required parameter' in result['error']


class TestDashboardValidation:
    """Test dashboard validation functionality"""

    def test_validate_dashboard_all_scope(self):
        """Test dashboard validation with all scope"""
        data = {
            'parameters': {
                'dashboard_name': 'Complex Dashboard',
                'validation_scope': 'all'
            }
        }

        result = validate_dashboard(data)

        assert result['success'] == True
        assert result['operation'] == 'validate_dashboard'
        assert 'validation_results' in result
        assert 'performance_assessment' in result['validation_results']
        assert 'security_assessment' in result['validation_results']
        assert 'usability_assessment' in result['validation_results']
        assert result['validation_results']['overall_score'] > 0

    def test_validate_dashboard_performance_only(self):
        """Test dashboard validation with performance scope only"""
        data = {
            'parameters': {
                'dashboard_name': 'Performance Test Dashboard',
                'validation_scope': 'performance'
            }
        }

        result = validate_dashboard(data)

        assert result['success'] == True
        assert 'performance_assessment' in result['validation_results']
        assert 'security_assessment' not in result['validation_results']

    def test_validate_dashboard_security_only(self):
        """Test dashboard validation with security scope only"""
        data = {
            'parameters': {
                'dashboard_name': 'Security Test Dashboard',
                'validation_scope': 'security'
            }
        }

        result = validate_dashboard(data)

        assert result['success'] == True
        assert 'security_assessment' in result['validation_results']
        assert 'performance_assessment' not in result['validation_results']

    def test_validate_dashboard_missing_name(self):
        """Test dashboard validation without dashboard name"""
        data = {
            'parameters': {
                'validation_scope': 'all'
            }
        }

        result = validate_dashboard(data)

        assert result['success'] == False
        assert 'Missing required parameter' in result['error']


class TestDashboardCloning:
    """Test dashboard cloning functionality"""

    def test_clone_dashboard_success(self):
        """Test successful dashboard cloning"""
        data = {
            'parameters': {
                'source_dashboard': 'Original Dashboard',
                'new_dashboard_name': 'Cloned Dashboard',
                'modifications': 'Change data sources to different indexes'
            }
        }

        result = clone_dashboard(data)

        assert result['success'] == True
        assert result['operation'] == 'clone_dashboard'
        assert 'clone_result' in result
        assert result['clone_result']['source_dashboard'] == 'Original Dashboard'
        assert result['clone_result']['new_dashboard_name'] == 'Cloned Dashboard'
        assert len(result['clone_result']['modifications_applied']) > 0

    def test_clone_dashboard_no_modifications(self):
        """Test dashboard cloning without modifications"""
        data = {
            'parameters': {
                'source_dashboard': 'Source Dashboard',
                'new_dashboard_name': 'Copy Dashboard'
            }
        }

        result = clone_dashboard(data)

        assert result['success'] == True
        assert result['clone_result']['modifications_applied'] == []

    def test_clone_dashboard_missing_parameters(self):
        """Test dashboard cloning with missing parameters"""
        data = {
            'parameters': {
                'source_dashboard': 'Source Dashboard'
                # Missing new_dashboard_name
            }
        }

        result = clone_dashboard(data)

        assert result['success'] == False
        assert 'Missing required parameters' in result['error']

    def test_clone_dashboard_invalid_new_name(self):
        """Test dashboard cloning with invalid new name"""
        data = {
            'parameters': {
                'source_dashboard': 'Valid Source',
                'new_dashboard_name': '123invalid@name'
            }
        }

        result = clone_dashboard(data)

        assert result['success'] == False
        assert 'Invalid new dashboard name' in result['error']


class TestDashboardDeletion:
    """Test dashboard deletion functionality"""

    def test_delete_dashboard_success(self):
        """Test successful dashboard deletion"""
        data = {
            'parameters': {
                'dashboard_name': 'Dashboard to Delete',
                'confirm_deletion': True,
                'check_dependencies': True,
                'backup_before_delete': True
            }
        }

        result = delete_dashboard(data)

        assert result['success'] == True
        assert result['operation'] == 'delete_dashboard'
        assert 'deletion_result' in result
        assert 'dependencies' in result
        assert 'backup_info' in result
        assert result['deletion_result']['dashboard_deleted'] == True

    def test_delete_dashboard_not_confirmed(self):
        """Test dashboard deletion without confirmation"""
        data = {
            'parameters': {
                'dashboard_name': 'Test Dashboard',
                'confirm_deletion': False
            }
        }

        result = delete_dashboard(data)

        assert result['success'] == False
        assert 'not confirmed' in result['error']

    def test_delete_dashboard_no_backup(self):
        """Test dashboard deletion without backup"""
        data = {
            'parameters': {
                'dashboard_name': 'Test Dashboard',
                'confirm_deletion': True,
                'backup_before_delete': False
            }
        }

        result = delete_dashboard(data)

        assert result['success'] == True
        assert result['backup_info'] is None

    def test_delete_dashboard_missing_name(self):
        """Test dashboard deletion without name"""
        data = {
            'parameters': {
                'confirm_deletion': True
            }
        }

        result = delete_dashboard(data)

        assert result['success'] == False
        assert 'Missing required parameter' in result['error']


class TestVisualizationRecommendations:
    """Test visualization recommendation functionality"""

    def test_recommend_visualizations_success(self):
        """Test successful visualization recommendations"""
        data = {
            'parameters': {
                'data_sample': 'timestamp, user, action, count',
                'analysis_intent': 'Trends over time',
                'audience_level': 'business'
            }
        }

        result = recommend_visualizations(data)

        assert result['success'] == True
        assert result['operation'] == 'recommend_visualizations'
        assert 'recommendations' in result
        assert 'data_characteristics' in result
        assert 'implementation_guidance' in result
        assert len(result['recommendations']) > 0

    def test_recommend_visualizations_executive_audience(self):
        """Test visualization recommendations for executive audience"""
        data = {
            'parameters': {
                'data_sample': 'revenue, quarter, region',
                'analysis_intent': 'Performance metrics',
                'audience_level': 'executive'
            }
        }

        result = recommend_visualizations(data)

        assert result['success'] == True
        assert result['audience_level'] == 'executive'
        # Check that recommendations include executive-appropriate notes
        assert any('executive' in rec.get('audience_notes', '').lower()
                  for rec in result['recommendations'])

    def test_recommend_visualizations_technical_audience(self):
        """Test visualization recommendations for technical audience"""
        data = {
            'parameters': {
                'data_sample': 'error_code, timestamp, server, count',
                'analysis_intent': 'Distribution analysis',
                'audience_level': 'technical'
            }
        }

        result = recommend_visualizations(data)

        assert result['success'] == True
        assert result['audience_level'] == 'technical'
        # Check that recommendations include technical options
        assert any('technical_options' in rec
                  for rec in result['recommendations'])

    def test_recommend_visualizations_missing_parameters(self):
        """Test visualization recommendations with missing parameters"""
        data = {
            'parameters': {
                'data_sample': 'test data'
                # Missing analysis_intent
            }
        }

        result = recommend_visualizations(data)

        assert result['success'] == False
        assert 'Missing required parameters' in result['error']


class TestDashboardExport:
    """Test dashboard export functionality"""

    def test_export_dashboard_json(self):
        """Test dashboard export in JSON format"""
        data = {
            'parameters': {
                'dashboard_name': 'Export Test Dashboard',
                'export_format': 'json',
                'include_data': False
            }
        }

        result = export_dashboard(data)

        assert result['success'] == True
        assert result['operation'] == 'export_dashboard'
        assert 'export_info' in result
        assert 'export_content' in result
        assert result['export_info']['export_format'] == 'json'
        # Verify JSON is valid
        json.loads(result['export_content'])

    def test_export_dashboard_with_data(self):
        """Test dashboard export including sample data"""
        data = {
            'parameters': {
                'dashboard_name': 'Data Export Dashboard',
                'export_format': 'json',
                'include_data': True
            }
        }

        result = export_dashboard(data)

        assert result['success'] == True
        assert result['export_info']['includes_data'] == True
        # Verify export content contains sample_data
        export_data = json.loads(result['export_content'])
        assert 'sample_data' in export_data

    def test_export_dashboard_yaml_format(self):
        """Test dashboard export in YAML format"""
        data = {
            'parameters': {
                'dashboard_name': 'YAML Export Dashboard',
                'export_format': 'yaml'
            }
        }

        result = export_dashboard(data)

        assert result['success'] == True
        assert result['export_info']['export_format'] == 'yaml'
        assert 'metadata:' in result['export_content']

    def test_export_dashboard_xml_format(self):
        """Test dashboard export in XML format"""
        data = {
            'parameters': {
                'dashboard_name': 'XML Export Dashboard',
                'export_format': 'xml'
            }
        }

        result = export_dashboard(data)

        assert result['success'] == True
        assert result['export_info']['export_format'] == 'xml'
        assert '<?xml version="1.0"' in result['export_content']

    def test_export_dashboard_missing_name(self):
        """Test dashboard export without name"""
        data = {
            'parameters': {
                'export_format': 'json'
            }
        }

        result = export_dashboard(data)

        assert result['success'] == False
        assert 'Missing required parameter' in result['error']


class TestDashboardManager:
    """Test DashboardManager utility class"""

    def test_validate_dashboard_name_valid(self):
        """Test valid dashboard name validation"""
        manager = DashboardManager()

        valid, error = manager._validate_dashboard_name("Security Dashboard")
        assert valid == True
        assert error == ""

        valid, error = manager._validate_dashboard_name("Executive_Summary_2024")
        assert valid == True
        assert error == ""

    def test_validate_dashboard_name_invalid(self):
        """Test invalid dashboard name validation"""
        manager = DashboardManager()

        # Empty name
        valid, error = manager._validate_dashboard_name("")
        assert valid == False
        assert "cannot be empty" in error

        # Starts with number
        valid, error = manager._validate_dashboard_name("123Dashboard")
        assert valid == False
        assert "must start with letter" in error

        # Too long
        valid, error = manager._validate_dashboard_name("a" * 101)
        assert valid == False
        assert "100 characters or less" in error

        # Invalid characters
        valid, error = manager._validate_dashboard_name("Dashboard@#$")
        assert valid == False
        assert "must start with letter" in error

    def test_analyze_data_characteristics(self):
        """Test data characteristics analysis"""
        manager = DashboardManager()

        analysis = manager._analyze_data_characteristics(
            "index=security _time user host",
            "Monitor user activity over time"
        )

        assert analysis['temporal_component'] == True
        assert analysis['categorical_component'] == True
        assert len(analysis['recommended_panels']) > 0

    def test_recommend_visualizations_by_purpose(self):
        """Test visualization recommendations by purpose"""
        manager = DashboardManager()

        # Time series recommendations
        recs = manager._recommend_visualizations("trends over time")
        assert any(rec['visualization'] in ['line', 'area'] for rec in recs)

        # Comparison recommendations
        recs = manager._recommend_visualizations("comparison between categories")
        assert any(rec['visualization'] in ['column', 'bar', 'pie'] for rec in recs)

        # Metrics recommendations
        recs = manager._recommend_visualizations("key performance metrics")
        assert any(rec['visualization'] in ['single_value', 'radial_gauge'] for rec in recs)

    def test_validate_search_performance(self):
        """Test search performance validation"""
        manager = DashboardManager()

        # Simple search - should score well
        validation = manager._validate_search_performance("index=security | stats count by user")
        assert validation['performance_impact'] == 'low'
        assert validation['performance_score'] >= 8

        # Complex search - should score poorly
        validation = manager._validate_search_performance(
            "index=* | join type=outer src_ip [search index=* earliest=0] | stats count"
        )
        assert validation['performance_impact'] == 'high'
        assert validation['performance_score'] <= 5
        assert len(validation['warnings']) > 0

    def test_optimize_panel_layout(self):
        """Test panel layout optimization"""
        manager = DashboardManager()

        panels = [
            {'visualization': 'single_value', 'title': 'KPI 1'},
            {'visualization': 'line', 'title': 'Trends'},
            {'visualization': 'table', 'title': 'Details'}
        ]

        layout = manager._optimize_panel_layout(panels, 'studio')

        assert layout['type'] == 'studio'
        assert len(layout['panels']) == 3
        # Single value should come first (priority)
        assert layout['panels'][0]['visualization'] == 'single_value'
        assert layout['panels'][0]['row'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])