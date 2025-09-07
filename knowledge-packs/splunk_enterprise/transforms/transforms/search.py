"""
Enhanced Multi-LLM Search Transform - Adaptive summarization with guardrails for any LLM provider
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
import re
import json
from collections import Counter, defaultdict
import os
import sys
import importlib.util

# Add transforms directory to path for imports
transforms_dir = os.path.dirname(__file__)
if transforms_dir not in sys.path:
    sys.path.insert(0, transforms_dir)

# Import guardrails and context manager
try:
    from guardrails import get_guardrails_engine
except ImportError:
    # Fallback: direct file import
    guardrails_path = os.path.join(transforms_dir, 'guardrails.py')
    if os.path.exists(guardrails_path):
        spec = importlib.util.spec_from_file_location("guardrails", guardrails_path)
        guardrails_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guardrails_module)
        get_guardrails_engine = guardrails_module.get_guardrails_engine
    else:
        # Mock guardrails if not available
        def get_guardrails_engine():
            class MockGuardrails:
                def validate_search(self, query, user_context):
                    return {'blocked': False, 'violations': [], 'warnings': []}
                def apply_data_masking(self, events, user_context):
                    return events
            return MockGuardrails()

try:
    from llm_context_manager import get_context_manager, detect_and_configure, LLMProfile, QueryStrategy, ContextSize
except ImportError:
    # Fallback implementation
    logger.warning("LLM context manager not available, using basic implementation")
    from dataclasses import dataclass
    from enum import Enum
    
    class ContextSize(Enum):
        SMALL = "small_context"
        MEDIUM = "medium_context" 
        LARGE = "large_context"
    
    @dataclass
    class LLMProfile:
        name: str = "default"
        context_window: int = 8192
        chars_per_token: int = 4
        reserved_tokens: int = 2000
        optimal_usage: float = 0.6
        token_efficiency: str = "medium"
        best_for: List[str] = None
        context_class: ContextSize = ContextSize.SMALL
    
    @dataclass
    class QueryStrategy:
        max_results: int = 50
        max_samples: int = 5
        summarization_level: str = "aggressive"
        include_raw_events: bool = False
        pattern_detection: str = "basic"
        field_analysis_depth: str = "minimal"
        diversity_analysis: bool = False
    
    def detect_and_configure(request_context):
        return LLMProfile(), {"fallback": "using basic configuration"}

logger = logging.getLogger(__name__)

def extract_search_results(data: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Enhanced search results extraction with multi-LLM context awareness and guardrails
    
    Features:
    - Auto-detects LLM provider and optimizes for their context window
    - Applies guardrails for security
    - Intelligent summarization based on query intent and LLM capabilities
    - Adaptive token management for different model sizes
    """
    try:
        variables = variables or {}
        
        # Extract request context for LLM detection
        request_context = _extract_request_context(variables)
        
        # Detect LLM and get optimal configuration
        llm_profile, llm_config = detect_and_configure(request_context)
        
        # Apply guardrails first
        guardrails = get_guardrails_engine()
        user_context = _extract_user_context(variables)
        
        # Validate search query if provided
        search_query = variables.get('search_query', '')
        validation_result = {'blocked': False, 'violations': [], 'warnings': []}
        
        if search_query:
            validation_result = guardrails.validate_search(search_query, user_context)
            
            # If search was blocked, return block information
            if validation_result['blocked']:
                return _blocked_response(validation_result, llm_config)
        
        # Extract basic results
        results = []
        if isinstance(data.get('results'), list):
            results = data['results']
        elif isinstance(data, list):
            results = data
            
        if not results:
            return _empty_result_response(variables, llm_config)
        
        # Determine query intent
        query_intent = _analyze_query_intent(search_query, variables.get('query_intent', 'general'))
        
        # Get LLM-specific strategy
        context_manager = get_context_manager()
        strategy = context_manager.get_query_strategy(llm_profile, query_intent)
        
        # Apply adaptive summarization based on LLM capabilities
        summarized_results = _apply_adaptive_summarization(
            results, llm_profile, strategy, query_intent
        )
        
        # Apply data masking
        events_to_mask = summarized_results.get('events', [])
        masked_results = guardrails.apply_data_masking(events_to_mask, user_context)
        
        # Calculate final token usage
        final_tokens = context_manager.estimate_tokens(masked_results, llm_profile)
        available_tokens = context_manager.calculate_available_tokens(llm_profile)
        
        # Build final response
        final_result = {
            'success': True,
            'llm_optimization': {
                'detected_llm': llm_profile.name,
                'context_class': llm_profile.context_class.value,
                'strategy_applied': query_intent,
                'summarization_level': strategy.summarization_level
            },
            'events': masked_results,
            'count': len(masked_results),
            'total_processed': len(results),
            'search_info': {
                'query': search_query,
                'intent': query_intent,
                'time_range': f"{variables.get('earliest_time', '')} to {variables.get('latest_time', '')}",
                'optimization': f"Optimized for {llm_profile.name} ({llm_profile.context_class.value})"
            },
            'token_usage': {
                'estimated_tokens': final_tokens,
                'available_tokens': available_tokens,
                'usage_percentage': round((final_tokens / available_tokens * 100), 1) if available_tokens > 0 else 0,
                'context_window': llm_profile.context_window
            },
            'guardrails_info': {
                'data_masking_applied': len(masked_results) != len(events_to_mask) or 
                                     any('[MASKED]' in str(event) or '***' in str(event) for event in masked_results),
                'user_role': user_context.get('user_role', 'unknown'),
                'validation_warnings': validation_result.get('warnings', [])
            }
        }
        
        # Add summarization details
        final_result.update(summarized_results)
        
        # Add configuration details for debugging
        final_result['llm_config'] = llm_config
        
        return final_result
        
    except Exception as e:
        logger.error(f"Enhanced search result extraction failed: {str(e)}")
        return _error_response(str(e), variables)

