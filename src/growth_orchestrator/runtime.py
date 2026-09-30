"""Wires the pieces together. One place to build a working system for the API, the demo, the evals and the tests."""

from __future__ import annotations

from dataclasses import dataclass

from .ai.interpreter import ReplyInterpreter
from .clock import Clock
from .config import Settings, load_settings
from .db import Database
from .integrations.crm import MockCRM
from .orchestrator import Orchestrator
from .policy import PolicyStore


@dataclass
class Runtime:
    settings: Settings
    db: Database
    crm: MockCRM
    interpreter: ReplyInterpreter
    policies: PolicyStore
    clock: Clock
    orchestrator: Orchestrator


def build_runtime(settings: Settings | None = None, db_path: str | None = None) -> Runtime:
    settings = settings or load_settings()
    db = Database(db_path or settings.db_path)
    crm = MockCRM()
    clock = Clock()
    interpreter = ReplyInterpreter(settings)
    policies = PolicyStore(settings.policy_path)
    orch = Orchestrator(db, crm, interpreter, policies, clock=clock)
    return Runtime(settings, db, crm, interpreter, policies, clock, orch)
