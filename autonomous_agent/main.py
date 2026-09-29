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
from .planner import ResearchPlanner
from .policies import ResearchPolicy
from .scraper import WebScraper

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def build_agent(settings: Settings, memory_path: str) -> ResearchAgent:
    memory = MemoryStore(memory_path)
    policy = ResearchPolicy(settings.allowed_domains, settings.max_pages_per_cycle, settings.max_errors_per_task)
    budget = BudgetTracker(settings.token_budget_per_day, settings.fetch_budget_per_day)
    llm = LLMClient(model=settings.model_name, provider=settings.model_provider) if settings.model_provider != "none" else None
    return ResearchAgent(memory, budget, policy, WebScraper(), llm, ResearchPlanner(memory, settings.max_pages_per_cycle))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a bounded autonomous research agent.")
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--memory-path", default=".autonomous_agent_state.sqlite3")
    parser.add_argument("--seed-url", default="https://example.com")
    parser.add_argument("--goal", default="Collect useful information from the approved source")
    args = parser.parse_args()
    settings = Settings.from_env()
    settings.polling_interval_seconds = max(1, args.interval)
    agent = build_agent(settings, args.memory_path)
    agent.submit_goal(args.goal, [args.seed_url])
    if settings.paused:
        logging.getLogger("autonomous-agent").warning("Agent is paused; set AUTO_AGENT_PAUSED=false to run.")
        return
    run_heartbeat(agent, settings.polling_interval_seconds)


if __name__ == "__main__":
    main()
