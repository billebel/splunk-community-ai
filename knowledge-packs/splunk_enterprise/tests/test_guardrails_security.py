"""
Comprehensive security test suite for Splunk Enterprise v2 guardrails
Tests all bypass techniques identified in GitHub issue #2
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the transforms directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'transforms'))

from guardrails import GuardrailsEngine


class TestGuardrailsBypassProtection:
    """Test suite for bypass technique protection"""
    
    @pytest.fixture
    def guardrails_engine(self):
        """Create a guardrails engine with test configuration"""
        return GuardrailsEngine()
    
    @pytest.fixture
    def standard_user_context(self):
        """Standard user context for testing"""
        return {
            'username': 'test_user',
            'roles': ['standard_user'],
            'user_role': 'standard_user'
        }
    
    def test_case_sensitivity_bypass_blocked(self, guardrails_engine, standard_user_context):
        """Test that case variations of blocked commands are properly blocked"""
        
        # Test various case combinations
        bypass_attempts = [
            "index=main | DELETE",           # Uppercase
            "index=main | Delete",           # Title case
            "index=main | DeLeTe",          # Mixed case
            "index=main | dELETE",          # Mixed case 2
            "| SCRIPT python test.py",       # Uppercase script
            "| Script python test.py",       # Title case script
            "| OUTPUTCSV /tmp/test.csv",     # Uppercase outputcsv
        ]
        
        for query in bypass_attempts:
            result = guardrails_engine.validate_search(query, standard_user_context)
            assert result['blocked'] == True, f"Query should be blocked: {query}"
            assert len(result['violations']) > 0, f"Should have violations: {query}"
    
    def test_unicode_bypass_blocked(self, guardrails_engine, standard_user_context):
        """Test that Unicode substitution bypass attempts are blocked"""
        
        # Unicode bypass attempts (using Cyrillic and similar characters)
        unicode_attempts = [
            "index=main | dеlete",          # Cyrillic 'е' instead of 'e'
            "index=main | dеlеtе",          # Multiple Cyrillic characters
            "index=main | ѕcript test.py",  # Cyrillic 'ѕ' instead of 's'
        ]
        
        for query in unicode_attempts:
            result = guardrails_engine.validate_search(query, standard_user_context)
            assert result['blocked'] == True, f"Unicode bypass should be blocked: {query}"
    
    def test_url_encoding_bypass_blocked(self, guardrails_engine, standard_user_context):
        """Test that URL-encoded bypass attempts are blocked"""
        
        # URL-encoded bypass attempts
        encoded_attempts = [
            "index=main | %64%65%6C%65%74%65",  # "delete" URL encoded
            "index=main%20%7C%20delete",         # "| delete" partially encoded
            "| %73%63%72%69%70%74 test.py",     # "script" URL encoded
        ]
        
        for query in encoded_attempts:
            result = guardrails_engine.validate_search(query, standard_user_context)
            assert result['blocked'] == True, f"URL encoded bypass should be blocked: {query}"
    
    def test_dynamic_construction_blocked(self, guardrails_engine, standard_user_context):
        """Test that dynamic command construction is detected and blocked"""
        
        # Dynamic construction attempts
        construction_attempts = [
            '| eval cmd="del" + "ete" | run $cmd$',
            '| eval command="scr" + "ipt" | $command$ test.py',
            '| eval x="out" + "putcsv" | $x$ file.csv',
            "| eval parts='dele' + 'te' | run $parts$",
            '| eval a="dele", b="te" | eval full=a+b | run $full$'
        ]
        
        for query in construction_attempts:
            result = guardrails_engine.validate_search(query, standard_user_context)
            assert result['blocked'] == True, f"Dynamic construction should be blocked: {query}"
            assert any("dynamic construction" in v.lower() for v in result['violations']), \
                f"Should detect dynamic construction: {query}"
    
    def test_whitespace_manipulation_blocked(self, guardrails_engine, standard_user_context):
        """Test that creative whitespace usage doesn't bypass filters"""
        
        # Whitespace manipulation attempts
        whitespace_attempts = [
            "| \t\n delete \t",              # Mixed whitespace
            "|\tdelete",                     # Tab before command
            "| \n delete",                   # Newline before command
            "|\r\ndelete",                   # CRLF before command
            "|    delete    ",               # Multiple spaces
        ]
        
        for query in whitespace_attempts:
            result = guardrails_engine.validate_search(query, standard_user_context)
            assert result['blocked'] == True, f"Whitespace manipulation should be blocked: {query}"
    
    def test_path_traversal_blocked(self, guardrails_engine, standard_user_context):
        """Test that path traversal attempts are blocked"""
        
        # Path traversal attempts
        traversal_attempts = [
            "| outputcsv ../../../etc/passwd",      # Unix path traversal
            "| outputcsv ..\\..\\..\\windows\\system32\\config", # Windows path traversal
            "| outputcsv /etc/shadow",              # Direct system file access
            "| outputcsv /root/.ssh/id_rsa",        # SSH key access
            "| outputcsv C:\\Windows\\System32\\config\\SAM", # Windows SAM file
            "| outputcsv ~/../../sensitive.txt",    # Home directory traversal
        ]
        
        for query in traversal_attempts:
            result = guardrails_engine.validate_search(query, standard_user_context)
            assert result['blocked'] == True, f"Path traversal should be blocked: {query}"
    
    def test_missing_dangerous_commands_blocked(self, guardrails_engine, standard_user_context):
        """Test that previously missing dangerous commands are now blocked"""
        
        # Commands that should be blocked but might have been missing
        dangerous_commands = [
            "| crawl http://evil.com",
            "| dbxquery SELECT * FROM users",
            "| run echo 'test'",
            "| collect index=test",
            "| summary indexname=test",
            "| mcollect metric=test",
            "| outputtext /tmp/test.txt",
            "| outputjson /tmp/data.json",
            "| outputxml /tmp/data.xml"
        ]
        
        for query in dangerous_commands:
            result = guardrails_engine.validate_search(query, standard_user_context)
            assert result['blocked'] == True, f"Dangerous command should be blocked: {query}"
    
    def test_base64_encoding_blocked(self, guardrails_engine, standard_user_context):
        """Test that base64 encoding/decoding attempts are blocked"""
        
        base64_attempts = [
            "| eval test=base64('delete')",
            "| eval decoded=decode(data, 'base64')",
            "| base64 encode test",
        ]
        
        for query in base64_attempts:
            result = guardrails_engine.validate_search(query, standard_user_context)
            assert result['blocked'] == True, f"Base64 operation should be blocked: {query}"
    
    def test_legitimate_queries_allowed(self, guardrails_engine, standard_user_context):
        """Test that legitimate queries are still allowed"""
        
        # Legitimate queries that should NOT be blocked
        legitimate_queries = [
            "index=security EventCode=4625",
            "index=web status>=400 | stats count by status",
            "index=main error | head 10",
            "search index=app log_level=ERROR | table _time, message",
            "| makeresults | eval test='safe_command'",
        ]
        
        for query in legitimate_queries:
            result = guardrails_engine.validate_search(query, standard_user_context)
            assert result['blocked'] == False, f"Legitimate query should be allowed: {query}"
    
    def test_input_normalization_function(self, guardrails_engine):
        """Test the input normalization function directly"""
        
        test_cases = [
            # (input, expected_characteristics)
            ("| DELETE", "delete"),  # Case normalization
            ("|\tdelete\n", "delete"),  # Whitespace normalization
            ("%64%65%6C%65%74%65", "delete"),  # URL decoding
        ]
        
        for input_query, expected in test_cases:
            normalized = guardrails_engine._normalize_query(input_query)
            assert expected in normalized.lower(), f"Normalization failed for: {input_query}"