def _extract_request_context(variables: Dict[str, Any]) -> Dict[str, Any]:
    """Extract context clues for LLM detection"""
    return {
        'user_agent': variables.get('user_agent', ''),
        'api_endpoint': variables.get('api_endpoint', ''),
        'model': variables.get('model', variables.get('llm_model', '')),
        'client_info': variables.get('client_info', {}),
        'query_intent': variables.get('query_intent', 'general')
    }

def _analyze_query_intent(search_query: str, explicit_intent: str = 'general') -> str:
    """Enhanced query intent analysis"""
    
    # Use explicit intent if provided
    if explicit_intent and explicit_intent != 'general':
        return explicit_intent
    
    query_lower = search_query.lower()
    
    # Statistical queries - aggregated data
    if any(cmd in query_lower for cmd in ['stats', 'chart', 'timechart', 'top', 'rare', 'sistats', 'mstats']):
        return 'statistical'
    
    # Investigation queries - detailed analysis needed
    investigation_keywords = ['error', 'failed', 'failure', 'exception', 'alert', 'security', 'breach', 'attack', 'suspicious', 'anomaly']
    if any(keyword in query_lower for keyword in investigation_keywords):
        return 'investigation'
    
    # Discovery queries - exploring data structure
    discovery_keywords = ['metadata', 'sourcetype', 'index', 'host', 'fields', 'describe', 'explore', 'list']
    if any(keyword in query_lower for keyword in discovery_keywords):
        return 'discovery'
    
    # Performance queries - system health
    performance_keywords = ['performance', 'slow', 'cpu', 'memory', 'disk', 'bandwidth', 'latency', 'response_time']
    if any(keyword in query_lower for keyword in performance_keywords):
        return 'performance'
    
    return 'general'

