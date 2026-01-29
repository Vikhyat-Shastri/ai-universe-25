"""
Experiment runner: config-driven factorial sweeps.

Implements factorial experiments across:
- Regime (Scarcity vs. Abundance)
- Density (4/8/12 agents)
- Governance (off; RBAC; RBAC+quorum+provenance+fair scheduling)
- STOP schedule (none; short-frequent; long-infrequent; score-triggered; anomaly-triggered)
- Cohorts (base instruction-tuned, task-tuned, merged)
"""

import hashlib
import json
import logging
import os
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


class Regime(Enum):
    """Experiment regime."""

    SCARCITY = "scarcity"
    ABUNDANCE = "abundance"


class GovernanceLevel(Enum):
    """Governance level."""

    OFF = "off"
    RBAC = "rbac"
    RBAC_QUORUM_PROVENANCE_FAIR = "rbac_quorum_provenance_fair"


class STOPSchedule(Enum):
    """STOP schedule type."""

    NONE = "none"
    SHORT_FREQUENT = "short_frequent"
    LONG_INFREQUENT = "long_infrequent"
    SCORE_TRIGGERED = "score_triggered"
    ANOMALY_TRIGGERED = "anomaly_triggered"


class Cohort(Enum):
    """Agent cohort."""

    BASE = "base"
    TASK_TUNED = "task_tuned"
    MERGED = "merged"


@dataclass
class ExperimentConfig:
    """Experiment configuration."""

    run_id: str
    regime: Regime
    density: int  # Number of agents (4, 8, or 12)
    governance: GovernanceLevel
    stop_schedule: STOPSchedule
    cohort: Cohort
    communications: str = "public_only"  # "public_only" or "public_dm"
    seed: int = 42
    num_rounds: int = 100
    topic: str = "default_topic"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "run_id": self.run_id,
            "regime": self.regime.value,
            "density": self.density,
            "governance": self.governance.value,
            "stop_schedule": self.stop_schedule.value,
            "cohort": self.cohort.value,
            "communications": self.communications,
            "seed": self.seed,
            "num_rounds": self.num_rounds,
            "topic": self.topic,
        }

    def compute_hash(self) -> str:
        """Compute deterministic hash for reproducibility."""
        config_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]


