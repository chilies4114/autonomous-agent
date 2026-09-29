from __future__ import annotations

import time
import logging
from typing import Callable


logger = logging.getLogger("autonomous-agent")


def run_heartbeat(agent, interval_seconds: int = 30, stop_event: Callable[[], bool] | None = None):
    while True:
        if stop_event is not None and stop_event():
            logger.info("Heartbeat stop requested.")
            break

        try:
            summary = agent.run_cycle()
            logger.info("Heartbeat cycle completed: %s", summary)
        except Exception as exc:  # pragma: no cover - resilient runtime path
            logger.exception("Heartbeat cycle crashed: %s", exc)

        time.sleep(interval_seconds)