def _apply_adaptive_summarization(results: List[Dict], llm_profile: LLMProfile, 
                                strategy: QueryStrategy, query_intent: str) -> Dict[str, Any]:
    """Apply summarization based on LLM capabilities and query intent"""
    
    if query_intent == 'statistical':
        return _handle_statistical_query_adaptive(results, strategy, llm_profile)
    elif query_intent == 'investigation':
        return _handle_investigation_query_adaptive(results, strategy, llm_profile)
    elif query_intent == 'discovery':
        return _handle_discovery_query_adaptive(results, strategy, llm_profile)
    elif query_intent == 'performance':
        return _handle_performance_query_adaptive(results, strategy, llm_profile)
    else:
        return _handle_general_query_adaptive(results, strategy, llm_profile)

def _handle_statistical_query_adaptive(results: List[Dict], strategy: QueryStrategy, llm_profile: LLMProfile) -> Dict[str, Any]:
    """Handle statistical queries with LLM-specific optimization"""
    
    # Limit results based on LLM capacity
    max_results = min(strategy.max_results, len(results))
    cleaned_results = []
    
    for result in results[:max_results]:
        cleaned_result = {k: v for k, v in result.items() if not k.startswith('_')}
        cleaned_results.append(cleaned_result)
    
    return {
        'events': cleaned_results,
        'summarization_applied': True,
        'summarization_type': f'statistical_aggregation_{llm_profile.context_class.value}',
        'summary': {
            'type': 'Statistical aggregation optimized for ' + llm_profile.name,
            'results_included': len(cleaned_results),
            'results_truncated': len(results) - len(cleaned_results),
            'optimization_level': strategy.summarization_level
        }
    }

def _handle_investigation_query_adaptive(results: List[Dict], strategy: QueryStrategy, llm_profile: LLMProfile) -> Dict[str, Any]:
    """Handle investigation queries with pattern detection based on LLM capacity"""
    
    # Pattern detection level based on LLM capacity
    if strategy.pattern_detection == 'comprehensive':
        patterns = _detect_comprehensive_patterns(results)
    elif strategy.pattern_detection == 'focused':
        patterns = _detect_focused_patterns(results)
    else:
        patterns = _detect_basic_patterns(results)
    
    # Sample selection based on strategy
    samples = []
    pattern_summaries = []
    
    for pattern_key, pattern_events in patterns.items():
        if len(samples) >= strategy.max_samples:
            break
            
        # Create sample based on detail level
        if llm_profile.context_class == ContextSize.LARGE:
            sample = _create_detailed_sample(pattern_events[0])
        elif llm_profile.context_class == ContextSize.MEDIUM:
            sample = _create_moderate_sample(pattern_events[0])
        else:
            sample = _create_minimal_sample(pattern_events[0], ['timestamp', 'sourcetype', 'host'])
            
        samples.append(sample)
        
        pattern_summaries.append({
            'pattern_signature': pattern_key,
            'event_count': len(pattern_events),
            'percentage': round(len(pattern_events) / len(results) * 100, 1),
            'representative_fields': _extract_pattern_key_fields(pattern_events[:3])
        })
    
    return {
        'events': samples,
        'summarization_applied': True,
        'summarization_type': f'investigation_{strategy.pattern_detection}_{llm_profile.context_class.value}',
        'patterns': pattern_summaries,
        'summary': {
            'type': f'Investigation analysis for {llm_profile.name}',
            'patterns_detected': len(patterns),
            'samples_included': len(samples),
            'pattern_detection_level': strategy.pattern_detection,
            'context_optimization': llm_profile.context_class.value
        }
    }

