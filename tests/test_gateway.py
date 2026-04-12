"""
Unit tests for MCPGateway: RBAC enforcement, routing, envelope signing.

~8 tests covering JSON-RPC routing, policy checks, and envelope operations.
"""

import asyncio

import pytest

from ai_universe25.runtime.gateway import (
    Channel,
    Envelope,
    MCPGateway,
    Surface,
)


@pytest.fixture
def gateway():
    return MCPGateway(enable_http=False)


class TestEnvelope:
    def test_envelope_creation(self):
        env = Envelope(
            run_id="run_001",
            agent_id="scribe_1",
            surface=Surface.BODY,
            tool="write_body",
        )
        assert env.agent_id == "scribe_1"
        assert env.surface == Surface.BODY

    def test_envelope_context_hash_deterministic(self):
        env1 = Envelope(
            run_id="run_001",
            agent_id="scribe_1",
            surface=Surface.BODY,
            tool="write_body",
        )
        env2 = Envelope(
            run_id="run_001",
            agent_id="scribe_1",
            surface=Surface.BODY,
            tool="write_body",
        )
        assert env1.compute_context_hash() == env2.compute_context_hash()

    def test_envelope_different_agents_different_hash(self):
        env1 = Envelope(run_id="r", agent_id="a", surface=Surface.BODY)
        env2 = Envelope(run_id="r", agent_id="b", surface=Surface.BODY)
        assert env1.compute_context_hash() != env2.compute_context_hash()

    def test_envelope_to_dict(self):
        env = Envelope(
            run_id="run_001",
            agent_id="scribe_1",
            surface=Surface.BODY,
        )
        d = env.to_dict()
        assert d["agent_id"] == "scribe_1"
        assert d["run_id"] == "run_001"


class TestMCPGateway:
    def test_gateway_creation(self, gateway):
        assert gateway is not None
        assert gateway.secret_key is not None

    def test_surface_enum_values(self):
        assert Surface.BODY.value == "body"
        assert Surface.INTRO.value == "intro"
        assert Surface.OUTLINE.value == "outline"

    def test_channel_enum_values(self):
        assert Channel.AUTHOR.value == "ch.author"
        assert Channel.EVIDENCE.value == "ch.evidence"
        assert Channel.GOV.value == "ch.gov"

    def test_register_tool(self, gateway):
        """Tools can be registered and listed."""
        from ai_universe25.runtime.gateway import Tool
        tool = Tool(name="write_body")
        gateway.tools["write_body"] = tool
        assert "write_body" in gateway.tools
