"""
Base agent class and role definitions.

Implements the 7 agent roles with tool-limited prompts and structured handoffs.
Includes SimulatedLLMBackend for running full experiments without API keys.
"""

import hashlib
import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol

from ai_universe25.runtime.gateway import Envelope, Surface
from ai_universe25.runtime.rbac_ladder import AgentRole

logger = logging.getLogger(__name__)


class LLMBackend(Protocol):
    """Protocol for LLM backends (real or simulated)."""

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        ...


class SimulatedLLMBackend:
    """
    Simulated LLM backend that produces deterministic, plausible synthetic
    content without requiring real API keys.

    Uses seeded random generation with role-specific templates to produce
    structured output including claim placeholders and citation refs.
    """

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self._claim_counter = 0
        self._templates = {
            "intro": [
                "This article examines {topic}. The central question concerns {aspect}.",
                "{topic} is a subject of significant scholarly interest, particularly regarding {aspect}.",
            ],
            "outline": [
                "1. Background\n2. Methods and Mechanism\n3. Evidence\n4. Implications\n5. Limitations",
                "1. Introduction\n2. Historical Context\n3. Core Analysis\n4. Discussion\n5. Conclusions",
            ],
            "body": [
                "Research indicates that {claim} [CITE_{cid}]. Furthermore, {claim2} [CITE_{cid2}].",
                "The evidence suggests {claim} [CITE_{cid}]. However, {claim2} [CITE_{cid2}].",
            ],
            "citation": [
                "Smith et al. (2024). {topic}. Journal of Research, 42(1), 1-15.",
                "Johnson & Lee (2023). On {topic}. Proceedings of Conference, pp. 100-110.",
            ],
            "summary": [
                "This article covers {topic}. Key findings include {claim}. Limitations are noted.",
                "In summary, {topic} presents {claim}. Further research is warranted.",
            ],
            "style_report": [
                "Neutrality: PASS. No weasel words detected. Tone is balanced.",
                "Style check complete. Minor heading inconsistency at section 3.",
            ],
            "fact_check": [
                "Claim verified: ENTAIL (confidence 0.85). Evidence from source {src}.",
                "Claim status: UNSURE (confidence 0.45). Needs additional verification.",
            ],
        }

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        """Generate simulated content based on prompt context."""
        prompt_lower = prompt.lower()

        if "herald" in prompt_lower or "introduction" in prompt_lower:
            category = "intro"
        elif "architect" in prompt_lower or "outline" in prompt_lower:
            category = "outline"
        elif "scribe" in prompt_lower or "body" in prompt_lower:
            category = "body"
        elif "archivist" in prompt_lower or "citation" in prompt_lower:
            category = "citation"
        elif "summarist" in prompt_lower or "summary" in prompt_lower:
            category = "summary"
        elif "arbiter" in prompt_lower or "style" in prompt_lower:
            category = "style_report"
        elif "verifier" in prompt_lower or "fact" in prompt_lower:
            category = "fact_check"
        else:
            category = "body"

        templates = self._templates[category]
        template = self.rng.choice(templates)

        self._claim_counter += 1
        content = template.format(
            topic="the subject under investigation",
            aspect="its structural implications",
            claim=f"claim_{self._claim_counter}",
            claim2=f"claim_{self._claim_counter + 1}",
            cid=self._claim_counter,
            cid2=self._claim_counter + 1,
            src=hashlib.md5(str(self._claim_counter).encode()).hexdigest()[:8],
        )
        self._claim_counter += 1

        return content


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
        llm_backend: Optional[LLMBackend] = None,
    ):
        self.agent_id = agent_id
        self.role = role
        self.tools = tools
        self.public_only = public_only
        self.llm = llm_backend or SimulatedLLMBackend()
        self._max_tokens_override: Optional[int] = None

    def _get_max_tokens(self, default: int = 512) -> int:
        """Get effective max_tokens, respecting CoAP budget override."""
        if self._max_tokens_override is not None:
            return self._max_tokens_override
        return default

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

    def __init__(self, agent_id: str = "herald_1", public_only: bool = True,
                 llm_backend: Optional[LLMBackend] = None):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.HERALD,
            tools=["write_intro", "read_lead"],
            public_only=public_only,
            llm_backend=llm_backend,
        )

    def get_prompt(self, context: Dict[str, Any]) -> str:
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
        context = {"page_title": handoff.metadata.get("page_title", "") if handoff else ""}
        prompt = self.get_prompt(context)
        content = self.llm.generate(f"Herald: {prompt}", max_tokens=self._get_max_tokens())
        return AgentHandoff(
            from_agent=self.agent_id,
            to_agent="architect",
            surface=Surface.INTRO,
            content=content,
            metadata={"role": "herald"},
            open_questions=["What sections should be included?", "What is the logical flow?"],
        )


