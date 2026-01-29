"""
Append-only ledger with hash chain and Merkle checkpoints.

Implements tamper-evident event storage with HMAC-signed envelopes,
schema IDs, content hashes, and periodic Merkle tree checkpoints.
"""

import hashlib
import hmac
import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_universe25.runtime.gateway import Envelope

logger = logging.getLogger(__name__)


@dataclass
class LedgerEntry:
    """A single ledger entry."""

    run_id: str
    sequence: int  # Sequential entry number
    timestamp: float
    schema_id: str
    content_hash: str
    envelope: Dict[str, Any]
    entry_hash: str  # Hash of this entry
    prev_hash: Optional[str] = None  # Hash of previous entry (hash chain)
    merkle_path: Optional[List[str]] = None  # Merkle proof path

    def compute_hash(self) -> str:
        """Compute hash of this entry."""
        data = {
            "run_id": self.run_id,
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "schema_id": self.schema_id,
            "content_hash": self.content_hash,
            "envelope": self.envelope,
            "prev_hash": self.prev_hash,
        }
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()


@dataclass
class MerkleCheckpoint:
    """Merkle tree checkpoint."""

    checkpoint_id: str
    timestamp: float
    root_hash: str
    entry_count: int
    first_sequence: int
    last_sequence: int
    tree_depth: int
    leaves: List[str]  # Leaf hashes


