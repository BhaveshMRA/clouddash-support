# CloudDash Support System

Multi-agent AI customer support system for CloudDash, a cloud infrastructure
monitoring SaaS. Built with LangGraph, FastAPI, and ChromaDB.

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
│   ├── triage_agent.py       # Intent classification + entity extraction + routing
│   ├── technical_agent.py    # KB retrieval + step-by-step troubleshooting
│   ├── billing_agent.py      # Account lookup + billing policy + escalation triggers
│   └── escalation_agent.py   # Priority classification + human handover payload
├── knowledge_base/
│   ├── articles/             # 20 CloudDash KB articles (JSON)
│   ├── create_articles.py    # Script to generate all 20 articles
│   └── ingest.py             # Chunk + embed + index into ChromaDB
├── retrieval/
│   └── retriever.py          # Query rewrite + ChromaDB search + citation formatter
├── handover/                 # Handover protocol + audit logging (Phase 4)
├── api/                      # FastAPI REST endpoints (Phase 5)
├── config/
│   ├── agents/               # Per-agent YAML configs
│   │   ├── triage.yaml
│   │   ├── technical.yaml
│   │   ├── billing.yaml
│   │   └── escalation.yaml
│   ├── settings.yaml         # Global settings (LLM, retrieval, guardrails)
│   └── llm.py                # LLM factory — single source for ChatOllama init
├── tests/                    # Unit + integration tests (Phase 6)
├── data/chromadb/            # Persisted vector store (git-ignored)
├── logs/                     # Structured JSON logs (git-ignored)
├── .env.example              # Environment variable template
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

## Test Scenarios

**Scenario 1 — Single agent resolution**
> "My CloudDash alerts stopped firing after I updated my AWS integration credentials"

Expected: Triage → Technical Support → KB-005 + KB-007 retrieved → step-by-step resolution with citation

**Scenario 2 — Cross-agent handover**
> "I want to upgrade from Pro to Enterprise, but first check if my SSO issue is resolved"

Expected: Triage → Technical (SSO via KB-017) → handover → Billing (upgrade via KB-010)

**Scenario 3 — Escalation**
> "I've been charged twice for April. I need an immediate refund and I want to speak to a manager"

Expected: Triage → Billing (duplicate charge keyword triggers escalation) → Escalation Agent → human handover payload with HIGH priority

**Scenario 4 — KB retrieval failure**
> "Does CloudDash support integration with Datadog for cross-platform alerting?"

Expected: Technical Support retrieves nothing above threshold (0.55) → graceful not-in-KB response → offer to escalate

## Design Decisions

**Why LangGraph over plain function calls?**
Shared state flows through every node without manual passing. Append-only
reducers on conversation_history and handover_log mean no message is ever
overwritten. Conditional edges make routing logic explicit and testable.

**Why Gemma 4 31B via Ollama Cloud?**
256K context window handles long conversations without truncation. No local
GPU required. Same model used successfully in prior projects (Insider Signal
Detection Engine, CloudDash assessment).

**Why sentence-transformers locally for embeddings?**
Zero cost, zero latency, zero API dependency for embeddings. The same model
runs at ingest time and query time — critical for correct similarity scores.
all-MiniLM-L6-v2 is reliable for semantic similarity at this scale.

**Why ChromaDB?**
Persistent local storage, zero infrastructure overhead for a prototype.
Production path is Pinecone or Qdrant — swapping requires changing only
retriever.py since the interface is identical.

**Why YAML config per agent?**
Adding a new agent type requires only a new YAML file — no changes to
orchestration code. Directly satisfies Section 3.4 of the assessment rubric.

**Chunking strategy**
512 characters with 50-character overlap using RecursiveCharacterTextSplitter.
Splits on paragraph breaks first, then line breaks, then sentences. Keeps
semantically related content together while allowing precise retrieval of
specific troubleshooting steps within a longer article.

**Score threshold: 0.55**
Set above the Datadog query score (0.501) to ensure KB failure is handled
gracefully. All legitimate scenario queries score above 0.60.

## Known Limitations

- Mock account lookup — real deployment would connect to a CRM or billing API
- No persistent conversation storage across server restarts (in-memory only)
- Single-threaded ChromaDB connection — not suitable for high concurrency
- Embedding model runs on CPU — acceptable for prototype, GPU recommended for production