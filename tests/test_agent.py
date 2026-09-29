from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from autonomous_agent.memory import MemoryStore
from autonomous_agent.budget import BudgetTracker
from autonomous_agent.policies import ResearchPolicy
from autonomous_agent.scraper import WebScraper
from autonomous_agent.crawler import URLFrontier
from autonomous_agent.planner import ResearchPlanner
from autonomous_agent.agent import ResearchAgent


def test_memory_store():
    """Test SQLite memory store."""
    print("[TEST] Memory store...")
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = MemoryStore(Path(tmpdir) / "test.sqlite3")
        assert mem.enqueue({"id": "task-1", "url": "https://example.com", "goal": "test"})
        tasks = mem.queued_tasks(1)
        assert len(tasks) == 1
        assert tasks[0]["url"] == "https://example.com"
        mem.mark_done("task-1")
        assert len(mem.queued_tasks(1)) == 0
        stats = mem.stats()
        assert stats.get("done", 0) == 1
    print("  ✓ Memory store works")


def test_budget():
    """Test budget tracking."""
    print("[TEST] Budget...")
    budget = BudgetTracker(token_budget_per_day=1000, fetch_budget_per_day=10)
    assert budget.can_fetch()
    assert budget.can_use_tokens(100)
    budget.consume(tokens=500, fetch_count=5)
    assert budget.can_fetch()
    assert budget.can_use_tokens(400)
    assert not budget.can_use_tokens(600)
    snapshot = budget.snapshot()
    assert snapshot["token_spent"] == 500
    assert snapshot["fetches_used"] == 5
    print("  ✓ Budget tracking works")


def test_policy():
    """Test URL allowlist policy."""
    print("[TEST] Policy...")
    policy = ResearchPolicy(
        allowed_domains=["example.com", "docs.example.com"],
        max_pages_per_cycle=5,
        max_errors_per_task=3,
    )
    assert policy.is_allowed_url("https://example.com/page")
    assert policy.is_allowed_url("https://docs.example.com/api")
    assert not policy.is_allowed_url("https://evil.com")
    assert not policy.is_allowed_url("https://example.co")
    print("  ✓ Policy works")


def test_planner():
    """Test planner task creation."""
    print("[TEST] Planner...")
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = MemoryStore(Path(tmpdir) / "test.sqlite3")
        planner = ResearchPlanner(mem, max_tasks=3)
        tasks = planner.plan("find facts", ["https://example.com", "https://example.com/page"])
        assert len(tasks) == 2
        queued = mem.queued_tasks(10)
        assert len(queued) == 2
        tasks2 = planner.plan("find facts", ["https://example.com"])
        assert len(tasks2) == 0
    print("  ✓ Planner works")


def test_crawler():
    """Test URL frontier extraction."""
    print("[TEST] Crawler...")
    policy = ResearchPolicy(["example.com"], 5, 3)
    frontier = URLFrontier(policy, WebScraper())
    page = {
        "url": "https://example.com/page",
        "links": [
            "/page2",
            "https://example.com/page3",
            "https://evil.com/bad",
            "#anchor",
        ],
    }
    links = frontier.discover(page, limit=10)
    assert len(links) <= 3
    assert all("example.com" in link for link in links)
    assert not any("evil.com" in link for link in links)
    print("  ✓ Crawler works")


def test_agent_cycle():
    """Test agent run cycle without network."""
    print("[TEST] Agent cycle...")
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = MemoryStore(Path(tmpdir) / "test.sqlite3")
        budget = BudgetTracker(100000, 50)
        policy = ResearchPolicy(["example.com"], 5, 3)
        agent = ResearchAgent(mem, budget, policy)
        agent.submit_goal("test goal", ["https://example.com"])
        tasks = mem.queued_tasks(1)
        assert len(tasks) == 1
    print("  ✓ Agent initialization works")


if __name__ == "__main__":
    print("\n=== autonomous-agent test suite ===")
    try:
        test_memory_store()
        test_budget()
        test_policy()
        test_planner()
        test_crawler()
        test_agent_cycle()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