def _handle_discovery_query_adaptive(results: List[Dict], strategy: QueryStrategy, llm_profile: LLMProfile) -> Dict[str, Any]:
    """Handle discovery queries with field analysis depth based on LLM capacity"""
    
    # Field analysis depth based on strategy
    if strategy.field_analysis_depth == 'complete':
        field_analysis = _analyze_all_fields_comprehensive(results)
    elif strategy.field_analysis_depth == 'important_fields':
        field_analysis = _analyze_important_fields(results)
    else:
        field_analysis = _analyze_top_fields_only(results)
    
    # Create samples based on LLM capacity
    samples = []
    sample_count = min(strategy.max_samples, len(results))
    
    for i, event in enumerate(results[:sample_count]):
        if llm_profile.context_class == ContextSize.LARGE:
            important_fields = field_analysis.get('important_fields', [])[:20]
        elif llm_profile.context_class == ContextSize.MEDIUM:
            important_fields = field_analysis.get('important_fields', [])[:10]
        else:
            important_fields = field_analysis.get('important_fields', [])[:5]
            
        sample = _create_minimal_sample(event, important_fields)
        samples.append(sample)
    
    return {
        'events': samples,
        'summarization_applied': True,
        'summarization_type': f'discovery_{strategy.field_analysis_depth}_{llm_profile.context_class.value}',
        'field_analysis': field_analysis,
        'summary': {
            'type': f'Data discovery for {llm_profile.name}',
            'analysis_depth': strategy.field_analysis_depth,
            'total_fields_analyzed': field_analysis.get('total_fields', 0),
            'samples_included': len(samples)
        }
    }

def _handle_performance_query_adaptive(results: List[Dict], strategy: QueryStrategy, llm_profile: LLMProfile) -> Dict[str, Any]:
    """Handle performance queries with metric focus"""
    
    # Extract performance metrics
    perf_metrics = _extract_performance_metrics(results)
    
    # Create focused samples
    samples = []
    for i, event in enumerate(results[:strategy.max_samples]):
        # Focus on performance-related fields
        perf_fields = ['timestamp', 'cpu_usage', 'memory_usage', 'disk_usage', 'response_time', 'latency', 'throughput']
        sample = _create_focused_sample(event, perf_fields)
        samples.append(sample)
    
    return {
        'events': samples,
        'summarization_applied': True,
        'summarization_type': f'performance_{llm_profile.context_class.value}',
        'performance_metrics': perf_metrics,
        'summary': {
            'type': f'Performance analysis for {llm_profile.name}',
            'metrics_extracted': len(perf_metrics),
            'samples_included': len(samples),
            'focus': 'system_performance_indicators'
        }
    }

def _handle_general_query_adaptive(results: List[Dict], strategy: QueryStrategy, llm_profile: LLMProfile) -> Dict[str, Any]:
    """Handle general queries with balanced approach based on LLM capacity"""
    
    # Smart sampling based on LLM capacity
    if strategy.diversity_analysis:
        samples = _smart_sampling_with_diversity(results, strategy.max_samples, llm_profile)
    else:
        samples = _simple_sampling(results, strategy.max_samples)
    
    # Field summary
    field_summary = _generate_adaptive_field_summary(samples, llm_profile.context_class)
    
    return {
        'events': samples,
        'summarization_applied': True,
        'summarization_type': f'general_balanced_{llm_profile.context_class.value}',
        'field_summary': field_summary,
        'summary': {
            'type': f'Balanced analysis for {llm_profile.name}',
            'sampling_strategy': 'diversity' if strategy.diversity_analysis else 'simple',
            'samples_included': len(samples),
            'context_optimization': llm_profile.context_class.value
        }
    }

# Helper functions for different pattern detection levels
def _detect_comprehensive_patterns(results: List[Dict]) -> Dict[str, List[Dict]]:
    """Comprehensive pattern detection for large context LLMs"""
    patterns = defaultdict(list)
    
    for event in results:
        signature_fields = []
        
        # Use many fields for pattern detection
        pattern_fields = ['sourcetype', 'EventCode', 'action', 'status', 'method', 'user', 'host', 'process']
        for field in pattern_fields:
            if field in event:
                signature_fields.append(f"{field}={event[field]}")
        
        if not signature_fields:
            signature_fields.append(f"fields={len(event)}")
            
        pattern_key = "|".join(signature_fields[:6])  # Use more fields
        patterns[pattern_key].append(event)
    
    return dict(patterns)

