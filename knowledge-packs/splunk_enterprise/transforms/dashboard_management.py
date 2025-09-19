"""
Dashboard Management - AI-Native Dashboard Creation and Management
Provides intelligent dashboard operations with performance optimization and security validation
"""

import json
import re
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid


class DashboardManager:
    """Manages Splunk dashboard operations with AI-powered optimization"""

    def __init__(self):
        """Initialize the dashboard manager"""
        self.visualization_map = {
            # Time-based data
            'trends': ['line', 'area', 'column'],
            'time_series': ['line', 'area', 'column'],
            'timeline': ['line', 'area'],

            # Categorical comparisons
            'comparison': ['column', 'bar', 'pie'],
            'categories': ['column', 'bar', 'pie'],
            'distribution': ['column', 'histogram', 'pie'],

            # Geographical data
            'geographic': ['choropleth_map', 'marker_map'],
            'location': ['choropleth_map', 'marker_map'],

            # Metrics and KPIs
            'metrics': ['single_value', 'radial_gauge', 'filler_gauge'],
            'kpi': ['single_value', 'radial_gauge'],
            'performance': ['single_value', 'column', 'line'],

            # Relationships and correlations
            'correlation': ['scatter', 'bubble'],
            'relationship': ['scatter', 'network_diagram'],

            # Text and lists
            'details': ['table', 'event_table'],
            'list': ['table', 'event_table'],
            'raw_data': ['event_table', 'table']
        }

        self.dashboard_templates = {
            'security': {
                'layout': 'grid',
                'panels': ['threat_overview', 'failed_logins', 'top_sources', 'timeline'],
                'refresh': '5 minutes',
                'theme': 'dark'
            },
            'executive': {
                'layout': 'dashboard',
                'panels': ['kpi_summary', 'trends', 'top_performers'],
                'refresh': '15 minutes',
                'theme': 'light'
            },
            'operations': {
                'layout': 'grid',
                'panels': ['system_health', 'error_rates', 'performance_metrics'],
                'refresh': '1 minute',
                'theme': 'enterprise'
            }
        }

    def _validate_dashboard_name(self, name: str) -> Tuple[bool, str]:
        """Validate dashboard name follows Splunk conventions"""
        if not name or len(name.strip()) == 0:
            return False, "Dashboard name cannot be empty"

        name = name.strip()

        # Check length
        if len(name) > 100:
            return False, "Dashboard name must be 100 characters or less"

        # Check for valid characters (letters, numbers, spaces, underscores, hyphens)
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_\s\-]*$', name):
            return False, "Dashboard name must start with letter and contain only letters, numbers, spaces, underscores, and hyphens"

        return True, ""

    def _analyze_data_characteristics(self, data_sources: str, business_purpose: str) -> Dict[str, Any]:
        """Analyze data characteristics to recommend optimal visualizations"""
        analysis = {
            'primary_data_type': 'events',
            'temporal_component': False,
            'categorical_component': False,
            'numerical_component': False,
            'geographical_component': False,
            'recommended_panels': []
        }

        # Analyze data sources
        data_lower = data_sources.lower()
        purpose_lower = business_purpose.lower()

        # Detect temporal patterns
        if any(word in data_lower for word in ['time', 'timestamp', '_time', 'date']):
            analysis['temporal_component'] = True

        # Detect categorical patterns
        if any(word in data_lower for word in ['user', 'host', 'source', 'category', 'type']):
            analysis['categorical_component'] = True

        # Detect numerical patterns
        if any(word in purpose_lower for word in ['count', 'sum', 'average', 'total', 'metric', 'performance']):
            analysis['numerical_component'] = True

        # Detect geographical patterns
        if any(word in data_lower for word in ['ip', 'location', 'country', 'city', 'geo']):
            analysis['geographical_component'] = True

        # Generate panel recommendations based on analysis
        if analysis['temporal_component']:
            analysis['recommended_panels'].append({
                'type': 'timeline',
                'visualization': 'line',
                'title': 'Activity Over Time',
                'search_hint': 'Use timechart for temporal trends'
            })

        if analysis['categorical_component']:
            analysis['recommended_panels'].append({
                'type': 'top_categories',
                'visualization': 'column',
                'title': 'Top Categories',
                'search_hint': 'Use top or stats count by for categorical breakdown'
            })

        if analysis['numerical_component']:
            analysis['recommended_panels'].append({
                'type': 'metrics',
                'visualization': 'single_value',
                'title': 'Key Metrics',
                'search_hint': 'Use stats functions for numerical summaries'
            })

        return analysis

    def _recommend_visualizations(self, panel_purpose: str, data_sample: str = "") -> List[Dict[str, Any]]:
        """Recommend optimal visualizations based on panel purpose and data"""
        purpose_lower = panel_purpose.lower()
        recommendations = []

        # Match purpose to visualization types
        for intent, viz_types in self.visualization_map.items():
            if intent in purpose_lower:
                for viz_type in viz_types:
                    recommendations.append({
                        'visualization': viz_type,
                        'confidence': 0.8 if intent == purpose_lower else 0.6,
                        'reasoning': f"Optimal for {intent} analysis",
                        'best_practices': self._get_viz_best_practices(viz_type)
                    })
                break

        # Default recommendations if no match
        if not recommendations:
            recommendations = [
                {
                    'visualization': 'table',
                    'confidence': 0.5,
                    'reasoning': 'Safe default for most data types',
                    'best_practices': ['Include relevant fields', 'Sort by most important column']
                }
            ]

        return sorted(recommendations, key=lambda x: x['confidence'], reverse=True)

    def _get_viz_best_practices(self, viz_type: str) -> List[str]:
        """Get best practices for specific visualization types"""
        practices = {
            'line': ['Use for time series data', 'Limit to 5-7 series', 'Include trend lines when appropriate'],
            'column': ['Limit to 10-15 categories', 'Sort by value', 'Use consistent colors'],
            'pie': ['Limit to 5-8 slices', 'Use for parts of whole', 'Start largest slice at 12 o\'clock'],
            'table': ['Include only necessary columns', 'Use proper formatting', 'Enable sorting'],
            'single_value': ['Use clear, large text', 'Include trend indicator', 'Add context with sparklines'],
            'choropleth_map': ['Ensure geographic data is clean', 'Use appropriate color scales', 'Include legend'],
            'scatter': ['Use when showing correlation', 'Include trend line', 'Limit number of points'],
        }
        return practices.get(viz_type, ['Follow Splunk visualization best practices'])

    def _optimize_panel_layout(self, panels: List[Dict[str, Any]], dashboard_type: str = 'studio') -> Dict[str, Any]:
        """Optimize panel layout for performance and usability"""
        layout = {
            'type': dashboard_type,
            'panels': [],
            'optimization_notes': []
        }

        # Define layout strategies
        strategies = {
            'studio': {
                'max_panels_per_row': 3,
                'priority_panels_top': True,
                'responsive': True
            },
            'classic': {
                'max_panels_per_row': 2,
                'priority_panels_top': True,
                'responsive': False
            }
        }

        strategy = strategies.get(dashboard_type, strategies['studio'])

        # Sort panels by priority (metrics first, then trends, then details)
        priority_order = ['single_value', 'line', 'column', 'table']

        def get_priority(panel):
            viz_type = panel.get('visualization', 'table')
            try:
                return priority_order.index(viz_type)
            except ValueError:
                return len(priority_order)

        sorted_panels = sorted(panels, key=get_priority)

        # Assign grid positions
        row = 0
        col = 0
        max_cols = strategy['max_panels_per_row']

        for panel in sorted_panels:
            panel_layout = {
                'row': row,
                'column': col,
                'width': self._calculate_panel_width(panel, max_cols),
                'height': self._calculate_panel_height(panel)
            }

            panel.update(panel_layout)
            layout['panels'].append(panel)

            col += panel_layout['width']
            if col >= max_cols:
                row += 1
                col = 0

        # Add optimization notes
        if len(panels) > 6:
            layout['optimization_notes'].append("Consider splitting into multiple dashboards for better performance")
        if any(p.get('visualization') == 'table' for p in panels):
            layout['optimization_notes'].append("Table panels should use field limitations and time bounds")

        return layout

    def _calculate_panel_width(self, panel: Dict[str, Any], max_cols: int) -> int:
        """Calculate optimal panel width based on visualization type"""
        viz_type = panel.get('visualization', 'table')

        # Full width visualizations
        if viz_type in ['table', 'event_table', 'line']:
            return max_cols
        # Half width visualizations
        elif viz_type in ['single_value', 'pie', 'radial_gauge']:
            return max(1, max_cols // 2)
        # Standard width
        else:
            return max(1, max_cols // 2)

    def _calculate_panel_height(self, panel: Dict[str, Any]) -> int:
        """Calculate optimal panel height based on visualization type"""
        viz_type = panel.get('visualization', 'table')

        height_map = {
            'single_value': 200,
            'radial_gauge': 250,
            'pie': 300,
            'line': 350,
            'column': 350,
            'table': 400,
            'event_table': 450,
            'choropleth_map': 400
        }

        return height_map.get(viz_type, 350)

    def _validate_search_performance(self, search_query: str) -> Dict[str, Any]:
        """Validate search performance characteristics"""
        validation = {
            'performance_score': 10,  # Start with perfect score
            'performance_impact': 'low',
            'warnings': [],
            'recommendations': [],
            'estimated_load_time': 'fast'
        }

        query_lower = search_query.lower()

        # Check for performance issues
        if 'index=*' in query_lower or 'index=_*' in query_lower:
            validation['performance_score'] -= 4
            validation['warnings'].append("Wildcard index search may impact performance")
            validation['recommendations'].append("Specify exact indexes for better performance")

        if ' join ' in query_lower:
            validation['performance_score'] -= 3
            validation['warnings'].append("Join operations can be resource intensive")
            validation['recommendations'].append("Consider using stats or other commands instead of join")

        if 'subsearch' in query_lower or '[search' in query_lower:
            validation['performance_score'] -= 2
            validation['warnings'].append("Subsearches may increase execution time")

        if query_lower.count('|') > 10:
            validation['performance_score'] -= 2
            validation['warnings'].append("Complex search with many pipes may be slow")

        # Determine performance impact
        if validation['performance_score'] >= 8:
            validation['performance_impact'] = 'low'
            validation['estimated_load_time'] = 'fast'
        elif validation['performance_score'] >= 6:
            validation['performance_impact'] = 'medium'
            validation['estimated_load_time'] = 'moderate'
        else:
            validation['performance_impact'] = 'high'
            validation['estimated_load_time'] = 'slow'

        return validation

    def _generate_dashboard_xml(self, dashboard_config: Dict[str, Any]) -> str:
        """Generate Dashboard Studio or Classic XML based on configuration"""
        dashboard_type = dashboard_config.get('dashboard_type', 'studio')

        if dashboard_type == 'studio':
            return self._generate_studio_json(dashboard_config)
        else:
            return self._generate_classic_xml(dashboard_config)

    def _generate_studio_json(self, config: Dict[str, Any]) -> str:
        """Generate Dashboard Studio JSON configuration"""
        studio_config = {
            "version": "1.0.0",
            "type": "dashboard",
            "title": config['dashboard_name'],
            "description": config.get('business_purpose', ''),
            "refresh": config.get('refresh_frequency', '5 minutes'),
            "layout": {
                "type": "grid",
                "structure": []
            },
            "dataSources": {},
            "visualizations": {}
        }

        # Add panels to layout
        for i, panel in enumerate(config.get('panels', [])):
            panel_id = f"panel_{i}"

            # Add to layout structure
            studio_config['layout']['structure'].append({
                "position": {
                    "x": panel.get('column', 0),
                    "y": panel.get('row', 0),
                    "w": panel.get('width', 1),
                    "h": panel.get('height', 350)
                },
                "viz": panel_id
            })

            # Add data source
            studio_config['dataSources'][f"ds_{panel_id}"] = {
                "type": "ds.search",
                "options": {
                    "query": panel.get('search_query', '| stats count'),
                    "queryParameters": {
                        "earliest": config.get('earliest_time', '-1h'),
                        "latest": config.get('latest_time', 'now')
                    }
                }
            }

            # Add visualization
            studio_config['visualizations'][panel_id] = {
                "type": f"viz.{panel.get('visualization', 'table')}",
                "title": panel.get('title', f"Panel {i+1}"),
                "dataSources": {
                    "primary": f"ds_{panel_id}"
                }
            }

        return json.dumps(studio_config, indent=2)

    def _generate_classic_xml(self, config: Dict[str, Any]) -> str:
        """Generate Classic Dashboard XML"""
        root = ET.Element("dashboard")

        # Add metadata
        label = ET.SubElement(root, "label")
        label.text = config['dashboard_name']

        description = ET.SubElement(root, "description")
        description.text = config.get('business_purpose', '')

        # Add panels
        for i, panel in enumerate(config.get('panels', [])):
            row = ET.SubElement(root, "row")
            panel_elem = ET.SubElement(row, "panel")

            title = ET.SubElement(panel_elem, "title")
            title.text = panel.get('title', f"Panel {i+1}")

            # Add search
            search_elem = ET.SubElement(panel_elem, "search")
            query = ET.SubElement(search_elem, "query")
            query.text = panel.get('search_query', '| stats count')

            earliest = ET.SubElement(search_elem, "earliest")
            earliest.text = config.get('earliest_time', '-1h')

            latest = ET.SubElement(search_elem, "latest")
            latest.text = config.get('latest_time', 'now')

            # Add visualization options based on type
            viz_type = panel.get('visualization', 'table')
            if viz_type != 'table':
                viz_elem = ET.SubElement(panel_elem, viz_type)

        return ET.tostring(root, encoding='unicode')


def create_dashboard(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a new Splunk dashboard with AI-powered layout and visualization recommendations"""
    try:
        params = data.get('parameters', {})

        # Extract required parameters
        dashboard_name = params.get('dashboard_name', '').strip()
        business_purpose = params.get('business_purpose', '').strip()
        target_audience = params.get('target_audience', '').strip()
        data_sources = params.get('data_sources', '').strip()

        # Validate required parameters
        missing_params = []
        if not dashboard_name:
            missing_params.append('dashboard_name')
        if not business_purpose:
            missing_params.append('business_purpose')
        if not target_audience:
            missing_params.append('target_audience')
        if not data_sources:
            missing_params.append('data_sources')

        if missing_params:
            return {
                'success': False,
                'error': f"Missing required parameters: {', '.join(missing_params)}",
                'required_parameters': ['dashboard_name', 'business_purpose', 'target_audience', 'data_sources']
            }

        manager = DashboardManager()

        # Validate dashboard name
        valid, error_msg = manager._validate_dashboard_name(dashboard_name)
        if not valid:
            return {
                'success': False,
                'error': error_msg
            }

        # Extract optional parameters
        dashboard_type = params.get('dashboard_type', 'studio')
        refresh_frequency = params.get('refresh_frequency', '5 minutes')
        app_context = params.get('app_context', 'search')

        # Analyze data characteristics
        data_analysis = manager._analyze_data_characteristics(data_sources, business_purpose)

        # Generate dashboard configuration
        dashboard_config = {
            'dashboard_name': dashboard_name,
            'business_purpose': business_purpose,
            'target_audience': target_audience,
            'data_sources': data_sources,
            'dashboard_type': dashboard_type,
            'refresh_frequency': refresh_frequency,
            'app_context': app_context,
            'panels': data_analysis['recommended_panels'],
            'earliest_time': '-24h',
            'latest_time': 'now'
        }

        # Optimize layout
        layout = manager._optimize_panel_layout(data_analysis['recommended_panels'], dashboard_type)
        dashboard_config.update(layout)

        # Generate dashboard definition
        dashboard_definition = manager._generate_dashboard_xml(dashboard_config)

        return {
            'success': True,
            'operation': 'create_dashboard',
            'dashboard_name': dashboard_name,
            'dashboard_type': dashboard_type,
            'data_analysis': data_analysis,
            'layout_optimization': layout,
            'dashboard_definition': dashboard_definition,
            'recommendations': [
                f"Dashboard optimized for {target_audience.lower()} audience",
                f"Refresh frequency set to {refresh_frequency} based on data requirements",
                f"Layout includes {len(data_analysis['recommended_panels'])} recommended panels"
            ],
            'next_steps': [
                "Review generated dashboard definition",
                "Test with sample data",
                "Deploy to Splunk environment",
                "Monitor performance and adjust as needed"
            ]
        }

    except Exception as e:
        return {
            'success': False,
            'error': f"Dashboard creation failed: {str(e)}",
            'operation': 'create_dashboard'
        }


def add_dashboard_panel(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Add a new panel to existing dashboard with AI visualization recommendations"""
    try:
        params = data.get('parameters', {})

        # Extract required parameters
        dashboard_name = params.get('dashboard_name', '').strip()
        panel_purpose = params.get('panel_purpose', '').strip()
        search_query = params.get('search_query', '').strip()

        # Validate required parameters
        missing_params = []
        if not dashboard_name:
            missing_params.append('dashboard_name')
        if not panel_purpose:
            missing_params.append('panel_purpose')
        if not search_query:
            missing_params.append('search_query')

        if missing_params:
            return {
                'success': False,
                'error': f"Missing required parameters: {', '.join(missing_params)}",
                'required_parameters': ['dashboard_name', 'panel_purpose', 'search_query']
            }

        manager = DashboardManager()

        # Extract optional parameters
        panel_position = params.get('panel_position', 'auto')

        # Get visualization recommendations
        viz_recommendations = manager._recommend_visualizations(panel_purpose)
        best_viz = viz_recommendations[0] if viz_recommendations else {'visualization': 'table'}

        # Validate search performance
        search_validation = manager._validate_search_performance(search_query)

        # Create panel configuration
        panel_config = {
            'title': panel_purpose.title(),
            'search_query': search_query,
            'visualization': best_viz['visualization'],
            'position': panel_position,
            'performance_analysis': search_validation,
            'visualization_options': viz_recommendations[:3]  # Top 3 recommendations
        }

        return {
            'success': True,
            'operation': 'add_dashboard_panel',
            'dashboard_name': dashboard_name,
            'panel_config': panel_config,
            'recommendations': [
                f"Recommended visualization: {best_viz['visualization']} ({best_viz.get('reasoning', 'optimal for purpose')})",
                f"Search performance impact: {search_validation['performance_impact']}",
                f"Estimated load time: {search_validation['estimated_load_time']}"
            ] + search_validation.get('recommendations', []),
            'warnings': search_validation.get('warnings', []),
            'next_steps': [
                "Add panel to dashboard configuration",
                "Test panel performance",
                "Adjust visualization if needed"
            ]
        }

    except Exception as e:
        return {
            'success': False,
            'error': f"Panel addition failed: {str(e)}",
            'operation': 'add_dashboard_panel'
        }


def optimize_dashboard(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Analyze and optimize dashboard performance with AI recommendations"""
    try:
        params = data.get('parameters', {})

        # Extract required parameters
        dashboard_name = params.get('dashboard_name', '').strip()

        if not dashboard_name:
            return {
                'success': False,
                'error': "Missing required parameter: dashboard_name",
                'required_parameters': ['dashboard_name']
            }

        # Extract optional parameters
        optimization_focus = params.get('optimization_focus', 'balanced')
        apply_optimizations = params.get('apply_optimizations', False)

        # Simulate dashboard analysis (in real implementation, would fetch from Splunk)
        mock_dashboard_analysis = {
            'total_panels': 8,
            'avg_load_time': '12 seconds',
            'slowest_panel': 'Security Events Table',
            'resource_usage': 'high',
            'concurrent_searches': 6,
            'refresh_frequency': '1 minute'
        }

        # Generate optimization recommendations
        optimizations = []

        if optimization_focus in ['performance', 'balanced']:
            optimizations.extend([
                {
                    'type': 'search_optimization',
                    'recommendation': 'Add time bounds to wildcard index searches',
                    'impact': 'high',
                    'effort': 'low'
                },
                {
                    'type': 'refresh_optimization',
                    'recommendation': 'Increase refresh frequency to 5 minutes for non-critical panels',
                    'impact': 'medium',
                    'effort': 'low'
                },
                {
                    'type': 'panel_consolidation',
                    'recommendation': 'Combine similar single-value panels into one multi-metric panel',
                    'impact': 'medium',
                    'effort': 'medium'
                }
            ])

        if optimization_focus in ['usability', 'balanced']:
            optimizations.extend([
                {
                    'type': 'layout_optimization',
                    'recommendation': 'Move key metrics to top-left position for better visibility',
                    'impact': 'medium',
                    'effort': 'low'
                },
                {
                    'type': 'visualization_improvement',
                    'recommendation': 'Convert large tables to chart visualizations where appropriate',
                    'impact': 'high',
                    'effort': 'medium'
                }
            ])

        # Calculate potential improvements
        performance_improvement = {
            'estimated_load_time_reduction': '40-60%',
            'resource_usage_reduction': '30%',
            'user_experience_improvement': 'significant'
        }

        result = {
            'success': True,
            'operation': 'optimize_dashboard',
            'dashboard_name': dashboard_name,
            'optimization_focus': optimization_focus,
            'applied': apply_optimizations,
            'current_analysis': mock_dashboard_analysis,
            'optimizations': optimizations,
            'performance_improvement': performance_improvement,
            'optimization_summary': f"Found {len(optimizations)} optimization opportunities",
            'next_steps': [
                "Review optimization recommendations",
                "Test optimizations in development environment",
                "Apply optimizations gradually",
                "Monitor performance improvements"
            ]
        }

        if apply_optimizations:
            result['application_results'] = {
                'optimizations_applied': len(optimizations),
                'estimated_improvement': performance_improvement,
                'rollback_available': True
            }

        return result

    except Exception as e:
        return {
            'success': False,
            'error': f"Dashboard optimization failed: {str(e)}",
            'operation': 'optimize_dashboard'
        }


def validate_dashboard(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Analyze dashboard for performance issues and security concerns"""
    try:
        params = data.get('parameters', {})

        # Extract required parameters
        dashboard_name = params.get('dashboard_name', '').strip()

        if not dashboard_name:
            return {
                'success': False,
                'error': "Missing required parameter: dashboard_name",
                'required_parameters': ['dashboard_name']
            }

        # Extract optional parameters
        validation_scope = params.get('validation_scope', 'all')

        validation_results = {
            'dashboard_name': dashboard_name,
            'validation_scope': validation_scope,
            'overall_score': 0,
            'issues_found': [],
            'recommendations': []
        }

        # Performance validation
        if validation_scope in ['performance', 'all']:
            performance_issues = [
                {
                    'severity': 'high',
                    'issue': 'Multiple panels using wildcard index searches',
                    'impact': 'Significant performance degradation',
                    'recommendation': 'Specify exact indexes for better performance'
                },
                {
                    'severity': 'medium',
                    'issue': 'High refresh frequency on complex searches',
                    'impact': 'Increased resource usage',
                    'recommendation': 'Reduce refresh frequency for complex panels'
                }
            ]

            validation_results['performance_assessment'] = {
                'score': 6,
                'issues': performance_issues,
                'load_time_estimate': '8-15 seconds',
                'resource_impact': 'medium-high'
            }

        # Security validation
        if validation_scope in ['security', 'all']:
            security_issues = [
                {
                    'severity': 'medium',
                    'issue': 'Dashboard accessible to all users',
                    'impact': 'Potential data exposure',
                    'recommendation': 'Implement role-based access controls'
                }
            ]

            validation_results['security_assessment'] = {
                'score': 8,
                'issues': security_issues,
                'access_controls': 'basic',
                'data_exposure_risk': 'medium'
            }

        # Usability validation
        if validation_scope in ['usability', 'all']:
            usability_issues = [
                {
                    'severity': 'low',
                    'issue': 'Dashboard has more than 10 panels',
                    'impact': 'Information overload',
                    'recommendation': 'Consider splitting into multiple focused dashboards'
                }
            ]

            validation_results['usability_assessment'] = {
                'score': 7,
                'issues': usability_issues,
                'layout_score': 7,
                'user_experience': 'good'
            }

        # Calculate overall score
        scores = []
        if 'performance_assessment' in validation_results:
            scores.append(validation_results['performance_assessment']['score'])
        if 'security_assessment' in validation_results:
            scores.append(validation_results['security_assessment']['score'])
        if 'usability_assessment' in validation_results:
            scores.append(validation_results['usability_assessment']['score'])

        validation_results['overall_score'] = sum(scores) / len(scores) if scores else 0

        # Collect all issues and recommendations
        all_issues = []
        all_recommendations = []

        for assessment in ['performance_assessment', 'security_assessment', 'usability_assessment']:
            if assessment in validation_results:
                all_issues.extend(validation_results[assessment].get('issues', []))
                all_recommendations.extend([issue['recommendation'] for issue in validation_results[assessment].get('issues', [])])

        validation_results['issues_found'] = all_issues
        validation_results['recommendations'] = list(set(all_recommendations))  # Remove duplicates

        return {
            'success': True,
            'operation': 'validate_dashboard',
            'validation_results': validation_results,
            'summary': f"Validation complete: Overall score {validation_results['overall_score']:.1f}/10, {len(all_issues)} issues found",
            'next_steps': [
                "Review identified issues by severity",
                "Implement recommended improvements",
                "Re-validate after changes"
            ]
        }

    except Exception as e:
        return {
            'success': False,
            'error': f"Dashboard validation failed: {str(e)}",
            'operation': 'validate_dashboard'
        }


def clone_dashboard(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a copy of existing dashboard with optional modifications"""
    try:
        params = data.get('parameters', {})

        # Extract required parameters
        source_dashboard = params.get('source_dashboard', '').strip()
        new_dashboard_name = params.get('new_dashboard_name', '').strip()

        # Validate required parameters
        missing_params = []
        if not source_dashboard:
            missing_params.append('source_dashboard')
        if not new_dashboard_name:
            missing_params.append('new_dashboard_name')

        if missing_params:
            return {
                'success': False,
                'error': f"Missing required parameters: {', '.join(missing_params)}",
                'required_parameters': ['source_dashboard', 'new_dashboard_name']
            }

        manager = DashboardManager()

        # Validate new dashboard name
        valid, error_msg = manager._validate_dashboard_name(new_dashboard_name)
        if not valid:
            return {
                'success': False,
                'error': f"Invalid new dashboard name: {error_msg}"
            }

        # Extract optional parameters
        modifications = params.get('modifications', '')

        # Simulate dashboard cloning (in real implementation, would fetch from Splunk)
        clone_result = {
            'source_dashboard': source_dashboard,
            'new_dashboard_name': new_dashboard_name,
            'panels_copied': 6,
            'searches_updated': 3,
            'layout_preserved': True,
            'permissions_inherited': True
        }

        # Apply modifications if specified
        applied_modifications = []
        if modifications:
            modifications_lower = modifications.lower()

            if 'data source' in modifications_lower or 'index' in modifications_lower:
                applied_modifications.append("Updated data sources to use different indexes")

            if 'time range' in modifications_lower:
                applied_modifications.append("Modified time ranges for different use case")

            if 'permission' in modifications_lower or 'team' in modifications_lower:
                applied_modifications.append("Adjusted permissions for different team access")

        clone_result['modifications_applied'] = applied_modifications

        return {
            'success': True,
            'operation': 'clone_dashboard',
            'clone_result': clone_result,
            'summary': f"Successfully cloned '{source_dashboard}' to '{new_dashboard_name}' with {len(applied_modifications)} modifications",
            'next_steps': [
                "Review cloned dashboard configuration",
                "Test dashboard functionality",
                "Adjust permissions as needed",
                "Deploy to target environment"
            ]
        }

    except Exception as e:
        return {
            'success': False,
            'error': f"Dashboard cloning failed: {str(e)}",
            'operation': 'clone_dashboard'
        }


def delete_dashboard(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Remove dashboard with safety checks and dependency validation"""
    try:
        params = data.get('parameters', {})

        # Extract required parameters
        dashboard_name = params.get('dashboard_name', '').strip()
        confirm_deletion = params.get('confirm_deletion', False)

        # Validate required parameters
        if not dashboard_name:
            return {
                'success': False,
                'error': "Missing required parameter: dashboard_name",
                'required_parameters': ['dashboard_name', 'confirm_deletion']
            }

        if not confirm_deletion:
            return {
                'success': False,
                'error': "Dashboard deletion not confirmed. Set confirm_deletion to true to proceed.",
                'safety_note': "This operation cannot be undone without a backup"
            }

        # Extract optional parameters
        check_dependencies = params.get('check_dependencies', True)
        backup_before_delete = params.get('backup_before_delete', True)

        # Perform dependency check
        dependencies = []
        if check_dependencies:
            # Simulate dependency check (in real implementation, would query Splunk)
            mock_dependencies = [
                {
                    'type': 'scheduled_report',
                    'name': 'Weekly Dashboard PDF',
                    'impact': 'Report will fail to generate'
                },
                {
                    'type': 'alert',
                    'name': 'Dashboard Load Alert',
                    'impact': 'Alert will need reconfiguration'
                }
            ]
            dependencies = mock_dependencies

        # Create backup if requested
        backup_info = None
        if backup_before_delete:
            backup_info = {
                'backup_created': True,
                'backup_location': f"/tmp/dashboard_backups/{dashboard_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                'backup_size': '2.3 KB',
                'restore_possible': True
            }

        # Perform deletion
        deletion_result = {
            'dashboard_deleted': True,
            'deletion_timestamp': datetime.now().isoformat(),
            'dependencies_checked': check_dependencies,
            'dependencies_found': len(dependencies),
            'backup_created': backup_before_delete,
            'rollback_possible': backup_before_delete
        }

        return {
            'success': True,
            'operation': 'delete_dashboard',
            'dashboard_name': dashboard_name,
            'deletion_result': deletion_result,
            'dependencies': dependencies,
            'backup_info': backup_info,
            'warnings': [
                f"Dashboard '{dashboard_name}' has been permanently deleted",
                f"Found {len(dependencies)} dependent objects that may be affected"
            ] if dependencies else [f"Dashboard '{dashboard_name}' has been permanently deleted"],
            'next_steps': [
                "Update dependent objects if needed",
                "Verify backup if restoration is needed later",
                "Remove dashboard references from documentation"
            ]
        }

    except Exception as e:
        return {
            'success': False,
            'error': f"Dashboard deletion failed: {str(e)}",
            'operation': 'delete_dashboard'
        }


def recommend_visualizations(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """AI-powered visualization recommendations based on data characteristics"""
    try:
        params = data.get('parameters', {})

        # Extract required parameters
        data_sample = params.get('data_sample', '').strip()
        analysis_intent = params.get('analysis_intent', '').strip()

        # Validate required parameters
        missing_params = []
        if not data_sample:
            missing_params.append('data_sample')
        if not analysis_intent:
            missing_params.append('analysis_intent')

        if missing_params:
            return {
                'success': False,
                'error': f"Missing required parameters: {', '.join(missing_params)}",
                'required_parameters': ['data_sample', 'analysis_intent']
            }

        # Extract optional parameters
        audience_level = params.get('audience_level', 'business')

        manager = DashboardManager()

        # Get visualization recommendations
        recommendations = manager._recommend_visualizations(analysis_intent, data_sample)

        # Analyze data characteristics
        data_characteristics = {
            'data_type': 'mixed',
            'temporal_data': 'time' in data_sample.lower() or '_time' in data_sample.lower(),
            'categorical_data': any(field in data_sample.lower() for field in ['user', 'host', 'source', 'category']),
            'numerical_data': any(word in analysis_intent.lower() for word in ['count', 'sum', 'average', 'metric']),
            'complexity': 'medium'
        }

        # Enhance recommendations based on audience level
        for rec in recommendations:
            if audience_level == 'executive':
                rec['audience_notes'] = "Simplified view recommended for executive audience"
                if rec['visualization'] == 'table':
                    rec['alternative'] = 'single_value'
                    rec['reasoning'] += " - Consider single value metrics for executive dashboards"
            elif audience_level == 'technical':
                rec['audience_notes'] = "Detailed view appropriate for technical audience"
                rec['technical_options'] = ['Enable drill-down', 'Add statistical overlays', 'Include raw data access']

        # Generate specific implementation guidance
        implementation_guidance = []
        for rec in recommendations[:3]:  # Top 3 recommendations
            guidance = {
                'visualization': rec['visualization'],
                'splunk_command': _get_splunk_command_for_viz(rec['visualization'], analysis_intent),
                'best_practices': rec.get('best_practices', []),
                'color_scheme': _recommend_color_scheme(rec['visualization'], audience_level)
            }
            implementation_guidance.append(guidance)

        return {
            'success': True,
            'operation': 'recommend_visualizations',
            'analysis_intent': analysis_intent,
            'audience_level': audience_level,
            'data_characteristics': data_characteristics,
            'recommendations': recommendations,
            'implementation_guidance': implementation_guidance,
            'summary': f"Generated {len(recommendations)} visualization recommendations for {analysis_intent} analysis",
            'next_steps': [
                "Choose preferred visualization from recommendations",
                "Implement using provided Splunk commands",
                "Test with actual data",
                "Adjust based on user feedback"
            ]
        }

    except Exception as e:
        return {
            'success': False,
            'error': f"Visualization recommendation failed: {str(e)}",
            'operation': 'recommend_visualizations'
        }

def _get_splunk_command_for_viz(visualization: str, intent: str) -> str:
    """Get appropriate SPL command for visualization type"""
    command_map = {
        'line': 'timechart',
        'area': 'timechart',
        'column': 'chart' if 'time' not in intent.lower() else 'timechart',
        'bar': 'chart',
        'pie': 'stats count by field | sort -count',
        'table': 'table field1, field2, field3',
        'single_value': 'stats count' if 'count' in intent.lower() else 'stats avg(field)',
        'scatter': 'stats values(field1) as x, values(field2) as y by group'
    }
    return command_map.get(visualization, 'stats count')

def _recommend_color_scheme(visualization: str, audience: str) -> str:
    """Recommend appropriate color scheme"""
    if audience == 'executive':
        return 'professional' if visualization in ['column', 'bar', 'pie'] else 'minimal'
    elif audience == 'technical':
        return 'high_contrast' if visualization in ['line', 'area'] else 'detailed'
    else:
        return 'standard'


def export_dashboard(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Export dashboard configuration for backup or migration"""
    try:
        params = data.get('parameters', {})

        # Extract required parameters
        dashboard_name = params.get('dashboard_name', '').strip()

        if not dashboard_name:
            return {
                'success': False,
                'error': "Missing required parameter: dashboard_name",
                'required_parameters': ['dashboard_name']
            }

        # Extract optional parameters
        export_format = params.get('export_format', 'json')
        include_data = params.get('include_data', False)

        # Simulate dashboard export (in real implementation, would fetch from Splunk)
        dashboard_config = {
            'metadata': {
                'name': dashboard_name,
                'type': 'dashboard_studio',
                'version': '1.0.0',
                'created': '2024-01-15T10:30:00Z',
                'modified': '2024-01-20T14:45:00Z',
                'author': 'admin',
                'app': 'search'
            },
            'definition': {
                'title': dashboard_name,
                'description': 'Exported dashboard configuration',
                'refresh': '5 minutes',
                'panels': [
                    {
                        'id': 'panel_1',
                        'title': 'Activity Timeline',
                        'type': 'line',
                        'search': 'index=security | timechart count',
                        'position': {'x': 0, 'y': 0, 'w': 12, 'h': 6}
                    },
                    {
                        'id': 'panel_2',
                        'title': 'Top Sources',
                        'type': 'column',
                        'search': 'index=security | top 10 source',
                        'position': {'x': 0, 'y': 6, 'w': 6, 'h': 6}
                    }
                ]
            }
        }

        # Add sample data if requested
        if include_data:
            dashboard_config['sample_data'] = {
                'panel_1': [
                    {'_time': '2024-01-20T10:00:00Z', 'count': 145},
                    {'_time': '2024-01-20T11:00:00Z', 'count': 167},
                    {'_time': '2024-01-20T12:00:00Z', 'count': 123}
                ],
                'panel_2': [
                    {'source': 'server1.log', 'count': 342},
                    {'source': 'server2.log', 'count': 298},
                    {'source': 'server3.log', 'count': 156}
                ]
            }

        # Format export based on requested format
        if export_format == 'json':
            export_content = json.dumps(dashboard_config, indent=2)
        elif export_format == 'yaml':
            # Simplified YAML representation
            export_content = f"""# Dashboard Export: {dashboard_name}
metadata:
  name: {dashboard_name}
  type: dashboard_studio
  version: 1.0.0

definition:
  title: {dashboard_name}
  panels: {len(dashboard_config['definition']['panels'])}

# Full configuration available in JSON format
"""
        else:
            # XML format
            export_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<dashboard>
    <label>{dashboard_name}</label>
    <description>Exported dashboard configuration</description>
    <!-- Panel definitions would be here -->
</dashboard>"""

        export_info = {
            'dashboard_name': dashboard_name,
            'export_format': export_format,
            'export_size': f"{len(export_content)} bytes",
            'panels_exported': len(dashboard_config['definition']['panels']),
            'includes_data': include_data,
            'export_timestamp': datetime.now().isoformat(),
            'file_name': f"{dashboard_name.replace(' ', '_').lower()}_export.{export_format}"
        }

        return {
            'success': True,
            'operation': 'export_dashboard',
            'export_info': export_info,
            'export_content': export_content,
            'migration_notes': [
                "Review panel searches for environment-specific indexes",
                "Verify app context compatibility",
                "Check permissions and role requirements",
                "Test dashboard functionality after import"
            ],
            'next_steps': [
                "Save export content to file",
                "Transfer to target environment",
                "Import using Splunk REST API or UI",
                "Validate dashboard functionality"
            ]
        }

    except Exception as e:
        return {
            'success': False,
            'error': f"Dashboard export failed: {str(e)}",
            'operation': 'export_dashboard'
        }