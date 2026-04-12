"""
Unit tests for PSI aggregation pipeline.

~10 tests covering winsorize, rank normalization, PCA weights,
OMP permutation test, and BH-FDR correction.
"""

import numpy as np
import pytest

from ai_universe25.analytics.psi import (
    OMPPermutationTest,
    PSIAnalytics,
    PSIComponents,
    PSIPipeline,
    PSIScore,
    benjamini_hochberg,
    rank_normalize_across_agents,
    winsorize,
)


# ---------------------------------------------------------------------------
# Winsorize
# ---------------------------------------------------------------------------

class TestWinsorize:
    def test_clamps_outliers(self):
        values = np.array([0.0, 1.0, 2.0, 3.0, 100.0])
        result = winsorize(values, alpha=0.1)
        assert result[-1] < 100.0
        assert result[0] >= 0.0

    def test_identity_for_narrow_distribution(self):
        values = np.array([0.5, 0.5, 0.5, 0.5])
        result = winsorize(values, alpha=0.05)
        np.testing.assert_allclose(result, values)

    def test_empty_input(self):
        result = winsorize(np.array([]))
        assert len(result) == 0


# ---------------------------------------------------------------------------
# Rank normalization
# ---------------------------------------------------------------------------

class TestRankNormalize:
    def test_produces_zero_one_range(self):
        values = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        ranks = rank_normalize_across_agents(values)
        assert ranks.min() >= 0.0
        assert ranks.max() <= 1.0

    def test_preserves_ordering(self):
        values = np.array([1.0, 3.0, 2.0])
        ranks = rank_normalize_across_agents(values)
        assert ranks[0] < ranks[2] < ranks[1]

    def test_single_agent(self):
        ranks = rank_normalize_across_agents(np.array([5.0]))
        assert ranks[0] == 0.5


# ---------------------------------------------------------------------------
# PSI Pipeline
# ---------------------------------------------------------------------------

class TestPSIPipeline:
    def test_score_round_equal_weights(self):
        pipeline = PSIPipeline(weights=np.ones(5) / 5.0)
        comps = {
            "a": PSIComponents(RC=1.0, PO=0.5, CC=0.3, PS=0.8, RP=0.2),
            "b": PSIComponents(RC=0.5, PO=0.8, CC=0.7, PS=0.2, RP=0.6),
            "c": PSIComponents(RC=0.3, PO=0.2, CC=0.5, PS=0.5, RP=0.4),
        }
        scores = pipeline.score_round(comps)
        assert len(scores) == 3
        for aid, s in scores.items():
            assert 0.0 <= s.psi <= 1.0

    def test_ranking_across_agents(self):
        """Ranking happens across agents, not temporally."""
        pipeline = PSIPipeline()
        # Agent 'a' dominates all components
        comps = {
            "a": PSIComponents(RC=10.0, PO=10.0, CC=10.0, PS=10.0, RP=10.0),
            "b": PSIComponents(RC=1.0, PO=1.0, CC=1.0, PS=1.0, RP=1.0),
            "c": PSIComponents(RC=0.1, PO=0.1, CC=0.1, PS=0.1, RP=0.1),
        }
        scores = pipeline.score_round(comps)
        assert scores["a"].psi > scores["c"].psi

    def test_scale_free_property(self):
        """Monotone transforms don't change PSI rankings."""
        pipeline1 = PSIPipeline()
        pipeline2 = PSIPipeline()
        comps1 = {
            "a": PSIComponents(1.0, 2.0, 3.0, 4.0, 5.0),
            "b": PSIComponents(2.0, 4.0, 6.0, 8.0, 10.0),
            "c": PSIComponents(0.5, 1.0, 1.5, 2.0, 2.5),
        }
        # Monotone transform: square all values
        comps2 = {
            aid: PSIComponents(c.RC**2, c.PO**2, c.CC**2, c.PS**2, c.RP**2)
            for aid, c in comps1.items()
        }
        scores1 = pipeline1.score_round(comps1)
        scores2 = pipeline2.score_round(comps2)
        # Rankings should be preserved (same rank order)
        order1 = sorted(scores1.keys(), key=lambda x: scores1[x].psi)
        order2 = sorted(scores2.keys(), key=lambda x: scores2[x].psi)
        assert order1 == order2


# ---------------------------------------------------------------------------
# PCA weights
# ---------------------------------------------------------------------------

class TestPCAWeights:
    def test_pca_weights_sum_to_one(self):
        pipeline = PSIPipeline()
        np.random.seed(42)
        data = np.random.randn(50, 5)
        weights = pipeline.compute_pca_weights(data)
        assert weights.sum() == pytest.approx(1.0, abs=1e-10)
        assert np.all(weights >= 0)

    def test_pca_weights_small_sample_fallback(self):
        pipeline = PSIPipeline()
        data = np.random.randn(3, 5)
        weights = pipeline.compute_pca_weights(data)
        np.testing.assert_allclose(weights, np.ones(5) / 5.0)


# ---------------------------------------------------------------------------
# OMP Permutation Test
# ---------------------------------------------------------------------------

class TestOMPPermutationTest:
    def test_p_value_valid(self):
        np.random.seed(42)
        omp = OMPPermutationTest(n_permutations=100)
        observed = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        stat, p = omp.test(observed)
        assert 0.0 <= p <= 1.0
        assert stat == 0.9

    def test_uniform_data_nonsignificant(self):
        np.random.seed(42)
        omp = OMPPermutationTest(n_permutations=100)
        observed = np.array([0.5, 0.5, 0.5, 0.5])
        stat, p = omp.test(observed)
        # Uniform data should not be significant
        assert p > 0.01


# ---------------------------------------------------------------------------
# BH-FDR
# ---------------------------------------------------------------------------

class TestBenjaminiHochberg:
    def test_all_significant(self):
        p_values = np.array([0.001, 0.002, 0.003])
        result = benjamini_hochberg(p_values, alpha=0.05)
        assert np.all(result)

    def test_none_significant(self):
        p_values = np.array([0.5, 0.6, 0.7])
        result = benjamini_hochberg(p_values, alpha=0.05)
        assert not np.any(result)

    def test_empty_input(self):
        result = benjamini_hochberg(np.array([]))
        assert len(result) == 0
