"""
retrieval/retriever.py

Retrieval chain used by all agents.

Flow:
  1. Takes user query + conversation history
  2. Rewrites query to be context-aware using the LLM
  3. Embeds the rewritten query
  4. Searches ChromaDB
  5. Filters by score threshold
  6. Returns formatted chunks with citations
"""
from __future__ import annotations

import os
from pathlib import Path

import chromadb
import yaml
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from sentence_transformers import SentenceTransformer

from agents.state import RetrievedChunk
from config.llm import get_llm

load_dotenv()

# ── Settings ───────────────────────────────────────────────────────────────────
ROOT          = Path(__file__).parent.parent
SETTINGS_PATH = ROOT / "config" / "settings.yaml"

with open(SETTINGS_PATH) as f:
    _settings = yaml.safe_load(f)

CHROMA_DIR       = str(ROOT / _settings["chromadb"]["persist_directory"])
COLLECTION_NAME  = _settings["chromadb"]["collection_name"]
TOP_K            = _settings["retrieval"]["top_k"]
SCORE_THRESHOLD  = _settings["retrieval"]["score_threshold"]
EMBEDDING_MODEL  = _settings["retrieval"]["embedding_model"]

# ── Singletons (loaded once, reused across all calls) ─────────────────────────
_embedding_model: SentenceTransformer | None = None
_collection: chromadb.Collection | None      = None


def _get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embedding_model


def _get_collection() -> chromadb.Collection:
    global _collection
    if _collection is None:
        client      = chromadb.PersistentClient(path=CHROMA_DIR)
        _collection = client.get_collection(COLLECTION_NAME)
    return _collection


# ── Query rewriter ─────────────────────────────────────────────────────────────

REWRITE_SYSTEM = """You are a search query optimizer for a customer support knowledge base.

Given a customer's latest message and recent conversation history, rewrite the
query into a concise, standalone search query that will find the most relevant
knowledge base articles.

Rules:
- Output ONLY the rewritten query — no explanation, no preamble
- Keep it under 20 words
- Include specific technical terms, product names, or error messages
- If the message is already a clear standalone query, return it unchanged
- Resolve pronouns using conversation history (e.g. "it" → "AWS integration")"""


def rewrite_query(query: str, history: list[dict]) -> str:
    """
    Rewrites the raw user query into a context-aware search query.

    Why this matters:
    Customer: "My alerts stopped working yesterday"
    → poor search query (no specifics)

    After 2 turns of conversation establishing it's an AWS issue:
    Customer: "It still isn't working"
    → terrible search query without context

    Rewriter turns "It still isn't working" into
    "AWS CloudWatch integration alerts not firing" — a great search query.
    """
    if not history:
        return query

    # Only pass last 3 turns to keep the rewrite prompt short
    recent = history[-3:]
    history_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in recent
    )

    llm      = get_llm(temperature=0.1)
    messages = [
        SystemMessage(content=REWRITE_SYSTEM),
        HumanMessage(content=f"Conversation history:\n{history_text}\n\nLatest message: {query}\n\nRewritten search query:"),
    ]

    result = llm.invoke(messages)
    rewritten = result.content.strip().strip('"').strip("'")
    return rewritten if rewritten else query


# ── Core retriever ─────────────────────────────────────────────────────────────

def retrieve(
    query: str,
    history: list[dict] | None = None,
    category_filter: str | None = None,
    top_k: int | None = None,
) -> tuple[list[RetrievedChunk], str]:
    """
    Main retrieval function called by every agent.

    Args:
        query:           Raw user query
        history:         Conversation history for context-aware rewriting
        category_filter: Optional — restrict to one KB category
                         ("faq", "troubleshooting", "billing", "api", "account")
        top_k:           Override default top_k from settings

    Returns:
        chunks:          List of RetrievedChunk objects above score threshold
        rewritten_query: The query actually used for search (useful for logging)
    """
    k          = top_k or TOP_K
    hist       = history or []

    # Step 1 — rewrite query for context awareness
    rewritten = rewrite_query(query, hist)

    # Step 2 — embed the rewritten query
    model     = _get_embedding_model()
    embedding = model.encode(rewritten).tolist()

    # Step 3 — build ChromaDB where filter
    where = None
    if category_filter:
        where = {"category": {"$eq": category_filter}}

    # Step 4 — search ChromaDB
    collection = _get_collection()
    results    = collection.query(
        query_embeddings=[embedding],
        n_results=k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    # Step 5 — convert to RetrievedChunk, filter by threshold
    chunks: list[RetrievedChunk] = []

    if not results["metadatas"] or not results["metadatas"][0]:
        return chunks, rewritten

    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        score = 1 - dist  # cosine distance → similarity
        if score < SCORE_THRESHOLD:
            continue

        chunks.append(RetrievedChunk(
            kb_id    = meta["kb_id"],
            title    = meta["title"],
            content  = doc,
            score    = round(score, 3),
            category = meta["category"],
        ))

    return chunks, rewritten


# ── Citation formatter ─────────────────────────────────────────────────────────

def format_context(chunks: list[RetrievedChunk]) -> str:
    """
    Formats retrieved chunks into a context block for agent prompts.

    Output format:
        [KB-005] Alerts Not Firing After Updating Cloud Integration Credentials
        ---
        <chunk content>

        [KB-007] AWS CloudWatch Integration Failing
        ---
        <chunk content>

    The agent's system prompt instructs it to cite [KB-XXX] in its response,
    so the customer can see which article the answer came from.
    """
    if not chunks:
        return "No relevant knowledge base articles found."

    sections = []
    seen_kb_ids = set()

    for chunk in chunks:
        # Deduplicate by KB id — show each article once even if multiple chunks matched
        if chunk.kb_id in seen_kb_ids:
            continue
        seen_kb_ids.add(chunk.kb_id)

        sections.append(
            f"[{chunk.kb_id}] {chunk.title}\n"
            f"---\n"
            f"{chunk.content}"
        )

    return "\n\n".join(sections)


def format_citations(chunks: list[RetrievedChunk]) -> str:
    """Returns a short citation line for the end of agent responses."""
    if not chunks:
        return ""
    seen = {}
    for c in chunks:
        if c.kb_id not in seen:
            seen[c.kb_id] = c.title
    return "Sources: " + " | ".join(f"[{k}] {v}" for k, v in seen.items())


def format_context_full(chunks: list[RetrievedChunk]) -> str:
    """
    Like format_context but shows ALL chunks per KB article,
    grouped together. This gives the agent the complete article
    content rather than just the first matching chunk.

    Use this in agent prompts instead of format_context.
    """
    if not chunks:
        return "No relevant knowledge base articles found."

    # Group chunks by KB ID preserving order
    grouped: dict[str, list[RetrievedChunk]] = {}
    for chunk in chunks:
        grouped.setdefault(chunk.kb_id, []).append(chunk)

    sections = []
    for kb_id, kb_chunks in grouped.items():
        title   = kb_chunks[0].title
        content = "\n\n".join(c.content for c in kb_chunks)
        sections.append(f"[{kb_id}] {title}\n---\n{content}")

    return "\n\n".join(sections)
