"""Tests for rate limiting utilities."""

import time
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from fbx_core.utils.rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    TokenBucket,
    CircuitBreaker,
    CircuitState,
    rate_limited
)


class TestTokenBucket:
    """Test token bucket implementation."""
    
    def test_initial_tokens(self):
        """Test bucket starts with full capacity."""
        bucket = TokenBucket(rate=1.0, capacity=10)
        assert bucket.tokens == 10
    
    def test_consume_tokens(self):
        """Test consuming tokens from bucket."""
        bucket = TokenBucket(rate=1.0, capacity=10)
        
        # Should succeed when tokens available
        success, wait_time = bucket.consume(5)
        assert success is True
        assert wait_time == 0.0
        assert bucket.tokens == 5
        
        # Should fail when not enough tokens
        success, wait_time = bucket.consume(6)
        assert success is False
        assert wait_time > 0
    
    def test_token_refill(self):
        """Test tokens refill over time."""
        bucket = TokenBucket(rate=10.0, capacity=10)
        
        # Consume all tokens
        bucket.consume(10)
        assert bucket.tokens == 0
        
        # Wait for refill
        time.sleep(0.5)  # Should refill 5 tokens
        success, _ = bucket.consume(4)
        assert success is True


class TestCircuitBreaker:
    """Test circuit breaker implementation."""
    
    def test_initial_state_closed(self):
        """Test circuit starts in closed state."""
        config = RateLimitConfig(failure_threshold=3)
        breaker = CircuitBreaker(config)
        assert breaker.state == CircuitState.CLOSED
        assert breaker.call_allowed() is True
    
    def test_open_after_threshold(self):
        """Test circuit opens after failure threshold."""
        config = RateLimitConfig(failure_threshold=3)
        breaker = CircuitBreaker(config)
        
        # Record failures
        for _ in range(3):
            breaker.record_failure()
        
        assert breaker.state == CircuitState.OPEN
        assert breaker.call_allowed() is False
    
    def test_half_open_transition(self):
        """Test transition to half-open state."""
        config = RateLimitConfig(
            failure_threshold=2,
            recovery_timeout=0.1  # 100ms for fast test
        )
        breaker = CircuitBreaker(config)
        
        # Open the circuit
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        time.sleep(0.15)
        
        # Should transition to half-open
        assert breaker.call_allowed() is True
        assert breaker.state == CircuitState.HALF_OPEN
    
    def test_close_after_success(self):
        """Test circuit closes after successful call in half-open state."""
        config = RateLimitConfig(failure_threshold=2, half_open_max_calls=3)
        breaker = CircuitBreaker(config)
        
        # Force to half-open state
        breaker.state = CircuitState.HALF_OPEN
        
        # Record success
        breaker.record_success()
        assert breaker.state == CircuitState.CLOSED


class TestRateLimiter:
    """Test rate limiter with circuit breaker."""
    
    def test_successful_execution(self):
        """Test successful function execution."""
        config = RateLimitConfig(requests_per_second=10.0)
        limiter = RateLimiter(config)
        
        mock_func = Mock(return_value="success")
        result = limiter.execute(mock_func, "arg1", key="value")
        
        assert result == "success"
        mock_func.assert_called_once_with("arg1", key="value")
        assert limiter.stats.successful_requests == 1
    
    def test_retry_on_failure(self):
        """Test retry logic on failure."""
        config = RateLimitConfig(
            max_retries=2,
            initial_backoff=0.01,  # Fast for testing
            backoff_multiplier=2.0
        )
        limiter = RateLimiter(config)
        
        # Mock function that fails twice then succeeds
        mock_func = Mock(side_effect=[Exception("fail"), Exception("fail"), "success"])
        
        result = limiter.execute(mock_func)
        assert result == "success"
        assert mock_func.call_count == 3
        assert limiter.stats.failed_requests == 2
        assert limiter.stats.successful_requests == 1
    
    def test_circuit_breaker_rejection(self):
        """Test circuit breaker rejects calls when open."""
        config = RateLimitConfig(failure_threshold=1)
        limiter = RateLimiter(config)
        
        # Open the circuit
        limiter.circuit_breaker.state = CircuitState.OPEN
        
        mock_func = Mock()
        with pytest.raises(Exception) as exc_info:
            limiter.execute(mock_func)
        
        assert "Circuit breaker is open" in str(exc_info.value)
        mock_func.assert_not_called()
        assert limiter.stats.circuit_breaker_rejections == 1
    
    def test_rate_limiting(self):
        """Test rate limiting delays requests."""
        config = RateLimitConfig(
            requests_per_second=2.0,
            burst_size=2,
            log_rate_limits=False
        )
        limiter = RateLimiter(config)
        
        mock_func = Mock(return_value="result")
        
        # First two should be immediate (burst)
        start = time.time()
        limiter.execute(mock_func)
        limiter.execute(mock_func)
        elapsed = time.time() - start
        assert elapsed < 0.1  # Should be fast
        
        # Third should be rate limited
        start = time.time()
        limiter.execute(mock_func)
        elapsed = time.time() - start
        assert elapsed >= 0.4  # Should wait ~0.5s for token
    
    def test_get_stats(self):
        """Test statistics collection."""
        config = RateLimitConfig()
        limiter = RateLimiter(config)
        
        # Execute some operations
        mock_func = Mock(return_value="ok")
        limiter.execute(mock_func)
        
        mock_fail = Mock(side_effect=Exception("error"))
        try:
            limiter.execute(mock_fail)
        except:
            pass
        
        stats = limiter.get_stats()
        assert stats["total_requests"] == 2
        assert stats["successful_requests"] == 1
        assert stats["failed_requests"] == 1
        assert stats["circuit_state"] == "closed"
        assert "success_rate" in stats


class TestRateLimitedDecorator:
    """Test rate limited decorator."""
    
    def test_decorator_basic(self):
        """Test basic decorator functionality."""
        
        @rate_limited(RateLimitConfig(requests_per_second=10.0))
        def my_function(x, y):
            return x + y
        
        result = my_function(2, 3)
        assert result == 5
        
        # Check stats are accessible
        stats = my_function.rate_limiter.get_stats()
        assert stats["successful_requests"] == 1
    
    def test_decorator_with_retry(self):
        """Test decorator with retry logic."""
        call_count = 0
        
        @rate_limited(RateLimitConfig(max_retries=2, initial_backoff=0.01))
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Flaky error")
            return "success"
        
        result = flaky_function()
        assert result == "success"
        assert call_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])