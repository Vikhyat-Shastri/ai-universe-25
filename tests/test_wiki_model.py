"""
Unit tests for WikiPage model.

~8 tests covering surface operations, revision history, shadow surfaces,
citation graph, and fact ledger.
"""

import pytest

from ai_universe25.runtime.gateway import Surface
from ai_universe25.tools.wiki_model import WikiPage


@pytest.fixture
def page():
    return WikiPage(page_id="test_001", title="Test Article")


class TestWikiPage:
    def test_create_page(self, page):
        assert page.title == "Test Article"
        assert page.page_id == "test_001"

    def test_write_surface(self, page):
        page.write_surface(Surface.INTRO, "Introduction content", "herald_1")
        content = page.get_current_content(Surface.INTRO)
        assert content == "Introduction content"

    def test_append_surface(self, page):
        page.write_surface(Surface.BODY, "First paragraph.", "scribe_1")
        page.append_surface(Surface.BODY, "Second paragraph.", "scribe_1")
        content = page.get_current_content(Surface.BODY)
        assert "First paragraph." in content
        assert "Second paragraph." in content

    def test_revision_history(self, page):
        page.write_surface(Surface.INTRO, "V1", "herald_1")
        page.write_surface(Surface.INTRO, "V2", "herald_1")
        revisions = page.get_revision_history(Surface.INTRO)
        assert len(revisions) == 2

    def test_citation_graph(self, page):
        page.add_citation(
            claim="The sky is blue",
            source_hash="abc123",
            quote_span=(0, 10),
        )
        citations = page.citation_graph
        assert len(citations) == 1

    def test_fact_ledger_append(self, page):
        page.add_fact_entry(
            claim="Test claim",
            verification_status="ENTAIL",
            evidence_hash="ev_hash_1",
            verifier_id="verifier_1",
        )
        assert len(page.fact_ledger) == 1
        assert page.fact_ledger[0].verification_status == "ENTAIL"

    def test_shadow_revision(self, page):
        page.write_surface(Surface.INTRO, "Normal content", "herald_1")
        page.write_surface(Surface.INTRO, "Shadow content", "herald_1", is_shadow=True)
        shadows = page.shadow_surfaces.get(Surface.INTRO, [])
        assert len(shadows) == 1

    def test_read_nonexistent_surface(self, page):
        content = page.get_current_content(Surface.SUMMARY)
        assert content is None
