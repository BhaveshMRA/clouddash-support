import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_ollama import ChatOllama

load_dotenv()


@lru_cache(maxsize=1)
def get_llm(temperature: float | None = None) -> ChatOllama:
    api_key = os.getenv("OLLAMA_API_KEY")
    if not api_key:
        raise ValueError("OLLAMA_API_KEY not set in .env")

    return ChatOllama(
        model="gemma4:31b-cloud",
        base_url="https://ollama.com",
        client_kwargs={
            "headers": {"Authorization": f"Bearer {api_key}"}
        },
        temperature=temperature if temperature is not None else 1.0,
        top_p=0.95,
        top_k=64,
        num_predict=2048,
    )


def get_triage_llm() -> ChatOllama:
    """Low temperature for Triage — routing needs determinism."""
    api_key = os.getenv("OLLAMA_API_KEY")
    return ChatOllama(
        model="gemma4:31b-cloud",
        base_url="https://ollama.com",
        client_kwargs={
            "headers": {"Authorization": f"Bearer {api_key}"}
        },
        temperature=0.1,
        top_p=0.95,
        top_k=64,
        num_predict=2048,
    )
