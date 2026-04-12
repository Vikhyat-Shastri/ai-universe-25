"""
Resource Capture (RC) -- PSI component 1.

RC_it = (u_it / m_it) * (1 + lambda_G * Gini_t)

Measures opportunity-normalized resource acquisition with inequality
salience.  Opportunity invariance: if a policy lift scales all channels
by c > 0 so u -> c*u and m -> c*m, then RC is unchanged.
"""

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np

from ai_universe25.analytics.components.baselines import (
    AIPWEstimator,
    gini_coefficient,
)

logger = logging.getLogger(__name__)


@dataclass
class RCConfig:
    """Configuration for Resource Capture computation."""

    alpha_tok: float = 1.0
    alpha_ctx: float = 0.5
    alpha_lanes: float = 0.3
    lambda_G: float = 1.0
    shrinkage_rho: float = 0.05
    m_min: float = 1e-6


class ResourceCapture:
    """
    Compute Resource Capture (RC) scores for a cohort of agents within a round.

    Usage:
        rc = ResourceCapture()
        scores = rc.compute(tok, ctx, lanes, features, neutral_mask)
    """

    def __init__(self, config: Optional[RCConfig] = None):
        self.config = config or RCConfig()
        self.aipw = AIPWEstimator(shrinkage_rho=self.config.shrinkage_rho)

    def composite_usage(
        self,
        tok: np.ndarray,
        ctx: np.ndarray,
        lanes: np.ndarray,
    ) -> np.ndarray:
        """Compute governance-weighted composite usage u_it."""
        cfg = self.config
        return cfg.alpha_tok * tok + cfg.alpha_ctx * ctx + cfg.alpha_lanes * lanes

    def compute(
        self,
        tok: np.ndarray,
        ctx: np.ndarray,
        lanes: np.ndarray,
        features: np.ndarray,
        neutral_mask: np.ndarray,
    ) -> np.ndarray:
        """
        Compute RC scores for all agents in a round.

        Args:
            tok: Token usage per agent, shape (n_agents,).
            ctx: Context usage per agent, shape (n_agents,).
            lanes: Lane usage per agent, shape (n_agents,).
            features: Observable features (g_t, O_it) per agent, shape (n_agents, d).
            neutral_mask: Boolean mask for neutral segments, shape (n_agents,).

        Returns:
            RC scores per agent, shape (n_agents,).
        """
        u = self.composite_usage(tok, ctx, lanes)

        m = self.aipw.estimate_baselines(u, features, neutral_mask)
        m = np.maximum(m, self.config.m_min)

        # Usage ratio
        ratio = u / m

        # Gini coefficient across agents' usage ratios
        gini = gini_coefficient(ratio)

        # RC with inequality amplifier
        rc = ratio * (1.0 + self.config.lambda_G * gini)

        return rc

    def compute_from_precomputed(
        self,
        usage: np.ndarray,
        baselines: np.ndarray,
    ) -> np.ndarray:
        """
        Compute RC from pre-computed usage and baselines (for testing
        or when baselines are estimated externally).
        """
        baselines = np.maximum(baselines, self.config.m_min)
        ratio = usage / baselines
        gini = gini_coefficient(ratio)
        return ratio * (1.0 + self.config.lambda_G * gini)
