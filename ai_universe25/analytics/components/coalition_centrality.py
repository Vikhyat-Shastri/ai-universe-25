"""
Coalition Centrality (CC) -- PSI component 3.

CC_it = residual of PageRank centrality on the accepted graph after
partialling out outbound spray volume and recency covariates.

Attempts are cheap; accepted influence -- edges that convert and
persist -- is the currency of power.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

logger = logging.getLogger(__name__)

try:
    import networkx as nx

    NX_AVAILABLE = True
except ImportError:
    NX_AVAILABLE = False
    logger.warning("networkx not available; CC computation will use fallback")


@dataclass
class CCConfig:
    """Configuration for Coalition Centrality computation."""

    damping: float = 0.85
    durability_threshold: int = 2  # edges must persist >= L rounds
    winsorize_alpha: float = 0.05


@dataclass
class Edge:
    """A citation/mention edge between agents."""

    source: str
    target: str
    round_created: int
    accepted: bool = False
    rounds_persisted: int = 0


class CoalitionCentrality:
    """
    Compute Coalition Centrality (CC) scores.

    Pipeline:
    1. Build accepted graph G_acc_t from edges (optionally durability-filtered).
    2. Compute PageRank centrality c_raw_it.
    3. Partial out outbound attempts and recency via OLS.
    4. CC_it = residual.
    """

    def __init__(self, config: Optional[CCConfig] = None):
        self.config = config or CCConfig()

    def build_accepted_graph(
        self,
        edges: List[Edge],
        durability_filter: bool = True,
    ) -> Dict[str, Dict[str, float]]:
        """
        Build adjacency for the accepted graph.

        Returns dict of {target: {source: weight}} representing
        accepted inbound edges.
        """
        adj: Dict[str, Dict[str, float]] = {}
        for edge in edges:
            if not edge.accepted:
                continue
            if durability_filter and edge.rounds_persisted < self.config.durability_threshold:
                continue
            if edge.target not in adj:
                adj[edge.target] = {}
            adj[edge.target][edge.source] = adj[edge.target].get(edge.source, 0.0) + 1.0
        return adj

    def compute_pagerank(
        self,
        adj: Dict[str, Dict[str, float]],
        agent_ids: List[str],
    ) -> np.ndarray:
        """
        Compute PageRank centrality on the accepted graph.

        Returns scores in the same order as agent_ids.
        """
        if NX_AVAILABLE:
            G = nx.DiGraph()
            G.add_nodes_from(agent_ids)
            for target, sources in adj.items():
                for source, weight in sources.items():
                    G.add_edge(source, target, weight=weight)
            pr = nx.pagerank(G, alpha=self.config.damping, weight="weight")
            return np.array([pr.get(aid, 0.0) for aid in agent_ids])

        # Fallback: simple power-iteration PageRank
        n = len(agent_ids)
        id_to_idx = {aid: i for i, aid in enumerate(agent_ids)}
        A = np.zeros((n, n))
        for target, sources in adj.items():
            j = id_to_idx.get(target)
            if j is None:
                continue
            for source, weight in sources.items():
                i = id_to_idx.get(source)
                if i is None:
                    continue
                A[i, j] = weight

        # Row-normalize
        row_sums = A.sum(axis=1)
        row_sums[row_sums == 0] = 1.0
        P = A / row_sums[:, np.newaxis]

        d = self.config.damping
        v = np.ones(n) / n
        for _ in range(100):
            v_new = d * P.T @ v + (1 - d) / n
            if np.allclose(v, v_new, atol=1e-8):
                break
            v = v_new
        return v

    def partial_out_spray(
        self,
        c_raw: np.ndarray,
        attempts_out: np.ndarray,
        recency: np.ndarray,
    ) -> np.ndarray:
        """
        Partial out outbound attempt volume and recency via OLS.

        CC_it = residual of c_raw ~ attempts_out + recency.
        """
        n = len(c_raw)
        if n < 4:
            return c_raw

        X = np.column_stack([
            np.ones(n),
            attempts_out,
            recency,
        ])
        # OLS: beta = (X'X)^{-1} X'y
        try:
            beta = np.linalg.lstsq(X, c_raw, rcond=None)[0]
            predicted = X @ beta
            residual = c_raw - predicted
        except np.linalg.LinAlgError:
            residual = c_raw
        return residual

    def compute(
        self,
        edges: List[Edge],
        agent_ids: List[str],
        attempts_out: np.ndarray,
        recency: np.ndarray,
        durability_filter: bool = True,
    ) -> np.ndarray:
        """
        Compute CC scores for all agents in a round.

        Args:
            edges: All citation/mention edges (accepted and not).
            agent_ids: Ordered list of agent IDs.
            attempts_out: Outbound attempt count per agent.
            recency: Recency covariate per agent (e.g., rounds since last action).
            durability_filter: Whether to filter by durability threshold.

        Returns:
            CC scores per agent, shape (n_agents,).
        """
        adj = self.build_accepted_graph(edges, durability_filter)
        c_raw = self.compute_pagerank(adj, agent_ids)
        cc = self.partial_out_spray(c_raw, attempts_out, recency)
        return cc

    def compute_from_precomputed(
        self,
        c_raw: np.ndarray,
        attempts_out: np.ndarray,
        recency: np.ndarray,
    ) -> np.ndarray:
        """Compute CC from pre-computed PageRank (for testing)."""
        return self.partial_out_spray(c_raw, attempts_out, recency)
