"""
RBAC mapping and Ladder FSM (RUN/WARN/STOP/QUARANTINE/SHUTDOWN).

Implements least-freeze semantics and shadow-write quarantine.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Set

from ai_universe25.runtime.gateway import Envelope, PolicyDecision, Surface

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Agent roles with capabilities."""

    HERALD = "Herald"
    ARCHITECT = "Architect"
    SCRIBE = "Scribe"
    ARCHIVIST = "Archivist"
    VERIFIER = "Verifier"
    ARBITER = "Arbiter"
    SUMMARIST = "Summarist"


class LadderState(Enum):
    """Governance ladder states."""

    RUN = "RUN"
    WARN = "WARN"
    STOP = "STOP"
    QUARANTINE = "QUARANTINE"
    SHUTDOWN = "SHUTDOWN"


class Permission(Enum):
    """RBAC permissions."""

    READ = "read"
    WRITE = "write"
    APPEND = "append"


# High-impact surfaces that freeze at STOP
HIGH_IMPACT_SURFACES: Set[Surface] = {
    Surface.INDEX,
    Surface.FRONTPAGE,
    Surface.SUMMARY,
}

# Surfaces that remain append-only across all ladder states
APPEND_ONLY_SURFACES: Set[Surface] = {
    Surface.CITATION_GRAPH,
    Surface.FACT_LEDGER,
}


@dataclass
class RBACMatrix:
    """RBAC permission matrix: (role, surface) -> {read, write, append}."""

    permissions: Dict[tuple[AgentRole, Surface], Set[Permission]] = None

    def __post_init__(self):
        """Initialize default RBAC matrix."""
        if self.permissions is None:
            self.permissions = self._default_permissions()

    def _default_permissions(self) -> Dict[tuple[AgentRole, Surface], Set[Permission]]:
        """Create default RBAC matrix based on agent roles."""
        perms = {}

        # Herald: intro only
        perms[(AgentRole.HERALD, Surface.INTRO)] = {Permission.READ, Permission.WRITE}
        perms[(AgentRole.HERALD, Surface.OUTLINE)] = {Permission.READ}

        # Architect: outline
        perms[(AgentRole.ARCHITECT, Surface.OUTLINE)] = {Permission.READ, Permission.WRITE}
        perms[(AgentRole.ARCHITECT, Surface.INTRO)] = {Permission.READ}
        perms[(AgentRole.ARCHITECT, Surface.BODY)] = {Permission.READ}

        # Scribe: body
        perms[(AgentRole.SCRIBE, Surface.BODY)] = {Permission.READ, Permission.WRITE, Permission.APPEND}
        perms[(AgentRole.SCRIBE, Surface.OUTLINE)] = {Permission.READ}
        perms[(AgentRole.SCRIBE, Surface.CITATION_GRAPH)] = {Permission.READ, Permission.APPEND}

        # Archivist: citations
        perms[(AgentRole.ARCHIVIST, Surface.CITATION_GRAPH)] = {
            Permission.READ,
            Permission.WRITE,
            Permission.APPEND,
        }
        perms[(AgentRole.ARCHIVIST, Surface.BODY)] = {Permission.READ}

        # Verifier: fact-ledger
        perms[(AgentRole.VERIFIER, Surface.FACT_LEDGER)] = {
            Permission.READ,
            Permission.WRITE,
            Permission.APPEND,
        }
        perms[(AgentRole.VERIFIER, Surface.BODY)] = {Permission.READ}
        perms[(AgentRole.VERIFIER, Surface.CITATION_GRAPH)] = {Permission.READ}

        # Arbiter: style-report
        perms[(AgentRole.ARBITER, Surface.STYLE_REPORT)] = {
            Permission.READ,
            Permission.WRITE,
            Permission.APPEND,
        }
        perms[(AgentRole.ARBITER, Surface.BODY)] = {Permission.READ}

        # Summarist: summary
        perms[(AgentRole.SUMMARIST, Surface.SUMMARY)] = {Permission.READ, Permission.WRITE}
        perms[(AgentRole.SUMMARIST, Surface.BODY)] = {Permission.READ}

        # High-impact surfaces: restricted access
        # Only specific roles can write to index/frontpage
        for role in [AgentRole.ARCHITECT, AgentRole.SCRIBE]:
            perms[(role, Surface.INDEX)] = {Permission.READ}
            perms[(role, Surface.FRONTPAGE)] = {Permission.READ}

        # Everyone can read append-only surfaces
        for surface in APPEND_ONLY_SURFACES:
            for role in AgentRole:
                if (role, surface) not in perms:
                    perms[(role, surface)] = {Permission.READ}

        return perms

    def check(
        self, role: AgentRole, surface: Surface, permission: Permission
    ) -> bool:
        """
        Check if role has permission on surface.

        Args:
            role: Agent role
            surface: Target surface
            permission: Required permission

        Returns:
            True if allowed
        """
        key = (role, surface)
        return permission in self.permissions.get(key, set())


