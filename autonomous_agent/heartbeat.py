from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .budget import BudgetTracker
from .memory import MemoryStore
from .policies import Policy
from .scraper import WebScraper


class ResearchAgent:
    def __init__(self, memory_store: MemoryStore, budget: BudgetTracker, policy: Policy, scraper: Optional[WebScraper] = None):
        self.memory = memory_store
        self.budget = budget
        self.policy = policy
        self.scraper = scraper or WebScraper()
        self.logger = logging.getLogger("autonomous-agent")

    def _seed_default_tasks(self) -> None:
        state = self.memory.load()
        if state.get("queue"):
            return
        state["queue"] = [
            {"id": "example-1", "url": "https://example.com", "goal": "Fetch a safe example page."},
        ]
        self.memory.save(state)

    def _task_status(self, task: Dict[str, Any]) -> Dict[str, Any]:
        errors = self.memory.last_errors(limit=20)
        matched = [e for e in errors if e.get("task") == task.get("id")]
        return {"errors": len(matched), "retry_count": task.get("retry_count", 0)}

    def run_cycle(self) -> Dict[str, Any]:
        self._seed_default_tasks()
        state = self.memory.load()
        queue = state.get("queue", [])
        processed: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        for task in queue[: self.policy.max_pages_per_cycle]:
            task_id = task.get("id", task.get("url", "task"))
            task_url = task.get("url")

            if not task_url:
                errors.append({"task": task_id, "timestamp": self._now(), "error": "Task is missing a URL."})
                continue

            if not self.policy.is_allowed_url(task_url):
                errors.append({
                    "task": task_id,
                    "timestamp": self._now(),
                    "error": self.policy.explain_block(task_url),
                })
                continue

            if not self.budget.can_fetch():
                errors.append({
                    "task": task_id,
                    "timestamp": self._now(),
                    "error": "Fetch budget exhausted for the day.",
                })
                break

            if not self.budget.can_use_tokens():
                errors.append({
                    "task": task_id,
                    "timestamp": self._now(),
                    "error": "Token budget exhausted for the day.",
                })
                break

            try:
                result = self.scraper.fetch(task_url)
                self.budget.consume(tokens=250, fetch_count=1)
                observation = {
                    "task": task_id,
                    "url": task_url,
                    "title": result["title"],
                    "summary": result["text"][:500],
                    "timestamp": self._now(),
                }
                self.memory.add_observation(observation)
                processed.append(observation)
                queue.remove(task)
            except Exception as exc:  # pragma: no cover - safety path
                self.logger.warning("Task failed: %s", exc)
                error = {
                    "task": task_id,
                    "url": task_url,
                    "timestamp": self._now(),
                    "error": str(exc),
                }
                errors.append(error)
                self.memory.add_error(error)

                if self.policy.should_retry(task, self.memory.last_errors(limit=100)):
                    task["retry_count"] = task.get("retry_count", 0) + 1
                    task["last_error"] = str(exc)
                    task["last_attempt"] = self._now()
                else:
                    queue.remove(task)

        state["queue"] = queue
        state["last_run"] = self._now()
        self.memory.save(state)

        return {
            "processed": processed,
            "errors": errors,
            "budget": self.budget.snapshot(),
            "queue_length": len(queue),
        }

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
