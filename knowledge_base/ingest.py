"""
knowledge_base/ingest.py

Reads all 20 KB articles, chunks the content, embeds each chunk
using sentence-transformers, and indexes everything into ChromaDB.

Run once before starting the API:
    python knowledge_base/ingest.py

To rebuild from scratch (e.g. after updating articles):
    python knowledge_base/ingest.py --reset
"""
import argparse
import json
import os
from pathlib import Path

import chromadb
import yaml
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT         = Path(__file__).parent.parent
ARTICLES_DIR = Path(__file__).parent / "articles"
SETTINGS_PATH = ROOT / "config" / "settings.yaml"

# ── Load settings ──────────────────────────────────────────────────────────────
with open(SETTINGS_PATH) as f:
    settings = yaml.safe_load(f)

CHROMA_DIR      = str(ROOT / settings["chromadb"]["persist_directory"])
COLLECTION_NAME = settings["chromadb"]["collection_name"]
CHUNK_SIZE      = settings["retrieval"]["chunk_size"]
CHUNK_OVERLAP   = settings["retrieval"]["chunk_overlap"]
EMBEDDING_MODEL = settings["retrieval"]["embedding_model"]


# ── Step 1: Load articles ──────────────────────────────────────────────────────

def load_articles() -> list[dict]:
    """Load every JSON file from knowledge_base/articles/."""
    articles = []
    for path in sorted(ARTICLES_DIR.glob("*.json")):
        with open(path) as f:
            articles.append(json.load(f))
    print(f"✓ Loaded {len(articles)} articles")
    return articles


# ── Step 2: Chunk content ──────────────────────────────────────────────────────

def chunk_articles(articles: list[dict]) -> list[dict]:
    """
    Split article content into overlapping chunks.

    Why chunk at all?
    An entire article (500-800 words) often covers multiple topics.
    Chunking lets the retriever return the specific paragraph that answers
    the customer's question rather than the entire article.

    Why RecursiveCharacterTextSplitter?
    It tries to split on paragraph breaks first (\n\n), then line breaks,
    then sentences. This keeps semantically related sentences together
    rather than cutting mid-thought.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []
    for article in articles:
        texts = splitter.split_text(article["content"])
        for i, text in enumerate(texts):
            chunks.append({
                "id": f"{article['id']}_chunk_{i}",
                "text": text,
                "metadata": {
                    "kb_id":        article["id"],
                    "title":        article["title"],
                    "category":     article["category"],
                    "tags":         ", ".join(article["tags"]),
                    "applies_to":   ", ".join(article["applies_to"]),
                    "last_updated": article["last_updated"],
                    "chunk_index":  i,
                    "total_chunks": len(texts),
                }
            })

    print(f"✓ Created {len(chunks)} chunks "
          f"(avg {len(chunks)/len(articles):.1f} per article)")
    return chunks


# ── Step 3: Embed and index ────────────────────────────────────────────────────

def embed_and_index(chunks: list[dict], reset: bool = False) -> chromadb.Collection:
    """
    Convert each chunk to a vector and store in ChromaDB.

    Why sentence-transformers locally instead of an API?
    - Zero cost: no API call per chunk
    - Zero latency: runs on CPU, fast enough for 20 articles
    - Consistent: same model used at ingest time and query time
      (critical — mismatched models produce garbage similarity scores)

    Why cosine similarity?
    We care about the direction of meaning, not the magnitude.
    Two chunks that discuss the same topic should have high cosine
    similarity even if one is twice as long as the other.
    """
    os.makedirs(CHROMA_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"✓ Deleted existing collection: {COLLECTION_NAME}")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    existing = collection.count()
    if existing > 0 and not reset:
        print(f"⚠ Collection already has {existing} chunks.")
        print("  Use --reset to rebuild from scratch.")
        return collection

    print(f"✓ Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    # Batch to avoid memory spikes
    batch_size   = 32
    total_batches = (len(chunks) + batch_size - 1) // batch_size

    for batch_num in range(total_batches):
        start = batch_num * batch_size
        end   = min(start + batch_size, len(chunks))
        batch = chunks[start:end]

        embeddings = model.encode(
            [c["text"] for c in batch],
            show_progress_bar=False,
        ).tolist()

        collection.add(
            ids        = [c["id"]       for c in batch],
            documents  = [c["text"]     for c in batch],
            embeddings = embeddings,
            metadatas  = [c["metadata"] for c in batch],
        )
        print(f"  Batch {batch_num + 1}/{total_batches} "
              f"({end}/{len(chunks)} chunks indexed)")

    print(f"✓ ChromaDB collection ready — {collection.count()} chunks "
          f"at {CHROMA_DIR}")
    return collection


# ── Step 4: Verify retrieval ───────────────────────────────────────────────────

def verify(collection: chromadb.Collection) -> None:
    """
    Run test queries that map to the 4 assessment scenarios.
    Confirms the right articles surface before we build agents on top.
    """
    model = SentenceTransformer(EMBEDDING_MODEL)

    test_queries = [
        ("alerts stopped firing after updating AWS credentials", "KB-005"),
        ("upgrade from Pro to Enterprise plan",                  "KB-010"),
        ("set up SSO SAML single sign on",                       "KB-017"),
        ("Datadog cross platform alerting integration",           "none — expect low score"),
    ]

    print("\n── Retrieval verification ────────────────────────────────────────")
    all_passed = True

    for query, expected_kb in test_queries:
        embedding = model.encode(query).tolist()
        results   = collection.query(
            query_embeddings=[embedding],
            n_results=2,
            include=["documents", "metadatas", "distances"],
        )

        top      = results["metadatas"][0][0]
        score    = 1 - results["distances"][0][0]  # distance → similarity
        hit      = top["kb_id"] == expected_kb
        status   = "✓" if hit or "none" in expected_kb else "✗"
        if not hit and "none" not in expected_kb:
            all_passed = False

        print(f"\n  {status} Query: '{query}'")
        print(f"    Top hit : [{top['kb_id']}] {top['title']}")
        print(f"    Score   : {score:.3f}  (expected: {expected_kb})")

    if all_passed:
        print("\n✓ All retrieval checks passed — RAG pipeline is ready")
    else:
        print("\n⚠ Some checks failed — review chunk size or embedding model")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reset", action="store_true",
        help="Delete and rebuild the ChromaDB collection from scratch"
    )
    args = parser.parse_args()

    print("=== CloudDash KB Ingestion Pipeline ===\n")
    articles   = load_articles()
    chunks     = chunk_articles(articles)
    collection = embed_and_index(chunks, reset=args.reset)
    verify(collection)
    print("\n=== Done — ready for Phase 3 (agent implementations) ===")
