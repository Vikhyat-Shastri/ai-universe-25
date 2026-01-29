"""
Fairness scheduler: DRR + burst limits + token buckets + lane caps.

Implements deficit round-robin scheduling with per-agent/per-tool token buckets,
burst limits, and lane caps per surface. Integrates with CAP/CoAP enforcement.
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, Optional, Set

from ai_universe25.runtime.gateway import Envelope, Surface

logger = logging.getLogger(__name__)


@dataclass
class TokenBucket:
    """Token bucket for rate limiting."""

    capacity: int  # Maximum tokens
    tokens: float = 0.0  # Current tokens
    refill_rate: float = 1.0  # Tokens per second
    last_refill: float = field(default_factory=time.time)

    def refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def consume(self, tokens: int) -> bool:
        """
        Try to consume tokens.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if insufficient
        """
        self.refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def available(self) -> float:
        """Get available tokens."""
        self.refill()
        return self.tokens


@dataclass
class DRRQueue:
    """Deficit Round-Robin queue for an agent."""

    agent_id: str
    quantum: int = 100  # Quantum size
    deficit: int = 0  # Current deficit
    queue: deque = field(default_factory=deque)
    priority: int = 0  # Priority (higher = more important)
    max_burst: int = 10  # Maximum burst size

    def add_request(self, envelope: Envelope, cost: int = 1):
        """Add request to queue."""
        self.queue.append((envelope, cost))

    def get_next(self) -> Optional[tuple[Envelope, int]]:
        """
        Get next request using DRR.

        Returns:
            (envelope, cost) or None if queue empty
        """
        if not self.queue:
            return None

        # Add quantum to deficit
        self.deficit += self.quantum

        # Process requests while deficit allows
        while self.queue and self.deficit > 0:
            envelope, cost = self.queue[0]
            if cost <= self.deficit:
                self.deficit -= cost
                self.queue.popleft()
                return (envelope, cost)
            else:
                # Can't process this request yet
                break

        return None


@dataclass
class LaneCap:
    """Lane capacity limits per surface."""

    surface: Surface
    max_concurrent: int = 2  # Maximum concurrent operations
    current: int = 0  # Current operations

    def acquire(self) -> bool:
        """Try to acquire a lane slot."""
        if self.current < self.max_concurrent:
            self.current += 1
            return True
        return False

    def release(self):
        """Release a lane slot."""
        if self.current > 0:
            self.current -= 1


@dataclass
class Budget:
    """Compute budget from CoAP."""

    tokens_per_sec: float = 40.0
    max_steps: int = 64
    ctx_cap: int = 16000
    lanes: int = 2


class FairScheduler:
    """
    Fair scheduler with DRR, token buckets, burst limits, and lane caps.

    Implements:
    - Deficit Round-Robin (DRR) for fairness
    - Per-agent and per-tool token buckets
    - Burst limits per agent
    - Lane caps per surface
    - CAP/CoAP budget enforcement
    """

    def __init__(
        self,
        default_quantum: int = 100,
        default_burst: int = 10,
        enable_lane_caps: bool = True,
    ):
        """
        Initialize scheduler.

        Args:
            default_quantum: Default DRR quantum size
            default_burst: Default burst limit
            enable_lane_caps: Enable lane capacity limits
        """
        self.default_quantum = default_quantum
        self.default_burst = default_burst
        self.enable_lane_caps = enable_lane_caps

        # Agent queues (DRR)
        self.agent_queues: Dict[str, DRRQueue] = {}

        # Token buckets: per-agent and per-tool
        self.agent_buckets: Dict[str, TokenBucket] = {}
        self.tool_buckets: Dict[str, TokenBucket] = {}

        # Lane caps per surface
        self.lane_caps: Dict[Surface, LaneCap] = {}

        # Agent budgets (from CoAP)
        self.agent_budgets: Dict[str, Budget] = {}

        # Burst tracking
        self.burst_counts: Dict[str, int] = defaultdict(int)
        self.burst_window_start: Dict[str, float] = {}
        self.burst_window_size: float = 1.0  # 1 second window

        # Priority queue for scheduling (higher priority first)
        self.priority_agents: list[str] = []

        self._lock = asyncio.Lock()

    def set_agent_budget(self, agent_id: str, budget: Budget):
        """Set compute budget for agent (from CoAP)."""
        self.agent_budgets[agent_id] = budget
        # Update token bucket based on budget
        if agent_id not in self.agent_buckets:
            self.agent_buckets[agent_id] = TokenBucket(
                capacity=int(budget.tokens_per_sec * 2),  # 2 second buffer
                refill_rate=budget.tokens_per_sec,
            )
        else:
            bucket = self.agent_buckets[agent_id]
            bucket.capacity = int(budget.tokens_per_sec * 2)
            bucket.refill_rate = budget.tokens_per_sec

    def set_agent_priority(self, agent_id: str, priority: int):
        """
        Set agent priority (from CAP).

        Args:
            agent_id: Agent identifier
            priority: Priority level (higher = more important)
        """
        if agent_id not in self.agent_queues:
            self.agent_queues[agent_id] = DRRQueue(
                agent_id=agent_id,
                quantum=self.default_quantum,
                max_burst=self.default_burst,
            )
        self.agent_queues[agent_id].priority = priority

        # Rebuild priority list
        self.priority_agents = sorted(
            self.agent_queues.keys(),
            key=lambda a: self.agent_queues[a].priority,
            reverse=True,
        )

    def set_tool_rate_limit(self, tool_name: str, rate: float, capacity: int):
        """Set rate limit for a tool."""
        self.tool_buckets[tool_name] = TokenBucket(
            capacity=capacity,
            refill_rate=rate,
        )

    def set_lane_cap(self, surface: Surface, max_concurrent: int):
        """Set lane capacity for a surface."""
        if surface not in self.lane_caps:
            self.lane_caps[surface] = LaneCap(surface=surface)
        self.lane_caps[surface].max_concurrent = max_concurrent

    async def enqueue(
        self,
        envelope: Envelope,
        cost: int = 1,
    ) -> bool:
        """
        Enqueue a request for scheduling.

        Args:
            envelope: Request envelope
            cost: Request cost (in tokens/credits)

        Returns:
            True if enqueued, False if rejected (burst limit)
        """
        async with self._lock:
            agent_id = envelope.agent_id

            # Check burst limit
            if not self._check_burst_limit(agent_id):
                logger.warning(f"Burst limit exceeded for agent {agent_id}")
                return False

            # Initialize queue if needed
            if agent_id not in self.agent_queues:
                self.agent_queues[agent_id] = DRRQueue(
                    agent_id=agent_id,
                    quantum=self.default_quantum,
                    max_burst=self.default_burst,
                )
                self.priority_agents.append(agent_id)
                self.priority_agents.sort(
                    key=lambda a: self.agent_queues[a].priority,
                    reverse=True,
                )

            # Add to queue
            self.agent_queues[agent_id].add_request(envelope, cost)
            self.burst_counts[agent_id] += 1

            return True

    def _check_burst_limit(self, agent_id: str) -> bool:
        """Check if agent is within burst limit."""
        now = time.time()
        window_start = self.burst_window_start.get(agent_id, now)

        # Reset window if expired
        if now - window_start >= self.burst_window_size:
            self.burst_counts[agent_id] = 0
            self.burst_window_start[agent_id] = now

        queue = self.agent_queues.get(agent_id)
        if queue:
            return self.burst_counts[agent_id] < queue.max_burst
        return self.burst_counts[agent_id] < self.default_burst

    async def schedule_next(
        self,
        tool_name: Optional[str] = None,
    ) -> Optional[tuple[Envelope, int]]:
        """
        Schedule next request using DRR.

        Args:
            tool_name: Optional tool name filter

        Returns:
            (envelope, cost) or None if no request available
        """
        async with self._lock:
            # Process agents in priority order
            for agent_id in self.priority_agents:
                queue = self.agent_queues[agent_id]

                # Check agent token bucket
                if agent_id in self.agent_buckets:
                    bucket = self.agent_buckets[agent_id]
                    if bucket.available() < 1:
                        continue  # Skip if no tokens

                # Get next request from queue
                result = queue.get_next()
                if result is None:
                    continue

                envelope, cost = result

                # Check tool-specific rate limit
                if tool_name and tool_name in self.tool_buckets:
                    tool_bucket = self.tool_buckets[tool_name]
                    if not tool_bucket.consume(cost):
                        # Put back in queue
                        queue.queue.appendleft((envelope, cost))
                        queue.deficit += cost
                        continue

                # Check lane cap
                if self.enable_lane_caps and envelope.surface:
                    lane_cap = self.lane_caps.get(envelope.surface)
                    if lane_cap and not lane_cap.acquire():
                        # Put back in queue
                        queue.queue.appendleft((envelope, cost))
                        queue.deficit += cost
                        continue

                # Consume agent tokens
                if agent_id in self.agent_buckets:
                    self.agent_buckets[agent_id].consume(cost)

                return (envelope, cost)

            return None

    async def release_lane(self, surface: Surface):
        """Release a lane slot for a surface."""
        async with self._lock:
            if surface in self.lane_caps:
                self.lane_caps[surface].release()

    def get_queue_stats(self) -> Dict[str, Dict[str, any]]:
        """Get statistics for all queues."""
        stats = {}
        for agent_id, queue in self.agent_queues.items():
            stats[agent_id] = {
                "queue_size": len(queue.queue),
                "deficit": queue.deficit,
                "priority": queue.priority,
                "burst_count": self.burst_counts.get(agent_id, 0),
                "tokens_available": (
                    self.agent_buckets[agent_id].available()
                    if agent_id in self.agent_buckets
                    else 0
                ),
            }
        return stats
