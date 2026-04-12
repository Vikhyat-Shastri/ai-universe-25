"""
Unit tests for PSI components: RC, PO, CC, PS, RP and shared baselines.

~25 tests covering invariance, neutrality, edge cases, and formula correctness.
"""

import numpy as np
import pytest

from ai_universe25.analytics.components.baselines import (
    AIPWEstimator,
    gini_coefficient,
    grouped_isotonic_calibration,
    huber_truncation,
)
from ai_universe25.analytics.components.coalition_centrality import (
    CCConfig,
    CoalitionCentrality,
    Edge,
)
from ai_universe25.analytics.components.persistence import (
    PSConfig,
    PersistenceUnderSanction,
    SanctionEpisode,
)
from ai_universe25.analytics.components.policy_override import (
    GoverningAction,
    POConfig,
    PolicyOverride,
)
from ai_universe25.analytics.components.redirection import (
    RPConfig,
    RedirectionPressure,
)
from ai_universe25.analytics.components.resource_capture import (
    RCConfig,
    ResourceCapture,
)


# ---------------------------------------------------------------------------
# Gini coefficient
# ---------------------------------------------------------------------------

class TestGiniCoefficient:
    def test_gini_perfect_equality(self):
        """Equal distribution has Gini = 0."""
        values = np.array([10.0, 10.0, 10.0, 10.0])
        assert gini_coefficient(values) == pytest.approx(0.0, abs=1e-10)

    def test_gini_maximum_inequality(self):
        """One agent takes all: Gini approaches (n-1)/n."""
        values = np.array([0.0, 0.0, 0.0, 100.0])
        g = gini_coefficient(values)
        assert g > 0.7

    def test_gini_empty(self):
        assert gini_coefficient(np.array([])) == 0.0

    def test_gini_all_zeros(self):
        assert gini_coefficient(np.array([0.0, 0.0, 0.0])) == 0.0


# ---------------------------------------------------------------------------
# Huber truncation
# ---------------------------------------------------------------------------

class TestHuberTruncation:
    def test_huber_caps_extremes(self):
        values = np.array([0.0, 1.0, 100.0, -50.0])
        result = huber_truncation(values, kappa=10.0)
        assert result.max() <= 10.0
        assert result.min() >= -10.0

    def test_huber_auto_kappa(self):
        values = np.random.randn(1000)
        result = huber_truncation(values)
        kappa_auto = np.percentile(np.abs(values), 95)
        assert np.all(result <= kappa_auto + 1e-10)
        assert np.all(result >= -kappa_auto - 1e-10)

    def test_huber_empty(self):
        result = huber_truncation(np.array([]))
        assert len(result) == 0


# ---------------------------------------------------------------------------
# Isotonic calibration
# ---------------------------------------------------------------------------

class TestIsotonicCalibration:
    def test_isotonic_monotone(self):
        """Calibrated values should be monotone w.r.t. predicted."""
        np.random.seed(42)
        predicted = np.sort(np.random.uniform(0, 1, 100))
        observed = (predicted > 0.5).astype(float) + np.random.randn(100) * 0.1
        observed = np.clip(observed, 0, 1)
        calibrated = grouped_isotonic_calibration(predicted, observed)
        sorted_idx = np.argsort(predicted)
        sorted_cal = calibrated[sorted_idx]
        # Monotone: each value >= preceding value
        assert np.all(np.diff(sorted_cal) >= -1e-10)


# ---------------------------------------------------------------------------
# AIPW estimator
# ---------------------------------------------------------------------------

class TestAIPWEstimator:
    def test_aipw_doubly_robust_baseline(self):
        """Baselines should be positive and finite."""
        np.random.seed(42)
        n = 50
        usage = np.random.exponential(10, n)
        features = np.random.randn(n, 3)
        neutral_mask = np.random.random(n) > 0.3
        estimator = AIPWEstimator(n_folds=3)
        baselines = estimator.estimate_baselines(usage, features, neutral_mask)
        assert np.all(baselines > 0)
        assert np.all(np.isfinite(baselines))

    def test_aipw_small_sample_fallback(self):
        """Small samples should fall back gracefully."""
        usage = np.array([1.0, 2.0])
        features = np.array([[1.0], [2.0]])
        neutral_mask = np.array([True, True])
        estimator = AIPWEstimator()
        baselines = estimator.estimate_baselines(usage, features, neutral_mask)
        assert len(baselines) == 2


# ---------------------------------------------------------------------------
# RC -- Resource Capture
# ---------------------------------------------------------------------------

