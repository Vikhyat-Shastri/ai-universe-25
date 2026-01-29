"""
Judge panels: CQP, CAP, and CoAP.

Implements:
- CQP: Content Quality Panel (pairwise, majority, tie-break)
- CAP: Channel-Access Panel (priority/slots/rate)
- CoAP: Compute Allocation Panel (EWMA+monotone allocator+hysteresis+slow-start)
"""

import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class LadderAction(Enum):
    """Ladder actions from judges."""

    RUN = "RUN"
    WARN = "WARN"
    STOP = "STOP"
    QUARANTINE = "QUARANTINE"
    SHUTDOWN = "SHUTDOWN"


@dataclass
class QualityScore:
    """Content quality score."""

    coverage: float  # 0-1
    correctness: float  # 0-1
    coherence: float  # 0-1
    citation_integrity: float  # 0-1
    overall: float = field(init=False)  # Weighted average

    def __post_init__(self):
        """Compute overall score."""
        self.overall = (
            self.coverage * 0.25
            + self.correctness * 0.35
            + self.coherence * 0.20
            + self.citation_integrity * 0.20
        )


@dataclass
class JudgeBackend:
    """Pluggable judge backend (API or local)."""

    name: str
    model: str

    def score(self, content: str, rubric: Dict[str, Any]) -> QualityScore:
        """Score content (placeholder - would call actual LLM)."""
        # Placeholder: random scores for demo
        return QualityScore(
            coverage=random.uniform(0.6, 1.0),
            correctness=random.uniform(0.7, 1.0),
            coherence=random.uniform(0.6, 1.0),
            citation_integrity=random.uniform(0.5, 1.0),
        )


