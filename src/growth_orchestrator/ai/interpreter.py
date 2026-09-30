"""Reply interpreter: the single LLM capability in the system.

Contract: text in, validated `ReplyInterpretation` out, or an explicit invalid result.
Two modes:
  live    -> Anthropic API with structured outputs (schema enforced server-side) + our semantic validation
  offline -> recorded responses keyed by the reply text, so tests/demo run without a key
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ..config import Settings
from ..models import AIResult, Intent, ReplyInterpretation, RiskFlag
from .prompts import PROMPT_VERSION, SYSTEM_PROMPT, repair_prompt, user_prompt

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)


# ----------------------------------------------------------------------------------
# Validation: the model's output is a claim; these checks make it evidence.
# ----------------------------------------------------------------------------------
def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).lower()
    s = re.sub(r"[‘’“”]", "'", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _parse_iso_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value[:10])
    except (ValueError, TypeError):
        return None


def validate(interp: ReplyInterpretation, reply_text: str, reply_date: date) -> list[str]:
    errors: list[str] = []
    norm_text = _norm(reply_text)

    # 1. Evidence must be verbatim.
    if not interp.evidence and interp.intent not in (Intent.UNCLEAR,):
        errors.append("no evidence quoted for a non-unclear intent")
    for quote in interp.evidence:
        if _norm(quote) not in norm_text:
            errors.append(f"evidence not found verbatim in reply: {quote!r}")

    # 2. Extracted facts must be grounded.
    ex = interp.extracted
    if ex.referral_email:
        if ex.referral_email.lower() not in reply_text.lower():
            errors.append(f"referral_email {ex.referral_email!r} does not appear in the reply")
    if interp.intent == Intent.REFERRAL and not ex.referral_email and not ex.referral_name:
        errors.append("intent is referral but no referral_email or referral_name extracted")

    for field_name in ("return_date", "follow_up_date"):
        raw = getattr(ex, field_name)
        if raw:
            d = _parse_iso_date(raw)
            if d is None:
                errors.append(f"{field_name} is not an ISO date: {raw!r}")
            elif d <= reply_date:
                errors.append(f"{field_name} {d.isoformat()} is not after the reply date {reply_date.isoformat()}")
            elif d > reply_date + timedelta(days=400):
                errors.append(f"{field_name} {d.isoformat()} is implausibly far in the future")

    if ex.company_size is not None:
        if not re.search(rf"\b{ex.company_size}\b", reply_text):
            errors.append(f"company_size {ex.company_size} does not appear in the reply")

    # 3. Internal consistency.
    if interp.intent == Intent.UNSUBSCRIBE and RiskFlag.UNSUBSCRIBE_REQUEST not in interp.risk_flags:
        errors.append("intent unsubscribe without unsubscribe_request flag")
    if interp.intent == Intent.OUT_OF_OFFICE and not ex.return_date:
        # allowed, but then the policy uses the default wait; not an error.
        pass

    return errors


# ----------------------------------------------------------------------------------
# Interpreter
# ----------------------------------------------------------------------------------
def fixture_key(reply_text: str) -> str:
    return hashlib.sha1(_norm(reply_text).encode("utf-8")).hexdigest()[:12]


class ReplyInterpreter:
    def __init__(self, settings: Settings, client: Any | None = None):
        self.settings = settings
        self._client = client
        self.fixtures_path = Path(settings.fixtures_path)
        self._fixtures: dict[str, Any] | None = None

    # -- fixtures --------------------------------------------------------------------
    @property
    def fixtures(self) -> dict[str, Any]:
        if self._fixtures is None:
            if self.fixtures_path.exists():
                self._fixtures = json.loads(self.fixtures_path.read_text(encoding="utf-8"))
            else:
                self._fixtures = {}
        return self._fixtures

    def _save_fixture(self, reply_text: str, parsed: dict[str, Any], meta: dict[str, Any]) -> None:
        self.fixtures[fixture_key(reply_text)] = {"reply": reply_text, "parsed": parsed, "meta": meta}
        self.fixtures_path.parent.mkdir(parents=True, exist_ok=True)
        self.fixtures_path.write_text(json.dumps(self.fixtures, ensure_ascii=False, indent=2), encoding="utf-8")

    # -- client ----------------------------------------------------------------------
    @property
    def client(self):
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key, max_retries=2, timeout=60.0)
        return self._client

    # -- main entry ------------------------------------------------------------------
    def interpret(self, reply_text: str, reply_at: datetime, context: dict[str, Any]) -> AIResult:
        reply_date = reply_at.date()
        if self.settings.offline:
            return self._interpret_offline(reply_text, reply_date)
        return self._interpret_live(reply_text, reply_at, reply_date, context)

    def _interpret_offline(self, reply_text: str, reply_date: date) -> AIResult:
        fx = self.fixtures.get(fixture_key(reply_text))
        if not fx:
            return AIResult(
                interpretation=None, valid=False, mode="offline", model="fixtures", prompt_version=PROMPT_VERSION,
                validation_errors=["no recorded response for this reply (offline mode)"],
            )
        try:
            interp = ReplyInterpretation.model_validate(fx["parsed"])
        except ValidationError as e:
            return AIResult(interpretation=None, valid=False, mode="offline", model="fixtures",
                            prompt_version=PROMPT_VERSION, validation_errors=[f"schema: {e.errors()[0]['msg']}"])
        errors = validate(interp, reply_text, reply_date)
        return AIResult(
            interpretation=interp, valid=not errors, validation_errors=errors, mode="offline",
            model=fx.get("meta", {}).get("model", "fixtures"), prompt_version=fx.get("meta", {}).get("prompt_version", PROMPT_VERSION),
            raw_output=json.dumps(fx["parsed"], ensure_ascii=False),
        )

    def _interpret_live(self, reply_text: str, reply_at: datetime, reply_date: date, context: dict[str, Any]) -> AIResult:
        import anthropic

        messages: list[dict[str, Any]] = [{"role": "user", "content": user_prompt(reply_text, reply_at.date().isoformat(), context)}]
        attempts = 0
        total_in = total_out = 0
        started = time.perf_counter()
        last_errors: list[str] = []
        raw = None
        interp: ReplyInterpretation | None = None

        while attempts < 2:  # one call + one repair attempt
            attempts += 1
            try:
                response = self.client.messages.parse(
                    model=self.settings.model,
                    max_tokens=4000,
                    system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
                    messages=messages,
                    output_format=ReplyInterpretation,
                    output_config={"effort": "medium"},
                )
            except anthropic.RateLimitError as e:
                return AIResult(interpretation=None, valid=False, mode="live", model=self.settings.model,
                                prompt_version=PROMPT_VERSION, attempts=attempts, validation_errors=[f"rate_limited: {e}"])
            except anthropic.APIStatusError as e:
                return AIResult(interpretation=None, valid=False, mode="live", model=self.settings.model,
                                prompt_version=PROMPT_VERSION, attempts=attempts, validation_errors=[f"api_error {e.status_code}: {e.message}"])
            except anthropic.APIConnectionError as e:
                return AIResult(interpretation=None, valid=False, mode="live", model=self.settings.model,
                                prompt_version=PROMPT_VERSION, attempts=attempts, validation_errors=[f"connection_error: {e}"])

            total_in += response.usage.input_tokens
            total_out += response.usage.output_tokens

            if response.stop_reason == "refusal":
                detail = response.stop_details.category if response.stop_details else "unknown"
                return AIResult(interpretation=None, valid=False, refused=True, mode="live", model=self.settings.model,
                                prompt_version=PROMPT_VERSION, attempts=attempts, input_tokens=total_in, output_tokens=total_out,
                                validation_errors=[f"model refused (category={detail})"])

            interp = response.parsed_output
            raw = next((b.text for b in response.content if b.type == "text"), None)
            if interp is None:
                last_errors = ["model returned no parseable output"]
            else:
                last_errors = validate(interp, reply_text, reply_date)
            if not last_errors:
                break
            # Repair: feed the errors back once. Structured outputs already guarantee the schema,
            # so this only fires on semantic failures (ungrounded evidence, invented facts).
            messages.append({"role": "assistant", "content": raw or "{}"})
            messages.append({"role": "user", "content": repair_prompt(last_errors)})

        latency_ms = int((time.perf_counter() - started) * 1000)
        result = AIResult(
            interpretation=interp, valid=not last_errors, validation_errors=last_errors, mode="live",
            model=self.settings.model, prompt_version=PROMPT_VERSION, attempts=attempts, latency_ms=latency_ms,
            input_tokens=total_in, output_tokens=total_out, raw_output=raw,
        )
        if self.settings.ai_mode == "record" and interp is not None:
            self._save_fixture(reply_text, interp.model_dump(mode="json"),
                               {"model": self.settings.model, "prompt_version": PROMPT_VERSION, "valid": result.valid,
                                "validation_errors": last_errors, "recorded_at": datetime.utcnow().isoformat() + "Z"})
        return result
