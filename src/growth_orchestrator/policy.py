"""Policy: the editable contract of what the system may do on its own."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from .models import Action, Intent

AutomationMode = Literal["auto", "assisted", "off"]


class ICP(BaseModel):
    min_employees: int = 50
    countries: list[str] = Field(default_factory=lambda: ["MX", "BR", "CO"])


class EligibilityPolicy(BaseModel):
    cooldown_days: int = 14
    max_active_contacts_per_account: int = 3
    icp: ICP = Field(default_factory=ICP)


class AIPolicy(BaseModel):
    min_confidence_auto: float = 0.75
    high_risk_intents: list[Intent] = Field(default_factory=lambda: [Intent.UNSUBSCRIBE, Intent.REFERRAL])
    min_confidence_high_risk: float = 0.85
    freshness_check_before_irreversible: bool = True


class Defaults(BaseModel):
    wait_days_when_no_date: int = 30


class Policy(BaseModel):
    version: int = 1
    eligibility: EligibilityPolicy = Field(default_factory=EligibilityPolicy)
    automation: dict[Action, AutomationMode] = Field(default_factory=dict)
    ai: AIPolicy = Field(default_factory=AIPolicy)
    intent_actions: dict[Intent, Action] = Field(default_factory=dict)
    defaults: Defaults = Field(default_factory=Defaults)

    def mode_for(self, action: Action) -> AutomationMode:
        # Anything not listed is treated as "assisted": unknown == not automated.
        return self.automation.get(action, "assisted")


class PolicyStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._cache: Policy | None = None

    def load(self) -> Policy:
        if self._cache is None:
            with open(self.path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            self._cache = Policy.model_validate(data)
        return self._cache

    def save(self, policy: Policy) -> Policy:
        policy = policy.model_copy(update={"version": policy.version + 1})
        data = policy.model_dump(mode="json")
        with open(self.path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
        self._cache = policy
        return policy

    def replace(self, policy: Policy) -> None:
        """In-memory override (tests, demo). Does not touch disk."""
        self._cache = policy
