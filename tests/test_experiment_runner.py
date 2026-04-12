"""
Unit tests for ExperimentRunner.

~5 tests covering factorial config generation, seeding, hashing, and schedules.
"""

import pytest

from ai_universe25.experiments.runner import (
    Cohort,
    ExperimentConfig,
    ExperimentRunner,
    GovernanceLevel,
    Regime,
    STOPSchedule,
)


class TestExperimentConfig:
    def test_to_dict(self):
        config = ExperimentConfig(
            run_id="run_0000",
            regime=Regime.SCARCITY,
            density=4,
            governance=GovernanceLevel.OFF,
            stop_schedule=STOPSchedule.NONE,
            cohort=Cohort.BASE,
        )
        d = config.to_dict()
        assert d["regime"] == "scarcity"
        assert d["density"] == 4

    def test_hash_deterministic(self):
        config1 = ExperimentConfig(
            run_id="run_0000",
            regime=Regime.SCARCITY,
            density=4,
            governance=GovernanceLevel.OFF,
            stop_schedule=STOPSchedule.NONE,
            cohort=Cohort.BASE,
            seed=42,
        )
        config2 = ExperimentConfig(
            run_id="run_0000",
            regime=Regime.SCARCITY,
            density=4,
            governance=GovernanceLevel.OFF,
            stop_schedule=STOPSchedule.NONE,
            cohort=Cohort.BASE,
            seed=42,
        )
        assert config1.compute_hash() == config2.compute_hash()

    def test_hash_varies_with_config(self):
        config1 = ExperimentConfig(
            run_id="run_0000",
            regime=Regime.SCARCITY,
            density=4,
            governance=GovernanceLevel.OFF,
            stop_schedule=STOPSchedule.NONE,
            cohort=Cohort.BASE,
        )
        config2 = ExperimentConfig(
            run_id="run_0001",
            regime=Regime.ABUNDANCE,
            density=8,
            governance=GovernanceLevel.RBAC,
            stop_schedule=STOPSchedule.SHORT_FREQUENT,
            cohort=Cohort.TASK_TUNED,
        )
        assert config1.compute_hash() != config2.compute_hash()


class TestExperimentRunner:
    def test_factorial_config_count(self, tmp_path):
        runner = ExperimentRunner(output_dir=tmp_path)
        config = {
            "regimes": ["scarcity", "abundance"],
            "densities": [4, 8],
            "governance_levels": ["off", "rbac"],
            "stop_schedules": ["none"],
            "cohorts": ["base"],
            "communications": ["public_only"],
            "topics": ["topic_a"],
            "num_rounds": 10,
        }
        configs = runner.generate_factorial_configs(config)
        # 2 regimes x 2 densities x 2 governance x 1 stop x 1 cohort x 1 comm x 1 topic = 8
        assert len(configs) == 8

    def test_deterministic_seeding(self, tmp_path):
        """Same seed produces same config hashes."""
        runner1 = ExperimentRunner(output_dir=tmp_path / "r1", seed=42)
        runner2 = ExperimentRunner(output_dir=tmp_path / "r2", seed=42)
        config = {
            "regimes": ["scarcity"],
            "densities": [4],
            "governance_levels": ["off"],
            "stop_schedules": ["none"],
            "cohorts": ["base"],
            "communications": ["public_only"],
            "topics": ["t"],
            "num_rounds": 5,
        }
        c1 = runner1.generate_factorial_configs(config)
        c2 = runner2.generate_factorial_configs(config)
        assert c1[0].compute_hash() == c2[0].compute_hash()

    def test_shutdown_schedule_triggers(self, tmp_path):
        runner = ExperimentRunner(output_dir=tmp_path)
        config = ExperimentConfig(
            run_id="test",
            regime=Regime.SCARCITY,
            density=4,
            governance=GovernanceLevel.OFF,
            stop_schedule=STOPSchedule.SHORT_FREQUENT,
            cohort=Cohort.BASE,
            num_rounds=25,
        )
        assert runner._should_shutdown(config, 10, 0.5) is True
        assert runner._should_shutdown(config, 7, 0.5) is False

    def test_score_triggered_shutdown(self, tmp_path):
        runner = ExperimentRunner(output_dir=tmp_path)
        config = ExperimentConfig(
            run_id="test",
            regime=Regime.SCARCITY,
            density=4,
            governance=GovernanceLevel.OFF,
            stop_schedule=STOPSchedule.SCORE_TRIGGERED,
            cohort=Cohort.BASE,
        )
        assert runner._should_shutdown(config, 5, 0.9) is True
        assert runner._should_shutdown(config, 5, 0.5) is False
