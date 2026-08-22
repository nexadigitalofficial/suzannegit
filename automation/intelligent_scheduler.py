# -*- coding: utf-8 -*-
"""
intelligent_scheduler.py — Adaptive Dynamic Cron & Task Scheduler with Circuit Breaker
"""

import time
from typing import Dict, Any, Callable, List

logger = __import__("logging").getLogger("nexa.scheduler")


class AdaptiveScheduler:
    def __init__(self):
        self.circuit_breaker_tripped: bool = False
        self.consecutive_failures: int = 0
        self.max_failures: int = 5

    def execute_with_circuit_breaker(self, task_name: str, task_fn: Callable[[], Any]) -> Dict[str, Any]:
        if self.circuit_breaker_tripped:
            logger.warning("Circuit breaker active: Task %s skipped.", task_name)
            return {"success": False, "status": "CIRCUIT_BREAKER_OPEN"}

        try:
            start_t = time.time()
            res = task_fn()
            duration = time.time() - start_t
            self.consecutive_failures = 0
            return {"success": True, "duration_sec": duration, "result": res}
        except Exception as e:
            self.consecutive_failures += 1
            logger.error("Task %s failed (failure #%d): %s", task_name, self.consecutive_failures, e)
            if self.consecutive_failures >= self.max_failures:
                self.circuit_breaker_tripped = True
                logger.critical("Circuit breaker TRIPPED for task %s!", task_name)
            return {"success": False, "error": str(e), "failures": self.consecutive_failures}
