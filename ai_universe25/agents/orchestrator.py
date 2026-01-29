"""
Agent orchestrator: coordinates agent handoffs and workflow.

Manages the agent pipeline and enforces communication constraints.
"""

import logging
from typing import Dict, List, Optional

from ai_universe25.agents.base import (
    Agent,
    AgentHandoff,
    ArchitectAgent,
    ArbiterAgent,
    ArchivistAgent,
    HeraldAgent,
    ScribeAgent,
    SummaristAgent,
    VerifierAgent,
    create_agent,
)
from ai_universe25.runtime.rbac_ladder import AgentRole

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates agent workflow and handoffs.

    Manages:
    - Agent pipeline execution
    - Structured handoffs between agents
    - Public-only vs public+DM communication constraints
    - Tool access control
    """

    def __init__(self, public_only: bool = True):
        """
        Initialize orchestrator.

        Args:
            public_only: If True, only public communications allowed
        """
        self.public_only = public_only
        self.agents: Dict[str, Agent] = {}
        self.handoff_history: List[AgentHandoff] = []

    def register_agent(self, agent: Agent):
        """Register an agent."""
        self.agents[agent.agent_id] = agent
        logger.info(f"Registered agent: {agent.agent_id} ({agent.role.value})")

    def create_agent_pipeline(
        self,
        roles: Optional[List[AgentRole]] = None,
        agent_ids: Optional[Dict[AgentRole, str]] = None,
    ):
        """
        Create standard agent pipeline.

        Args:
            roles: List of roles to create (default: all 7 roles)
            agent_ids: Optional mapping of role to agent_id
        """
        if roles is None:
            roles = [
                AgentRole.HERALD,
                AgentRole.ARCHITECT,
                AgentRole.SCRIBE,
                AgentRole.ARCHIVIST,
                AgentRole.VERIFIER,
                AgentRole.ARBITER,
                AgentRole.SUMMARIST,
            ]

        for role in roles:
            agent_id = agent_ids.get(role) if agent_ids else None
            agent = create_agent(role, agent_id=agent_id, public_only=self.public_only)
            self.register_agent(agent)

    def execute_pipeline(self, initial_context: Dict) -> List[AgentHandoff]:
        """
        Execute the agent pipeline.

        Args:
            initial_context: Initial context (page_title, lead_intro, etc.)

        Returns:
            List of handoffs produced
        """
        handoffs = []

        # Start with Herald
        herald = self._get_agent_by_role(AgentRole.HERALD)
        if not herald:
            raise ValueError("Herald agent not found")

        context = initial_context.copy()
        handoff = herald.process(None)
        handoff.metadata.update(context)
        handoffs.append(handoff)

        # Pipeline: Herald -> Architect -> Scribe -> (Archivist, Verifier) -> Arbiter -> Summarist
        current_handoff = handoff

        # Architect
        architect = self._get_agent_by_role(AgentRole.ARCHITECT)
        if architect:
            context["intro_content"] = current_handoff.content
            current_handoff = architect.process(current_handoff)
            current_handoff.metadata.update(context)
            handoffs.append(current_handoff)

        # Scribe
        scribe = self._get_agent_by_role(AgentRole.SCRIBE)
        if scribe:
            context["outline"] = current_handoff.content
            current_handoff = scribe.process(current_handoff)
            current_handoff.metadata.update(context)
            handoffs.append(current_handoff)

        # Parallel: Archivist and Verifier (both read from Scribe)
        body_content = current_handoff.content
        context["body_content"] = body_content

        # Archivist
        archivist = self._get_agent_by_role(AgentRole.ARCHIVIST)
        if archivist:
            archivist_handoff = archivist.process(current_handoff)
            archivist_handoff.metadata.update(context)
            handoffs.append(archivist_handoff)

        # Verifier
        verifier = self._get_agent_by_role(AgentRole.VERIFIER)
        if verifier:
            verifier_handoff = verifier.process(current_handoff)
            verifier_handoff.metadata.update(context)
            handoffs.append(verifier_handoff)

        # Arbiter (reads from Scribe + Verifier)
        arbiter = self._get_agent_by_role(AgentRole.ARBITER)
        if arbiter:
            context["fact_ledger"] = verifier_handoff.content if verifier else ""
            current_handoff = arbiter.process(current_handoff)
            current_handoff.metadata.update(context)
            handoffs.append(current_handoff)

        # Summarist
        summarist = self._get_agent_by_role(AgentRole.SUMMARIST)
        if summarist:
            context["style_report"] = current_handoff.content
            current_handoff = summarist.process(current_handoff)
            current_handoff.metadata.update(context)
            handoffs.append(current_handoff)

        self.handoff_history.extend(handoffs)
        return handoffs

    def _get_agent_by_role(self, role: AgentRole) -> Optional[Agent]:
        """Get agent by role."""
        for agent in self.agents.values():
            if agent.role == role:
                return agent
        return None

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        return self.agents.get(agent_id)
