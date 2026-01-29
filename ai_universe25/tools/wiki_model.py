"""
Grokipedia page model with surfaces and revision history.

Implements wiki pages with typed surfaces (intro/outline/body/summary/index/frontpage/
citation-graph/fact-ledger/style-report) and revision history. Supports quarantine
shadow surfaces for diverted writes.
"""

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from ai_universe25.runtime.gateway import Surface

logger = logging.getLogger(__name__)


class RevisionStatus(Enum):
    """Revision status."""

    DRAFT = "draft"
    APPROVED = "approved"
    QUARANTINED = "quarantined"
    REJECTED = "rejected"


@dataclass
class Revision:
    """A single revision of a surface."""

    revision_id: str
    surface: Surface
    content: str
    author_id: str
    timestamp: float
    parent_revision_id: Optional[str] = None
    status: RevisionStatus = RevisionStatus.DRAFT
    content_hash: str = field(init=False)
    diff: Optional[str] = None  # Diff from parent

    def __post_init__(self):
        """Compute content hash."""
        self.content_hash = hashlib.sha256(self.content.encode()).hexdigest()


@dataclass
class Citation:
    """A citation reference."""

    citation_id: str
    claim: str  # The claim being cited
    source_hash: str  # Hash of source document
    quote_span: tuple[int, int]  # (start, end) byte offsets in source
    source_url: Optional[str] = None  # Optional URL (salted-hashed if sensitive)
    confidence: float = 1.0  # Confidence score (0-1)


@dataclass
class FactEntry:
    """A fact ledger entry."""

    fact_id: str
    claim: str
    verification_status: str  # "ENTAIL", "CONTRADICT", "UNSURE"
    evidence_hash: str
    verifier_id: str
    timestamp: float
    citations: List[str] = field(default_factory=list)  # Citation IDs


@dataclass
class StyleReport:
    """Style and neutrality report."""

    report_id: str
    surface: Surface
    neutrality_score: float  # 0-1 (higher = more neutral)
    bias_flags: List[str] = field(default_factory=list)
    style_violations: List[str] = field(default_factory=list)
    arbiter_id: str = ""
    timestamp: float = field(default_factory=time.time)


