"""Tests for retry utilities module."""

import pytest
import time
from datetime import timedelta
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st, settings, HealthCheck

from autoframe.utils.retry import (
    with_database_retry,
    with_network_retry,
    retry_with_backoff,
    is_transient_error,
    is_database_error,
    retry_result
)
from autoframe.types import DataSourceError
from logerr import Ok, Err


class TestRetryDecorators:
    """Test retry decorator functions."""
    
    def test_with_database_retry_success(self):
        """Test database retry decorator with successful function."""
        @with_database_retry
        def successful_func():
            return "success"
        
        result = successful_func()
        assert result.is_ok()
        assert result.unwrap() == "success"
    
    def test_with_database_retry_failure(self):
        """Test database retry decorator with failing function."""
        call_count = 0
        
        @with_database_retry
        def failing_func():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Database connection failed")
        
        result = failing_func()
        assert result.is_err()
        assert isinstance(result.unwrap_err(), DataSourceError)
        assert "Operation failed after retries" in str(result.unwrap_err())
    
    def test_with_network_retry_success(self):
        """Test network retry decorator with successful function."""
        @with_network_retry
        def successful_func():
            return {"data": "response"}
        
        result = successful_func()
        assert result.is_ok()
        assert result.unwrap() == {"data": "response"}
    
    def test_with_network_retry_failure(self):
        """Test network retry decorator with failing function."""
        @with_network_retry
        def failing_func():
            raise TimeoutError("Network timeout")
        
        result = failing_func()
        assert result.is_err()
        assert isinstance(result.unwrap_err(), DataSourceError)
        assert "Network operation failed after retries" in str(result.unwrap_err())


class TestCustomRetry:
    """Test custom retry functions."""
    
    def test_retry_with_backoff_success(self):
        """Test custom retry with backoff - successful case."""
        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def successful_func():
            return "result"
        
        result = successful_func()
        assert result.is_ok()
        assert result.unwrap() == "result"
    
    def test_retry_with_backoff_failure(self):
        """Test retry with backoff when function fails."""
        @retry_with_backoff(max_attempts=2, base_delay=0.01)
        def always_fails():
            raise ConnectionError("Always fails")
        
        with patch('time.sleep'):  # Speed up test by mocking sleep
            result = always_fails()
        
        assert result.is_err()
        assert "Always fails" in str(result.unwrap_err())


class TestErrorConditions:
    """Test error condition checking functions."""
    
    def test_is_transient_error_connection_error(self):
        """Test transient error detection for connection errors."""
        assert is_transient_error(ConnectionError("Connection failed"))
        assert is_transient_error(TimeoutError("Request timeout"))
        assert is_transient_error(OSError("Network unreachable"))
    
    def test_is_transient_error_by_message(self):
        """Test transient error detection by error message."""
        assert is_transient_error(Exception("Connection timeout occurred"))
        assert is_transient_error(Exception("Network unavailable"))
        assert is_transient_error(Exception("Service temporarily unavailable"))
        assert is_transient_error(Exception("Rate limit exceeded"))
    
    def test_is_not_transient_error(self):
        """Test non-transient error detection."""
        assert not is_transient_error(ValueError("Invalid input"))
        assert not is_transient_error(Exception("Fatal error"))
    
    def test_is_database_error_types(self):
        """Test database error detection by exception type."""
        assert is_database_error(ConnectionError("DB connection lost"))
        assert is_database_error(TimeoutError("Query timeout"))
    
    def test_is_database_error_by_message(self):
        """Test database error detection by message keywords."""
        assert is_database_error(Exception("Database connection refused"))
        assert is_database_error(Exception("Server timeout occurred"))
        assert is_database_error(Exception("Deadlock detected"))
        assert is_database_error(Exception("Transaction failed"))


class TestResultRetry:
    """Test retry functions that work with Result types."""
    
    def test_retry_result_success(self):
        """Test retry_result with successful function."""
        def successful_result():
            return Ok("success")
        
        result = retry_result(successful_result, max_attempts=3, delay=0.01)
        assert result.is_ok()
        assert result.unwrap() == "success"
    
    def test_retry_result_eventual_success(self):
        """Test retry_result that succeeds after failures."""
        call_count = 0
        
        def eventually_successful():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return Err("Temporary failure")
            return Ok("success")
        
        result = retry_result(eventually_successful, max_attempts=3, delay=0.01)
        assert result.is_ok()
        assert result.unwrap() == "success"
        assert call_count == 2
    
    def test_retry_result_all_failures(self):
        """Test retry_result when all attempts fail."""
        call_count = 0
        
        def always_fails():
            nonlocal call_count
            call_count += 1
            return Err(f"Failure {call_count}")
        
        result = retry_result(always_fails, max_attempts=3, delay=0.01)
        assert result.is_err()
        assert result.unwrap_err() == "Failure 3"
        assert call_count == 3


# Hypothesis-based property tests (marked as slow)
@pytest.mark.slow
class TestRetryPropertiesHypothesis:
    """Property-based tests using Hypothesis for retry logic."""
    
    @given(
        max_attempts=st.integers(min_value=1, max_value=10),
        base_delay=st.floats(min_value=0.001, max_value=0.1),
        success_after=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def test_retry_backoff_properties(self, max_attempts, base_delay, success_after):
        """Property test: retry should succeed if success_after <= max_attempts."""
        call_count = 0
        
        @retry_with_backoff(max_attempts=max_attempts, base_delay=base_delay)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < success_after:
                raise ConnectionError(f"Attempt {call_count}")
            return f"Success after {call_count} attempts"
        
        result = test_func()
        
        if success_after <= max_attempts:
            assert result.is_ok()
            assert call_count == success_after
        else:
            assert result.is_err()
            assert call_count == max_attempts
    
    @given(
        error_messages=st.lists(
            st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')), 
                   min_size=3, max_size=50),
            min_size=1, max_size=5
        )
    )
    @settings(max_examples=20)
    def test_transient_error_detection_properties(self, error_messages):
        """Property test: transient error detection should be consistent."""
        for msg in error_messages:
            exception = Exception(msg)
            
            # Should be transient if contains known keywords
            transient_keywords = ["timeout", "connection", "network", "unavailable"]
            contains_keyword = any(keyword in msg.lower() for keyword in transient_keywords)
            
            if contains_keyword:
                assert is_transient_error(exception)
    
    @given(
        items=st.lists(st.integers(), min_size=0, max_size=100),
        batch_size=st.integers(min_value=1, max_value=50)
    )
    @settings(max_examples=10)
    def test_batch_processing_properties(self, items, batch_size):
        """Property test: batch retry should process all items correctly."""
        from autoframe.utils.retry import batch_with_retry
        from logerr import Ok
        
        processed_items = []
        
        def batch_processor(batch):
            processed_items.extend(batch)
            return Ok(len(batch))
        
        result = batch_with_retry(items, batch_processor, batch_size=batch_size)
        
        if items:  # Non-empty list
            assert result.is_ok()
            assert len(processed_items) == len(items)
            assert set(processed_items) == set(items)
        else:  # Empty list
            assert result.is_ok()
            assert len(processed_items) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])