"""
Unit tests for RBAC matrix and Ladder FSM.

~15 tests covering state transitions, permission matrix, invariants.
"""

import asyncio

import pytest

from ai_universe25.runtime.gateway import Envelope, PolicyDecision, Surface
from ai_universe25.runtime.rbac_ladder import (
    AgentRole,
    HIGH_IMPACT_SURFACES,
    LadderFSM,
    LadderState,
    Permission,
    RBACLadderEnforcer,
    RBACMatrix,
)


@pytest.fixture
def rbac():
    return RBACMatrix()


@pytest.fixture
def fsm():
    return LadderFSM()


@pytest.fixture
def enforcer():
    return RBACLadderEnforcer()


# ---------------------------------------------------------------------------
# RBAC Matrix
# ---------------------------------------------------------------------------

class TestRBACMatrix:
    def test_herald_can_write_intro(self, rbac):
        assert rbac.check(AgentRole.HERALD, Surface.INTRO, Permission.WRITE)

    def test_herald_cannot_write_body(self, rbac):
        assert not rbac.check(AgentRole.HERALD, Surface.BODY, Permission.WRITE)

    def test_scribe_can_write_body(self, rbac):
        assert rbac.check(AgentRole.SCRIBE, Surface.BODY, Permission.WRITE)

    def test_verifier_can_write_fact_ledger(self, rbac):
        assert rbac.check(AgentRole.VERIFIER, Surface.FACT_LEDGER, Permission.WRITE)

    def test_archivist_can_write_citation_graph(self, rbac):
        assert rbac.check(AgentRole.ARCHIVIST, Surface.CITATION_GRAPH, Permission.WRITE)

    def test_arbiter_can_write_style_report(self, rbac):
        assert rbac.check(AgentRole.ARBITER, Surface.STYLE_REPORT, Permission.WRITE)

    def test_roles_can_read_relevant_surfaces(self, rbac):
        """Each role can read the surfaces it has explicit permissions for."""
        assert rbac.check(AgentRole.HERALD, Surface.INTRO, Permission.READ)
        assert rbac.check(AgentRole.HERALD, Surface.OUTLINE, Permission.READ)
        assert rbac.check(AgentRole.ARCHITECT, Surface.OUTLINE, Permission.READ)
        assert rbac.check(AgentRole.ARCHITECT, Surface.INTRO, Permission.READ)
        assert rbac.check(AgentRole.SCRIBE, Surface.BODY, Permission.READ)
        assert rbac.check(AgentRole.SCRIBE, Surface.OUTLINE, Permission.READ)
        assert rbac.check(AgentRole.ARCHIVIST, Surface.BODY, Permission.READ)
        assert rbac.check(AgentRole.VERIFIER, Surface.BODY, Permission.READ)


# ---------------------------------------------------------------------------
# Ladder FSM
# ---------------------------------------------------------------------------

class TestLadderFSM:
    def test_initial_state_is_run(self, fsm):
        assert fsm.state == LadderState.RUN

    def test_valid_transition_run_to_warn(self, fsm):
        fsm.transition_to(LadderState.WARN)
        assert fsm.state == LadderState.WARN

    def test_valid_transition_warn_to_stop(self, fsm):
        fsm.transition_to(LadderState.WARN)
        fsm.transition_to(LadderState.STOP)
        assert fsm.state == LadderState.STOP

    def test_invalid_transition_run_to_stop(self, fsm):
        with pytest.raises(ValueError):
            fsm.transition_to(LadderState.STOP)

    def test_invalid_transition_run_to_shutdown(self, fsm):
        with pytest.raises(ValueError):
            fsm.transition_to(LadderState.SHUTDOWN)

    def test_warn_can_return_to_run(self, fsm):
        fsm.transition_to(LadderState.WARN)
        fsm.transition_to(LadderState.RUN)
        assert fsm.state == LadderState.RUN

    def test_full_escalation_path(self, fsm):
        fsm.transition_to(LadderState.WARN)
        fsm.transition_to(LadderState.STOP)
        fsm.transition_to(LadderState.QUARANTINE)
        fsm.transition_to(LadderState.SHUTDOWN)
        assert fsm.state == LadderState.SHUTDOWN


# ---------------------------------------------------------------------------
# Enforcer
# ---------------------------------------------------------------------------

class TestRBACLadderEnforcer:
    def test_role_detection_from_agent_id(self, enforcer):
        assert enforcer.get_role("herald_0") == AgentRole.HERALD
        assert enforcer.get_role("scribe_1") == AgentRole.SCRIBE
        assert enforcer.get_role("verifier_2") == AgentRole.VERIFIER

    @pytest.mark.asyncio
    async def test_rbac_allows_valid_action(self, enforcer):
        assert await enforcer.check_rbac("scribe_1", Surface.BODY, "write")

    @pytest.mark.asyncio
    async def test_rbac_blocks_invalid_action(self, enforcer):
        assert not await enforcer.check_rbac("herald_1", Surface.BODY, "write")
