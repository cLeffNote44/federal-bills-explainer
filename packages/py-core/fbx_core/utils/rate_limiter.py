"""Rate limiting utilities for API calls with circuit breaker pattern."""

import time
import logging
from typing import Optional, Dict, Any, Callable, TypeVar
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    # Rate limiting
    requests_per_second: float = 10.0
    burst_size: int = 20
    
    # Retry logic
    max_retries: int = 3
    initial_backoff: float = 1.0
    max_backoff: float = 60.0
    backoff_multiplier: float = 2.0
    
    # Circuit breaker
    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # seconds
    half_open_max_calls: int = 3
    
    # Monitoring
    log_rate_limits: bool = True
    log_circuit_state: bool = True


@dataclass
class RateLimitStats:
    """Statistics for rate limiting."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limited_requests: int = 0
    circuit_breaker_rejections: int = 0
    total_retry_attempts: int = 0
    last_request_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests


class TokenBucket:
    """Token bucket implementation for rate limiting."""
    
    def __init__(self, rate: float, capacity: int):
        """
        Initialize token bucket.
        
        Args:
            rate: Tokens added per second
            capacity: Maximum tokens in bucket
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.monotonic()
        self.lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> tuple[bool, float]:
        """
        Try to consume tokens from bucket.
        
        Returns:
            Tuple of (success, wait_time_if_failed)
        """
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            
            # Add new tokens based on elapsed time
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True, 0.0
            else:
                # Calculate wait time needed
                needed = tokens - self.tokens
                wait_time = needed / self.rate
                return False, wait_time


class CircuitBreaker:
    """Circuit breaker implementation."""
    
    def __init__(self, config: RateLimitConfig):
        """Initialize circuit breaker."""
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
        self.lock = threading.Lock()
        
    def call_allowed(self) -> bool:
        """Check if call is allowed based on circuit state."""
        with self.lock:
            if self.state == CircuitState.CLOSED:
                return True
            
            elif self.state == CircuitState.OPEN:
                # Check if we should transition to half-open
                if self.last_failure_time:
                    elapsed = datetime.now() - self.last_failure_time
                    if elapsed.total_seconds() >= self.config.recovery_timeout:
                        self._transition_to(CircuitState.HALF_OPEN)
                        return True
                return False
            
            elif self.state == CircuitState.HALF_OPEN:
                # Allow limited calls in half-open state
                if self.half_open_calls < self.config.half_open_max_calls:
                    self.half_open_calls += 1
                    return True
                return False
            
            return False
    
    def record_success(self):
        """Record successful call."""
        with self.lock:
            if self.state == CircuitState.HALF_OPEN:
                # Transition back to closed after successful call
                self._transition_to(CircuitState.CLOSED)
            self.failure_count = 0
    
    def record_failure(self):
        """Record failed call."""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.state == CircuitState.HALF_OPEN:
                # Immediately open circuit on failure in half-open state
                self._transition_to(CircuitState.OPEN)
            elif self.failure_count >= self.config.failure_threshold:
                # Open circuit after threshold exceeded
                self._transition_to(CircuitState.OPEN)
    
    def _transition_to(self, new_state: CircuitState):
        """Transition to new state."""
        old_state = self.state
        self.state = new_state
        
        if new_state == CircuitState.HALF_OPEN:
            self.half_open_calls = 0
        elif new_state == CircuitState.CLOSED:
            self.failure_count = 0
            self.half_open_calls = 0
        
        if self.config.log_circuit_state:
            logger.info(f"Circuit breaker transitioned from {old_state.value} to {new_state.value}")


class RateLimiter:
    """Rate limiter with circuit breaker and retry logic."""
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        """Initialize rate limiter."""
        self.config = config or RateLimitConfig()
        self.token_bucket = TokenBucket(
            self.config.requests_per_second,
            self.config.burst_size
        )
        self.circuit_breaker = CircuitBreaker(self.config)
        self.stats = RateLimitStats()
        self.lock = threading.Lock()
    
    def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with rate limiting and retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries failed or circuit is open
        """
        # Check circuit breaker
        if not self.circuit_breaker.call_allowed():
            with self.lock:
                self.stats.circuit_breaker_rejections += 1
            raise Exception(f"Circuit breaker is open - service unavailable")
        
        last_exception = None
        retry_count = 0
        backoff = self.config.initial_backoff
        
        while retry_count <= self.config.max_retries:
            # Rate limiting
            allowed, wait_time = self.token_bucket.consume()
            if not allowed:
                with self.lock:
                    self.stats.rate_limited_requests += 1
                if self.config.log_rate_limits:
                    logger.info(f"Rate limit reached, waiting {wait_time:.2f}s")
                time.sleep(wait_time)
                # Try again after waiting
                allowed, _ = self.token_bucket.consume()
                if not allowed:
                    # Still not allowed, treat as failure
                    continue
            
            # Execute function
            try:
                with self.lock:
                    self.stats.total_requests += 1
                    self.stats.last_request_time = datetime.now()
                
                result = func(*args, **kwargs)
                
                with self.lock:
                    self.stats.successful_requests += 1
                
                self.circuit_breaker.record_success()
                return result
                
            except Exception as e:
                last_exception = e
                retry_count += 1
                
                with self.lock:
                    self.stats.failed_requests += 1
                    self.stats.total_retry_attempts += 1
                    self.stats.last_failure_time = datetime.now()
                
                self.circuit_breaker.record_failure()
                
                if retry_count <= self.config.max_retries:
                    # Calculate backoff time
                    wait_time = min(backoff, self.config.max_backoff)
                    logger.warning(f"Request failed (attempt {retry_count}/{self.config.max_retries}): {e}. "
                                 f"Retrying in {wait_time:.2f}s...")
                    time.sleep(wait_time)
                    backoff *= self.config.backoff_multiplier
        
        # All retries exhausted
        raise last_exception or Exception("All retry attempts failed")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        with self.lock:
            return {
                "total_requests": self.stats.total_requests,
                "successful_requests": self.stats.successful_requests,
                "failed_requests": self.stats.failed_requests,
                "success_rate": f"{self.stats.success_rate():.2%}",
                "rate_limited_requests": self.stats.rate_limited_requests,
                "circuit_breaker_rejections": self.stats.circuit_breaker_rejections,
                "total_retry_attempts": self.stats.total_retry_attempts,
                "circuit_state": self.circuit_breaker.state.value,
                "last_request_time": self.stats.last_request_time.isoformat() if self.stats.last_request_time else None,
                "last_failure_time": self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
            }
    
    def reset_stats(self):
        """Reset statistics."""
        with self.lock:
            self.stats = RateLimitStats()


def rate_limited(config: Optional[RateLimitConfig] = None):
    """
    Decorator for rate limiting functions.
    
    Usage:
        @rate_limited(RateLimitConfig(requests_per_second=5))
        def my_api_call():
            ...
    """
    rate_limiter = RateLimiter(config)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return rate_limiter.execute(func, *args, **kwargs)
        wrapper.rate_limiter = rate_limiter  # Expose for stats access
        return wrapper
    return decorator