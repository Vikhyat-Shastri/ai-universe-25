"""
Unit tests for judge panels: CQP, CAP, CoAP.

~10 tests covering scoring, ladder mapping, priority, and budget allocation.
"""

import pytest

from ai_universe25.tools.judges import (
    CAPDecision,
    ChannelAccessPanel,
    ComputeAllocationPanel,
    ComputeBudget,
    ContentQualityPanel,
    LadderAction,
    QualityScore,
    StabilityMetrics,
)


# ---------------------------------------------------------------------------
# QualityScore
# ---------------------------------------------------------------------------

class TestQualityScore:
    def test_overall_computation(self):
        qs = QualityScore(coverage=1.0, correctness=1.0, coherence=1.0, citation_integrity=1.0)
        assert qs.overall == pytest.approx(1.0)

    def test_overall_weighted(self):
        qs = QualityScore(coverage=0.5, correctness=0.5, coherence=0.5, citation_integrity=0.5)
        assert qs.overall == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# CQP
# ---------------------------------------------------------------------------

class TestContentQualityPanel:
    def test_score_section_returns_tuple(self):
        cqp = ContentQualityPanel()
        score, action = cqp.score_section("Test content")
        assert isinstance(score, QualityScore)
        assert isinstance(action, LadderAction)

    def test_score_to_ladder_mapping_high(self):
        cqp = ContentQualityPanel()
        assert cqp._score_to_ladder_action(0.9) == LadderAction.RUN

    def test_score_to_ladder_mapping_warn(self):
        cqp = ContentQualityPanel()
        assert cqp._score_to_ladder_action(0.8) == LadderAction.WARN

    def test_score_to_ladder_mapping_stop(self):
        cqp = ContentQualityPanel()
        assert cqp._score_to_ladder_action(0.6) == LadderAction.STOP

    def test_score_to_ladder_mapping_quarantine(self):
        cqp = ContentQualityPanel()
        assert cqp._score_to_ladder_action(0.4) == LadderAction.QUARANTINE

    def test_score_to_ladder_mapping_shutdown(self):
        cqp = ContentQualityPanel()
        assert cqp._score_to_ladder_action(0.2) == LadderAction.SHUTDOWN


# ---------------------------------------------------------------------------
# CAP
# ---------------------------------------------------------------------------

class TestChannelAccessPanel:
    def test_decide_default(self):
        cap = ChannelAccessPanel()
        decision = cap.decide("agent_1")
        assert isinstance(decision, CAPDecision)
        assert decision.priority >= 0

    def test_decide_high_quality_agent(self):
        cap = ChannelAccessPanel()
        for _ in range(10):
            cap.update_quality("good_agent", 0.95)
        decision = cap.decide("good_agent")
        assert decision.priority > 50
        assert decision.rate >= 1.0


# ---------------------------------------------------------------------------
# CoAP
# ---------------------------------------------------------------------------

class TestComputeAllocationPanel:
    def test_ema_smoothing(self):
        coap = ComputeAllocationPanel(alpha=0.5)
        coap.update_reliability("a", quality_score=1.0, reversals=0, cite_errors=0.0)
        ema1 = coap.ema_scores["a"]
        coap.update_reliability("a", quality_score=0.0, reversals=0, cite_errors=0.0)
        ema2 = coap.ema_scores["a"]
        # EMA should be smoothed: 0.5 * 0.0 + 0.5 * 1.0 = 0.5
        assert ema2 == pytest.approx(0.5)

    def test_monotone_allocator_hysteresis(self):
        """Budget changes should be capped by delta_max."""
        coap = ComputeAllocationPanel(delta_max=5.0, bbase=40.0)
        b1 = coap.update_reliability("a", quality_score=0.5, reversals=0, cite_errors=0.0)
        tps1 = b1.tokens_per_sec
        b2 = coap.update_reliability("a", quality_score=1.0, reversals=0, cite_errors=0.0)
        tps2 = b2.tokens_per_sec
        assert abs(tps2 - tps1) <= 5.0 + 0.01

    def test_budget_floor_enforcement(self):
        coap = ComputeAllocationPanel(bmin=10.0)
        budget = coap.update_reliability("a", quality_score=0.0, reversals=10, cite_errors=1.0)
        assert budget.tokens_per_sec >= 10.0

    def test_budget_lanes_based_on_reliability(self):
        coap = ComputeAllocationPanel()
        budget = coap.update_reliability("a", quality_score=1.0, reversals=0, cite_errors=0.0)
        assert budget.lanes >= 1
