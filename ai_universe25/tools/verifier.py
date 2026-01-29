"""
Verifier: Two-stage fact-checking (retrieval + entailment/NLI).

Implements retrieval (k=5) + entailment/NLI verification, writes results
to fact-ledger, and emits precise edit requests.
"""

import hashlib
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ai_universe25.tools.retrieval import CorpusIndex, ProvenanceObject
from ai_universe25.tools.wiki_model import FactEntry, WikiPage

logger = logging.getLogger(__name__)


class VerificationStatus(Enum):
    """Verification status from NLI."""

    ENTAIL = "ENTAIL"  # Claim is entailed by evidence
    CONTRADICT = "CONTRADICT"  # Claim contradicts evidence
    UNSURE = "UNSURE"  # Cannot determine


@dataclass
class Claim:
    """A claim to verify."""

    claim_id: str
    text: str
    surface: str  # Surface where claim appears
    context: str  # Surrounding context


@dataclass
class VerificationResult:
    """Result of verification."""

    claim_id: str
    claim_text: str
    status: VerificationStatus
    confidence: float  # 0-1
    evidence_hash: str
    quote_spans: List[Dict[str, Any]]
    rationale: str
    edit_request: Optional[str] = None  # Suggested edit if needed


class NLIEngine:
    """
    Natural Language Inference engine (placeholder).

    In production, would use a real NLI model (e.g., DeBERTa, RoBERTa-based).
    """

    def __init__(self, model_name: str = "deberta-v3"):
        """
        Initialize NLI engine.

        Args:
            model_name: Model identifier
        """
        self.model_name = model_name
        # In production, would load actual model here
        logger.info(f"Initialized NLI engine: {model_name}")

    def verify(
        self,
        claim: str,
        evidence: str,
    ) -> Tuple[VerificationStatus, float]:
        """
        Verify claim against evidence using NLI.

        Args:
            claim: The claim to verify
            evidence: Evidence text

        Returns:
            (status, confidence)
        """
        # Placeholder implementation
        # In production, would:
        # 1. Tokenize claim and evidence
        # 2. Run through NLI model
        # 3. Return entailment/contradiction/neutral probabilities
        # 4. Convert to VerificationStatus

        # Simple heuristic for demo
        claim_lower = claim.lower()
        evidence_lower = evidence.lower()

        if any(word in evidence_lower for word in claim_lower.split()[:3]):
            return VerificationStatus.ENTAIL, 0.8
        elif "not" in claim_lower and "not" not in evidence_lower:
            return VerificationStatus.CONTRADICT, 0.7
        else:
            return VerificationStatus.UNSURE, 0.5


