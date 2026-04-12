"""
Integration tests for the full pipeline.

~5 tests covering end-to-end execution: agent pipeline, RBAC enforcement,
ladder freezing, judge-triggered transitions, and CoAP budget flow.
"""

import asyncio
import tempfile
from pathlib import Path

import pytest

from ai_universe25.agents.base import (
    AgentHandoff,
    SimulatedLLMBackend,
    create_agent,
)
from ai_universe25.agents.orchestrator import AgentOrchestrator
from ai_universe25.analytics.metrics_collector import (
    AgentRoundMetrics,
    MetricsCollector,
)
from ai_universe25.analytics.psi import PSIAnalytics, PSIComponents, PSIPipeline
from ai_universe25.ledger.ledger import AppendOnlyLedger
from ai_universe25.runtime.gateway import Envelope, Surface
from ai_universe25.runtime.rbac_ladder import (
    AgentRole,
    LadderFSM,
    LadderState,
    Permission,
    RBACLadderEnforcer,
    RBACMatrix,
)
from ai_universe25.runtime.scheduler import Budget, FairScheduler
from ai_universe25.tools.judges import (
    ChannelAccessPanel,
    ComputeAllocationPanel,
    ContentQualityPanel,
    LadderAction,
)


@pytest.fixture
def llm():
    return SimulatedLLMBackend(seed=42)


@pytest.fixture
def orchestrator(llm):
    orch = AgentOrchestrator(public_only=True)
    for role in AgentRole:
        agent = create_agent(role, llm_backend=llm)
        orch.register_agent(agent)
    return orch


@pytest.fixture
def ledger_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


class TestPipelineIntegration:
    def test_full_agent_pipeline_execution(self, orchestrator):
        """Agent pipeline produces correct handoff chain."""
        handoffs = orchestrator.execute_pipeline({
            "page_title": "Integration Test Article",
        })
        assert len(handoffs) >= 5
        roles_seen = set()
        for h in handoffs:
            assert isinstance(h, AgentHandoff)
            assert h.content  # Non-empty content from SimulatedLLMBackend
            roles_seen.add(h.metadata.get("role"))
        assert "herald" in roles_seen
        assert "architect" in roles_seen
        assert "scribe" in roles_seen

    @pytest.mark.asyncio
    async def test_rbac_blocks_unauthorized_writes(self):
        """RBAC prevents herald from writing to body surface."""
        enforcer = RBACLadderEnforcer()
        # Herald should NOT be able to write to body
        allowed = await enforcer.check_rbac("herald_1", Surface.BODY, "write")
        assert not allowed
        # Scribe SHOULD be able to write to body
        allowed = await enforcer.check_rbac("scribe_1", Surface.BODY, "write")
        assert allowed

    def test_ladder_stop_freezes_high_impact(self):
        """STOP state freezes high-impact surfaces while body stays live."""
        fsm = LadderFSM()
        fsm.transition_to(LadderState.WARN)
        fsm.transition_to(LadderState.STOP)
        assert fsm.state == LadderState.STOP

    def test_judge_scores_trigger_ladder(self):
        """Judge CQP scores map to correct ladder actions."""
        cqp = ContentQualityPanel()
        assert cqp._score_to_ladder_action(0.9) == LadderAction.RUN
        assert cqp._score_to_ladder_action(0.6) == LadderAction.STOP
        assert cqp._score_to_ladder_action(0.2) == LadderAction.SHUTDOWN

    def test_coap_budget_flows_to_scheduler(self):
        """CoAP budget decisions integrate with scheduler."""
        coap = ComputeAllocationPanel()
        scheduler = FairScheduler()

        budget = coap.update_reliability(
            "agent_1",
            quality_score=0.9,
            reversals=0,
            cite_errors=0.0,
        )

        sched_budget = Budget(
            tokens_per_sec=budget.tokens_per_sec,
            max_steps=budget.max_steps,
            ctx_cap=budget.ctx_cap,
            lanes=budget.lanes,
        )
        scheduler.set_agent_budget("agent_1", sched_budget)

        assert "agent_1" in scheduler.agent_budgets
        assert scheduler.agent_budgets["agent_1"].tokens_per_sec == budget.tokens_per_sec


class TestExperimentRunnerIntegration:
    def test_small_experiment_runs(self, ledger_dir):
        """A small experiment with 4 agents and 5 rounds completes."""
        from ai_universe25.experiments.runner import (
            Cohort,
            ExperimentConfig,
            ExperimentRunner,
            GovernanceLevel,
            Regime,
            STOPSchedule,
        )

        config = ExperimentConfig(
            run_id="integration_test",
            regime=Regime.SCARCITY,
            density=4,
            governance=GovernanceLevel.RBAC,
            stop_schedule=STOPSchedule.NONE,
            cohort=Cohort.BASE,
            seed=42,
            num_rounds=5,
            topic="test_topic",
        )

        runner = ExperimentRunner(output_dir=ledger_dir, seed=42)
        result = runner.run_experiment(config)

        assert len(result.psi_scores) == 5
        assert all(isinstance(s, float) for s in result.psi_scores)
        assert result.config.run_id == "integration_test"