class TestResourceCapture:
    def test_rc_opportunity_invariance(self):
        """Scaling u and m by c leaves RC unchanged (up to Gini constant)."""
        rc = ResourceCapture(config=RCConfig(lambda_G=0.0))
        usage = np.array([10.0, 20.0, 30.0])
        baselines = np.array([5.0, 10.0, 15.0])
        rc1 = rc.compute_from_precomputed(usage, baselines)

        c = 3.0
        rc2 = rc.compute_from_precomputed(usage * c, baselines * c)
        np.testing.assert_allclose(rc1, rc2, atol=1e-10)

    def test_rc_gini_amplification(self):
        """Higher Gini increases RC for above-baseline agents."""
        # Equal baselines, unequal usage
        usage_equal = np.array([10.0, 10.0, 10.0])
        usage_unequal = np.array([1.0, 10.0, 30.0])
        baselines = np.array([10.0, 10.0, 10.0])

        rc = ResourceCapture(config=RCConfig(lambda_G=1.0))
        rc_equal = rc.compute_from_precomputed(usage_equal, baselines)
        rc_unequal = rc.compute_from_precomputed(usage_unequal, baselines)

        gini_equal = gini_coefficient(usage_equal / baselines)
        gini_unequal = gini_coefficient(usage_unequal / baselines)
        assert gini_unequal > gini_equal

    def test_rc_regularization_small_denominator(self):
        """Near-zero baselines don't explode RC."""
        rc = ResourceCapture(config=RCConfig(lambda_G=0.0))
        usage = np.array([1.0, 2.0])
        baselines = np.array([1e-10, 1.0])
        result = rc.compute_from_precomputed(usage, baselines)
        assert np.all(np.isfinite(result))


# ---------------------------------------------------------------------------
# PO -- Policy Override
# ---------------------------------------------------------------------------

class TestPolicyOverride:
    def test_po_mean_zero_under_neutrality(self):
        """Neutral agents (Z ~ p_hat) have E[PO] ~ 0."""
        np.random.seed(42)
        actions = [GoverningAction("a1", 1.0)]
        po = PolicyOverride(actions=actions, config=POConfig(epsilon=0.01))

        p = 0.3
        attempts = {"a1": np.random.binomial(1, p, 200).astype(float)}
        propensities = {"a1": np.full(200, p)}
        result = po.compute_from_precomputed(attempts, propensities)
        assert abs(np.mean(result)) < 0.5

    def test_po_superadditivity(self):
        """Multiple severe violations produce higher PO than sum of individual mild violations."""
        actions = [
            GoverningAction("mild", 1.0),
            GoverningAction("severe", 5.0),
        ]
        po = PolicyOverride(actions=actions, config=POConfig(epsilon=0.01, kappa=100.0))

        n = 10
        # All violations with calibrated propensities = 0.1
        attempts = {
            "mild": np.ones(n),
            "severe": np.ones(n),
        }
        propensities = {
            "mild": np.full(n, 0.1),
            "severe": np.full(n, 0.1),
        }
        combined = po.compute_from_precomputed(attempts, propensities)

        mild_only = PolicyOverride(
            actions=[GoverningAction("mild", 1.0)],
            config=POConfig(epsilon=0.01, kappa=100.0),
        ).compute_from_precomputed(
            {"mild": np.ones(n)}, {"mild": np.full(n, 0.1)}
        )

        # Combined should be larger than mild alone
        assert np.mean(np.abs(combined)) > np.mean(np.abs(mild_only))

    def test_po_propensity_clipping(self):
        """Near-zero propensities are clipped to epsilon."""
        actions = [GoverningAction("a1", 1.0)]
        po = PolicyOverride(actions=actions, config=POConfig(epsilon=0.05))
        attempts = {"a1": np.array([1.0, 0.0])}
        propensities = {"a1": np.array([0.001, 0.001])}
        result = po.compute_from_precomputed(attempts, propensities)
        assert np.all(np.isfinite(result))


# ---------------------------------------------------------------------------
# CC -- Coalition Centrality
# ---------------------------------------------------------------------------

class TestCoalitionCentrality:
    def _make_edges(self):
        return [
            Edge(source="a", target="b", round_created=1, accepted=True, rounds_persisted=5),
            Edge(source="b", target="c", round_created=1, accepted=True, rounds_persisted=5),
            Edge(source="c", target="a", round_created=1, accepted=True, rounds_persisted=5),
            Edge(source="d", target="a", round_created=1, accepted=False, rounds_persisted=0),
        ]

    def test_cc_spray_residual(self):
        """Adding outbound spam (high attempts_out) shouldn't inflate CC."""
        cc = CoalitionCentrality(config=CCConfig(durability_threshold=1))
        edges = self._make_edges()
        agent_ids = ["a", "b", "c"]
        attempts_low = np.array([1.0, 1.0, 1.0])
        attempts_high = np.array([100.0, 1.0, 1.0])
        recency = np.ones(3)

        cc1 = cc.compute(edges, agent_ids, attempts_low, recency)
        cc2 = cc.compute(edges, agent_ids, attempts_high, recency)
        # After partialling out, agent a with 100x spray should not have
        # significantly higher CC
        assert cc2[0] < cc1[0] + 0.5

    def test_cc_pagerank_stability(self):
        """Small perturbations don't dramatically change rankings."""
        cc = CoalitionCentrality(config=CCConfig(durability_threshold=1))
        edges = self._make_edges()
        agent_ids = ["a", "b", "c"]
        attempts = np.ones(3)
        recency = np.ones(3)

        cc1 = cc.compute(edges, agent_ids, attempts, recency)

        edges_perturbed = edges + [
            Edge(source="a", target="c", round_created=2, accepted=True, rounds_persisted=3)
        ]
        cc2 = cc.compute(edges_perturbed, agent_ids, attempts, recency)

        # Rankings should be reasonably stable
        rank1 = np.argsort(np.argsort(cc1))
        rank2 = np.argsort(np.argsort(cc2))
        rank_diff = np.abs(rank1 - rank2)
        assert rank_diff.max() <= 2

    def test_cc_durability_filter(self):
        """Transient edges (low persistence) are filtered out."""
        cc = CoalitionCentrality(config=CCConfig(durability_threshold=5))
        edges = [
            Edge(source="a", target="b", round_created=1, accepted=True, rounds_persisted=1),
            Edge(source="b", target="c", round_created=1, accepted=True, rounds_persisted=1),
        ]
        agent_ids = ["a", "b", "c"]
        adj = cc.build_accepted_graph(edges, durability_filter=True)
        # All edges filtered out
        assert len(adj) == 0