def _detect_focused_patterns(results: List[Dict]) -> Dict[str, List[Dict]]:
    """Focused pattern detection for medium context LLMs"""
    patterns = defaultdict(list)
    
    for event in results:
        signature_fields = []
        
        # Use moderate fields for pattern detection
        pattern_fields = ['sourcetype', 'EventCode', 'action', 'status']
        for field in pattern_fields:
            if field in event:
                signature_fields.append(f"{field}={event[field]}")
        
        if not signature_fields:
            signature_fields.append(f"fields={len(event)}")
            
        pattern_key = "|".join(signature_fields[:3])  # Use fewer fields
        patterns[pattern_key].append(event)
    
    return dict(patterns)

def _detect_basic_patterns(results: List[Dict]) -> Dict[str, List[Dict]]:
    """Basic pattern detection for small context LLMs"""
    patterns = defaultdict(list)
    
    for event in results:
        signature_fields = []
        
        # Use minimal fields for pattern detection
        for field in ['sourcetype', 'EventCode']:
            if field in event:
                signature_fields.append(f"{field}={event[field]}")
                break  # Only use first match
        
        if not signature_fields:
            signature_fields.append("unknown_pattern")
            
        pattern_key = signature_fields[0]  # Use single field only
        patterns[pattern_key].append(event)
    
    return dict(patterns)

# Additional helper functions
def _create_moderate_sample(event: Dict) -> Dict:
    """Create moderate detail sample"""
    sample = {}
    
    # Include timestamp
    if '_time' in event:
        sample['timestamp'] = event['_time']
    
    # Include essential fields
    for field in ['host', 'sourcetype', 'index']:
        if field in event:
            sample[field] = event[field]
    
    # Include limited non-internal fields
    field_count = 0
    for key, value in event.items():
        if not key.startswith('_') and key not in sample and field_count < 10:
            if isinstance(value, str) and len(value) > 100:
                sample[key] = value[:100] + "..."
            else:
                sample[key] = value
            field_count += 1
    
    return sample

def _create_focused_sample(event: Dict, focus_fields: List[str]) -> Dict:
    """Create sample focused on specific fields"""
    sample = {}
    
    # Always include timestamp
    if '_time' in event:
        sample['timestamp'] = event['_time']
    
    # Include focused fields
    for field in focus_fields:
        if field in event:
            sample[field] = event[field]
    
    # Add a few other fields if space allows
    other_count = 0
    for key, value in event.items():
        if key not in sample and not key.startswith('_') and other_count < 3:
            sample[key] = value
            other_count += 1
    
    return sample

# Continue with other helper functions...
def _smart_sampling_with_diversity(results: List[Dict], sample_size: int, llm_profile: LLMProfile) -> List[Dict]:
    """Smart sampling with diversity for different LLM contexts"""
    if len(results) <= sample_size:
        return [_create_adaptive_sample(event, llm_profile) for event in results]
    
    samples = []
    step = len(results) // sample_size
    
    for i in range(sample_size):
        idx = i * step
        if idx < len(results):
            sample = _create_adaptive_sample(results[idx], llm_profile)
            samples.append(sample)
    
    return samples

def _create_adaptive_sample(event: Dict, llm_profile: LLMProfile) -> Dict:
    """Create sample adapted to LLM context capacity"""
    if llm_profile.context_class == ContextSize.LARGE:
        return _create_detailed_sample(event)
    elif llm_profile.context_class == ContextSize.MEDIUM:
        return _create_moderate_sample(event)
    else:
        return _create_minimal_sample(event, ['timestamp', 'sourcetype', 'host'])

