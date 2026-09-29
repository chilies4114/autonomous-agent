from __future__ import annotations

from dataclasses import dataclass, field
import os
from typing import List


@dataclass
class Settings:
    allowed_domains: List[str] = field(default_factory=lambda: ["example.com"])
    max_pages_per_cycle: int = 5
    max_errors_per_task: int = 3
    token_budget_per_day: int = 200000
    fetch_budget_per_day: int = 100
    polling_interval_seconds: int = 30
    paused: bool = False
    model_provider: str = "none"
    model_name: str = "gpt-4o-mini"

    @classmethod
    def from_env(cls) -> "Settings":
        raw_domains = os.getenv("AUTO_AGENT_ALLOWED_DOMAINS", "example.com")
        domains = [d.strip() for d in raw_domains.split(",") if d.strip()]

        return cls(
            allowed_domains=domains,
            max_pages_per_cycle=int(os.getenv("AUTO_AGENT_MAX_PER_CYCLE", "5")),
            max_errors_per_task=int(os.getenv("AUTO_AGENT_MAX_ERRORS_PER_TASK", "3")),
            token_budget_per_day=int(os.getenv("AUTO_AGENT_TOKEN_BUDGET_PER_DAY", "200000")),
            fetch_budget_per_day=int(os.getenv("AUTO_AGENT_FETCH_BUDGET_PER_DAY", "100")),
            polling_interval_seconds=int(os.getenv("AUTO_AGENT_POLL_INTERVAL_SECONDS", "30")),
            paused=os.getenv("AUTO_AGENT_PAUSED", "false").lower() in {"1", "true", "yes", "on"},
            model_provider=os.getenv("AUTO_AGENT_MODEL_PROVIDER", "none").strip() or "none",
            model_name=os.getenv("AUTO_AGENT_MODEL_NAME", "gpt-4o-mini").strip() or "gpt-4o-mini",
        )
