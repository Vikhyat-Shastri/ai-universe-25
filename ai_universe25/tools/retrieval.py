"""
Retrieval system: pinned corpus pipeline, BM25/FAISS indexing, provenance objects.

Implements retrieval from a pinned Wikipedia snapshot with source hashes
and quote spans for evidence tracking.
"""

import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not available, using BM25 only")


@dataclass
class EvidenceDocument:
    """A document in the evidence corpus."""

    doc_id: str
    title: str
    content: str
    source_hash: str  # SHA256 of original source
    source_url: Optional[str] = None  # Optional URL (salted-hashed if sensitive)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Compute source hash if not provided."""
        if not self.source_hash:
            content_bytes = self.content.encode()
            self.source_hash = hashlib.sha256(content_bytes).hexdigest()


@dataclass
class QuoteSpan:
    """A quote span with byte offsets."""

    start: int  # Start byte offset
    end: int  # End byte offset
    text: str  # The quoted text
    source_hash: str  # Hash of source document


@dataclass
class ProvenanceObject:
    """Provenance object with source hash and quote spans."""

    claim: str
    source_hash: str
    quote_spans: List[QuoteSpan]
    confidence: float = 1.0
    retrieval_method: str = "bm25"  # "bm25" or "faiss"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "claim": self.claim,
            "source_hash": self.source_hash,
            "quote_spans": [
                {
                    "start": span.start,
                    "end": span.end,
                    "text": span.text,
                    "source_hash": span.source_hash,
                }
                for span in self.quote_spans
            ],
            "confidence": self.confidence,
            "retrieval_method": self.retrieval_method,
        }


