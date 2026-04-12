"""
Shared baseline infrastructure for PSI components.

Implements:
- AIPW doubly-robust estimator for opportunity baselines m_it
- Cross-fitting (K-fold) for nuisance estimation
- Grouped isotonic calibration for propensity scores
- Gini coefficient computation
- Huber truncation function
"""

import logging
from typing import Optional, Tuple

import numpy as np
from scipy import stats
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import KFold

logger = logging.getLogger(__name__)


def gini_coefficient(values: np.ndarray) -> float:
    """
    Compute the Gini coefficient of a distribution.

    Returns 0 for perfect equality, approaches 1 for perfect inequality.
    """
    values = np.asarray(values, dtype=float)
    if len(values) == 0 or np.all(values == 0):
        return 0.0
    values = np.abs(values)
    sorted_vals = np.sort(values)
    n = len(sorted_vals)
    index = np.arange(1, n + 1)
    return float((2 * np.sum(index * sorted_vals) / (n * np.sum(sorted_vals))) - (n + 1) / n)


def huber_truncation(values: np.ndarray, kappa: Optional[float] = None) -> np.ndarray:
    """
    Apply Huber-style truncation to cap extreme values.

    If kappa is None, uses the 95th percentile of absolute values as the
    truncation threshold.
    """
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        return values
    if kappa is None:
        kappa = float(np.percentile(np.abs(values), 95))
    if kappa <= 0:
        return values
    return np.clip(values, -kappa, kappa)


def grouped_isotonic_calibration(
    predicted: np.ndarray,
    observed: np.ndarray,
    group_ids: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Apply grouped isotonic calibration to predicted probabilities.

    Within each group (queue-state stratum), fits an isotonic regression
    of observed outcomes on predicted probabilities, enforcing monotone
    reliability curves.

    Args:
        predicted: Raw predicted probabilities.
        observed: Binary observed outcomes (0/1).
        group_ids: Group indicators for stratification. If None, treats
                   all data as one group.

    Returns:
        Calibrated probabilities.
    """
    predicted = np.asarray(predicted, dtype=float)
    observed = np.asarray(observed, dtype=float)
    calibrated = np.zeros_like(predicted)

    if group_ids is None:
        group_ids = np.zeros(len(predicted), dtype=int)
    group_ids = np.asarray(group_ids)

    for gid in np.unique(group_ids):
        mask = group_ids == gid
        if np.sum(mask) < 3:
            calibrated[mask] = predicted[mask]
            continue
        iso = IsotonicRegression(y_min=0, y_max=1, out_of_bounds="clip")
        iso.fit(predicted[mask], observed[mask])
        calibrated[mask] = iso.predict(predicted[mask])

    return calibrated


class AIPWEstimator:
    """
    Augmented Inverse Probability Weighting (AIPW) doubly-robust estimator
    for opportunity baselines m_it.

    The estimating equation is:
        m_hat_it = mu_hat(g, O) + S / s_hat(g, O) * (u - mu_hat(g, O))

    where mu_hat is the outcome model and s_hat is the selection model.
    Doubly robust: consistent if either model is correctly specified.

    Uses cross-fitting (K-fold) to achieve Neyman orthogonality.
    """

    def __init__(
        self,
        n_folds: int = 5,
        shrinkage_rho: float = 0.05,
        s_min: float = 0.05,
    ):
        self.n_folds = n_folds
        self.shrinkage_rho = shrinkage_rho
        self.s_min = s_min

    def estimate_baselines(
        self,
        usage: np.ndarray,
        features: np.ndarray,
        neutral_mask: np.ndarray,
    ) -> np.ndarray:
        """
        Estimate opportunity baselines m_it via AIPW with cross-fitting.

        Args:
            usage: Realized composite usage u_it, shape (n,).
            features: Observable features (g_t, O_it), shape (n, d).
            neutral_mask: Boolean mask S_it indicating neutral segments, shape (n,).

        Returns:
            Estimated baselines m_hat_it, shape (n,).
        """
        n = len(usage)
        m_hat = np.zeros(n)
        mu_hat_full = np.zeros(n)
        s_hat_full = np.zeros(n)

        if n < self.n_folds * 2:
            m_bar = np.mean(usage[neutral_mask]) if np.any(neutral_mask) else np.mean(usage)
            return np.full(n, m_bar)

        kf = KFold(n_splits=self.n_folds, shuffle=True, random_state=42)

        for train_idx, test_idx in kf.split(features):
            train_neutral = neutral_mask[train_idx]
            if np.sum(train_neutral) < 3:
                mu_hat_full[test_idx] = np.mean(usage)
                s_hat_full[test_idx] = 0.5
                continue

            # Outcome model: E[u | g, O, S=1] fitted on neutral segments
            outcome_model = Ridge(alpha=1.0)
            outcome_model.fit(
                features[train_idx][train_neutral],
                usage[train_idx][train_neutral],
            )
            mu_hat_full[test_idx] = outcome_model.predict(features[test_idx])

            # Selection model: Pr(S=1 | g, O)
            train_labels = neutral_mask[train_idx].astype(int)
            if len(np.unique(train_labels)) < 2:
                s_hat_full[test_idx] = np.mean(train_labels)
            else:
                selection_model = LogisticRegression(max_iter=500, C=1.0)
                selection_model.fit(features[train_idx], train_labels)
                s_hat_full[test_idx] = selection_model.predict_proba(features[test_idx])[:, 1]

        # Enforce overlap
        s_hat_full = np.maximum(s_hat_full, self.s_min)

        # AIPW estimating equation
        m_hat = mu_hat_full + (neutral_mask.astype(float) / s_hat_full) * (usage - mu_hat_full)

        # Shrinkage for rare opportunity states
        m_bar = np.mean(m_hat)
        m_hat = (1 - self.shrinkage_rho) * m_hat + self.shrinkage_rho * m_bar

        # Floor to prevent division by zero downstream
        m_hat = np.maximum(m_hat, 1e-6)

        return m_hat

    def estimate_propensities(
        self,
        attempts: np.ndarray,
        features: np.ndarray,
        group_ids: Optional[np.ndarray] = None,
        epsilon: float = 0.01,
    ) -> np.ndarray:
        """
        Estimate calibrated propensities p_hat_it(a) via cross-fitting +
        grouped isotonic calibration.

        Args:
            attempts: Binary attempt indicators Z_it(a), shape (n,).
            features: Observable features (g_t, O_it), shape (n, d).
            group_ids: Queue-state group indicators for isotonic calibration.
            epsilon: Minimum propensity (overlap enforcement).

        Returns:
            Calibrated propensities, shape (n,).
        """
        n = len(attempts)
        p_hat = np.full(n, 0.5)

        if n < self.n_folds * 2:
            return p_hat

        kf = KFold(n_splits=self.n_folds, shuffle=True, random_state=42)

        for train_idx, test_idx in kf.split(features):
            if len(np.unique(attempts[train_idx])) < 2:
                p_hat[test_idx] = np.mean(attempts)
                continue
            clf = LogisticRegression(max_iter=500, C=1.0)
            clf.fit(features[train_idx], attempts[train_idx].astype(int))
            p_hat[test_idx] = clf.predict_proba(features[test_idx])[:, 1]

        # Grouped isotonic calibration
        p_hat = grouped_isotonic_calibration(p_hat, attempts, group_ids)

        # Enforce overlap
        p_hat = np.maximum(p_hat, epsilon)

        return p_hat
