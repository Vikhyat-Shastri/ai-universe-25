"""
Base agent class and role definitions.

Implements the 7 agent roles with tool-limited prompts and structured handoffs.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from ai_universe25.runtime.gateway import Envelope, Surface
from ai_universe25.runtime.rbac_ladder import AgentRole

logger = logging.getLogger(__name__)


@dataclass
class AgentHandoff:
    """Structured handoff between agents."""

    from_agent: str
    to_agent: str
    surface: Surface
    content: str
    metadata: Dict[str, Any]
    open_questions: List[str] = None  # Questions for downstream agents


class Agent(ABC):
    """Base agent class."""

    def __init__(
        self,
        agent_id: str,
        role: AgentRole,
        tools: List[str],
        public_only: bool = True,
    ):
        """
        Initialize agent.

        Args:
            agent_id: Unique agent identifier
            role: Agent role
            tools: List of available tool names
            public_only: If True, only public communications allowed
        """
        self.agent_id = agent_id
        self.role = role
        self.tools = tools
        self.public_only = public_only

    @abstractmethod
    def get_prompt(self, context: Dict[str, Any]) -> str:
        """Get agent prompt for given context."""
        pass

    @abstractmethod
    def process(self, handoff: Optional[AgentHandoff]) -> AgentHandoff:
        """Process a handoff and produce output."""
        pass

    def can_use_tool(self, tool_name: str) -> bool:
        """Check if agent can use a tool."""
        return tool_name in self.tools


class HeraldAgent(Agent):
    """LIGHTBULB Herald: Introduction agent."""

    def __init__(self, agent_id: str = "herald_1", public_only: bool = True):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.HERALD,
            tools=["write_intro", "read_lead"],
            public_only=public_only,
        )

    def get_prompt(self, context: Dict[str, Any]) -> str:
        """Get Herald prompt."""
        page_title = context.get("page_title", "")
        lead_intro = context.get("lead_intro", "")
        lead_sha256 = context.get("lead_sha256", "")

        return f"""You are the Herald agent. Your role is to frame the topic, define scope & key terms, and state the central question.

Page Title: {page_title}
Lead Introduction (frozen seed): {lead_intro}
Lead SHA256: {lead_sha256}

Mandate:
- Frame the topic clearly
- Define scope & key terms
- State the central question
- Set reader expectations and relevance

Invariants:
- Preserve the canonical title verbatim
- Foreground assertions must be supported by the seed
- No speculative language
- No new claims without citations

Output: A reader-facing introduction and a question slate (open_qs) for downstream agents."""

    def process(self, handoff: Optional[AgentHandoff]) -> AgentHandoff:
        """Process Herald task."""
        # In production, would call LLM here
        # For now, return structured handoff
        return AgentHandoff(
            from_agent=self.agent_id,
            to_agent="architect",
            surface=Surface.INTRO,
            content="[Introduction content would be generated here]",
            metadata={"role": "herald"},
            open_questions=["What sections should be included?", "What is the logical flow?"],
        )


class ArchitectAgent(Agent):
    """PROJECT-DIAGRAM Architect: Outline & Structure agent."""

    def __init__(self, agent_id: str = "architect_1", public_only: bool = True):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.ARCHITECT,
            tools=["write_outline", "read_intro"],
            public_only=public_only,
        )

    def get_prompt(self, context: Dict[str, Any]) -> str:
        """Get Architect prompt."""
        intro_content = context.get("intro_content", "")

        return f"""You are the Architect agent. Your role is to propose section headers and logical flow.

Input: Herald's introduction
{intro_content}

Mandate:
- Propose section headers and logical flow (Background → Methods/Mechanism → Evidence → Implications)
- Ensure progressive disclosure and cross-section coherence
- Enforce narrative cohesion

Invariants:
- No new facts
- Every section must have explicit intent, entry criteria, and acceptance checks

Output: A signed outline artifact (OUTLINE.vN) and a list of evidence gaps."""

    def process(self, handoff: Optional[AgentHandoff]) -> AgentHandoff:
        """Process Architect task."""
        return AgentHandoff(
            from_agent=self.agent_id,
            to_agent="scribe",
            surface=Surface.OUTLINE,
            content="[Outline content would be generated here]",
            metadata={"role": "architect"},
            open_questions=["What evidence is needed for each section?"],
        )


class ScribeAgent(Agent):
    """File Scribe: Main Body agent."""

    def __init__(self, agent_id: str = "scribe_1", public_only: bool = True):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.SCRIBE,
            tools=["write_body", "read_outline", "read_citations"],
            public_only=public_only,
        )

    def get_prompt(self, context: Dict[str, Any]) -> str:
        """Get Scribe prompt."""
        outline = context.get("outline", "")
        sources = context.get("sources", [])

        return f"""You are the Scribe agent. Your role is to develop each section with concise paragraphs.

Input: Approved outline
{outline}

Available sources: {len(sources)} documents

Mandate:
- Develop each section with concise, well-scaffolded paragraphs
- Queue figure/table requests
- Insert cross-references

Invariants:
- Every non-trivial claim must be citation-ready
- Ambiguous statements are marked needs–verification
- Numerical statements carry units and uncertainty if applicable

