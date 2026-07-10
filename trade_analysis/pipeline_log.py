"""Shared stage logging for pipeline Python steps."""

from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from typing import Any, Optional


def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_elapsed(seconds: float) -> str:
    s = int(max(0, round(seconds)))
    if s >= 3600:
        return f"{s // 3600}h {(s % 3600) // 60:02d}m {s % 60:02d}s"
    if s >= 60:
        return f"{s // 60}m {s % 60:02d}s"
    return f"{s}s"


def step_banner(title: str, **details: Any) -> None:
    print("", flush=True)
    print("─" * 72, flush=True)
    print(f"  {title}", flush=True)
    for key, val in details.items():
        if val is not None and val != "":
            print(f"    · {key}: {val}", flush=True)
    print(f"    · started {_ts()}", flush=True)
    print("─" * 72, flush=True)
    print("", flush=True)


def step_done(title: str, t0: float, **stats: Any) -> None:
    elapsed = time.time() - t0
    print("", flush=True)
    print(f"✓ {title} — {format_elapsed(elapsed)} — finished {_ts()}", flush=True)
    for key, val in stats.items():
        print(f"    · {key}: {val}", flush=True)
    print("", flush=True)


class StepTimer:
    def __init__(self, title: str, **details: Any):
        self.title = title
        self.details = details
        self.t0 = 0.0

    def __enter__(self) -> StepTimer:
        self.t0 = time.time()
        step_banner(self.title, **self.details)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            print(f"✗ {self.title} failed after {format_elapsed(time.time() - self.t0)}", file=sys.stderr, flush=True)
            return
        # caller should call finish() with stats; minimal exit if not
        return None

    def finish(self, **stats: Any) -> None:
        step_done(self.title, self.t0, **stats)
