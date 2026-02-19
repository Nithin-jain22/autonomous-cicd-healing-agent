from __future__ import annotations

from threading import Lock
from typing import Dict

from models import RunState


class InMemoryRunStore:
    def __init__(self) -> None:
        self._runs: Dict[str, RunState] = {}
        self._lock = Lock()

    def upsert(self, run_state: RunState) -> None:
        with self._lock:
            self._runs[run_state.run_id] = run_state

    def get(self, run_id: str) -> RunState | None:
        with self._lock:
            return self._runs.get(run_id)


run_store = InMemoryRunStore()
