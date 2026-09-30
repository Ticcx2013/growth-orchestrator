"""Runtime settings. Everything comes from environment variables; nothing is hardcoded per tenant."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    db_path: Path = field(default_factory=lambda: Path(os.getenv("GO_DB_PATH", ROOT / "data" / "orchestrator.db")))
    policy_path: Path = field(default_factory=lambda: Path(os.getenv("GO_POLICY_PATH", ROOT / "policy.yaml")))
    fixtures_path: Path = field(
        default_factory=lambda: Path(os.getenv("GO_FIXTURES_PATH", ROOT / "src" / "growth_orchestrator" / "ai" / "fixtures.json"))
    )
    model: str = field(default_factory=lambda: os.getenv("GO_MODEL", "claude-opus-5-5"))
    anthropic_api_key: str | None = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY") or None)
    webhook_secret: str | None = field(default_factory=lambda: os.getenv("GO_WEBHOOK_SECRET") or None)
    ai_mode: str = field(default_factory=lambda: os.getenv("GO_AI_MODE", "auto"))  # auto | live | offline | record

    @property
    def offline(self) -> bool:
        if self.ai_mode == "offline":
            return True
        if self.ai_mode in ("live", "record"):
            return False
        return self.anthropic_api_key is None


def load_settings() -> Settings:
    return Settings()
