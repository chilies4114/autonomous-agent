# autonomous-agent

A safe, bounded autonomous research agent prototype with:

- 24/7 heartbeat loop
- token / fetch budget enforcement
- self-correction from previous errors
- allowlisted web scraping
- durable memory and audit trail

This project is intentionally conservative: it is designed to be run in a controlled environment, with explicit allowlists, rate limits, and a stop mechanism.

## What it does

The agent can:

- poll a task queue
- fetch only approved domains
- extract page metadata and text
- store observations in a JSON-backed memory store
- detect recent failures and adapt retry behavior
- enforce daily token and fetch budgets

## Safety model

- No arbitrary shell access
- No unrestricted network access
- No destructive actions unless explicitly added later
- All actions are logged to a JSON state file
- The loop can be paused by setting `AUTO_AGENT_PAUSED=true`

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m autonomous_agent.main --interval 30 --memory-path .autonomous_agent_state.json --seed-url https://example.com
```

## Project structure

```text
autonomous_agent/
  __init__.py
  agent.py
  budget.py
  config.py
  heartbeat.py
  main.py
  memory.py
  policies.py
  scraper.py
requirements.txt
README.md
```

## Environment variables

```bash
export AUTO_AGENT_PAUSED=false
export AUTO_AGENT_MAX_PER_CYCLE=5
export AUTO_AGENT_ALLOWED_DOMAINS=example.com,news.ycombinator.com
export AUTO_AGENT_MAX_ERRORS_PER_TASK=3
```

## Notes

This is a foundation, not a fully autonomous black-box web agent. It is built to be safe and extensible so you can add model calls, database-backed memory, or approval gates later.
