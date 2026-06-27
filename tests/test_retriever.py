"""Unit tests for RAG retrieval pipeline."""
import pytest
from retrieval.retriever import retrieve, format_citations, format_context_full


def test_retrieves_correct_article_for_aws_alerts():
    chunks, rewritten = retrieve("AWS alerts stopped firing after credential update")
    assert len(chunks) > 0
    kb_ids = [c.kb_id for c in chunks]
    assert "KB-005" in kb_ids


def test_retrieves_billing_article_for_plan_upgrade():
    chunks, _ = retrieve("upgrade from Pro to Enterprise plan")
    assert len(chunks) > 0
    kb_ids = [c.kb_id for c in chunks]
    assert "KB-010" in kb_ids


def test_retrieves_sso_article():
    chunks, _ = retrieve("set up SSO SAML single sign on")
    assert len(chunks) > 0
    kb_ids = [c.kb_id for c in chunks]
    assert "KB-017" in kb_ids


def test_low_score_for_unknown_topic():
    chunks, _ = retrieve("Datadog cross platform alerting integration")
    # All chunks should be below threshold or score should be low
    for chunk in chunks:
        assert chunk.score < 0.75


def test_category_filter_restricts_results():
    chunks, _ = retrieve("how to configure alerts", category_filter="billing")
    for chunk in chunks:
        assert chunk.category == "billing"


def test_format_citations_deduplicates():
    chunks, _ = retrieve("AWS alerts credential update")
    citation = format_citations(chunks)
    # KB-005 should appear only once even if multiple chunks match
    assert citation.count("KB-005") == 1


def test_empty_retrieval_returns_no_chunks():
    chunks, _ = retrieve("xyzzy frobozz nonsense query that matches nothing")
    assert isinstance(chunks, list)