class Verifier:
    """
    Two-stage verifier: retrieval (k=5) + entailment/NLI.

    Stages:
    1. Retrieve k=5 relevant documents using BM25/FAISS
    2. Run NLI on claim vs. retrieved evidence
    3. Write results to fact-ledger
    4. Emit precise edit requests if needed
    """

    def __init__(
        self,
        corpus_index: CorpusIndex,
        nli_engine: Optional[NLIEngine] = None,
        k: int = 5,
    ):
        """
        Initialize verifier.

        Args:
            corpus_index: Indexed corpus for retrieval
            nli_engine: NLI engine (default: create new)
            k: Number of documents to retrieve
        """
        self.corpus_index = corpus_index
        self.nli_engine = nli_engine or NLIEngine()
        self.k = k

    def extract_claims(self, content: str) -> List[Claim]:
        """
        Extract claims from content (simplified).

        Args:
            content: Content to extract claims from

        Returns:
            List of claims
        """
        # Simplified: split by sentences
        # In production, would use better claim extraction
        sentences = content.split(". ")
        claims = []

        for i, sentence in enumerate(sentences):
            if len(sentence.strip()) > 20:  # Filter short sentences
                claim_id = f"claim_{i}"
                claim = Claim(
                    claim_id=claim_id,
                    text=sentence.strip(),
                    surface="body",
                    context=content[max(0, content.find(sentence) - 100) : content.find(sentence) + len(sentence) + 100],
                )
                claims.append(claim)

        return claims

    def verify_claim(
        self,
        claim: Claim,
    ) -> VerificationResult:
        """
        Verify a single claim using two-stage process.

        Args:
            claim: Claim to verify

        Returns:
            Verification result
        """
        # Stage 1: Retrieve evidence
        provenance = self.corpus_index.get_provenance(claim.text, k=self.k)

        if not provenance.quote_spans:
            # No evidence found
            return VerificationResult(
                claim_id=claim.claim_id,
                claim_text=claim.text,
                status=VerificationStatus.UNSURE,
                confidence=0.0,
                evidence_hash="",
                quote_spans=[],
                rationale="No evidence found in corpus",
                edit_request="Mark as needs-verification",
            )

        # Stage 2: Run NLI on top evidence
        top_evidence = provenance.quote_spans[0].text if provenance.quote_spans else ""
        status, confidence = self.nli_engine.verify(claim.text, top_evidence)

        # Generate rationale
        rationale = self._generate_rationale(claim.text, status, confidence, top_evidence)

        # Generate edit request if needed
        edit_request = None
        if status == VerificationStatus.CONTRADICT:
            edit_request = f"Revise claim: {claim.text} (contradicts evidence)"
        elif status == VerificationStatus.UNSURE and confidence < 0.5:
            edit_request = f"Mark as needs-verification: {claim.text}"

        return VerificationResult(
            claim_id=claim.claim_id,
            claim_text=claim.text,
            status=status,
            confidence=confidence,
            evidence_hash=provenance.source_hash,
            quote_spans=[
                {
                    "start": span.start,
                    "end": span.end,
                    "text": span.text,
                    "source_hash": span.source_hash,
                }
                for span in provenance.quote_spans
            ],
            rationale=rationale,
            edit_request=edit_request,
        )

    def _generate_rationale(
        self,
        claim: str,
        status: VerificationStatus,
        confidence: float,
        evidence: str,
    ) -> str:
        """Generate human-readable rationale."""
        if status == VerificationStatus.ENTAIL:
            return f"Claim is entailed by evidence (confidence: {confidence:.2f}). Evidence excerpt: {evidence[:200]}..."
        elif status == VerificationStatus.CONTRADICT:
            return f"Claim contradicts evidence (confidence: {confidence:.2f}). Evidence excerpt: {evidence[:200]}..."
        else:
            return f"Cannot determine relationship (confidence: {confidence:.2f}). Evidence excerpt: {evidence[:200]}..."

    def verify_content(
        self,
        content: str,
        page: WikiPage,
        verifier_id: str,
    ) -> List[FactEntry]:
        """
        Verify all claims in content and write to fact-ledger.

        Args:
            content: Content to verify
            page: Wiki page (for fact-ledger)
            verifier_id: Verifier agent ID

        Returns:
            List of fact ledger entries created
        """
        # Extract claims
        claims = self.extract_claims(content)

        fact_entries = []

        for claim in claims:
            # Verify claim
            result = self.verify_claim(claim)

            # Create fact ledger entry
            fact_entry = page.add_fact_entry(
                claim=result.claim_text,
                verification_status=result.status.value,
                evidence_hash=result.evidence_hash,
                verifier_id=verifier_id,
                citations=[span["source_hash"] for span in result.quote_spans],
            )

            fact_entries.append(fact_entry)

            logger.info(
                f"Verified claim {claim.claim_id}: {result.status.value} "
                f"(confidence: {result.confidence:.2f})"
            )

            # Emit edit request if needed
            if result.edit_request:
                logger.warning(f"Edit request for {claim.claim_id}: {result.edit_request}")

        return fact_entries

    def batch_verify(
        self,
        claims: List[Claim],
    ) -> List[VerificationResult]:
        """
        Verify multiple claims in batch.

        Args:
            claims: List of claims to verify

        Returns:
            List of verification results
        """
        results = []
        for claim in claims:
            result = self.verify_claim(claim)
            results.append(result)
        return results