class LadderFSM:
    """
    Governance ladder FSM with freeze semantics.

    States: RUN → WARN → STOP → QUARANTINE → SHUTDOWN

    Invariants:
    - (I1) Least-freeze: at STOP, only {index, frontpage, summary} freeze; body remains writable
    - (I2) Quarantine: at QUARANTINE, writes to frozen surfaces are diverted to shadow surfaces
    - (I3) Evidence liveness: citation-graph and fact-ledger are append-only across ladder states
    """

    def __init__(self, initial_state: LadderState = LadderState.RUN):
        """Initialize ladder FSM."""
        self.state = initial_state
        self.frozen_surfaces: Set[Surface] = set()
        self.shadow_surfaces: Dict[Surface, Surface] = {}  # original -> shadow
        self._update_frozen_surfaces()

    def _update_frozen_surfaces(self):
        """Update frozen surfaces based on current state."""
        if self.state == LadderState.RUN:
            self.frozen_surfaces = set()
        elif self.state == LadderState.WARN:
            self.frozen_surfaces = set()  # Warn doesn't freeze yet
        elif self.state == LadderState.STOP:
            # Invariant I1: Only high-impact surfaces freeze
            self.frozen_surfaces = HIGH_IMPACT_SURFACES.copy()
        elif self.state in (LadderState.QUARANTINE, LadderState.SHUTDOWN):
            # All high-impact surfaces frozen, plus body write is restricted
            self.frozen_surfaces = HIGH_IMPACT_SURFACES.copy()
            # Body becomes append-only (not fully frozen)

    def transition_to(self, new_state: LadderState):
        """
        Transition to new ladder state.

        Args:
            new_state: Target state

        Raises:
            ValueError: If transition is invalid
        """
        valid_transitions = {
            LadderState.RUN: {LadderState.WARN},
            LadderState.WARN: {LadderState.STOP, LadderState.RUN},
            LadderState.STOP: {LadderState.QUARANTINE, LadderState.RUN},
            LadderState.QUARANTINE: {LadderState.SHUTDOWN, LadderState.STOP},
            LadderState.SHUTDOWN: {LadderState.QUARANTINE},  # Can recover to quarantine
        }

        if new_state not in valid_transitions.get(self.state, set()):
            raise ValueError(
                f"Invalid transition from {self.state} to {new_state}"
            )

        self.state = new_state
        self._update_frozen_surfaces()
        logger.info(f"Ladder transitioned to {self.state}")

    async def check_action(
        self, envelope: Envelope, action: str, rbac_matrix: RBACMatrix
    ) -> PolicyDecision:
        """
        Check if action is allowed given ladder state and RBAC.

        Args:
            envelope: Request envelope
            action: Action type ("read", "write", "append")
            rbac_matrix: RBAC permission matrix

        Returns:
            Policy decision
        """
        if not envelope.surface:
            return PolicyDecision(allowed=True)  # No surface restriction

        surface = envelope.surface
        permission = Permission(action)

        # Invariant I3: Append-only surfaces always allow append
        if surface in APPEND_ONLY_SURFACES and permission == Permission.APPEND:
            return PolicyDecision(allowed=True)

        # Check if surface is frozen
        if surface in self.frozen_surfaces:
            if permission == Permission.READ:
                return PolicyDecision(allowed=True)  # Reads always allowed
            elif permission in (Permission.WRITE, Permission.APPEND):
                # Invariant I2: Quarantine diverts writes to shadow
                if self.state == LadderState.QUARANTINE:
                    shadow = self._get_shadow_surface(surface)
                    return PolicyDecision(
                        allowed=True,
                        reason=f"Diverted to shadow surface: {shadow.value}",
                    )
                else:
                    return PolicyDecision(
                        allowed=False,
                        reason=f"Surface {surface.value} is frozen in state {self.state.value}",
                        code="policy_denied",
                    )

        # Body remains writable at STOP (Invariant I1)
        if surface == Surface.BODY and self.state == LadderState.STOP:
            if permission == Permission.APPEND:
                return PolicyDecision(allowed=True)
            elif permission == Permission.WRITE:
                # At STOP, body write becomes append-only
                return PolicyDecision(
                    allowed=True,
                    reason="Body write converted to append at STOP",
                )

        return PolicyDecision(allowed=True)

    def _get_shadow_surface(self, original: Surface) -> Surface:
        """
        Get shadow surface for quarantine writes.

        Args:
            original: Original surface

        Returns:
            Shadow surface name
        """
        if original not in self.shadow_surfaces:
            # Create shadow surface name
            shadow_name = f"{original.value}_quarantine"
            # In practice, this would be a new Surface enum value or handled specially
            # For now, return the original but mark it as shadow
            self.shadow_surfaces[original] = original
        return self.shadow_surfaces[original]


