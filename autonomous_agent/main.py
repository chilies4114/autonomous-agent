from __future__ import annotations

import argparse
import logging
import os

from .agent import ResearchAgent
from .budget import BudgetTracker
from .config import Settings
from .heartbeat import run_heartbeat
from .llm import LLMClient
from .memory import MemoryStore
from .policies import ResearchPolicy
from .scraper import WebScraper


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def build_agent(settings: Settings, memory_path: str) -> ResearchAgent:
    budget = BudgetTracker(
        token_budget_per_day=settings.token_budget_per_day,
        fetch_budget_per_day=settings.fetch_budget_per_day,
    )
    policy = ResearchPolicy(
        allowed_domains=settings.allowed_domains,
        max_pages_per_cycle=settings.max_pages_per_cycle,
        max_errors_per_task=settings.max_errors_per_task,
    )
    memory = MemoryStore(memory_path)

    llm_client = None
    if settings.model_provider.lower() in {"openai", "openrouter"}:
        llm_client = LLMClient(model=settings.model_name, provider=settings.model_provider)

    return ResearchAgent(memory, budget, policy, WebScraper(timeout_seconds=15), llm_client)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a bounded autonomous research agent.")
    parser.add_argument("--interval", type=int, default=30, help="Seconds between heartbeat cycles.")
    parser.add_argument("--memory-path", type=str, default=".autonomous_agent_state.json", help="JSON state file path.")
    parser.add_argument("--seed-url", type=str, default="https://example.com", help="A safe allowlisted URL to seed the queue.")
    parser.add_argument("--pause", action="store_true", help="Start in paused mode.")
    args = parser.parse_args()

    if args.pause:
        os.environ["AUTO_AGENT_PAUSED"] = "true"

    settings = Settings.from_env()
    settings.polling_interval_seconds = args.interval

    agent = build_agent(settings, args.memory_path)
    state = agent.memory.load()
    if not state.get("queue"):
        agent.memory.enqueue({"id": "seed-task", "url": args.seed_url, "goal": "Seeded research task"})

    run_heartbeat(agent, interval_seconds=settings.polling_interval_seconds)


if __name__ == "__main__":
    main()
