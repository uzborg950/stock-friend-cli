"""
Token bucket rate limiter for API rate limiting.

Prevents exceeding API rate limits by using the token bucket algorithm.
"""

import logging
import threading
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class TokenBucket:
    """
    Token bucket implementation for rate limiting.

    Tokens refill at constant rate until bucket is full.
    Each request consumes one token.
    """

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.

        Args:
            capacity: Maximum tokens in bucket
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill_time = time.time()
        self.lock = threading.Lock()

    def consume(self) -> bool:
        """
        Attempt to consume one token.

        Returns:
            True if token consumed, False if no tokens available
        """
        with self.lock:
            self._refill()

            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return True

            return False

    def _refill(self) -> None:
        """Refill bucket based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill_time

        # Add tokens based on refill rate
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)

        self.last_refill_time = now

    def time_until_next_token(self) -> float:
        """Calculate seconds until next token available."""
        if self.tokens >= 1.0:
            return 0.0

        tokens_needed = 1.0 - self.tokens
        time_needed = tokens_needed / self.refill_rate

        return time_needed


class RateLimiter:
    """
    Token bucket rate limiter for API rate limiting.

    Features:
    - Per-API rate limits
    - Thread-safe
    - Automatic token refill
    - Blocking and non-blocking acquisition

    Example:
        rate_limiter = RateLimiter()
        rate_limiter.configure("yahoo_finance", requests_per_hour=2000)

        rate_limiter.acquire("yahoo_finance")  # Blocks until token available
        # ... make API call
    """

    def __init__(self) -> None:
        self.buckets: Dict[str, TokenBucket] = {}
        self.lock = threading.Lock()

    def configure(self, api_name: str, requests_per_hour: int) -> None:
        """
        Configure rate limit for an API.

        Args:
            api_name: API identifier (e.g., "yahoo_finance")
            requests_per_hour: Maximum requests per hour
        """
        with self.lock:
            self.buckets[api_name] = TokenBucket(
                capacity=requests_per_hour,
                refill_rate=requests_per_hour / 3600.0,  # Tokens per second
            )

        logger.info(
            f"Configured rate limit for {api_name}: {requests_per_hour} requests/hour"
        )

    def acquire(self, api_name: str, timeout: Optional[float] = None) -> None:
        """
        Acquire a token for API call (blocks if necessary).

        Args:
            api_name: API identifier
            timeout: Maximum wait time in seconds (None = wait indefinitely)

        Raises:
            RateLimitException: If timeout exceeded
            ValueError: If API not configured
        """
        if api_name not in self.buckets:
            raise ValueError(f"API not configured: {api_name}")

        bucket = self.buckets[api_name]
        start_time = time.time()

        while True:
            if bucket.consume():
                # Token acquired
                return

            # No tokens available, wait
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    raise RateLimitException(
                        f"Rate limit timeout for {api_name} after {elapsed:.1f}s"
                    )

            # Wait for next refill
            wait_time = min(1.0, bucket.time_until_next_token())
            logger.debug(
                f"Rate limit reached for {api_name}, waiting {wait_time:.2f}s"
            )
            time.sleep(wait_time)

    def try_acquire(self, api_name: str) -> bool:
        """
        Try to acquire token without blocking.

        Args:
            api_name: API identifier

        Returns:
            True if token acquired, False if rate limit reached

        Raises:
            ValueError: If API not configured
        """
        if api_name not in self.buckets:
            raise ValueError(f"API not configured: {api_name}")

        bucket = self.buckets[api_name]
        return bucket.consume()

    def get_available_tokens(self, api_name: str) -> int:
        """
        Get number of available tokens.

        Args:
            api_name: API identifier

        Returns:
            Number of available tokens

        Raises:
            ValueError: If API not configured
        """
        if api_name not in self.buckets:
            return 0

        bucket = self.buckets[api_name]
        bucket._refill()  # Ensure up-to-date count
        return int(bucket.tokens)


class RateLimitException(Exception):
    """Raised when rate limit timeout is exceeded."""

    pass