# Additional analysis functions for different depths
def _analyze_all_fields_comprehensive(results: List[Dict]) -> Dict[str, Any]:
    """Comprehensive field analysis for large context LLMs"""
    field_counts = Counter()
    field_samples = defaultdict(set)
    field_types = {}
    field_relationships = {}
    
    sample_size = min(len(results), 100)  # Analyze more events
    
    for event in results[:sample_size]:
        for field, value in event.items():
            if not field.startswith('_'):
                field_counts[field] += 1
                field_samples[field].add(str(value)[:100])
                
                if field not in field_types:
                    field_types[field] = _infer_field_type(value)
    
    total_events = sample_size
    important_fields = sorted(field_counts.keys(), 
                            key=lambda f: field_counts[f] / total_events, 
                            reverse=True)
    
    return {
        'total_fields': len(field_counts),
        'important_fields': important_fields[:30],  # More fields
        'field_coverage': {f: round(field_counts[f] / total_events * 100, 1) 
                          for f in important_fields[:15]},
        'field_types': field_types,
        'field_variety_score': len(field_counts) / total_events if total_events > 0 else 0,
        'sample_values': {f: list(field_samples[f])[:10] for f in important_fields[:15]},
        'analysis_depth': 'comprehensive'
    }

def _analyze_important_fields(results: List[Dict]) -> Dict[str, Any]:
    """Important fields analysis for medium context LLMs"""
    field_counts = Counter()
    field_types = {}
    
    sample_size = min(len(results), 50)
    
    for event in results[:sample_size]:
        for field, value in event.items():
            if not field.startswith('_'):
                field_counts[field] += 1
                if field not in field_types:
                    field_types[field] = _infer_field_type(value)
    
    total_events = sample_size
    important_fields = sorted(field_counts.keys(), 
                            key=lambda f: field_counts[f] / total_events, 
                            reverse=True)
    
    return {
        'total_fields': len(field_counts),
        'important_fields': important_fields[:15],  # Moderate number
        'field_coverage': {f: round(field_counts[f] / total_events * 100, 1) 
                          for f in important_fields[:10]},
        'field_types': field_types,
        'analysis_depth': 'important_fields'
    }

def _analyze_top_fields_only(results: List[Dict]) -> Dict[str, Any]:
    """Top fields only analysis for small context LLMs"""
    field_counts = Counter()
    
    sample_size = min(len(results), 20)
    
    for event in results[:sample_size]:
        for field in event.keys():
            if not field.startswith('_'):
                field_counts[field] += 1
    
    important_fields = sorted(field_counts.keys(), 
                            key=lambda f: field_counts[f], 
                            reverse=True)
    
    return {
        'total_fields': len(field_counts),
        'important_fields': important_fields[:8],  # Very limited
        'analysis_depth': 'top_fields_only'
    }

def _simple_sampling(results: List[Dict], sample_size: int) -> List[Dict]:
    """Simple sampling without diversity analysis"""
    if len(results) <= sample_size:
        return results[:sample_size]
    
    step = len(results) // sample_size
    return [results[i * step] for i in range(sample_size)]

def _generate_adaptive_field_summary(samples: List[Dict], context_class: ContextSize) -> Dict[str, Any]:
    """Generate field summary adapted to context size"""
    if not samples:
        return {}
    
    all_fields = set()
    field_types = {}
    
    for sample in samples:
        for field, value in sample.items():
            all_fields.add(field)
            if field not in field_types:
                field_types[field] = _infer_field_type(value)
    
    # Adapt detail level to context size
    if context_class == ContextSize.LARGE:
        return {
            'total_fields': len(all_fields),
            'common_fields': list(all_fields),
            'field_types': field_types,
            'detail_level': 'comprehensive'
        }
    elif context_class == ContextSize.MEDIUM:
        return {
            'total_fields': len(all_fields),
            'common_fields': list(all_fields)[:15],
            'field_types': {k: v for k, v in list(field_types.items())[:10]},
            'detail_level': 'moderate'
        }
    else:
        return {
            'total_fields': len(all_fields),
            'common_fields': list(all_fields)[:8],
            'detail_level': 'minimal'
        }

# Utility functions
def _extract_performance_metrics(results: List[Dict]) -> Dict[str, Any]:
    """Extract performance-related metrics from results"""
    metrics = {}
    numeric_fields = []
    
    for event in results[:10]:  # Sample for metric detection
        for field, value in event.items():
            if isinstance(value, (int, float)) or (isinstance(value, str) and value.replace('.', '').isdigit()):
                if any(perf_term in field.lower() for perf_term in ['cpu', 'memory', 'disk', 'time', 'usage', 'percent']):
                    numeric_fields.append(field)
    
    metrics['performance_fields_detected'] = list(set(numeric_fields))
    return metrics

