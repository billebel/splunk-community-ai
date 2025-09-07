"""
Multi-LLM Context Manager - Adaptive pagination and summarization for different LLM providers
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
import yaml
import os
import re
import json
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ContextSize(Enum):
    SMALL = "small_context"      # <16K tokens
    MEDIUM = "medium_context"    # 16K-200K tokens  
    LARGE = "large_context"      # >200K tokens

@dataclass
class LLMProfile:
    name: str
    context_window: int
    chars_per_token: int
    reserved_tokens: int
    optimal_usage: float
    token_efficiency: str
    best_for: List[str]
    context_class: ContextSize

@dataclass
class QueryStrategy:
    max_results: int
    max_samples: int
    summarization_level: str
    include_raw_events: bool
    pattern_detection: str
    field_analysis_depth: str
    diversity_analysis: bool

class LLMContextManager:
    """Manages context window adaptation for different LLM providers"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), '..', 'llm_context_config.yaml'
        )
        self.config = self._load_config()
        self.llm_profiles = self._parse_llm_profiles()
        self.strategies = self._parse_strategies()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load LLM context configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load LLM config: {e}, using defaults")
            return self._get_default_config()
    
    def _parse_llm_profiles(self) -> Dict[str, LLMProfile]:
        """Parse LLM profiles from config"""
        profiles = {}
        
        for name, config in self.config.get('llm_profiles', {}).items():
            context_window = config['context_window']
            
            # Determine context class
            if context_window < 16384:
                context_class = ContextSize.SMALL
            elif context_window < 200000:
                context_class = ContextSize.MEDIUM
            else:
                context_class = ContextSize.LARGE
                
            profiles[name] = LLMProfile(
                name=name,
                context_window=context_window,
                chars_per_token=config['chars_per_token'],
                reserved_tokens=config['reserved_tokens'],
                optimal_usage=config['optimal_usage'],
                token_efficiency=config['token_efficiency'],
                best_for=config['best_for'],
                context_class=context_class
            )
            
        return profiles
    
    def _parse_strategies(self) -> Dict[ContextSize, Dict[str, QueryStrategy]]:
        """Parse query strategies by context size"""
        strategies = {}
        
        for context_size, size_strategies in self.config.get('strategy_matrix', {}).items():
            context_enum = ContextSize(context_size)
            strategies[context_enum] = {}
            
            for query_type, strategy_config in size_strategies.items():
                strategies[context_enum][query_type] = QueryStrategy(
                    max_results=strategy_config.get('max_results', 100),
                    max_samples=strategy_config.get('max_samples', 10),
                    summarization_level=strategy_config.get('summarization_level', 'moderate'),
                    include_raw_events=strategy_config.get('include_raw_events', True),
                    pattern_detection=strategy_config.get('pattern_detection', 'focused'),
                    field_analysis_depth=strategy_config.get('field_analysis_depth', 'important_fields'),
                    diversity_analysis=strategy_config.get('diversity_analysis', True)
                )
                
        return strategies
    
    def detect_llm_profile(self, request_context: Dict[str, Any]) -> LLMProfile:
        """Auto-detect LLM profile from request context"""
        
        # Try user agent detection
        user_agent = request_context.get('user_agent', '').lower()
        if user_agent:
            for pattern_config in self.config.get('llm_detection', {}).get('user_agent_patterns', []):
                if re.search(pattern_config['pattern'], user_agent, re.IGNORECASE):
                    profile_name = pattern_config['default_profile']
                    if profile_name in self.llm_profiles:
                        logger.info(f"Detected LLM profile from user agent: {profile_name}")
                        return self.llm_profiles[profile_name]
        
        # Try API endpoint detection
        api_endpoint = request_context.get('api_endpoint', '').lower()
        if api_endpoint:
            for pattern_config in self.config.get('llm_detection', {}).get('api_endpoint_patterns', []):
                if re.search(pattern_config['pattern'], api_endpoint, re.IGNORECASE):
                    profile_name = pattern_config['default_profile']
                    if profile_name in self.llm_profiles:
                        logger.info(f"Detected LLM profile from API endpoint: {profile_name}")
                        return self.llm_profiles[profile_name]
        
        # Check for explicit model specification
        model_name = request_context.get('model', '').lower()
        if model_name:
            # Direct match
            if model_name in self.llm_profiles:
                return self.llm_profiles[model_name]
            
            # Fuzzy match
            for profile_name in self.llm_profiles:
                if model_name in profile_name.lower():
                    logger.info(f"Fuzzy matched LLM profile: {profile_name}")
                    return self.llm_profiles[profile_name]
        
        # Fallback to default
        fallback_profile = self.config.get('fallback', {}).get('profile', 'gpt-4')
        logger.info(f"Using fallback LLM profile: {fallback_profile}")
        return self.llm_profiles.get(fallback_profile, self._get_conservative_profile())
    
    def get_query_strategy(self, llm_profile: LLMProfile, query_intent: str) -> QueryStrategy:
        """Get optimal query strategy for LLM and query type"""
        
        context_strategies = self.strategies.get(llm_profile.context_class, {})
        strategy = context_strategies.get(query_intent)
        
        if not strategy:
            # Fallback to general strategy
            strategy = context_strategies.get('general')
            
        if not strategy:
            # Ultimate fallback
            logger.warning(f"No strategy found for {llm_profile.context_class} + {query_intent}, using conservative default")
            strategy = self._get_conservative_strategy()
            
        return strategy
    
    def calculate_available_tokens(self, llm_profile: LLMProfile) -> int:
        """Calculate available tokens for data based on LLM profile"""
        total_context = llm_profile.context_window
        reserved = llm_profile.reserved_tokens
        optimal_usage = llm_profile.optimal_usage
        
        available = int((total_context - reserved) * optimal_usage)
        
        # Apply buffer from optimization config
        buffer = self.config.get('optimization', {}).get('token_estimation_buffer', 0.1)
        return int(available * (1 - buffer))
    
    def estimate_tokens(self, data: Any, llm_profile: LLMProfile) -> int:
        """Estimate token count for data based on LLM characteristics"""
        if isinstance(data, (dict, list)):
            json_str = json.dumps(data, default=str, separators=(',', ':'))
        else:
            json_str = str(data)
            
        char_count = len(json_str)
        return char_count // llm_profile.chars_per_token
    
    def should_compress(self, estimated_tokens: int, available_tokens: int) -> bool:
        """Determine if compression is needed"""
        threshold = self.config.get('optimization', {}).get('compression_threshold', 0.9)
        return estimated_tokens > (available_tokens * threshold)
    
    def get_context_summary(self, llm_profile: LLMProfile, query_intent: str) -> Dict[str, Any]:
        """Get summary of context management decisions"""
        strategy = self.get_query_strategy(llm_profile, query_intent)
        available_tokens = self.calculate_available_tokens(llm_profile)
        
        return {
            'llm_profile': {
                'name': llm_profile.name,
                'context_window': llm_profile.context_window,
                'context_class': llm_profile.context_class.value,
                'token_efficiency': llm_profile.token_efficiency
            },
            'strategy': {
                'max_results': strategy.max_results,
                'max_samples': strategy.max_samples,
                'summarization_level': strategy.summarization_level,
                'pattern_detection': strategy.pattern_detection
            },
            'token_budget': {
                'total_context': llm_profile.context_window,
                'reserved_tokens': llm_profile.reserved_tokens,
                'available_for_data': available_tokens,
                'optimal_usage_pct': int(llm_profile.optimal_usage * 100)
            }
        }
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Fallback configuration if config file cannot be loaded"""
        return {
            'llm_profiles': {
                'default': {
                    'context_window': 8192,
                    'chars_per_token': 4,
                    'reserved_tokens': 2000,
                    'optimal_usage': 0.6,
                    'token_efficiency': 'medium',
                    'best_for': ['general']
                }
            },
            'strategy_matrix': {
                'small_context': {
                    'general': {
                        'max_results': 50,
                        'max_samples': 5,
                        'summarization_level': 'aggressive',
                        'include_raw_events': False,
                        'pattern_detection': 'basic',
                        'field_analysis_depth': 'minimal',
                        'diversity_analysis': False
                    }
                }
            }
        }
    
    def _get_conservative_profile(self) -> LLMProfile:
        """Conservative default profile for unknown LLMs"""
        return LLMProfile(
            name="conservative_default",
            context_window=8192,
            chars_per_token=4,
            reserved_tokens=2000,
            optimal_usage=0.6,
            token_efficiency="medium",
            best_for=["general"],
            context_class=ContextSize.SMALL
        )
    
    def _get_conservative_strategy(self) -> QueryStrategy:
        """Conservative default strategy"""
        return QueryStrategy(
            max_results=50,
            max_samples=5,
            summarization_level="aggressive",
            include_raw_events=False,
            pattern_detection="basic",
            field_analysis_depth="minimal",
            diversity_analysis=False
        )

# Global instance
_context_manager = None

def get_context_manager() -> LLMContextManager:
    """Get global context manager instance"""
    global _context_manager
    if _context_manager is None:
        _context_manager = LLMContextManager()
    return _context_manager

def detect_and_configure(request_context: Dict[str, Any]) -> Tuple[LLMProfile, Dict[str, Any]]:
    """Convenience function to detect LLM and get configuration"""
    manager = get_context_manager()
    profile = manager.detect_llm_profile(request_context)
    
    # Default to general query intent if not specified
    query_intent = request_context.get('query_intent', 'general')
    
    config_summary = manager.get_context_summary(profile, query_intent)
    
    return profile, config_summary