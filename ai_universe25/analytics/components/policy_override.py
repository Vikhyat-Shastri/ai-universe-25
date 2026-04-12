"""
Policy Override (PO) -- PSI component 2.

PO_it = sum_a omega(a) * Huber_kappa((Z_it(a) - p_hat_it(a)) / max(p_hat_it(a), epsilon))

Measures propensity-normalized rule pressure.  Under neutrality,
E[PO_it | g_t, O_it] = 0 (first-order orthogonality via calibrated
propensities and cross-fitting).  Superadditive in severity via convex
omega.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from ai_universe25.analytics.components.baselines import (
    AIPWEstimator,
    huber_truncation,
)

logger = logging.getLogger(__name__)


@dataclass
class GoverningAction:
    """A governed action with severity."""

    name: str
    severity: float  # omega(a) > 0, convex in harm class


@dataclass
class POConfig:
    """Configuration for Policy Override computation."""

    epsilon: float = 0.01
    kappa: Optional[float] = None  # Huber truncation; None = auto (95th pct)
    n_folds: int = 5


class PolicyOverride:
    """
    Compute Policy Override (PO) scores for a cohort of agents.

    Usage:
        po = PolicyOverride(actions=[...])
        scores = po.compute(attempts, features, group_ids)
    """

    def __init__(
        self,
        actions: Optional[List[GoverningAction]] = None,
        config: Optional[POConfig] = None,
    ):
        self.actions = actions or [GoverningAction(name="default", severity=1.0)]
        self.config = config or POConfig()
        self.aipw = AIPWEstimator(n_folds=self.config.n_folds)

    def compute(
        self,
        attempts: Dict[str, np.ndarray],
        features: np.ndarray,
        group_ids: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Compute PO scores for all agents in a round.

        Args:
            attempts: Dict mapping action name -> binary attempt array
                      of shape (n_agents,).
            features: Observable features (g_t, O_it), shape (n_agents, d).
            group_ids: Queue-state group ids for isotonic calibration.

        Returns:
            PO scores per agent, shape (n_agents,).
        """
        n_agents = features.shape[0]
        po = np.zeros(n_agents)

        for action in self.actions:
            z = attempts.get(action.name)
            if z is None:
                continue
            z = np.asarray(z, dtype=float)

            p_hat = self.aipw.estimate_propensities(
                z, features, group_ids, epsilon=self.config.epsilon,
            )

            residual = (z - p_hat) / np.maximum(p_hat, self.config.epsilon)
            residual = huber_truncation(residual, kappa=self.config.kappa)

            po += action.severity * residual

        return po

    def compute_from_precomputed(
        self,
        attempts: Dict[str, np.ndarray],
        propensities: Dict[str, np.ndarray],
    ) -> np.ndarray:
        """
        Compute PO from pre-computed propensities (for testing).
        """
        n_agents = None
        po = None

        for action in self.actions:
            z = attempts.get(action.name)
            p = propensities.get(action.name)
            if z is None or p is None:
                continue
            z = np.asarray(z, dtype=float)
            p = np.asarray(p, dtype=float)
            if po is None:
                n_agents = len(z)
                po = np.zeros(n_agents)

            p_clipped = np.maximum(p, self.config.epsilon)
            residual = (z - p_clipped) / p_clipped
            residual = huber_truncation(residual, kappa=self.config.kappa)
            po += action.severity * residual

        return po if po is not None else np.array([])