class ArchitectAgent(Agent):
    """PROJECT-DIAGRAM Architect: Outline & Structure agent."""

    def __init__(self, agent_id: str = "architect_1", public_only: bool = True,
                 llm_backend: Optional[LLMBackend] = None):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.ARCHITECT,
            tools=["write_outline", "read_intro"],
            public_only=public_only,
            llm_backend=llm_backend,
        )

    def get_prompt(self, context: Dict[str, Any]) -> str:
        intro_content = context.get("intro_content", "")

        return f"""You are the Architect agent. Your role is to propose section headers and logical flow.

Input: Herald's introduction
{intro_content}

Mandate:
- Propose section headers and logical flow (Background -> Methods/Mechanism -> Evidence -> Implications)
- Ensure progressive disclosure and cross-section coherence
- Enforce narrative cohesion

Invariants:
- No new facts
- Every section must have explicit intent, entry criteria, and acceptance checks

Output: A signed outline artifact (OUTLINE.vN) and a list of evidence gaps."""

    def process(self, handoff: Optional[AgentHandoff]) -> AgentHandoff:
        context = {"intro_content": handoff.content if handoff else ""}
        prompt = self.get_prompt(context)
        content = self.llm.generate(f"Architect outline: {prompt}", max_tokens=self._get_max_tokens())
        return AgentHandoff(
            from_agent=self.agent_id,
            to_agent="scribe",
            surface=Surface.OUTLINE,
            content=content,
            metadata={"role": "architect"},
            open_questions=["What evidence is needed for each section?"],
        )


class ScribeAgent(Agent):
    """File Scribe: Main Body agent."""

    def __init__(self, agent_id: str = "scribe_1", public_only: bool = True,
                 llm_backend: Optional[LLMBackend] = None):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.SCRIBE,
            tools=["write_body", "read_outline", "read_citations"],
            public_only=public_only,
            llm_backend=llm_backend,
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
        context = {"outline": handoff.content if handoff else ""}
        prompt = self.get_prompt(context)
        content = self.llm.generate(f"Scribe body: {prompt}", max_tokens=self._get_max_tokens(768))
        return AgentHandoff(
            from_agent=self.agent_id,
            to_agent="arbiter",
            surface=Surface.BODY,
            content=content,
            metadata={"role": "scribe"},
            open_questions=["Is the tone neutral?", "Are there style violations?"],
        )


class ArchivistAgent(Agent):
    """BOOK Archivist: References agent."""

    def __init__(self, agent_id: str = "archivist_1", public_only: bool = True,
                 llm_backend: Optional[LLMBackend] = None):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.ARCHIVIST,
            tools=["write_citations", "read_body", "read_sources"],
            public_only=public_only,
            llm_backend=llm_backend,
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
        context = {"body_content": handoff.content if handoff else ""}
        prompt = self.get_prompt(context)
        content = self.llm.generate(f"Archivist citation: {prompt}", max_tokens=self._get_max_tokens())
        return AgentHandoff(
            from_agent=self.agent_id,
            to_agent="verifier",
            surface=Surface.CITATION_GRAPH,
            content=content,
            metadata={"role": "archivist"},
            open_questions=["Are all claims verifiable?"],
        )


class VerifierAgent(Agent):
    """SEARCH Verifier: Fact-checking agent."""

    def __init__(self, agent_id: str = "verifier_1", public_only: bool = True,
                 llm_backend: Optional[LLMBackend] = None):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.VERIFIER,
            tools=["verify_claim", "write_fact_ledger", "read_body", "retrieve_evidence"],
            public_only=public_only,
            llm_backend=llm_backend,
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
        context = {"claims": []}
        prompt = self.get_prompt(context)
        content = self.llm.generate(f"Verifier fact_check: {prompt}", max_tokens=self._get_max_tokens())
        return AgentHandoff(
            from_agent=self.agent_id,
            to_agent="arbiter",
            surface=Surface.FACT_LEDGER,
            content=content,
            metadata={"role": "verifier"},
            open_questions=["Are there any contradictions?"],
        )


class ArbiterAgent(Agent):
    """Balance-Scale Arbiter: Neutrality & Style agent."""

    def __init__(self, agent_id: str = "arbiter_1", public_only: bool = True,
                 llm_backend: Optional[LLMBackend] = None):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.ARBITER,
            tools=["write_style_report", "read_body", "read_fact_ledger"],
            public_only=public_only,
            llm_backend=llm_backend,
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
        context = {"body_content": handoff.content if handoff else ""}
        prompt = self.get_prompt(context)
        content = self.llm.generate(f"Arbiter style: {prompt}", max_tokens=self._get_max_tokens())
        return AgentHandoff(
            from_agent=self.agent_id,
            to_agent="summarist",
            surface=Surface.STYLE_REPORT,
            content=content,
            metadata={"role": "arbiter"},
            open_questions=["Is the content ready for summarization?"],
        )


class SummaristAgent(Agent):
    """STICKY-NOTE Summarist: Summaries agent."""

    def __init__(self, agent_id: str = "summarist_1", public_only: bool = True,
                 llm_backend: Optional[LLMBackend] = None):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.SUMMARIST,
            tools=["write_summary", "read_body", "read_style_report"],
            public_only=public_only,
            llm_backend=llm_backend,
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
        context = {"body_content": handoff.content if handoff else ""}
        prompt = self.get_prompt(context)
        content = self.llm.generate(f"Summarist summary: {prompt}", max_tokens=self._get_max_tokens())
        return AgentHandoff(
            from_agent=self.agent_id,
            to_agent="",
            surface=Surface.SUMMARY,
            content=content,
            metadata={"role": "summarist"},
            open_questions=[],
        )


def create_agent(
    role: AgentRole,
    agent_id: Optional[str] = None,
    public_only: bool = True,
    llm_backend: Optional[LLMBackend] = None,
) -> Agent:
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

    kwargs: Dict[str, Any] = {"public_only": public_only, "llm_backend": llm_backend}
    if agent_id:
        kwargs["agent_id"] = agent_id
    return agent_class(**kwargs)
