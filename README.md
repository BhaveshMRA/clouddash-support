# CloudDash Support System

Multi-agent AI customer support system for CloudDash, a cloud infrastructure
monitoring SaaS. Built with LangGraph, FastAPI, and ChromaDB.

**Live API:** https://web-production-4096b.up.railway.app
**Interactive docs:** https://web-production-4096b.up.railway.app/docs

> Note: hosted on Railway free tier — first request after inactivity may take
> 30-60 seconds (cold start). Hit `/health` first to warm it up before a demo.

## Tech Stack

| Component | Technology |
|---|---|
| LLM | Gemma 4 31B via Ollama Cloud |
| Orchestration | LangGraph StateGraph |
| Vector store | ChromaDB (persistent, local) |
| Embeddings | sentence-transformers all-MiniLM-L6-v2 (local CPU) |
| API | FastAPI REST |
| Config | YAML per agent + global settings.yaml |
| Logging | structlog (JSON structured logs with trace IDs) |

## Agents

| Agent | Responsibility | Escalates when |
|---|---|---|
| Triage | Classifies intent, extracts entities, routes | Unknown intent |
| Technical Support | KB retrieval + step-by-step troubleshooting | No KB match found |
| Billing | Account lookup + policy citation + plan changes | Duplicate charge, manager request |
| Escalation | Priority classification + human handover packaging | Terminal node |

## Project Structure

```
clouddash-support/
├── agents/
│   ├── state.py              # Shared LangGraph state schema (SupportState)
│   ├── base.py               # BaseAgent — YAML config loader, LLM picker
│   ├── orchestrator.py       # LangGraph StateGraph — nodes, routing, graph compile
│   ├── triage_agent.py       # Intent classification + entity extraction + routing
│   ├── technical_agent.py    # KB retrieval + step-by-step troubleshooting
│   ├── billing_agent.py      # Account lookup + billing policy + escalation triggers
│   └── escalation_agent.py   # Priority classification + human handover payload
├── knowledge_base/
│   ├── articles/             # 20 CloudDash KB articles (JSON)
│   ├── create_articles.py    # Script to generate all 20 articles
│   └── ingest.py             # Chunk + embed + index into ChromaDB
├── retrieval/
│   ├── retriever.py          # Query rewrite + ChromaDB search + citation formatter
│   └── guardrails.py         # Input guardrail (injection detection) + output grounding
├── handover/
│   ├── protocol.py           # Handover context packaging
│   └── audit_log.py          # JSON Lines audit log — every handover event
├── api/
│   ├── main.py               # FastAPI app — 3 endpoints + health check
│   └── models.py             # Pydantic request/response models
├── config/
│   ├── agents/               # Per-agent YAML configs
│   │   ├── triage.yaml
│   │   ├── technical.yaml
│   │   ├── billing.yaml
│   │   └── escalation.yaml
│   ├── settings.yaml         # Global settings (LLM, retrieval, guardrails)
│   └── llm.py                # LLM factory — single source for ChatOllama init
├── tests/
│   ├── test_guardrails.py    # 6 unit tests — input guardrail boundary conditions
│   ├── test_retriever.py     # 7 unit tests — RAG retrieval accuracy per scenario
│   ├── test_agents.py        # 10 unit tests — agent routing and escalation logic
│   └── test_api.py           # 8 integration tests — full API endpoint coverage
├── data/chromadb/            # Persisted vector store (git-ignored)
├── logs/                     # Structured JSON logs + handover audit (git-ignored)
├── .env.example              # Environment variable template
├── Procfile                  # Railway process definition
├── railway.json              # Railway deployment config
├── requirements.txt
└── README.md
```

## Setup

