from __future__ import annotations

from typing import Any, Dict, Iterable, List
from urllib.parse import urljoin, urldefrag, urlparse

from .policies import Policy
from .scraper import WebScraper


class URLFrontier:
    """Extracts same-allowlist links without recursively crawling by accident."""

    def __init__(self, policy: Policy, scraper: WebScraper | None = None):
        self.policy = policy
        self.scraper = scraper or WebScraper()

    def discover(self, page: Dict[str, Any], limit: int = 10) -> List[str]:
        base = page["url"]
        links: List[str] = []
        for href in page.get("links", []):
            absolute, _ = urldefrag(urljoin(base, href))
            parsed = urlparse(absolute)
            if parsed.scheme in {"http", "https"} and self.policy.is_allowed_url(absolute) and absolute not in links:
                links.append(absolute)
            if len(links) >= limit:
                break
        return links