def _extract_pattern_key_fields(events: List[Dict]) -> Dict[str, Any]:
    """Extract key fields that define a pattern - simplified version"""
    field_values = defaultdict(set)
    
    for event in events:
        for field, value in event.items():
            if not field.startswith('_'):
                field_values[field].add(str(value)[:50])  # Limit value length
    
    # Return fields with consistent values
    pattern_fields = {}
    for field, values in field_values.items():
        if len(values) == 1:
            pattern_fields[field] = list(values)[0]
    
    return pattern_fields

def _create_detailed_sample(event: Dict) -> Dict:
    """Create detailed sample for large context LLMs"""
    sample = {}
    
    if '_time' in event:
        sample['timestamp'] = event['_time']
    
    for field in ['host', 'source', 'sourcetype', 'index']:
        if field in event:
            sample[field] = event[field]
    
    for key, value in event.items():
        if not key.startswith('_') and key not in sample:
            if isinstance(value, str) and len(value) > 500:
                sample[key] = value[:500] + "..."
            else:
                sample[key] = value
    
    return sample

def _create_minimal_sample(event: Dict, important_fields: List[str]) -> Dict:
    """Create minimal sample for small context LLMs"""
    sample = {}
    
    if '_time' in event:
        sample['timestamp'] = event['_time']
    
    for field in important_fields[:8]:  # Limit field count
        if field in event:
            value = event[field]
            if isinstance(value, str) and len(value) > 50:
                sample[field] = value[:50] + "..."
            else:
                sample[field] = value
    
    return sample

def _infer_field_type(value) -> str:
    """Infer field type from value"""
    if isinstance(value, (int, float)):
        return 'numeric'
    elif isinstance(value, str):
        if re.match(r'^\d{4}-\d{2}-\d{2}', str(value)):
            return 'timestamp'
        elif re.match(r'^\d+\.\d+\.\d+\.\d+$', str(value)):
            return 'ip_address'
        elif '@' in str(value):
            return 'email'
        else:
            return 'text'
    else:
        return 'unknown'

# Response builders
def _extract_user_context(variables: Dict[str, Any]) -> Dict[str, Any]:
    """Extract user context from variables for guardrails"""
    return {
        'username': variables.get('user', 'unknown'),
        'roles': variables.get('user_roles', ['standard_user']),
        'user_role': 'standard_user'
    }

def _blocked_response(validation_result: Dict, llm_config: Dict) -> Dict[str, Any]:
    """Return response for blocked search"""
    return {
        'success': False,
        'blocked_by_guardrails': True,
        'violations': validation_result['violations'],
        'block_reason': validation_result.get('block_reason', 'Security violation'),
        'user_role': validation_result.get('user_role', 'unknown'),
        'events': [],
        'count': 0,
        'llm_config': llm_config,
        'search_info': {
            'original_query': validation_result.get('original_query', ''),
            'enforcement_level': validation_result.get('enforcement_level', 'strict')
        }
    }

def _empty_result_response(variables: Dict, llm_config: Dict) -> Dict[str, Any]:
    """Return response for empty results"""
    return {
        'success': True,
        'summarization_applied': False,
        'events': [],
        'count': 0,
        'message': 'No events found',
        'llm_config': llm_config,
        'search_info': {
            'query': variables.get('search_query', ''),
            'optimization': 'No data to process'
        }
    }

def _error_response(error_msg: str, variables: Dict) -> Dict[str, Any]:
    """Return error response"""
    return {
        'success': False,
        'error': error_msg,
        'events': [],
        'count': 0,
        'search_info': {
            'query': variables.get('search_query', ''),
            'error_context': 'Enhanced multi-LLM summarization failed'
        }
    }