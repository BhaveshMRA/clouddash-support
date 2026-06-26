# CloudDash Support System

Multi-agent AI customer support system for CloudDash, a cloud infrastructure
monitoring SaaS. Built with LangGraph, FastAPI, and ChromaDB.

## Architecture

See `ARCHITECTURE.md` for the full diagram.

**Agents:** Triage → Technical Support / Billing / Escalation
**LLM:** Gemma 4 31B via Ollama Cloud
**RAG:** ChromaDB + sentence-transformers (all-MiniLM-L6-v2)
**Orchestration:** LangGraph StateGraph with conditional routing
**API:** FastAPI REST — start conversation, send message, get history

## Setup

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your OLLAMA_API_KEY
python knowledge_base/ingest.py  # build the vector store
uvicorn api.main:app --reload
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| OLLAMA_API_KEY | Yes | Ollama Cloud API key |
| LANGCHAIN_API_KEY | No | LangSmith tracing (recommended) |
| LANGCHAIN_TRACING_V2 | No | Set to true to enable tracing |

## Design Decisions

- **LangGraph StateGraph** for orchestration — shared state eliminates manual context passing between agents
- **Gemma 4 31B via Ollama Cloud** — 256K context window, no local GPU required
- **ChromaDB** for vector store — persistent local storage, zero infrastructure overhead for prototype
- **YAML-configurable agents** — adding a new agent type requires only a new YAML file, no changes to orchestration code
- **Append-only conversation history** — LangGraph Annotated[list, add] reducer ensures no message is ever overwritten

## Known Limitations

_To be filled in before submission._
