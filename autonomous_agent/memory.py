from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


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
                "decisions": [],
                "last_run": None,
            }

        try:
            return json.loads(self.state_path.read_text())
        except json.JSONDecodeError:
            return {
                "queue": [],
                "observations": [],
                "errors": [],
                "decisions": [],
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

    def add_decision(self, decision: Dict[str, Any]) -> None:
        state = self.load()
        state.setdefault("decisions", []).append(decision)
        self.save(state)

    def last_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        state = self.load()
        return list(reversed(state.get("errors", [])))[:limit]

    def last_decisions(self, limit: int = 10) -> List[Dict[str, Any]]:
        state = self.load()
        return list(reversed(state.get("decisions", [])))[:limit]