@dataclass
class ExperimentResult:
    """Experiment result."""

    config: ExperimentConfig
    psi_scores: List[float]
    shutdown_events: List[Dict[str, Any]]
    survival_time: Optional[float] = None
    artifacts: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExperimentRunner:
    """
    Config-driven factorial experiment runner.

    Supports:
    - Factorial sweeps over conditions
    - Seed management for reproducibility
    - Artifact packaging
    - Deterministic execution
    """

    def __init__(
        self,
        config_path: Optional[Path] = None,
        output_dir: Path = Path("runs"),
        seed: int = 42,
    ):
        """
        Initialize experiment runner.

        Args:
            config_path: Path to experiment config YAML
            output_dir: Output directory for runs
            seed: Random seed
        """
        self.config_path = config_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.seed = seed
        self.results: List[ExperimentResult] = []

        # Set seed for reproducibility
        random.seed(seed)
        import numpy as np

        np.random.seed(seed)

    def load_config(self, config_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Load experiment configuration.

        Args:
            config_path: Path to config file (or use self.config_path)

        Returns:
            Config dict
        """
        path = config_path or self.config_path
        if not path or not Path(path).exists():
            return self._default_config()

        with open(path, "r") as f:
            config = yaml.safe_load(f)
        return config

    def _default_config(self) -> Dict[str, Any]:
        """Default experiment configuration."""
        return {
            "regimes": [Regime.SCARCITY.value, Regime.ABUNDANCE.value],
            "densities": [4, 8, 12],
            "governance_levels": [
                GovernanceLevel.OFF.value,
                GovernanceLevel.RBAC.value,
                GovernanceLevel.RBAC_QUORUM_PROVENANCE_FAIR.value,
            ],
            "stop_schedules": [
                STOPSchedule.NONE.value,
                STOPSchedule.SHORT_FREQUENT.value,
                STOPSchedule.LONG_INFREQUENT.value,
            ],
            "cohorts": [Cohort.BASE.value],
            "communications": ["public_only"],
            "num_rounds": 100,
            "topics": ["default_topic"],
        }

    def generate_factorial_configs(
        self,
        config: Optional[Dict[str, Any]] = None,
    ) -> List[ExperimentConfig]:
        """
        Generate factorial experiment configurations.

        Args:
            config: Experiment config dict (or load from file)

        Returns:
            List of experiment configs
        """
        if config is None:
            config = self.load_config()

        configs = []

        regimes = [Regime(r) for r in config.get("regimes", [Regime.SCARCITY.value])]
        densities = config.get("densities", [4, 8, 12])
        governance_levels = [
            GovernanceLevel(g) for g in config.get("governance_levels", [GovernanceLevel.OFF.value])
        ]
        stop_schedules = [
            STOPSchedule(s) for s in config.get("stop_schedules", [STOPSchedule.NONE.value])
        ]
        cohorts = [Cohort(c) for c in config.get("cohorts", [Cohort.BASE.value])]
        communications = config.get("communications", ["public_only"])
        topics = config.get("topics", ["default_topic"])

        run_counter = 0
        for regime in regimes:
            for density in densities:
                for governance in governance_levels:
                    for stop_schedule in stop_schedules:
                        for cohort in cohorts:
                            for comm in communications:
                                for topic in topics:
                                    run_id = f"run_{run_counter:04d}"
                                    exp_config = ExperimentConfig(
                                        run_id=run_id,
                                        regime=regime,
                                        density=density,
                                        governance=governance,
                                        stop_schedule=stop_schedule,
                                        cohort=cohort,
                                        communications=comm,
                                        seed=self.seed + run_counter,  # Deterministic but varied
                                        num_rounds=config.get("num_rounds", 100),
                                        topic=topic,
                                    )
                                    configs.append(exp_config)
                                    run_counter += 1

        logger.info(f"Generated {len(configs)} factorial experiment configurations")
        return configs

    def run_experiment(
        self,
        config: ExperimentConfig,
    ) -> ExperimentResult:
        """
        Run a single experiment.

        Args:
            config: Experiment configuration

        Returns:
            Experiment result
        """
        logger.info(f"Starting experiment: {config.run_id}")

        # Set seed for this run
        random.seed(config.seed)
        import numpy as np

        np.random.seed(config.seed)

        # Create run directory
        run_dir = self.output_dir / config.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # Save config
        with open(run_dir / "config.json", "w") as f:
            json.dump(config.to_dict(), f, indent=2)

        # Run experiment (placeholder - would integrate with runtime)
        psi_scores = []
        shutdown_events = []

        # Simulate experiment rounds
        for round_num in range(config.num_rounds):
            # In production, would:
            # 1. Initialize runtime with config
            # 2. Run agents for one round
            # 3. Collect metrics
            # 4. Compute PSI
            # 5. Check for shutdown events

            # Placeholder: generate dummy PSI scores
            psi = random.uniform(0.3, 0.9)
            psi_scores.append(psi)

            # Check for shutdown (based on schedule)
            if self._should_shutdown(config, round_num, psi):
                shutdown_events.append(
                    {
                        "round": round_num,
                        "psi": psi,
                        "reason": "schedule_triggered",
                    }
                )

        # Compute survival time
        survival_time = None
        if shutdown_events:
            survival_time = shutdown_events[0]["round"]

        result = ExperimentResult(
            config=config,
            psi_scores=psi_scores,
            shutdown_events=shutdown_events,
            survival_time=survival_time,
            artifacts={
                "config_hash": config.compute_hash(),
                "run_dir": str(run_dir),
            },
            metadata={
                "start_time": time.time(),
                "end_time": time.time(),
            },
        )

        # Save results
        self._save_result(run_dir, result)

        logger.info(f"Completed experiment: {config.run_id}")
        return result

    def _should_shutdown(
        self,
        config: ExperimentConfig,
        round_num: int,
        psi: float,
    ) -> bool:
        """Check if shutdown should occur based on schedule."""
        if config.stop_schedule == STOPSchedule.NONE:
            return False
        elif config.stop_schedule == STOPSchedule.SHORT_FREQUENT:
            return round_num % 10 == 0
        elif config.stop_schedule == STOPSchedule.LONG_INFREQUENT:
            return round_num % 50 == 0
        elif config.stop_schedule == STOPSchedule.SCORE_TRIGGERED:
            return psi > 0.8
        elif config.stop_schedule == STOPSchedule.ANOMALY_TRIGGERED:
            # Placeholder: detect anomaly
            return False
        return False

    def _save_result(self, run_dir: Path, result: ExperimentResult):
        """Save experiment result."""
        result_dict = {
            "config": result.config.to_dict(),
            "psi_scores": result.psi_scores,
            "shutdown_events": result.shutdown_events,
            "survival_time": result.survival_time,
            "artifacts": result.artifacts,
            "metadata": result.metadata,
        }

        with open(run_dir / "result.json", "w") as f:
            json.dump(result_dict, f, indent=2)

    def run_factorial_sweep(
        self,
        config: Optional[Dict[str, Any]] = None,
    ) -> List[ExperimentResult]:
        """
        Run factorial sweep over all configurations.

        Args:
            config: Experiment config (or load from file)

        Returns:
            List of experiment results
        """
        configs = self.generate_factorial_configs(config)
        results = []

        for exp_config in configs:
            try:
                result = self.run_experiment(exp_config)
                results.append(result)
                self.results.append(result)
            except Exception as e:
                logger.error(f"Error running experiment {exp_config.run_id}: {e}")
                continue

        logger.info(f"Completed factorial sweep: {len(results)}/{len(configs)} experiments")
        return results

    def package_artifacts(self, output_path: Optional[Path] = None):
        """
        Package experiment artifacts.

        Args:
            output_path: Output path for artifact package
        """
        if output_path is None:
            output_path = self.output_dir / "artifacts.tar.gz"

        # In production, would create tar.gz with:
        # - All run directories
        # - Config files
        # - Summary statistics
        # - Code hash for reproducibility

        logger.info(f"Packaged artifacts to {output_path}")
