from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


class Policy:
    def __init__(self, allowed_domains: List[str], max_pages_per_cycle: int, max_errors_per_task: int):
        self.allowed_domains = {d.lower().strip() for d in allowed_domains if d and d.strip()}
        self.max_pages_per_cycle = max_pages_per_cycle
        self.max_errors_per_task = max_errors_per_task

    def is_allowed_url(self, url: str) -> bool:
        parsed = urlparse(url)
        hostname = parsed.netloc.lower()
        if not hostname:
            return False
        return any(hostname == domain or hostname.endswith(f".{domain}") for domain in self.allowed_domains)

    def explain_block(self, url: str) -> str:
        return f"URL '{url}' is outside the allowed domain list: {sorted(self.allowed_domains)}"

    def should_retry(self, task: Dict[str, Any], errors: List[Dict[str, Any]]) -> bool:
        task_name = task.get("url", task.get("id", "task"))
        matching = [e for e in errors if e.get("task") == task_name]
        return len(matching) < self.max_errors_per_task


class ResearchPolicy(Policy):
    """Alias kept for clarity in the project."""
    pass
