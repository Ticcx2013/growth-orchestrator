"""Controllable clock so retries and backoff can be demonstrated without waiting."""

from __future__ import annotations

from datetime import datetime, timedelta

from .db import utcnow


class Clock:
    def __init__(self) -> None:
        self.offset = timedelta(0)

    def __call__(self) -> datetime:
        return utcnow() + self.offset

    def advance(self, seconds: float) -> datetime:
        self.offset += timedelta(seconds=seconds)
        return self()

    def reset(self) -> None:
        self.offset = timedelta(0)