class AppendOnlyLedger:
    """
    Append-only ledger with hash chain and Merkle checkpoints.

    Features:
    - Hash chain linking (each entry references previous)
    - HMAC-signed envelopes
    - Schema IDs for versioning
    - Content hashes for integrity
    - Periodic Merkle tree checkpoints
    - Tamper-evident storage
    """

    def __init__(
        self,
        ledger_dir: Path,
        secret_key: Optional[bytes] = None,
        checkpoint_interval: int = 100,
    ):
        """
        Initialize ledger.

        Args:
            ledger_dir: Directory for ledger storage
            secret_key: HMAC secret for signing (default: random)
            checkpoint_interval: Entries between Merkle checkpoints
        """
        self.ledger_dir = Path(ledger_dir)
        self.ledger_dir.mkdir(parents=True, exist_ok=True)

        self.secret_key = secret_key or os.urandom(32)
        self.checkpoint_interval = checkpoint_interval

        # In-memory state
        self.entries: List[LedgerEntry] = []
        self.checkpoints: List[MerkleCheckpoint] = []
        self.last_hash: Optional[str] = None
        self.sequence_counter = 0

        # File handles
        self.ledger_file = self.ledger_dir / "ledger.jsonl"
        self.checkpoint_file = self.ledger_dir / "checkpoints.jsonl"
        self.metadata_file = self.ledger_dir / "metadata.json"

        # Load existing ledger
        self._load_ledger()

    def _load_ledger(self):
        """Load existing ledger from disk."""
        if self.ledger_file.exists():
            logger.info(f"Loading ledger from {self.ledger_file}")
            with open(self.ledger_file, "r") as f:
                for line in f:
                    if line.strip():
                        entry_dict = json.loads(line)
                        entry = LedgerEntry(**entry_dict)
                        self.entries.append(entry)
                        self.last_hash = entry.entry_hash
                        self.sequence_counter = max(self.sequence_counter, entry.sequence)

            self.sequence_counter += 1
            logger.info(f"Loaded {len(self.entries)} entries")

        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, "r") as f:
                for line in f:
                    if line.strip():
                        checkpoint_dict = json.loads(line)
                        checkpoint = MerkleCheckpoint(**checkpoint_dict)
                        self.checkpoints.append(checkpoint)

    def append(
        self,
        envelope: Envelope,
        schema_id: str,
        content: Any,
        run_id: Optional[str] = None,
    ) -> LedgerEntry:
        """
        Append an entry to the ledger.

        Args:
            envelope: MCP envelope
            schema_id: Schema identifier (e.g., "write.v1")
            content: Content to store (will be hashed)
            run_id: Run identifier (default: from envelope)

        Returns:
            Created ledger entry
        """
        # Compute content hash
        content_str = json.dumps(content, sort_keys=True) if isinstance(content, dict) else str(content)
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()

        # Sign envelope
        envelope_dict = envelope.to_dict()
        envelope_signature = self._sign_envelope(envelope_dict)

        # Create entry
        entry = LedgerEntry(
            run_id=run_id or envelope.run_id,
            sequence=self.sequence_counter,
            timestamp=time.time(),
            schema_id=schema_id,
            content_hash=content_hash,
            envelope={**envelope_dict, "signature": envelope_signature},
            entry_hash="",  # Will compute after setting prev_hash
            prev_hash=self.last_hash,
        )

        # Compute entry hash
        entry.entry_hash = entry.compute_hash()
        self.last_hash = entry.entry_hash

        # Append to in-memory list
        self.entries.append(entry)
        self.sequence_counter += 1

        # Write to disk (append-only)
        self._write_entry(entry)

        # Check if checkpoint needed
        if len(self.entries) % self.checkpoint_interval == 0:
            self._create_checkpoint()

        logger.debug(f"Appended entry {entry.sequence} (hash: {entry.entry_hash[:16]}...)")
        return entry

    def _sign_envelope(self, envelope_dict: Dict[str, Any]) -> str:
        """Sign envelope with HMAC."""
        payload = json.dumps(envelope_dict, sort_keys=True).encode()
        return hmac.new(self.secret_key, payload, hashlib.sha256).hexdigest()

    def verify_envelope(self, entry: LedgerEntry) -> bool:
        """Verify envelope signature."""
        envelope_dict = entry.envelope.copy()
        signature = envelope_dict.pop("signature", None)
        if not signature:
            return False

        expected = self._sign_envelope(envelope_dict)
        return hmac.compare_digest(expected, signature)

    def _write_entry(self, entry: LedgerEntry):
        """Write entry to ledger file (append-only)."""
        with open(self.ledger_file, "a") as f:
            f.write(json.dumps(asdict(entry)) + "\n")

    def _create_checkpoint(self):
        """Create Merkle tree checkpoint."""
        if not self.entries:
            return

        # Get entries since last checkpoint
        last_checkpoint_seq = (
            self.checkpoints[-1].last_sequence if self.checkpoints else -1
        )
        checkpoint_entries = [
            e for e in self.entries if e.sequence > last_checkpoint_seq
        ]

        if not checkpoint_entries:
            return

        # Build Merkle tree
        leaves = [e.entry_hash for e in checkpoint_entries]
        root_hash, tree_depth = self._build_merkle_tree(leaves)

        # Create checkpoint
        checkpoint = MerkleCheckpoint(
            checkpoint_id=f"ckpt_{len(self.checkpoints)}",
            timestamp=time.time(),
            root_hash=root_hash,
            entry_count=len(checkpoint_entries),
            first_sequence=checkpoint_entries[0].sequence,
            last_sequence=checkpoint_entries[-1].sequence,
            tree_depth=tree_depth,
            leaves=leaves,
        )

        self.checkpoints.append(checkpoint)

        # Write checkpoint
        with open(self.checkpoint_file, "a") as f:
            f.write(json.dumps(asdict(checkpoint)) + "\n")

        logger.info(
            f"Created checkpoint {checkpoint.checkpoint_id} "
            f"(entries {checkpoint.first_sequence}-{checkpoint.last_sequence})"
        )

    def _build_merkle_tree(self, leaves: List[str]) -> tuple[str, int]:
        """
        Build Merkle tree from leaves.

        Returns:
            (root_hash, depth)
        """
        if not leaves:
            return "", 0

        if len(leaves) == 1:
            return leaves[0], 1

        # Build tree bottom-up
        current_level = leaves
        depth = 0

        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    # Pair of nodes
                    combined = current_level[i] + current_level[i + 1]
                else:
                    # Odd node, hash with itself
                    combined = current_level[i] + current_level[i]
                node_hash = hashlib.sha256(combined.encode()).hexdigest()
                next_level.append(node_hash)
            current_level = next_level
            depth += 1

        return current_level[0], depth

    def verify_chain(self) -> tuple[bool, Optional[str]]:
        """
        Verify hash chain integrity.

        Returns:
            (is_valid, error_message)
        """
        for i, entry in enumerate(self.entries):
            # Verify envelope signature
            if not self.verify_envelope(entry):
                return False, f"Invalid signature for entry {entry.sequence}"

            # Verify hash chain
            if i > 0:
                prev_entry = self.entries[i - 1]
                if entry.prev_hash != prev_entry.entry_hash:
                    return (
                        False,
                        f"Hash chain broken at entry {entry.sequence}",
                    )

            # Verify entry hash
            computed_hash = entry.compute_hash()
            if entry.entry_hash != computed_hash:
                return False, f"Invalid entry hash for entry {entry.sequence}"

        return True, None

    def get_entries(
        self,
        run_id: Optional[str] = None,
        schema_id: Optional[str] = None,
        start_sequence: Optional[int] = None,
        end_sequence: Optional[int] = None,
    ) -> List[LedgerEntry]:
        """
        Query ledger entries.

        Args:
            run_id: Filter by run_id
            schema_id: Filter by schema_id
            start_sequence: Start sequence number
            end_sequence: End sequence number

        Returns:
            List of matching entries
        """
        results = self.entries

        if run_id:
            results = [e for e in results if e.run_id == run_id]

        if schema_id:
            results = [e for e in results if e.schema_id == schema_id]

        if start_sequence is not None:
            results = [e for e in results if e.sequence >= start_sequence]

        if end_sequence is not None:
            results = [e for e in results if e.sequence <= end_sequence]

        return results

    def get_latest_checkpoint(self) -> Optional[MerkleCheckpoint]:
        """Get latest Merkle checkpoint."""
        return self.checkpoints[-1] if self.checkpoints else None

    def export_telemetry(self, run_id: str) -> Dict[str, Any]:
        """
        Export telemetry data for a run.

        Args:
            run_id: Run identifier

        Returns:
            Telemetry data dict
        """
        entries = self.get_entries(run_id=run_id)
        return {
            "run_id": run_id,
            "entry_count": len(entries),
            "first_sequence": entries[0].sequence if entries else None,
            "last_sequence": entries[-1].sequence if entries else None,
            "entries": [asdict(e) for e in entries],
            "checkpoints": [asdict(c) for c in self.checkpoints],
        }
