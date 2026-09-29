from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .budget import BudgetTracker
from .memory import MemoryStore
from .policies import Policy
from .scraper import WebScraper


class ResearchAgent:
    def __init__(
        self,
        memory_store: MemoryStore,
        budget: BudgetTracker,
        policy: Policy,
        scraper: Optional[WebScraper] = None,
        llm_client: Optional[Any] = None,
    ):
        self.memory = memory_store
        self.budget = budget
        self.policy = policy
        self.scraper = scraper or WebScraper()
        self.llm_client = llm_client
        self.logger = logging.getLogger("autonomous-agent")

    def _seed_default_tasks(self) -> None:
        state = self.memory.load()
        if state.get("queue"):
            return

        state["queue"] = [
            {"id": "seed-demo", "url": "https://example.com", "goal": "Fetch a safe example page."},
        ]
        self.memory.save(state)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _summarize_page(self, task: Dict[str, Any], result: Dict[str, str]) -> str:
        if self.llm_client is None:
            snippet = result.get("text", "")
            return snippet[:220].strip() or f"Fetched {result.get('url')}"

        try:
            return self.llm_client.generate_summary(task, result)
        except Exception as exc:  # pragma: no cover - fallback path
            self.logger.warning("LLM summary failed for task %s: %s", task.get("id"), exc)
            snippet = result.get("text", "")
            return snippet[:220].strip() or f"Fetched {result.get('url')}"

    def _apply_correction(self, task: Dict[str, Any], exc: Exception) -> None:
        task["retry_count"] = task.get("retry_count", 0) + 1
        task["last_error"] = str(exc)
        task["last_attempt"] = self._now()
        task["corrective_note"] = "retry with smaller fetch scope and more restrictive extraction"

    def run_cycle(self) -> Dict[str, Any]:
        self._seed_default_tasks()
        state = self.memory.load()
        queue = state.get("queue", [])
        processed: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        for task in list(queue):
            if len(processed) >= self.policy.max_pages_per_cycle:
                break

            task_id = task.get("id", task.get("url", "task"))
            task_url = task.get("url")

            if not task_url:
                errors.append({"task": task_id, "timestamp": self._now(), "error": "Task missing URL."})
                queue.remove(task)
                continue

            if not self.policy.is_allowed_url(task_url):
                errors.append({
                    "task": task_id,
                    "timestamp": self._now(),
                    "error": self.policy.explain_block(task_url),
                })
                queue.remove(task)
                continue

            if not self.budget.can_fetch():
                errors.append({
                    "task": task_id,
                    "timestamp": self._now(),
                    "error": "Fetch budget exhausted for the day.",
                })
                break

            if not self.budget.can_use_tokens(tokens=250):
                errors.append({
                    "task": task_id,
                    "timestamp": self._now(),
                    "error": "Token budget exhausted for the day.",
                })
                break

            try:
                result = self.scraper.fetch(task_url)
                self.budget.consume(tokens=250, fetch_count=1)
                summary = self._summarize_page(task, result)
                observation = {
                    "task": task_id,
                    "url": result["url"],
                    "title": result.get("title", ""),
                    "summary": summary,
                    "timestamp": self._now(),
                    "domain": result.get("domain", ""),
                }
                self.memory.add_observation(observation)
                self.memory.add_decision({
                    "task": task_id,
                    "decision": "fetched and summarized page",
                    "timestamp": self._now(),
                    "summary": summary,
                })
                processed.append(observation)
                queue.remove(task)
            except Exception as exc:  # pragma: no cover - resilient retry path
                self.logger.warning("Task %s failed: %s", task_id, exc)
                error = {
                    "task": task_id,
                    "url": task_url,
                    "timestamp": self._now(),
                    "error": str(exc),
                }
                errors.append(error)
                self.memory.add_error(error)

                if self.policy.should_retry(task, self.memory.last_errors(limit=100)):
                    self._apply_correction(task, exc)
                    task["retry_count"] = task.get("retry_count", 0)
                    continue
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