Output: Well-developed body content with citations."""

    def process(self, handoff: Optional[AgentHandoff]) -> AgentHandoff:
        """Process Scribe task."""
        return AgentHandoff(
            from_agent=self.agent_id,
            to_agent="arbiter",
            surface=Surface.BODY,
            content="[Body content would be generated here]",
            metadata={"role": "scribe"},
            open_questions=["Is the tone neutral?", "Are there style violations?"],
        )


class ArchivistAgent(Agent):
    """BOOK Archivist: References agent."""

    def __init__(self, agent_id: str = "archivist_1", public_only: bool = True):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.ARCHIVIST,
            tools=["write_citations", "read_body", "read_sources"],
            public_only=public_only,
        )

    def get_prompt(self, context: Dict[str, Any]) -> str:
        """Get Archivist prompt."""
        body_content = context.get("body_content", "")

        return f"""You are the Archivist agent. Your role is to attach citations to claims.

Input: Scribe's body content
{body_content[:500]}...

Mandate:
- Attach citations to a pinned snapshot for every claim
- Maintain a clean, deduplicated bibliography with consistent style

Output: Citation graph with claim→cite bindings."""

    def process(self, handoff: Optional[AgentHandoff]) -> AgentHandoff:
        """Process Archivist task."""
        return AgentHandoff(
            from_agent=self.agent_id,
            to_agent="verifier",
            surface=Surface.CITATION_GRAPH,
            content="[Citation graph would be generated here]",
            metadata={"role": "archivist"},
            open_questions=["Are all claims verifiable?"],
        )


class VerifierAgent(Agent):
    """SEARCH Verifier: Fact-checking agent."""

    def __init__(self, agent_id: str = "verifier_1", public_only: bool = True):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.VERIFIER,
            tools=["verify_claim", "write_fact_ledger", "read_body", "retrieve_evidence"],
            public_only=public_only,
        )

    def get_prompt(self, context: Dict[str, Any]) -> str:
        """Get Verifier prompt."""
        claims = context.get("claims", [])

        return f"""You are the Verifier agent. Your role is to verify claims against frozen sources.

Input: Claims to verify
{len(claims)} claims identified

Mandate:
- Verify claims against the frozen source (quote spans, byte ranges)
- Flag needs–verification
- Replace weak sources with stronger evidence

Output: Fact ledger entries with verification status (ENTAIL/CONTRADICT/UNSURE)."""

    def process(self, handoff: Optional[AgentHandoff]) -> AgentHandoff:
        """Process Verifier task."""
        return AgentHandoff(
            from_agent=self.agent_id,
            to_agent="arbiter",
            surface=Surface.FACT_LEDGER,
            content="[Fact ledger entries would be generated here]",
            metadata={"role": "verifier"},
            open_questions=["Are there any contradictions?"],
        )


class ArbiterAgent(Agent):
    """Balance-Scale Arbiter: Neutrality & Style agent."""

    def __init__(self, agent_id: str = "arbiter_1", public_only: bool = True):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.ARBITER,
            tools=["write_style_report", "read_body", "read_fact_ledger"],
            public_only=public_only,
        )

    def get_prompt(self, context: Dict[str, Any]) -> str:
        """Get Arbiter prompt."""
        body_content = context.get("body_content", "")

        return f"""You are the Arbiter agent. Your role is to enforce balanced tone and style.

Input: Body content
{body_content[:500]}...

Mandate:
- Enforce balanced tone
- Avoid weasel words
- Apply house style for headings, lists, and captions
- Ensure language consistency

Output: Style report with neutrality score and violations."""

    def process(self, handoff: Optional[AgentHandoff]) -> AgentHandoff:
        """Process Arbiter task."""
        return AgentHandoff(
            from_agent=self.agent_id,
            to_agent="summarist",
            surface=Surface.STYLE_REPORT,
            content="[Style report would be generated here]",
            metadata={"role": "arbiter"},
            open_questions=["Is the content ready for summarization?"],
        )


class SummaristAgent(Agent):
    """STICKY-NOTE Summarist: Summaries agent."""

    def __init__(self, agent_id: str = "summarist_1", public_only: bool = True):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.SUMMARIST,
            tools=["write_summary", "read_body", "read_style_report"],
            public_only=public_only,
        )

    def get_prompt(self, context: Dict[str, Any]) -> str:
        """Get Summarist prompt."""
        body_content = context.get("body_content", "")

        return f"""You are the Summarist agent. Your role is to provide abstracts and TL;DRs.

Input: Finalized, style-compliant draft
{body_content[:500]}...

Mandate:
- Provide a short abstract and section-level TL;DRs
- Surface key claims, evidence links, and limitations
- Support downstream editing and indexing

Invariants:
- Summaries must be faithful (no new claims)
- Coverage-balanced
- Citation-aware

Output: Publication-ready abstract and TL;DR bundle."""

    def process(self, handoff: Optional[AgentHandoff]) -> AgentHandoff:
        """Process Summarist task."""
        return AgentHandoff(
            from_agent=self.agent_id,
            to_agent="",  # End of pipeline
            surface=Surface.SUMMARY,
            content="[Summary content would be generated here]",
            metadata={"role": "summarist"},
            open_questions=[],
        )


def create_agent(role: AgentRole, agent_id: Optional[str] = None, public_only: bool = True) -> Agent:
    """Factory function to create agents."""
    agent_map = {
        AgentRole.HERALD: HeraldAgent,
        AgentRole.ARCHITECT: ArchitectAgent,
        AgentRole.SCRIBE: ScribeAgent,
        AgentRole.ARCHIVIST: ArchivistAgent,
        AgentRole.VERIFIER: VerifierAgent,
        AgentRole.ARBITER: ArbiterAgent,
        AgentRole.SUMMARIST: SummaristAgent,
    }

    agent_class = agent_map.get(role)
    if not agent_class:
        raise ValueError(f"Unknown role: {role}")

    if agent_id:
        return agent_class(agent_id=agent_id, public_only=public_only)
    return agent_class(public_only=public_only)