class CorpusIndex:
    """
    Indexed corpus for retrieval (BM25 + optional FAISS).

    Supports:
    - BM25 keyword retrieval
    - FAISS semantic search (if available)
    - Provenance tracking with source hashes
    - Quote span extraction
    """

    def __init__(self, corpus_dir: Optional[Path] = None):
        """
        Initialize corpus index.

        Args:
            corpus_dir: Directory containing corpus files
        """
        self.corpus_dir = corpus_dir or Path("corpus")
        self.documents: List[EvidenceDocument] = []
        self.bm25_index: Optional[BM25Okapi] = None
        self.faiss_index: Optional[Any] = None
        self.faiss_dimension = 384  # Default embedding dimension

        # Document lookup
        self.doc_by_id: Dict[str, EvidenceDocument] = {}
        self.doc_by_hash: Dict[str, EvidenceDocument] = {}

    def load_corpus(self, corpus_file: Optional[Path] = None):
        """
        Load corpus from file or directory.

        Args:
            corpus_file: Path to corpus JSON file (or None to scan directory)
        """
        if corpus_file:
            self._load_from_file(corpus_file)
        else:
            self._load_from_directory()

        self._build_indexes()
        logger.info(f"Loaded {len(self.documents)} documents")

    def _load_from_file(self, corpus_file: Path):
        """Load corpus from JSON file."""
        with open(corpus_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            for doc_data in data.get("documents", []):
                doc = EvidenceDocument(**doc_data)
                self.documents.append(doc)
                self.doc_by_id[doc.doc_id] = doc
                self.doc_by_hash[doc.source_hash] = doc

    def _load_from_directory(self):
        """Load corpus from directory (scans for .json files)."""
        if not self.corpus_dir.exists():
            logger.warning(f"Corpus directory {self.corpus_dir} does not exist")
            return

        for json_file in self.corpus_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for doc_data in data:
                            doc = EvidenceDocument(**doc_data)
                            self.documents.append(doc)
                            self.doc_by_id[doc.doc_id] = doc
                            self.doc_by_hash[doc.source_hash] = doc
                    elif isinstance(data, dict) and "documents" in data:
                        for doc_data in data["documents"]:
                            doc = EvidenceDocument(**doc_data)
                            self.documents.append(doc)
                            self.doc_by_id[doc.doc_id] = doc
                            self.doc_by_hash[doc.source_hash] = doc
            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")

    def _build_indexes(self):
        """Build BM25 and FAISS indexes."""
        if not self.documents:
            return

        # Build BM25 index
        tokenized_corpus = [self._tokenize(doc.content) for doc in self.documents]
        self.bm25_index = BM25Okapi(tokenized_corpus)
        logger.info("Built BM25 index")

        # Build FAISS index if available (requires embeddings)
        # This is a placeholder - would need actual embeddings
        if FAISS_AVAILABLE:
            # In production, would load pre-computed embeddings
            logger.info("FAISS available but embeddings not loaded")

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization (would use better tokenizer in production)."""
        return text.lower().split()

    def retrieve_bm25(
        self,
        query: str,
        k: int = 5,
    ) -> List[Tuple[EvidenceDocument, float]]:
        """
        Retrieve documents using BM25.

        Args:
            query: Search query
            k: Number of results

        Returns:
            List of (document, score) tuples
        """
        if not self.bm25_index:
            return []

        tokenized_query = self._tokenize(query)
        scores = self.bm25_index.get_scores(tokenized_query)

        # Get top k
        top_indices = np.argsort(scores)[::-1][:k]
        results = [
            (self.documents[i], float(scores[i])) for i in top_indices if scores[i] > 0
        ]

        return results

    def retrieve_faiss(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
    ) -> List[Tuple[EvidenceDocument, float]]:
        """
        Retrieve documents using FAISS (requires embeddings).

        Args:
            query_embedding: Query embedding vector
            k: Number of results

        Returns:
            List of (document, score) tuples
        """
        if not FAISS_AVAILABLE or not self.faiss_index:
            return []

        # FAISS search (placeholder - would need actual index)
        # In production, would:
        # 1. Compute query embedding
        # 2. Search FAISS index
        # 3. Return top k results
        logger.warning("FAISS retrieval not fully implemented")
        return []

    def extract_quote_spans(
        self,
        document: EvidenceDocument,
        claim: str,
        context_window: int = 100,
    ) -> List[QuoteSpan]:
        """
        Extract quote spans from document that support the claim.

        Args:
            document: Source document
            claim: The claim to find evidence for
            context_window: Context window size in bytes

        Returns:
            List of quote spans
        """
        claim_lower = claim.lower()
        content_lower = document.content.lower()
        spans = []

        # Simple substring matching (would use better matching in production)
        start = 0
        while True:
            idx = content_lower.find(claim_lower, start)
            if idx == -1:
                break

            # Extract context window
            span_start = max(0, idx - context_window)
            span_end = min(len(document.content), idx + len(claim) + context_window)
            span_text = document.content[span_start:span_end]

            span = QuoteSpan(
                start=span_start,
                end=span_end,
                text=span_text,
                source_hash=document.source_hash,
            )
            spans.append(span)
            start = idx + 1

        return spans

    def get_provenance(
        self,
        claim: str,
        k: int = 5,
        use_faiss: bool = False,
    ) -> ProvenanceObject:
        """
        Get provenance object for a claim.

        Args:
            claim: The claim to verify
            k: Number of documents to retrieve
            use_faiss: Use FAISS instead of BM25

        Returns:
            Provenance object with source hashes and quote spans
        """
        if use_faiss:
            # Would need query embedding
            results = []
        else:
            results = self.retrieve_bm25(claim, k=k)

        if not results:
            # Return empty provenance
            return ProvenanceObject(
                claim=claim,
                source_hash="",
                quote_spans=[],
                confidence=0.0,
            )

        # Use top result
        top_doc, score = results[0]
        quote_spans = self.extract_quote_spans(top_doc, claim)

        # Normalize score to confidence (0-1)
        confidence = min(1.0, score / 10.0)  # Rough normalization

        return ProvenanceObject(
            claim=claim,
            source_hash=top_doc.source_hash,
            quote_spans=quote_spans,
            confidence=confidence,
            retrieval_method="faiss" if use_faiss else "bm25",
        )

    def get_document_by_hash(self, source_hash: str) -> Optional[EvidenceDocument]:
        """Get document by source hash."""
        return self.doc_by_hash.get(source_hash)

    def add_document(self, document: EvidenceDocument):
        """Add a document to the corpus (rebuilds indexes)."""
        self.documents.append(document)
        self.doc_by_id[document.doc_id] = document
        self.doc_by_hash[document.source_hash] = document
        self._build_indexes()


class PinnedCorpusPipeline:
    """
    Pipeline for loading and indexing a pinned corpus snapshot.

    Handles:
    - Loading Wikipedia lead paragraphs
    - Creating evidence documents
    - Building retrieval indexes
    - Managing corpus snapshots
    """

    def __init__(self, snapshot_dir: Path):
        """
        Initialize pipeline.

        Args:
            snapshot_dir: Directory containing corpus snapshot
        """
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.index = CorpusIndex()

    def load_wikipedia_leads(self, leads_file: Path) -> List[EvidenceDocument]:
        """
        Load Wikipedia lead paragraphs from file.

        Args:
            leads_file: Path to leads file (JSON format)

        Returns:
            List of evidence documents
        """
        documents = []

        with open(leads_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                doc_id = item.get("page_id", f"wiki_{len(documents)}")
                title = item.get("title", "")
                lead_intro = item.get("lead_intro", "")
                lead_sha256 = item.get("lead_sha256", "")

                doc = EvidenceDocument(
                    doc_id=doc_id,
                    title=title,
                    content=lead_intro,
                    source_hash=lead_sha256,
                    source_url=item.get("source_url"),
                    metadata={
                        "page_id": doc_id,
                        "title": title,
                        "snapshot": self.snapshot_dir.name,
                    },
                )
                documents.append(doc)

        return documents

    def build_index(self, documents: Optional[List[EvidenceDocument]] = None):
        """
        Build retrieval index from documents.

        Args:
            documents: Documents to index (or None to load from snapshot)
        """
        if documents:
            self.index.documents = documents
            for doc in documents:
                self.index.doc_by_id[doc.doc_id] = doc
                self.index.doc_by_hash[doc.source_hash] = doc
        else:
            # Load from snapshot directory
            self.index.corpus_dir = self.snapshot_dir
            self.index.load_corpus()

        self.index._build_indexes()
        logger.info(f"Built index with {len(self.index.documents)} documents")