class WikiPage:
    """
    Grokipedia wiki page with typed surfaces and revision history.

    Supports:
    - Multiple typed surfaces (intro, outline, body, etc.)
    - Revision history per surface
    - Quarantine shadow surfaces
    - Citation graph
    - Fact ledger
    - Style reports
    """

    def __init__(self, page_id: str, title: str):
        """
        Initialize wiki page.

        Args:
            page_id: Unique page identifier
            title: Page title
        """
        self.page_id = page_id
        self.title = title
        self.created_at = time.time()

        # Surface content (current revision)
        self.surfaces: Dict[Surface, str] = {}

        # Revision history per surface
        self.revisions: Dict[Surface, List[Revision]] = {}

        # Quarantine shadow surfaces
        self.shadow_surfaces: Dict[Surface, List[Revision]] = {}

        # Citation graph (claim -> citations)
        self.citation_graph: Dict[str, List[Citation]] = {}

        # Fact ledger
        self.fact_ledger: List[FactEntry] = []

        # Style reports
        self.style_reports: Dict[Surface, List[StyleReport]] = {}

        # Metadata
        self.metadata: Dict[str, Any] = {}

    def write_surface(
        self,
        surface: Surface,
        content: str,
        author_id: str,
        parent_revision_id: Optional[str] = None,
        status: RevisionStatus = RevisionStatus.DRAFT,
        is_shadow: bool = False,
    ) -> Revision:
        """
        Write to a surface (creates new revision).

        Args:
            surface: Target surface
            content: Content to write
            author_id: Author agent ID
            parent_revision_id: Parent revision ID (for diff)
            status: Revision status
            is_shadow: If True, write to shadow surface (quarantine)

        Returns:
            Created revision
        """
        revision_id = f"{self.page_id}_{surface.value}_{int(time.time() * 1000)}"

        # Compute diff if parent exists
        diff = None
        if parent_revision_id:
            parent_rev = self._find_revision(surface, parent_revision_id, is_shadow)
            if parent_rev:
                diff = self._compute_diff(parent_rev.content, content)

        revision = Revision(
            revision_id=revision_id,
            surface=surface,
            content=content,
            author_id=author_id,
            timestamp=time.time(),
            parent_revision_id=parent_revision_id,
            status=status,
            diff=diff,
        )

        # Store revision
        if is_shadow:
            if surface not in self.shadow_surfaces:
                self.shadow_surfaces[surface] = []
            self.shadow_surfaces[surface].append(revision)
        else:
            if surface not in self.revisions:
                self.revisions[surface] = []
            self.revisions[surface].append(revision)
            # Update current surface content
            self.surfaces[surface] = content

        logger.debug(
            f"Wrote {surface.value} revision {revision_id} "
            f"(shadow={is_shadow}, status={status.value})"
        )
        return revision

    def append_surface(
        self,
        surface: Surface,
        content: str,
        author_id: str,
    ) -> Revision:
        """
        Append to a surface (for append-only surfaces like fact-ledger).

        Args:
            surface: Target surface
            content: Content to append
            author_id: Author agent ID

        Returns:
            Created revision
        """
        # Get current content
        current_content = self.surfaces.get(surface, "")
        new_content = current_content + "\n" + content if current_content else content

        return self.write_surface(surface, new_content, author_id)

    def _find_revision(
        self,
        surface: Surface,
        revision_id: str,
        is_shadow: bool = False,
    ) -> Optional[Revision]:
        """Find revision by ID."""
        if is_shadow:
            revisions = self.shadow_surfaces.get(surface, [])
        else:
            revisions = self.revisions.get(surface, [])

        for rev in revisions:
            if rev.revision_id == revision_id:
                return rev
        return None

    def _compute_diff(self, old_content: str, new_content: str) -> str:
        """Compute simple diff (placeholder - would use difflib in production)."""
        # Simplified diff - in production would use difflib or similar
        if old_content == new_content:
            return ""
        return f"[{len(old_content)} chars -> {len(new_content)} chars]"

    def get_current_content(self, surface: Surface) -> Optional[str]:
        """Get current content for a surface."""
        return self.surfaces.get(surface)

    def get_revision_history(
        self,
        surface: Surface,
        include_shadow: bool = False,
    ) -> List[Revision]:
        """Get revision history for a surface."""
        revisions = self.revisions.get(surface, []).copy()
        if include_shadow:
            revisions.extend(self.shadow_surfaces.get(surface, []))
        return sorted(revisions, key=lambda r: r.timestamp)

    def add_citation(
        self,
        claim: str,
        source_hash: str,
        quote_span: tuple[int, int],
        source_url: Optional[str] = None,
        confidence: float = 1.0,
    ) -> Citation:
        """
        Add a citation to the citation graph.

        Args:
            claim: The claim being cited
            source_hash: Hash of source document
            quote_span: (start, end) byte offsets
            source_url: Optional source URL
            confidence: Confidence score

        Returns:
            Created citation
        """
        citation_id = f"cite_{hashlib.sha256(f'{claim}{source_hash}'.encode()).hexdigest()[:16]}"
        citation = Citation(
            citation_id=citation_id,
            claim=claim,
            source_hash=source_hash,
            quote_span=quote_span,
            source_url=source_url,
            confidence=confidence,
        )

        if claim not in self.citation_graph:
            self.citation_graph[claim] = []
        self.citation_graph[claim].append(citation)

        return citation

    def add_fact_entry(
        self,
        claim: str,
        verification_status: str,
        evidence_hash: str,
        verifier_id: str,
        citations: Optional[List[str]] = None,
    ) -> FactEntry:
        """
        Add entry to fact ledger.

        Args:
            claim: The claim being verified
            verification_status: "ENTAIL", "CONTRADICT", or "UNSURE"
            evidence_hash: Hash of evidence
            verifier_id: Verifier agent ID
            citations: List of citation IDs

        Returns:
            Created fact entry
        """
        fact_id = f"fact_{len(self.fact_ledger)}"
        fact_entry = FactEntry(
            fact_id=fact_id,
            claim=claim,
            verification_status=verification_status,
            evidence_hash=evidence_hash,
            verifier_id=verifier_id,
            timestamp=time.time(),
            citations=citations or [],
        )

        self.fact_ledger.append(fact_entry)
        return fact_entry

    def add_style_report(
        self,
        surface: Surface,
        neutrality_score: float,
        bias_flags: Optional[List[str]] = None,
        style_violations: Optional[List[str]] = None,
        arbiter_id: str = "",
    ) -> StyleReport:
        """
        Add style report for a surface.

        Args:
            surface: Target surface
            neutrality_score: Neutrality score (0-1)
            bias_flags: List of bias flags
            style_violations: List of style violations
            arbiter_id: Arbiter agent ID

        Returns:
            Created style report
        """
        report_id = f"style_{surface.value}_{int(time.time() * 1000)}"
        report = StyleReport(
            report_id=report_id,
            surface=surface,
            neutrality_score=neutrality_score,
            bias_flags=bias_flags or [],
            style_violations=style_violations or [],
            arbiter_id=arbiter_id,
        )

        if surface not in self.style_reports:
            self.style_reports[surface] = []
        self.style_reports[surface].append(report)

        return report

    def promote_shadow_revision(
        self,
        surface: Surface,
        revision_id: str,
    ) -> bool:
        """
        Promote a shadow revision to main surface (after quarantine review).

        Args:
            surface: Target surface
            revision_id: Shadow revision ID

        Returns:
            True if promoted successfully
        """
        shadow_revs = self.shadow_surfaces.get(surface, [])
        shadow_rev = next((r for r in shadow_revs if r.revision_id == revision_id), None)

        if not shadow_rev:
            return False

        # Create new revision from shadow
        new_rev = Revision(
            revision_id=f"{revision_id}_promoted",
            surface=shadow_rev.surface,
            content=shadow_rev.content,
            author_id=shadow_rev.author_id,
            timestamp=time.time(),
            parent_revision_id=self._get_latest_revision_id(surface),
            status=RevisionStatus.APPROVED,
        )

        if surface not in self.revisions:
            self.revisions[surface] = []
        self.revisions[surface].append(new_rev)
        self.surfaces[surface] = new_rev.content

        logger.info(f"Promoted shadow revision {revision_id} to main surface")
        return True

    def _get_latest_revision_id(self, surface: Surface) -> Optional[str]:
        """Get latest revision ID for a surface."""
        revisions = self.revisions.get(surface, [])
        if revisions:
            return revisions[-1].revision_id
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize page to dict."""
        return {
            "page_id": self.page_id,
            "title": self.title,
            "created_at": self.created_at,
            "surfaces": {s.value: content for s, content in self.surfaces.items()},
            "revision_counts": {
                s.value: len(revs) for s, revs in self.revisions.items()
            },
            "shadow_revision_counts": {
                s.value: len(revs) for s, revs in self.shadow_surfaces.items()
            },
            "citation_count": sum(len(cits) for cits in self.citation_graph.values()),
            "fact_ledger_count": len(self.fact_ledger),
            "style_report_counts": {
                s.value: len(reports) for s, reports in self.style_reports.items()
            },
        }
