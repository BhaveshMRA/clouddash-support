"""
agents/base.py

Base class all agents inherit from.
Reads config from YAML so adding a new agent = new YAML file only.
No changes to orchestration code required.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from config.llm import get_llm, get_triage_llm

CONFIG_DIR = Path(__file__).parent.parent / "config" / "agents"


class BaseAgent:
    """
    Every agent inherits from this.

    Responsibilities:
    - Load system prompt and config from YAML
    - Provide a consistent .run(state) interface for LangGraph nodes
    - Handle errors without crashing the graph
    """

    def __init__(self, agent_name: str):
        config_path = CONFIG_DIR / f"{agent_name}.yaml"
        if not config_path.exists():
            raise FileNotFoundError(
                f"Agent config not found: {config_path}\n"
                f"Create config/agents/{agent_name}.yaml to define this agent."
            )

        with open(config_path) as f:
            self.config: dict[str, Any] = yaml.safe_load(f)

        self.name          = self.config["name"]
        self.display_name  = self.config["display_name"]
        self.system_prompt = self.config["system_prompt"].strip()

        # Triage uses low temperature for deterministic routing
        # All other agents use default temperature for natural responses
        if agent_name == "triage":
            self.llm = get_triage_llm()
        else:
            self.llm = get_llm()

    def get_routing_rules(self) -> dict:
        return self.config.get("routing_rules", {})

    def get_fallback(self) -> dict:
        return self.config.get("fallback", {})

    def get_guardrails(self) -> dict:
        return self.config.get("guardrails", {})

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name}>"
