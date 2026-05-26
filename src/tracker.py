"""Per-agent token usage tracker."""
import time
from collections import defaultdict
from threading import Lock


class TokenTracker:
    def __init__(self):
        self._lock = Lock()
        self._stats: dict[str, dict] = defaultdict(lambda: {
            "prompt": 0, "completion": 0, "calls": 0, "models": defaultdict(int),
        })
        self._started = time.time()

    def record(self, agent: str, model: str, prompt: int, completion: int):
        with self._lock:
            s = self._stats[agent]
            s["prompt"] += prompt
            s["completion"] += completion
            s["calls"] += 1
            s["models"][model] += prompt + completion

    def snapshot(self) -> dict:
        with self._lock:
            total_prompt = sum(s["prompt"] for s in self._stats.values())
            total_completion = sum(s["completion"] for s in self._stats.values())
            return {
                "uptime_seconds": int(time.time() - self._started),
                "agents": {
                    name: {
                        "prompt": s["prompt"],
                        "completion": s["completion"],
                        "total": s["prompt"] + s["completion"],
                        "calls": s["calls"],
                        "models": dict(s["models"]),
                    } for name, s in self._stats.items()
                },
                "total_prompt": total_prompt,
                "total_completion": total_completion,
                "total": total_prompt + total_completion,
            }
