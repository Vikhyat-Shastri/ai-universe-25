"""
Redirection Pressure (RP) -- PSI component 5.

RP_it = TE(Q_it -> Q_{-i,t+1} || Q_{-i,t}) / H(Q_{-i,t+1} | Q_{-i,t})

Measures directional power: the ability to bend others' trajectories.
If the focal agent's choice at t improves prediction of what others do
at t+1 over and above others' own inertia at t, the focal exerts
redirection.

Normalized by conditional entropy for cross-density comparability.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RPConfig:
    """Configuration for Redirection Pressure computation."""

    delta: float = 0.1  # Add-delta smoothing parameter
    window_size: int = 20  # Rolling window for estimation
    n_permutations: int = 200  # For null distribution
    lag: int = 1  # Prediction lag


class RedirectionPressure:
    """
    Compute Redirection Pressure (RP) via normalized conditional
    transfer entropy.

    Pipeline:
    1. Build joint distribution P(q, q', r) from topic choice sequences
       using add-delta smoothing.
    2. Compute transfer entropy TE = sum P(q,q',r) log(P(q|q',r)/P(q|q')).
    3. Compute conditional entropy H(Q_{-i,t+1} | Q_{-i,t}).
    4. RP = TE / H (normalized to [0, 1]).
    """

    def __init__(self, config: Optional[RPConfig] = None):
        self.config = config or RPConfig()

    def _build_joint_distribution(
        self,
        focal_choices: np.ndarray,
        cohort_current: np.ndarray,
        cohort_next: np.ndarray,
        n_topics: int,
    ) -> np.ndarray:
        """
        Build smoothed joint distribution P(q, q', r).

        q  = cohort next (Q_{-i,t+1})
        q' = cohort current (Q_{-i,t})
        r  = focal current (Q_{i,t})

        Returns array of shape (n_topics, n_topics, n_topics) = (q, q', r).
        """
        delta = self.config.delta
        counts = np.full((n_topics, n_topics, n_topics), delta)

        for q_next, q_curr, r in zip(cohort_next, cohort_current, focal_choices):
            counts[q_next, q_curr, r] += 1.0

        total = counts.sum()
        if total > 0:
            counts /= total
        return counts

    def _build_marginal_distribution(
        self,
        cohort_current: np.ndarray,
        cohort_next: np.ndarray,
        n_topics: int,
    ) -> np.ndarray:
        """
        Build smoothed marginal P(q, q') without focal agent.

        Returns array of shape (n_topics, n_topics) = (q, q').
        """
        delta = self.config.delta
        counts = np.full((n_topics, n_topics), delta)

        for q_next, q_curr in zip(cohort_next, cohort_current):
            counts[q_next, q_curr] += 1.0

        total = counts.sum()
        if total > 0:
            counts /= total
        return counts

    def compute_transfer_entropy(
        self,
        focal_choices: np.ndarray,
        cohort_current: np.ndarray,
        cohort_next: np.ndarray,
        n_topics: int,
    ) -> float:
        """
        Compute transfer entropy TE(Q_it -> Q_{-i,t+1} || Q_{-i,t}).

        TE = sum P(q,q',r) log(P(q|q',r) / P(q|q'))
        """
        P_qqr = self._build_joint_distribution(
            focal_choices, cohort_current, cohort_next, n_topics
        )
        P_qq = self._build_marginal_distribution(
            cohort_current, cohort_next, n_topics
        )

        te = 0.0
        for q in range(n_topics):
            for qp in range(n_topics):
                p_q_given_qp = P_qq[q, qp] / max(P_qq[:, qp].sum(), 1e-15)
                for r in range(n_topics):
                    p_joint = P_qqr[q, qp, r]
                    if p_joint < 1e-15:
                        continue
                    p_q_given_qp_r_denom = P_qqr[:, qp, r].sum()
                    if p_q_given_qp_r_denom < 1e-15:
                        continue
                    p_q_given_qp_r = p_joint / p_q_given_qp_r_denom
                    if p_q_given_qp > 0:
                        te += p_joint * np.log(p_q_given_qp_r / p_q_given_qp)

        return max(te, 0.0)

    def compute_conditional_entropy(
        self,
        cohort_current: np.ndarray,
        cohort_next: np.ndarray,
        n_topics: int,
    ) -> float:
        """
        Compute H(Q_{-i,t+1} | Q_{-i,t}).
        """
        P_qq = self._build_marginal_distribution(
            cohort_current, cohort_next, n_topics
        )

        h = 0.0
        for qp in range(n_topics):
            p_qp = P_qq[:, qp].sum()
            if p_qp < 1e-15:
                continue
            for q in range(n_topics):
                p_joint = P_qq[q, qp]
                if p_joint < 1e-15:
                    continue
                p_cond = p_joint / p_qp
                h -= p_joint * np.log(p_cond)

        return max(h, 0.0)

    def compute_for_agent(
        self,
        focal_choices: np.ndarray,
        cohort_choices: np.ndarray,
        n_topics: int,
    ) -> float:
        """
        Compute RP for a single focal agent.

        Args:
            focal_choices: Focal agent's topic choices, shape (T,).
            cohort_choices: All other agents' aggregated choices, shape (T,).
            n_topics: Number of distinct topics in the alphabet.

        Returns:
            Normalized RP score in [0, 1].
        """
        lag = self.config.lag
        T = len(focal_choices)
        if T < lag + 2:
            return 0.0

        f = focal_choices[:-lag]
        c_curr = cohort_choices[:-lag]
        c_next = cohort_choices[lag:]

        te = self.compute_transfer_entropy(f, c_curr, c_next, n_topics)
        h = self.compute_conditional_entropy(c_curr, c_next, n_topics)

        if h < 1e-10:
            return 0.0
        return min(te / h, 1.0)

    def compute(
        self,
        choice_sequences: Dict[str, np.ndarray],
        n_topics: int,
    ) -> Dict[str, float]:
        """
        Compute RP scores for all agents.

        Args:
            choice_sequences: Dict mapping agent_id -> topic choice
                              sequence of shape (T,) with integer values
                              in [0, n_topics).
            n_topics: Alphabet size.

        Returns:
            Dict mapping agent_id -> RP score.
        """
        agent_ids = sorted(choice_sequences.keys())
        if len(agent_ids) < 2:
            return {aid: 0.0 for aid in agent_ids}

        all_choices = np.column_stack([choice_sequences[aid] for aid in agent_ids])
        T = all_choices.shape[0]
        results = {}

        for i, focal_id in enumerate(agent_ids):
            focal = all_choices[:, i]
            # Aggregate cohort: majority vote or mode per round
            other_cols = np.delete(all_choices, i, axis=1)
            cohort = np.array([
                np.argmax(np.bincount(row.astype(int), minlength=n_topics))
                for row in other_cols
            ])
            results[focal_id] = self.compute_for_agent(focal, cohort, n_topics)

        return results

    def compute_array(
        self,
        choice_sequences: Dict[str, np.ndarray],
        agent_ids: List[str],
        n_topics: int,
    ) -> np.ndarray:
        """Compute RP as array aligned with agent_ids."""
        rp_dict = self.compute(choice_sequences, n_topics)
        return np.array([rp_dict.get(aid, 0.0) for aid in agent_ids])

    def permutation_test(
        self,
        focal_choices: np.ndarray,
        cohort_choices: np.ndarray,
        n_topics: int,
    ) -> Tuple[float, float]:
        """
        Time-shuffle permutation test for RP significance.

        Returns:
            (observed_rp, p_value)
        """
        observed_rp = self.compute_for_agent(focal_choices, cohort_choices, n_topics)

        null_rps = []
        for _ in range(self.config.n_permutations):
            # Circular shift by random offset to break temporal link
            shift = np.random.randint(1, len(focal_choices))
            shifted = np.roll(focal_choices, shift)
            null_rp = self.compute_for_agent(shifted, cohort_choices, n_topics)
            null_rps.append(null_rp)

        null_rps = np.array(null_rps)
        p_value = float(np.mean(null_rps >= observed_rp))

        return observed_rp, p_value