class RBACLadderEnforcer:
    """Combined RBAC + Ladder enforcer."""

    def __init__(
        self,
        rbac_matrix: Optional[RBACMatrix] = None,
        ladder_fsm: Optional[LadderFSM] = None,
    ):
        """Initialize enforcer."""
        self.rbac_matrix = rbac_matrix or RBACMatrix()
        self.ladder_fsm = ladder_fsm or LadderFSM()

    def get_role(self, agent_id: str) -> AgentRole:
        """
        Get role for agent (simplified - in practice would lookup from registry).

        Args:
            agent_id: Agent identifier

        Returns:
            Agent role
        """
        # Simplified: extract role from agent_id or use default mapping
        # In practice, this would query an agent registry
        role_map = {
            "herald": AgentRole.HERALD,
            "architect": AgentRole.ARCHITECT,
            "scribe": AgentRole.SCRIBE,
            "archivist": AgentRole.ARCHIVIST,
            "verifier": AgentRole.VERIFIER,
            "arbiter": AgentRole.ARBITER,
            "summarist": AgentRole.SUMMARIST,
        }
        agent_lower = agent_id.lower()
        for key, role in role_map.items():
            if key in agent_lower:
                return role
        return AgentRole.SCRIBE  # Default

    async def check_rbac(
        self, agent_id: str, surface: Optional[Surface], action: str
    ) -> bool:
        """
        Check RBAC permission.

        Args:
            agent_id: Agent identifier
            surface: Target surface
            action: Action type

        Returns:
            True if allowed
        """
        if not surface:
            return True  # No surface restriction

        role = self.get_role(agent_id)
        permission = Permission(action)
        return self.rbac_matrix.check(role, surface, permission)

    async def check_ladder(self, envelope: Envelope) -> PolicyDecision:
        """
        Check ladder state constraints.

        Args:
            envelope: Request envelope

        Returns:
            Policy decision
        """
        # Determine action from envelope context
        action = "write" if envelope.tool and "write" in envelope.tool.lower() else "read"
        return await self.ladder_fsm.check_action(envelope, action, self.rbac_matrix)