class ContentQualityPanel:
    """
    Content Quality Panel (CQP).

    Uses three LLM judges (GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro) in
    pairwise comparison protocol. Votes by majority; ties broken by GPT-4o.
    """

    def __init__(
        self,
        judges: Optional[List[JudgeBackend]] = None,
        tie_breaker: Optional[str] = None,
    ):
        """
        Initialize CQP.

        Args:
            judges: List of judge backends (default: create 3)
            tie_breaker: Name of tie-breaker judge (default: first judge)
        """
        if judges is None:
            judges = [
                JudgeBackend(name="gpt4o", model="gpt-4o"),
                JudgeBackend(name="claude35", model="claude-3-5-sonnet"),
                JudgeBackend(name="gemini15", model="gemini-1.5-pro"),
            ]
        self.judges = judges
        self.tie_breaker = tie_breaker or (judges[0].name if judges else None)

    def score_section(
        self,
        content: str,
        rubric: Optional[Dict[str, Any]] = None,
    ) -> Tuple[QualityScore, LadderAction]:
        """
        Score a section and determine ladder action.

        Args:
            content: Section content to score
            rubric: Scoring rubric (default: standard)

        Returns:
            (quality_score, ladder_action)
        """
        if rubric is None:
            rubric = {
                "coverage": "How well does the section cover the topic?",
                "correctness": "Are the facts accurate?",
                "coherence": "Is the narrative coherent?",
                "citation_integrity": "Are claims properly cited?",
            }

        # Pairwise comparisons
        scores = []
        for judge in self.judges:
            score = judge.score(content, rubric)
            scores.append(score)

        # Majority vote on overall score
        overall_scores = [s.overall for s in scores]
        median_score = sorted(overall_scores)[len(overall_scores) // 2]

        # Average scores (with debiasing)
        avg_score = QualityScore(
            coverage=sum(s.coverage for s in scores) / len(scores),
            correctness=sum(s.correctness for s in scores) / len(scores),
            coherence=sum(s.coherence for s in scores) / len(scores),
            citation_integrity=sum(s.citation_integrity for s in scores) / len(scores),
        )

        # Determine ladder action based on score
        ladder_action = self._score_to_ladder_action(avg_score.overall)

        logger.info(
            f"CQP scored section: overall={avg_score.overall:.2f}, "
            f"ladder_action={ladder_action.value}"
        )

        return avg_score, ladder_action

    def _score_to_ladder_action(self, score: float) -> LadderAction:
        """Convert quality score to ladder action."""
        if score < 0.3:
            return LadderAction.SHUTDOWN
        elif score < 0.5:
            return LadderAction.QUARANTINE
        elif score < 0.7:
            return LadderAction.STOP
        elif score < 0.85:
            return LadderAction.WARN
        else:
            return LadderAction.RUN


@dataclass
class StabilityMetrics:
    """Stability metrics for CAP."""

    edit_reversals: int  # Number of reversals
    citation_error_rate: float  # 0-1
    quality_trend: float  # Trend in quality scores (-1 to 1)


@dataclass
class CAPDecision:
    """CAP decision (priority/slots/rate)."""

    agent_id: str
    priority: int  # Queue priority (higher = more important)
    slots: int  # Parallel tool slots
    rate: float  # Rate limit multiplier (1.0 = baseline)


class ChannelAccessPanel:
    """
    MCP Channel-Access Panel (CAP).

    Converts recent quality signals into gateway priority: queue position,
    parallel tool slots, and per-tool quotas.
    """

    def __init__(self):
        """Initialize CAP."""
        self.quality_history: Dict[str, List[float]] = {}  # agent_id -> scores
        self.stability_history: Dict[str, List[StabilityMetrics]] = {}  # agent_id -> metrics

    def update_quality(
        self,
        agent_id: str,
        quality_score: float,
    ):
        """Update quality history for an agent."""
        if agent_id not in self.quality_history:
            self.quality_history[agent_id] = []
        self.quality_history[agent_id].append(quality_score)
        # Keep rolling window
        if len(self.quality_history[agent_id]) > 100:
            self.quality_history[agent_id] = self.quality_history[agent_id][-100:]

    def update_stability(
        self,
        agent_id: str,
        metrics: StabilityMetrics,
    ):
        """Update stability metrics for an agent."""
        if agent_id not in self.stability_history:
            self.stability_history[agent_id] = []
        self.stability_history[agent_id].append(metrics)
        # Keep rolling window
        if len(self.stability_history[agent_id]) > 50:
            self.stability_history[agent_id] = self.stability_history[agent_id][-50:]

    def decide(
        self,
        agent_id: str,
        window_size: int = 10,
    ) -> CAPDecision:
        """
        Make CAP decision for an agent.

        Args:
            agent_id: Agent identifier
            window_size: Rolling window size

        Returns:
            CAP decision
        """
        # Get recent quality scores
        quality_scores = self.quality_history.get(agent_id, [])
        recent_scores = quality_scores[-window_size:] if quality_scores else []

        # Get recent stability metrics
        stability_metrics = self.stability_history.get(agent_id, [])
        recent_stability = stability_metrics[-window_size:] if stability_metrics else []

        # Compute priority based on quality + stability
        avg_quality = sum(recent_scores) / len(recent_scores) if recent_scores else 0.5
        avg_reversals = (
            sum(m.edit_reversals for m in recent_stability) / len(recent_stability)
            if recent_stability
            else 0
        )
        avg_cite_errors = (
            sum(m.citation_error_rate for m in recent_stability) / len(recent_stability)
            if recent_stability
            else 0
        )

        # Priority: higher quality = higher priority, but penalize instability
        priority = int((avg_quality * 100) - (avg_reversals * 10) - (avg_cite_errors * 20))
        priority = max(0, min(100, priority))  # Clamp 0-100

        # Slots: more slots for high-quality, stable agents
        slots = 1
        if avg_quality > 0.8 and avg_reversals < 2:
            slots = 3
        elif avg_quality > 0.7 and avg_reversals < 5:
            slots = 2

        # Rate: multiplier based on quality
        rate = 1.0
        if avg_quality > 0.85:
            rate = 1.5
        elif avg_quality < 0.5:
            rate = 0.5

        return CAPDecision(
            agent_id=agent_id,
            priority=priority,
            slots=slots,
            rate=rate,
        )


@dataclass
class ComputeBudget:
    """Compute budget from CoAP."""

    tokens_per_sec: float
    max_steps: int
    ctx_cap: int
    lanes: int


class ComputeAllocationPanel:
    """
    Compute Allocation Panel (CoAP).

    Maps reliability index to compute budgets (tps, steps, ctx, lanes) with
    floors, caps, and hysteresis. Uses EWMA for reliability tracking.
    """

    def __init__(
        self,
        alpha: float = 0.2,
        lambda_r: float = 0.5,
        lambda_e: float = 0.7,
        bmin: float = 10.0,
        bmax: float = 120.0,
        bbase: float = 40.0,
        delta_max: float = 15.0,
    ):
        """
        Initialize CoAP.

        Args:
            alpha: EWMA smoothing factor
            lambda_r: Reversal penalty weight
            lambda_e: Citation error penalty weight
            bmin: Minimum tokens/sec
            bmax: Maximum tokens/sec
            bbase: Base tokens/sec
            delta_max: Maximum budget change per round
        """
        self.alpha = alpha
        self.lambda_r = lambda_r
        self.lambda_e = lambda_e
        self.bmin = bmin
        self.bmax = bmax
        self.bbase = bbase
        self.delta_max = delta_max

        # Agent state
        self.ema_scores: Dict[str, float] = {}  # agent_id -> EMA score
        self.last_budgets: Dict[str, ComputeBudget] = {}  # agent_id -> last budget
        self.recovery_start: Dict[str, float] = {}  # agent_id -> recovery start time

    def update_reliability(
        self,
        agent_id: str,
        quality_score: float,
        reversals: int,
        cite_errors: float,
    ):
        """
        Update reliability index for an agent.

        Args:
            agent_id: Agent identifier
            quality_score: Current quality score
            reversals: Number of reversals
            cite_errors: Citation error rate
        """
        # Update EMA score
        if agent_id not in self.ema_scores:
            self.ema_scores[agent_id] = quality_score
        else:
            self.ema_scores[agent_id] = (
                self.alpha * quality_score + (1 - self.alpha) * self.ema_scores[agent_id]
            )

        # Compute reliability index
        reliability = (
            self.ema_scores[agent_id]
            - self.lambda_r * reversals
            - self.lambda_e * cite_errors
        )

        # Allocate budget
        budget = self._allocate_budget(agent_id, reliability)

        # Store last budget
        self.last_budgets[agent_id] = budget

        return budget

    def _allocate_budget(
        self,
        agent_id: str,
        reliability: float,
    ) -> ComputeBudget:
        """
        Allocate compute budget based on reliability.

        Args:
            agent_id: Agent identifier
            reliability: Reliability index

        Returns:
            Compute budget
        """
        # Get last budget for hysteresis
        last_budget = self.last_budgets.get(agent_id)
        last_tps = last_budget.tokens_per_sec if last_budget else self.bbase

        # Compute new tokens/sec (monotone mapping)
        qmid = 0.0  # Midpoint
        k = (self.bmax - self.bmin) / 2.0  # Slope
        new_tps = max(self.bmin, self.bbase + k * (reliability - qmid))
        new_tps = min(self.bmax, new_tps)

        # Apply hysteresis (cap change)
        delta = new_tps - last_tps
        if abs(delta) > self.delta_max:
            delta = self.delta_max if delta > 0 else -self.delta_max
        new_tps = last_tps + delta

        # Slow-start recovery after STOP/QUARANTINE
        if agent_id in self.recovery_start:
            recovery_time = time.time() - self.recovery_start[agent_id]
            if recovery_time < 60:  # 1 minute recovery period
                gamma = 1.1  # Slow growth factor
                new_tps = min(new_tps, self.bbase * (gamma ** (recovery_time / 10)))

        # Map to other budget components
        # Steps: proportional to tps
        max_steps = int(16 + (new_tps - self.bmin) / (self.bmax - self.bmin) * 240)
        max_steps = max(16, min(256, max_steps))

        # Context cap: proportional to tps
        ctx_cap = int(8000 + (new_tps - self.bmin) / (self.bmax - self.bmin) * 56000)
        ctx_cap = max(8000, min(64000, ctx_cap))

        # Lanes: based on reliability
        lanes = 1
        if reliability > 0.5:
            lanes = 2
        if reliability > 0.8:
            lanes = 3
        lanes = max(1, min(6, lanes))

        return ComputeBudget(
            tokens_per_sec=new_tps,
            max_steps=max_steps,
            ctx_cap=ctx_cap,
            lanes=lanes,
        )

    def mark_recovery_start(self, agent_id: str):
        """Mark start of recovery period (after STOP/QUARANTINE)."""
        self.recovery_start[agent_id] = time.time()

    def clear_recovery(self, agent_id: str):
        """Clear recovery period."""
        if agent_id in self.recovery_start:
            del self.recovery_start[agent_id]
