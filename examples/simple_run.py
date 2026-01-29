"""
Simple example: Run a basic Grokipedia experiment.

Demonstrates the core components working together.
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_universe25.agents.orchestrator import AgentOrchestrator
from ai_universe25.runtime.rbac_ladder import AgentRole, RBACLadderEnforcer
from ai_universe25.tools.wiki_model import WikiPage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Run a simple example."""
    logger.info("Starting simple Grokipedia run")

    # Create wiki page
    page = WikiPage(page_id="test_page_1", title="Test Topic")

    # Create agent orchestrator
    orchestrator = AgentOrchestrator(public_only=True)
    orchestrator.create_agent_pipeline()

    # Initial context
    initial_context = {
        "page_title": "Test Topic",
        "lead_intro": "This is a test topic for demonstration.",
        "lead_sha256": "abc123",
    }

    # Execute pipeline
    handoffs = orchestrator.execute_pipeline(initial_context)

    logger.info(f"Pipeline completed: {len(handoffs)} handoffs")
    for handoff in handoffs:
        logger.info(f"  {handoff.from_agent} -> {handoff.to_agent}: {handoff.surface.value}")

    # Test RBAC + Ladder
    enforcer = RBACLadderEnforcer()
    from ai_universe25.runtime.gateway import Envelope, Surface

    envelope = Envelope(
        run_id="test_run",
        agent_id="scribe_1",
        surface=Surface.BODY,
        tool="write_body",
    )

    # Check RBAC
    can_write = await enforcer.check_rbac("scribe_1", Surface.BODY, "write")
    logger.info(f"Scribe can write to body: {can_write}")

    # Check ladder
    decision = await enforcer.check_ladder(envelope)
    logger.info(f"Ladder decision: {decision.allowed}, reason: {decision.reason}")

    logger.info("Simple run completed")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
