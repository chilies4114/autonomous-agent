from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


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
