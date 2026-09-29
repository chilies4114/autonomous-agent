from __future__ import annotations

import os
from typing import Any, Dict, Optional


class LLMClient:
    def __init__(self, model: str = "gpt-4o-mini", provider: str = "openai"):
        self.model = model
        self.provider = provider.lower()
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")

    def generate_summary(self, task: Dict[str, Any], result: Dict[str, Any]) -> str:
        if not self.api_key:
            return result.get("text", "")[:220].strip() or f"Fetched {result.get('url')}"

        provider = self.provider
        try:
            if provider == "openai":
                import openai

                client = openai.OpenAI(api_key=self.api_key)
                response = client.responses.create(
                    model=self.model,
                    input=[
                        {
                            "role": "user",
                            "content": (
                                f"Summarize this page in 2-3 sentences for the task: {task.get('goal', 'research')}\n"
                                f"URL: {result.get('url')}\n"
                                f"Title: {result.get('title', '')}\n"
                                f"Text: {result.get('text', '')[:3000]}"
                            ),
                        }
                    ],
                )
                return response.output_text.strip() if hasattr(response, "output_text") else str(response)

            if provider == "openrouter":
                import requests

                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "user",
                                "content": (
                                    f"Summarize this page in 2-3 sentences for the task: {task.get('goal', 'research')}\n"
                                    f"URL: {result.get('url')}\n"
                                    f"Title: {result.get('title', '')}\n"
                                    f"Text: {result.get('text', '')[:3000]}"
                                ),
                            }
                        ],
                    },
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception:
            pass

        return result.get("text", "")[:220].strip() or f"Fetched {result.get('url')}"