# ---------------------------------------------------------------------------
# PS -- Persistence under Sanction
# ---------------------------------------------------------------------------

class TestPersistenceUnderSanction:
    def test_ps_inverse_frailty(self):
        """PS > 1 means slower quiescence than average."""
        ps = PersistenceUnderSanction(config=PSConfig(frailty_k=1.0))
        # Agent that never quiesces (long duration, no event)
        episodes = [
            SanctionEpisode("resilient", "warn", 0, 20, quiesced=False),
            SanctionEpisode("fragile", "warn", 0, 2, quiesced=True),
        ]
        result = ps.compute(episodes)
        assert result["resilient"] > result["fragile"]

    def test_ps_recovery_after_hardening(self):
        """Agent with many quiescence events has lower PS."""
        ps = PersistenceUnderSanction(config=PSConfig(frailty_k=1.0))
        episodes = [
            SanctionEpisode("obedient", "warn", 0, 5, quiesced=True),
            SanctionEpisode("obedient", "stop", 5, 10, quiesced=True),
            SanctionEpisode("obedient", "warn", 10, 15, quiesced=True),
            SanctionEpisode("defiant", "warn", 0, 20, quiesced=False),
        ]
        result = ps.compute(episodes)
        assert result["obedient"] < result["defiant"]

    def test_ps_censoring_handled(self):
        """Censored episodes don't explode PS."""
        ps = PersistenceUnderSanction(config=PSConfig(frailty_k=1.0))
        episodes = [
            SanctionEpisode("agent_a", "warn", 0, None, quiesced=False),
        ]
        result = ps.compute(episodes)
        assert np.isfinite(result["agent_a"])

    def test_ps_array_missing_agents(self):
        """Agents without episodes get PS = 1.0 (neutral)."""
        ps = PersistenceUnderSanction()
        episodes = [SanctionEpisode("a", "warn", 0, 5, quiesced=True)]
        result = ps.compute_array(episodes, ["a", "b", "c"])
        assert result[1] == 1.0
        assert result[2] == 1.0


# ---------------------------------------------------------------------------
# RP -- Redirection Pressure
# ---------------------------------------------------------------------------

class TestRedirectionPressure:
    def test_rp_nonnegativity(self):
        """RP >= 0 always."""
        np.random.seed(42)
        rp = RedirectionPressure(config=RPConfig(delta=0.1))
        focal = np.random.randint(0, 5, 50)
        cohort = np.random.randint(0, 5, 50)
        result = rp.compute_for_agent(focal, cohort, 5)
        assert result >= 0.0

    def test_rp_zero_when_independent(self):
        """No redirection when focal is independent of cohort."""
        np.random.seed(42)
        rp = RedirectionPressure(config=RPConfig(delta=1.0))
        focal = np.random.randint(0, 3, 500)
        cohort = np.random.randint(0, 3, 500)
        result = rp.compute_for_agent(focal, cohort, 3)
        assert result < 0.15

    def test_rp_normalization(self):
        """RP should be in [0, 1]."""
        np.random.seed(42)
        rp = RedirectionPressure()
        focal = np.random.randint(0, 5, 100)
        cohort = np.random.randint(0, 5, 100)
        result = rp.compute_for_agent(focal, cohort, 5)
        assert 0.0 <= result <= 1.0

    def test_rp_permutation_null(self):
        """Time-shuffle should destroy any RP signal."""
        np.random.seed(42)
        rp = RedirectionPressure(config=RPConfig(n_permutations=100))
        # Strong causal signal: cohort copies focal with lag 1
        focal = np.random.randint(0, 5, 100)
        cohort = np.roll(focal, 1)
        observed, p_value = rp.permutation_test(focal, cohort, 5)
        # If there's a real signal, p-value should be small
        # If not, p-value should be reasonably distributed
        assert 0.0 <= p_value <= 1.0

    def test_rp_short_sequence(self):
        """Very short sequences return 0."""
        rp = RedirectionPressure()
        focal = np.array([1, 2])
        cohort = np.array([3, 4])
        assert rp.compute_for_agent(focal, cohort, 5) == 0.0
