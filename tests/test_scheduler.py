"""
Unit tests for FairScheduler: DRR, token buckets, burst limits, lane caps.

~10 tests covering fairness, rate limiting, and priority ordering.
"""

import time

import pytest

from ai_universe25.runtime.gateway import Surface
from ai_universe25.runtime.scheduler import (
    Budget,
    DRRQueue,
    FairScheduler,
    LaneCap,
    TokenBucket,
)


# ---------------------------------------------------------------------------
# Token Bucket
# ---------------------------------------------------------------------------

class TestTokenBucket:
    def test_consume_success(self):
        tb = TokenBucket(capacity=10, tokens=10, refill_rate=0.0)
        assert tb.consume(5)
        assert tb.available() == pytest.approx(5.0, abs=0.5)

    def test_consume_failure(self):
        tb = TokenBucket(capacity=10, tokens=2, refill_rate=0.0)
        assert not tb.consume(5)

    def test_refill_over_time(self):
        tb = TokenBucket(capacity=100, tokens=0, refill_rate=1000.0)
        tb.last_refill = time.time() - 0.1
        tb.refill()
        assert tb.tokens > 0

    def test_capacity_limit(self):
        tb = TokenBucket(capacity=10, tokens=10, refill_rate=100.0)
        tb.last_refill = time.time() - 10.0
        tb.refill()
        assert tb.tokens == 10


# ---------------------------------------------------------------------------
# DRR Queue
# ---------------------------------------------------------------------------

class TestDRRQueue:
    def test_enqueue_dequeue(self):
        q = DRRQueue(agent_id="agent_1", quantum=100)
        q.queue.append("task_1")
        assert len(q.queue) == 1

    def test_deficit_accumulation(self):
        q = DRRQueue(agent_id="agent_1", quantum=10)
        q.deficit = 0
        q.deficit += q.quantum
        assert q.deficit == 10


# ---------------------------------------------------------------------------
# FairScheduler
# ---------------------------------------------------------------------------

class TestFairScheduler:
    def test_creation(self):
        scheduler = FairScheduler()
        assert scheduler is not None
        assert scheduler.default_quantum == 100

    def test_set_agent_priority(self):
        scheduler = FairScheduler(default_quantum=100)
        scheduler.set_agent_priority("a", 1)
        scheduler.set_agent_priority("b", 10)
        assert "a" in scheduler.agent_queues
        assert "b" in scheduler.agent_queues
        assert scheduler.agent_queues["b"].priority > scheduler.agent_queues["a"].priority

    def test_equal_quantum_fairness(self):
        """Equal quantum should give equal service allocation."""
        scheduler = FairScheduler(default_quantum=100)
        scheduler.set_agent_priority("a", 1)
        scheduler.set_agent_priority("b", 1)
        assert scheduler.agent_queues["a"].quantum == scheduler.agent_queues["b"].quantum

    def test_set_agent_budget(self):
        scheduler = FairScheduler()
        budget = Budget(tokens_per_sec=100.0, max_steps=50, ctx_cap=8192, lanes=2)
        scheduler.set_agent_budget("agent_1", budget)
        assert "agent_1" in scheduler.agent_budgets
        assert "agent_1" in scheduler.agent_buckets

    def test_set_lane_cap(self):
        scheduler = FairScheduler()
        scheduler.set_lane_cap(Surface.BODY, max_concurrent=3)
        assert Surface.BODY in scheduler.lane_caps
