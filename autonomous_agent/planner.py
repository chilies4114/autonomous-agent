from __future__ import annotations

import hashlib
from typing import Any, Dict, List

from .memory import MemoryStore


class ResearchPlanner:
    """Converts a research goal into bounded, deduplicated fetch tasks."""

    def __init__(self, memory: MemoryStore, max_tasks: int = 5):
        self.memory = memory
        self.max_tasks = max_tasks

    def plan(self, goal: str, seed_urls: List[str]) -> List[Dict[str, Any]]:
        tasks = []
        for url in seed_urls[: self.max_tasks]:
            task_id = hashlib.sha256(f"{goal}:{url}".encode()).hexdigest()[:16]
            task = {"id": task_id, "url": url, "goal": goal}
            if self.memory.enqueue(task):
                tasks.append(task)
        return tasks
