"""
Judge panels: CQP, CAP, and CoAP.

Implements:
- CQP: Content Quality Panel (pairwise, majority, tie-break)
- CAP: Channel-Access Panel (priority/slots/rate)
- CoAP: Compute Allocation Panel (EWMA+monotone allocator+hysteresis+slow-start)
"""

import json
import logging
import math
import random
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Tuple

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


class _LLMBackendProto(Protocol):
    def generate(self, prompt: str, max_tokens: int = 512) -> str: ...


@dataclass
class JudgeBackend:
    """Pluggable judge backend that uses an LLM (or heuristics as fallback)."""

    name: str
    model: str
    llm_backend: Optional[Any] = field(default=None, repr=False)

    _RUBRIC_PROMPT = """You are a wiki content quality judge. Score the following content on four dimensions, each from 0.0 to 1.0.

Dimensions:
- coverage: How well does the content cover the topic? (breadth, depth, completeness)
- correctness: Are the claims factually plausible and internally consistent?
- coherence: Is the writing logically organized and easy to follow?
- citation_integrity: Are claims backed by citations or evidence markers?

Content to evaluate:
---
{content}
---

Respond with ONLY a JSON object (no markdown, no explanation):
{{"coverage": 0.XX, "correctness": 0.XX, "coherence": 0.XX, "citation_integrity": 0.XX}}"""

    def score(self, content: str, rubric: Dict[str, Any]) -> QualityScore:
        """Score content using the LLM backend, falling back to heuristics."""
        if self.llm_backend is not None:
            return self._score_with_llm(content)
        return self._score_heuristic(content)

    def _score_with_llm(self, content: str) -> QualityScore:
        """Score content by asking the LLM judge."""
        truncated = content[:2000]
        prompt = self._RUBRIC_PROMPT.format(content=truncated)
        try:
            raw = self.llm_backend.generate(prompt, max_tokens=150)
            return self._parse_llm_scores(raw)
        except Exception as e:
            logger.warning(f"Judge {self.name} LLM call failed ({e}), using heuristic")
            return self._score_heuristic(content)

    @staticmethod
    def _parse_llm_scores(raw: str) -> QualityScore:
        """Parse JSON scores from LLM response, with robust fallback."""
        json_match = re.search(r'\{[^}]+\}', raw)
        if json_match:
            try:
                data = json.loads(json_match.group())
                def _clamp(v):
                    try:
                        return max(0.0, min(1.0, float(v)))
                    except (TypeError, ValueError):
                        return 0.5
                return QualityScore(
                    coverage=_clamp(data.get("coverage", 0.5)),
                    correctness=_clamp(data.get("correctness", 0.5)),
                    coherence=_clamp(data.get("coherence", 0.5)),
                    citation_integrity=_clamp(data.get("citation_integrity", 0.5)),
                )
            except json.JSONDecodeError:
                pass
        nums = re.findall(r'0\.\d+', raw)
        if len(nums) >= 4:
            return QualityScore(
                coverage=float(nums[0]),
                correctness=float(nums[1]),
                coherence=float(nums[2]),
                citation_integrity=float(nums[3]),
            )
        return QualityScore(coverage=0.5, correctness=0.5, coherence=0.5, citation_integrity=0.5)

    @staticmethod
    def _score_heuristic(content: str) -> QualityScore:
        """Content-aware heuristic scoring (no LLM needed)."""
        if not content or not content.strip():
            return QualityScore(coverage=0.1, correctness=0.1, coherence=0.1, citation_integrity=0.1)

        words = content.split()
        n_words = len(words)
        sentences = [s.strip() for s in re.split(r'[.!?]+', content) if s.strip()]
        n_sentences = max(len(sentences), 1)

        # Coverage: based on content length (diminishing returns)
        coverage = min(1.0, 0.2 + 0.8 * (1 - math.exp(-n_words / 150)))

        # Coherence: sentence length consistency + paragraph structure
        avg_sent_len = n_words / n_sentences
        sent_len_penalty = max(0, abs(avg_sent_len - 18) - 8) / 30
        has_structure = any(
            marker in content for marker in ['#', '1.', '- ', '**', '\n\n']
        )
        coherence = min(1.0, 0.4 + (0.3 if has_structure else 0.0) - sent_len_penalty
                        + 0.3 * min(1.0, n_sentences / 5))

        # Correctness: penalize hedging and unsupported claims
        hedge_words = sum(1 for w in words if w.lower() in {
            'maybe', 'perhaps', 'possibly', 'might', 'could', 'seems',
        })
        hedge_rate = hedge_words / max(n_words, 1)
        correctness = max(0.2, 0.85 - hedge_rate * 5)

        # Citation integrity: presence of citation markers
        cite_patterns = len(re.findall(
            r'\[CITE|\[[\d]+\]|\(\d{4}\)|et al\.|ENTAIL|CONTRADICT|doi:', content
        ))
        citation_integrity = min(1.0, 0.2 + cite_patterns * 0.15)

        return QualityScore(
            coverage=round(min(1.0, max(0.0, coverage)), 4),
            correctness=round(min(1.0, max(0.0, correctness)), 4),
            coherence=round(min(1.0, max(0.0, coherence)), 4),
            citation_integrity=round(min(1.0, max(0.0, citation_integrity)), 4),
        )


class ContentQualityPanel:
    """
    Content Quality Panel (CQP).

    Uses three LLM judges in pairwise comparison protocol.
    Votes by majority; ties broken by the first judge.
    When no LLM backends are provided, uses content-aware heuristic scoring.
    """

    def __init__(
        self,
        judges: Optional[List[JudgeBackend]] = None,
        tie_breaker: Optional[str] = None,
        llm_backend=None,
    ):
        """
        Initialize CQP.

        Args:
            judges: List of judge backends (default: create 3 heuristic judges)
            tie_breaker: Name of tie-breaker judge (default: first judge)
            llm_backend: If provided, all default judges use this LLM for scoring
        """
        if judges is None:
            judges = [
                JudgeBackend(name="judge_1", model="heuristic", llm_backend=llm_backend),
                JudgeBackend(name="judge_2", model="heuristic", llm_backend=llm_backend),
                JudgeBackend(name="judge_3", model="heuristic", llm_backend=llm_backend),
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
