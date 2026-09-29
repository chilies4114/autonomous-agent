from __future__ import annotations

from typing import Dict
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


class WebScraper:
    def __init__(self, timeout_seconds: int = 15):
        self.timeout_seconds = timeout_seconds

    def fetch(self, url: str) -> Dict[str, str]:
        response = requests.get(url, timeout=self.timeout_seconds, headers={
            "User-Agent": "autonomous-agent/0.1 (+safe-bounded-research)",
        })
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.text.strip() if soup.title else ""
        text = " ".join(soup.get_text(" ", strip=True).split())

        return {
            "url": url,
            "title": title,
            "text": text[:6000],
            "status_code": str(response.status_code),
            "domain": urlparse(url).netloc,
        }
