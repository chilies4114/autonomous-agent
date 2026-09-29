# autonomous-agent

A bounded autonomous research agent with a heartbeat loop, planner, URL frontier, SQLite memory, token/fetch budgets, allowlisted scraping, and optional LLM summaries.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export AUTO_AGENT_ALLOWED_DOMAINS=example.com
python -m autonomous_agent.main --goal "Collect facts about this site" --seed-url https://example.com --interval 60
```

Set `AUTO_AGENT_PAUSED=true` to prevent execution. The default state file is SQLite at `.autonomous_agent_state.sqlite3`.

## Architecture

- **Planner:** turns a goal and approved seed URLs into deduplicated durable tasks.
- **Crawler:** extracts a small number of same-allowlist links per successful page; it does not perform unrestricted recursive crawling.
- **Memory:** SQLite stores tasks, retries, observations, errors, and decisions in a WAL-backed database.
- **Heartbeat:** processes bounded work on each cycle and sleeps between cycles.
- **Model layer:** optional OpenAI/OpenRouter summarization; the extractive fallback requires no model API.

## Safety controls

`AUTO_AGENT_ALLOWED_DOMAINS`, `AUTO_AGENT_MAX_PER_CYCLE`, `AUTO_AGENT_FETCH_BUDGET_PER_DAY`, `AUTO_AGENT_TOKEN_BUDGET_PER_DAY`, and `AUTO_AGENT_MAX_ERRORS_PER_TASK` limit operation. Use a dedicated account, obey site terms and robots/rate limits, and do not add credentials or destructive tools to the agent without human approval.
