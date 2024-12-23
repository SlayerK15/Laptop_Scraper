# src/utils/rate_limiter.py

import asyncio
import time
import random
from typing import Dict, Optional
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, 
                 requests_per_second: float = 0.5,  # Default: 1 request per 2 seconds
                 burst_limit: int = 5,              # Maximum burst requests
                 cooldown_time: int = 60):          # Cooldown time in seconds
        self.rate_limit = requests_per_second
        self.burst_limit = burst_limit
        self.cooldown_time = cooldown_time
        self.request_times: Dict[str, list] = {}    # Track request times per domain
        self.locks: Dict[str, asyncio.Lock] = {}    # Locks per domain
        self.cooldown_until: Dict[str, datetime] = {}  # Track cooldown periods

    async def acquire(self, domain: str):
        """Acquire rate limit lock with adaptive delays and burst protection."""
        # Create lock for domain if it doesn't exist
        if domain not in self.locks:
            self.locks[domain] = asyncio.Lock()
            self.request_times[domain] = []

        async with self.locks[domain]:
            await self._handle_cooldown(domain)
            await self._enforce_rate_limit(domain)
            self._update_request_times(domain)
            await self._add_jitter()

    async def _handle_cooldown(self, domain: str):
        """Check and handle cooldown periods."""
        if domain in self.cooldown_until:
            wait_time = (self.cooldown_until[domain] - datetime.now()).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            del self.cooldown_until[domain]

    async def _enforce_rate_limit(self, domain: str):
        """Enforce rate limiting with burst protection."""
        current_time = time.time()
        recent_requests = [t for t in self.request_times[domain] 
                         if current_time - t < (1 / self.rate_limit)]

        if len(recent_requests) >= self.burst_limit:
            # Enter cooldown if burst limit exceeded
            self.cooldown_until[domain] = datetime.now() + timedelta(seconds=self.cooldown_time)
            await asyncio.sleep(self.cooldown_time)
            self.request_times[domain].clear()
        elif recent_requests:
            # Calculate delay based on rate limit
            newest_request = max(recent_requests)
            time_since_request = current_time - newest_request
            if time_since_request < (1 / self.rate_limit):
                delay = (1 / self.rate_limit) - time_since_request
                await asyncio.sleep(delay)

    def _update_request_times(self, domain: str):
        """Update request history."""
        current_time = time.time()
        # Clean old requests
        self.request_times[domain] = [t for t in self.request_times[domain] 
                                    if current_time - t < 60]  # Keep last minute
        self.request_times[domain].append(current_time)

    async def _add_jitter(self):
        """Add random jitter to prevent synchronized requests."""
        jitter = random.uniform(0.1, 0.5)
        await asyncio.sleep(jitter)

    async def reset(self, domain: str):
        """Reset rate limiting for a domain."""
        if domain in self.request_times:
            self.request_times[domain].clear()
        if domain in self.cooldown_until:
            del self.cooldown_until[domain]

class AdaptiveRateLimiter(RateLimiter):
    def __init__(self, 
                 initial_rate: float = 0.5,
                 min_rate: float = 0.1,
                 max_rate: float = 2.0):
        super().__init__(requests_per_second=initial_rate)
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.success_count: Dict[str, int] = {}
        self.failure_count: Dict[str, int] = {}

    async def handle_response(self, domain: str, success: bool):
        """Adjust rate limit based on success/failure of requests."""
        if domain not in self.success_count:
            self.success_count[domain] = 0
            self.failure_count[domain] = 0

        if success:
            self.success_count[domain] += 1
            if self.success_count[domain] >= 10:
                self._increase_rate(domain)
                self.success_count[domain] = 0
        else:
            self.failure_count[domain] += 1
            if self.failure_count[domain] >= 3:
                self._decrease_rate(domain)
                self.failure_count[domain] = 0

    def _increase_rate(self, domain: str):
        """Increase the rate limit for a domain."""
        current_rate = self.rate_limit
        new_rate = min(current_rate * 1.2, self.max_rate)
        if new_rate != current_rate:
            self.rate_limit = new_rate

    def _decrease_rate(self, domain: str):
        """Decrease the rate limit for a domain."""
        current_rate = self.rate_limit
        new_rate = max(current_rate * 0.5, self.min_rate)
        if new_rate != current_rate:
            self.rate_limit = new_rate
            # Clear request history and enter cooldown
            self.request_times[domain].clear()
            self.cooldown_until[domain] = datetime.now() + timedelta(seconds=self.cooldown_time)

# Usage example:
# rate_limiter = AdaptiveRateLimiter()
# async with rate_limiter.acquire("amazon.in"):
#     # Make request
#     response = await make_request()
#     await rate_limiter.handle_response("amazon.in", response.status == 200)