```bash
# 1. Clone and create virtual environment
python3 -m venv venv && source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Add your OLLAMA_API_KEY to .env

# 4. Build the knowledge base vector store
python knowledge_base/ingest.py

# 5. Start the API
uvicorn api.main:app --reload

# API available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| OLLAMA_API_KEY | Yes | Ollama Cloud API key (ollama.com/settings/keys) |
| LANGCHAIN_API_KEY | No | LangSmith tracing (recommended for demo) |
| LANGCHAIN_TRACING_V2 | No | Set to true to enable LangSmith tracing |
| LANGCHAIN_PROJECT | No | LangSmith project name (default: clouddash-support) |

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /conversation | Start a new conversation (returns trace_id) |
| POST | /conversation/{id}/message | Send a message, get agent response |
| GET | /conversation/{id}/history | Retrieve full conversation history |
| GET | /health | Health check + active conversation count |

## Test Scenarios

**Scenario 1 — Single agent resolution**
> "My CloudDash alerts stopped firing after I updated my AWS integration credentials"

Expected: Triage → Technical Support → KB-005 + KB-008 retrieved → step-by-step resolution with inline citations

**Scenario 2 — Cross-agent handover**
> "I want to upgrade from Pro to Enterprise, but first check if my SSO issue is resolved"

Expected: Triage → Technical (SSO via KB-017) → handover logged → Billing (upgrade via KB-010)

**Scenario 3 — Escalation**
> "I've been charged twice for April. I need an immediate refund and I want to speak to a manager"

Expected: Triage → Billing (duplicate charge keyword triggers immediate escalation) → Escalation Agent → human handover payload with HIGH priority, awaiting_human: true

**Scenario 4 — KB retrieval failure**
> "Does CloudDash support integration with Datadog for cross-platform alerting?"

Expected: Technical Support retrieves nothing above score threshold (0.55) → graceful not-in-KB response → offer to escalate to product team

## Running Tests

```bash
python3 -m pytest tests/ -v
# 31 passed
```

## Design Decisions

**Why LangGraph over plain function calls?**
Shared state flows through every node without manual passing. Append-only
reducers on conversation_history and handover_log mean no message is ever
overwritten. Conditional edges make routing logic explicit and testable.
The orchestrator is the only file that knows about routing — agents are
completely decoupled from each other.

**Why Gemma 4 31B via Ollama Cloud?**
256K context window handles long multi-turn conversations without truncation.
No local GPU required. The same model was used in the Local AI Researcher
project (LangGraph + RAG pipeline), so the integration pattern is proven.

**Why sentence-transformers locally for embeddings?**
Zero cost, zero latency, zero API dependency for embeddings. The same model
runs at ingest time and query time — critical because mismatched models
produce garbage similarity scores. all-MiniLM-L6-v2 is reliable for semantic
similarity at this scale and runs on CPU in under 1 second per query.

**Why ChromaDB?**
Persistent local storage, zero infrastructure overhead for a prototype.
Production path is Pinecone or Qdrant — swapping requires changing only
retrieval/retriever.py since the interface is identical. ChromaDB's
hnsw:space cosine setting ensures direction-of-meaning comparison
rather than magnitude, which is more accurate for text of varying lengths.

**Why YAML config per agent?**
Adding a new agent type requires only a new YAML file — zero changes to
orchestration code. This directly satisfies Section 3.4 of the assessment
rubric. Demonstrating config/agents/onboarding.yaml as the only change
needed to add an Onboarding Agent is the concrete answer to that live
discussion question.

**Chunking strategy**
512 characters with 50-character overlap using RecursiveCharacterTextSplitter.
Splits on paragraph breaks first, then line breaks, then sentence ends.
This keeps semantically related content together while allowing precise
retrieval of specific troubleshooting steps within a longer article.
94 chunks from 20 articles (avg 4.7 per article).

**Score threshold: 0.55**
Tuned empirically. The Datadog query (Scenario 4) scores 0.501 against the
closest article — setting threshold at 0.55 ensures this correctly triggers
the not-in-KB fallback. All legitimate scenario queries score above 0.60.

**Handover audit logging**
Every handover event is written as a JSON line to logs/handover_audit.jsonl
with: trace_id, timestamp, source_agent, target_agent, reason,
entity_snapshot, success. This satisfies the Section 2.3 requirement
verbatim and provides a complete audit trail queryable by trace ID.

## Known Limitations

- Mock account lookup — real deployment would connect to a CRM or billing API
- No persistent conversation storage across server restarts (in-memory dict)
- Single-threaded ChromaDB connection — not suitable for high concurrency
- Embedding model runs on CPU — acceptable for prototype, GPU recommended for production
- Railway free tier cold start — first request after inactivity takes 30-60 seconds
- Scenario 2 dual-intent handover routes Technical to Escalation instead of Billing
  due to single-intent classification in Triage. Fix: add secondary_intent field to
  SupportState and check it after the first specialist resolves.
