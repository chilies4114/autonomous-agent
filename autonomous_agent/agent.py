from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .budget import BudgetTracker
from .crawler import URLFrontier
from .memory import MemoryStore
from .planner import ResearchPlanner
from .policies import Policy
from .scraper import WebScraper


class ResearchAgent:
    def __init__(self, memory_store: MemoryStore, budget: BudgetTracker, policy: Policy,
                 scraper: Optional[WebScraper] = None, llm_client: Optional[Any] = None,
                 planner: Optional[ResearchPlanner] = None):
        self.memory = memory_store
        self.budget = budget
        self.policy = policy
        self.scraper = scraper or WebScraper()
        self.llm_client = llm_client
        self.frontier = URLFrontier(policy, self.scraper)
        self.planner = planner or ResearchPlanner(memory_store, policy.max_pages_per_cycle)
        self.logger = logging.getLogger("autonomous-agent")

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def submit_goal(self, goal: str, seed_urls: List[str]) -> List[Dict[str, Any]]:
        return self.planner.plan(goal, seed_urls)

    def _summarize_page(self, task: Dict[str, Any], result: Dict[str, Any]) -> str:
        if self.llm_client is not None:
            try:
                return self.llm_client.generate_summary(task, result)
            except Exception as exc:
                self.logger.warning("Summary failed; using extractive fallback: %s", exc)
        return result.get("text", "")[:300].strip() or f"Fetched {result['url']}"

    def run_cycle(self) -> Dict[str, Any]:
        tasks = self.memory.queued_tasks(self.policy.max_pages_per_cycle)
        processed: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []
        for task in tasks:
            task_id, url = task["id"], task.get("url")
            if not url or not self.policy.is_allowed_url(url):
                error = {"task_id": task_id, "url": url, "timestamp": self._now(), "error": self.policy.explain_block(url or "")}
                self.memory.add_error(error); self.memory.discard(task_id); errors.append(error); continue
            if not self.budget.can_fetch() or not self.budget.can_use_tokens(250):
                break
            try:
                result = self.scraper.fetch(url)
                self.budget.consume(tokens=250, fetch_count=1)
                summary = self._summarize_page(task, result)
                observation = {"task_id": task_id, "url": url, "title": result.get("title", ""),
                               "summary": summary, "text": result.get("text", ""), "timestamp": self._now()}
                self.memory.add_observation(observation)
                self.memory.mark_done(task_id)
                self.memory.add_decision({"task_id": task_id, "decision": "fetched and summarized", "details": {"goal": task["goal"]}, "timestamp": self._now()})
                processed.append(observation)
                # Discovery is bounded by the cycle budget and the domain policy.
                for link in self.frontier.discover(result, limit=3):
                    self.planner.plan(task["goal"], [link])
            except Exception as exc:
                error = {"task_id": task_id, "url": url, "timestamp": self._now(), "error": str(exc)}
                self.memory.add_error(error); errors.append(error)
                if task["retries"] + 1 >= self.policy.max_errors_per_task:
                    self.memory.discard(task_id)
                else:
                    self.memory.mark_retry(task_id, str(exc))
        return {"processed": processed, "errors": errors, "budget": self.budget.snapshot(), "queue": self.memory.stats()}