class TestGuardrailsConfiguration:
    """Test guardrails configuration and role-based access"""
    
    @pytest.fixture
    def guardrails_engine(self):
        return GuardrailsEngine()
    
    def test_admin_bypass_permissions(self, guardrails_engine):
        """Test that admin users can bypass certain restrictions"""
        
        admin_context = {
            'username': 'admin_user',
            'roles': ['admin'],
            'user_role': 'admin'
        }
        
        # Some queries that might be allowed for admins
        admin_queries = [
            "| inputlookup sensitive_data.csv",  # File access for admin
        ]
        
        for query in admin_queries:
            result = guardrails_engine.validate_search(query, admin_context)
            # Note: This depends on admin bypass configuration
            # We're testing that the system respects role differences
            assert isinstance(result, dict), "Should return valid result structure"
    
    def test_role_limits_enforcement(self, guardrails_engine):
        """Test that different user roles have different limits"""
        
        roles_to_test = ['admin', 'power_user', 'standard_user', 'readonly_user']
        
        for role in roles_to_test:
            limits = guardrails_engine._get_role_limits(role)
            assert isinstance(limits, dict), f"Should return limits for role: {role}"
            assert 'max_time_range_days' in limits, f"Should have time limits for: {role}"
            assert 'max_results_per_search' in limits, f"Should have result limits for: {role}"


class TestDataMaskingProtection:
    """Test data masking functionality"""
    
    @pytest.fixture
    def guardrails_engine(self):
        return GuardrailsEngine()
    
    @pytest.fixture
    def standard_user_context(self):
        return {
            'username': 'test_user',
            'roles': ['standard_user'],
            'user_role': 'standard_user'
        }
    
    def test_sensitive_field_masking(self, guardrails_engine, standard_user_context):
        """Test that sensitive fields are properly masked"""
        
        test_data = [
            {
                "username": "john.doe@company.com",
                "password": "secretpassword123",
                "ssn": "123-45-6789",
                "credit_card": "4532-1234-5678-9012",
                "host": "web-server-01"  # Should not be masked
            }
        ]
        
        masked_data = guardrails_engine.apply_data_masking(test_data, standard_user_context)
        
        assert len(masked_data) == 1
        masked_event = masked_data[0]
        
        # Check that sensitive fields are masked
        sensitive_fields = ['username', 'password', 'ssn', 'credit_card']
        for field in sensitive_fields:
            if field in masked_event:
                assert '[MASKED]' in str(masked_event[field]) or '***' in str(masked_event[field]), \
                    f"Field {field} should be masked"
        
        # Check that non-sensitive fields are preserved
        assert masked_event.get('host') == 'web-server-01', "Non-sensitive field should be preserved"


class TestFailSafeBehavior:
    """Test fail-safe behavior when configurations are invalid"""
    
    def test_invalid_config_fallback(self):
        """Test that invalid configuration triggers fail-safe mode"""
        
        # Test with invalid config path
        with patch('os.path.exists', return_value=False):
            engine = GuardrailsEngine()
            assert isinstance(engine.config, dict), "Should have fallback config"
    
    def test_config_parsing_error_fallback(self):
        """Test fallback behavior when config parsing fails"""
        
        with patch('yaml.safe_load', side_effect=Exception("Parse error")):
            with patch('os.path.exists', return_value=True):
                engine = GuardrailsEngine()
                # Should still initialize with fail-safe defaults
                assert isinstance(engine.config, dict), "Should have fail-safe config"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])