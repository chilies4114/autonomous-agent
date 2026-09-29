from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
import json


@dataclass
class BudgetTracker:
    token_budget_per_day: int
    fetch_budget_per_day: int
    token_spent: int = 0
    fetches_used: int = 0

    def can_fetch(self) -> bool:
        return self.fetches_used < self.fetch_budget_per_day

    def can_use_tokens(self, tokens: int = 0) -> bool:
        return (self.token_spent + tokens) <= self.token_budget_per_day

    def consume(self, tokens: int = 0, fetch_count: int = 1) -> None:
        self.token_spent += tokens
        self.fetches_used += fetch_count

    def snapshot(self) -> Dict[str, int]:
        return {
            "token_spent": self.token_spent,
            "token_budget": self.token_budget_per_day,
            "fetches_used": self.fetches_used,
            "fetch_budget": self.fetch_budget_per_day,
        }


class MemoryStore:
    def __init__(self, state_path: str | Path):
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        if not self.state_path.exists():
            return {
                "queue": [],
                "observations": [],
                "errors": [],
                "last_run": None,
            }

        try:
            return json.loads(self.state_path.read_text())
        except json.JSONDecodeError:
            return {
                "queue": [],
                "observations": [],
                "errors": [],
                "last_run": None,
            }

    def save(self, state: Dict[str, Any]) -> None:
        self.state_path.write_text(json.dumps(state, indent=2, sort_keys=True))

    def enqueue(self, item: Dict[str, Any]) -> None:
        state = self.load()
        state.setdefault("queue", []).append(item)
        self.save(state)

    def add_observation(self, observation: Dict[str, Any]) -> None:
        state = self.load()
        state.setdefault("observations", []).append(observation)
        self.save(state)

    def add_error(self, error: Dict[str, Any]) -> None:
        state = self.load()
        state.setdefault("errors", []).append(error)
        self.save(state)

    def last_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        state = self.load()
        return list(reversed(state.get("errors", [])))[:limit]
