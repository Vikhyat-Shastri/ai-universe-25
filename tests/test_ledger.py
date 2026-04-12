"""
Unit tests for AppendOnlyLedger: hash chain, tamper detection, Merkle, HMAC.

~10 tests covering integrity, persistence, and verification.
"""

import json
import tempfile
from pathlib import Path

import pytest

from ai_universe25.ledger.ledger import AppendOnlyLedger, LedgerEntry
from ai_universe25.runtime.gateway import Envelope, Surface


@pytest.fixture
def ledger_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def ledger(ledger_dir):
    return AppendOnlyLedger(ledger_dir=ledger_dir, checkpoint_interval=5)


def _make_envelope(agent_id="agent_1", surface=Surface.BODY):
    return Envelope(
        run_id="test_run",
        agent_id=agent_id,
        surface=surface,
        tool="write_body",
    )


class TestAppendOnlyLedger:
    def test_append_creates_entry(self, ledger):
        envelope = _make_envelope()
        entry = ledger.append(envelope, schema_id="test.v1", content={"text": "hello"})
        assert entry.sequence == 0
        assert entry.schema_id == "test.v1"
        assert entry.entry_hash is not None

    def test_hash_chain_integrity(self, ledger):
        """Each entry references the previous entry's hash."""
        for i in range(5):
            ledger.append(
                _make_envelope(agent_id=f"agent_{i}"),
                schema_id="test.v1",
                content={"i": i},
            )
        for i in range(1, len(ledger.entries)):
            assert ledger.entries[i].prev_hash == ledger.entries[i - 1].entry_hash

    def test_tamper_detection(self, ledger):
        """Modifying an entry breaks the hash chain."""
        for i in range(5):
            ledger.append(
                _make_envelope(agent_id=f"agent_{i}"),
                schema_id="test.v1",
                content={"i": i},
            )
        # Tamper with entry 2
        original_hash = ledger.entries[2].entry_hash
        ledger.entries[2].schema_id = "tampered.v1"
        recomputed = ledger.entries[2].compute_hash()
        assert recomputed != original_hash

    def test_merkle_checkpoint(self, ledger):
        """Merkle checkpoints are created at intervals."""
        for i in range(10):
            ledger.append(
                _make_envelope(agent_id=f"agent_{i}"),
                schema_id="test.v1",
                content={"i": i},
            )
        # checkpoint_interval=5, so we should have checkpoints
        assert len(ledger.checkpoints) >= 1

    def test_jsonl_persistence(self, ledger_dir):
        """Ledger entries survive persistence round-trip."""
        ledger1 = AppendOnlyLedger(ledger_dir=ledger_dir)
        for i in range(3):
            ledger1.append(
                _make_envelope(agent_id=f"agent_{i}"),
                schema_id="test.v1",
                content={"i": i},
            )
        original_count = len(ledger1.entries)

        # Reload
        ledger2 = AppendOnlyLedger(ledger_dir=ledger_dir)
        assert len(ledger2.entries) == original_count

    def test_content_hash_consistency(self, ledger):
        """Same content produces same content hash."""
        content = {"text": "deterministic"}
        e1 = ledger.append(_make_envelope(), schema_id="t.v1", content=content)
        e2 = ledger.append(_make_envelope(), schema_id="t.v1", content=content)
        assert e1.content_hash == e2.content_hash

    def test_sequence_counter_increments(self, ledger):
        ledger.append(_make_envelope(), schema_id="t.v1", content={"a": 1})
        ledger.append(_make_envelope(), schema_id="t.v1", content={"b": 2})
        assert ledger.entries[0].sequence == 0
        assert ledger.entries[1].sequence == 1

    def test_empty_ledger(self, ledger):
        assert len(ledger.entries) == 0
        assert ledger.sequence_counter == 0

    def test_multiple_agents(self, ledger):
        for agent_id in ["herald_0", "scribe_1", "verifier_2"]:
            ledger.append(
                _make_envelope(agent_id=agent_id),
                schema_id="test.v1",
                content={"from": agent_id},
            )
        assert len(ledger.entries) == 3
        agents = [e.envelope.get("agent_id") or e.envelope.get("agent", "") for e in ledger.entries]
        assert len(set(agents)) == 3
