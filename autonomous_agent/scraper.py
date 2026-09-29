from __future__ import annotations

from typing import Dict, List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


class WebScraper:
    def __init__(self, timeout_seconds: int = 15):
        self.timeout_seconds = timeout_seconds

    def fetch(self, url: str) -> Dict[str, object]:
        response = requests.get(url, timeout=self.timeout_seconds, headers={"User-Agent": "autonomous-agent/0.1 (+bounded-research)"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.text.strip() if soup.title else ""
        text = " ".join(soup.get_text(" ", strip=True).split())
        links: List[str] = [anchor.get("href") for anchor in soup.find_all("a", href=True)[:100]]
        return {"url": url, "title": title, "text": text[:6000], "status_code": response.status_code,
                "domain": urlparse(url).netloc, "links": links}
