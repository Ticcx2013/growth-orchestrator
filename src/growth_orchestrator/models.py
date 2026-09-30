"""Domain and event schemas (Pydantic)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


# ----------------------------------------------------------------------------------
# Events (what arrives at the webhook)
# ----------------------------------------------------------------------------------
class EventType(str, Enum):
    PROSPECT_IDENTIFIED = "prospect.identified"
    REPLY_RECEIVED = "reply.received"
    CRM_ACCOUNT_UPDATED = "crm.account_updated"
    CONTACT_UNSUBSCRIBED = "contact.unsubscribed"


class InboundEvent(BaseModel):
    """Envelope for every event. `event_id` is the idempotency key from the source system."""

    event_id: str = Field(min_length=1, max_length=200)
    type: EventType
    occurred_at: datetime
    payload: dict[str, Any] = Field(default_factory=dict)


# ----------------------------------------------------------------------------------
# Decisions and actions
# ----------------------------------------------------------------------------------
class Action(str, Enum):
    HANDOFF_TO_AE = "handoff_to_ae"
    WAIT_UNTIL = "wait_until"
    CREATE_REFERRAL_CONTACT = "create_referral_contact"
    SUPPRESS_CONTACT = "suppress_contact"
    NURTURE_LONG_TERM = "nurture_long_term"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    ENROLL_IN_SEQUENCE = "enroll_in_sequence"
    ENRICH_CONTACT = "enrich_contact"
    NOTIFY_CSM = "notify_csm"
    NO_ACTION = "no_action"


# Actions that touch an external system and are not trivially reversible.
IRREVERSIBLE_ACTIONS = {
    Action.HANDOFF_TO_AE,
    Action.CREATE_REFERRAL_CONTACT,
    Action.ENROLL_IN_SEQUENCE,
}


class Decision(BaseModel):
    action: Action
    automated: bool
    requires_review: bool = False
    reason: str
    trace: list[dict[str, Any]] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)
    proposed_action: Action | None = None  # when escalated, what the system would have done


# ----------------------------------------------------------------------------------
# AI: the ONLY thing the model produces. It interprets; it never acts.
# ----------------------------------------------------------------------------------
class Intent(str, Enum):
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    OUT_OF_OFFICE = "out_of_office"
    REFERRAL = "referral"
    UNSUBSCRIBE = "unsubscribe"
    PRICING_QUESTION = "pricing_question"
    LATER = "later"
    MIXED = "mixed"
    UNCLEAR = "unclear"


class RiskFlag(str, Enum):
    PROMPT_INJECTION = "prompt_injection"
    CONTRADICTORY_SIGNALS = "contradictory_signals"
    UNSUBSCRIBE_REQUEST = "unsubscribe_request"
    LEGAL_OR_COMPLAINT = "legal_or_complaint"
    SENSITIVE_PERSONAL_DATA = "sensitive_personal_data"
    WRONG_PERSON = "wrong_person"


class ExtractedFacts(BaseModel):
    """Facts the model extracts. Dates are strings on purpose: we parse and validate them ourselves."""

    referral_email: str | None = None
    referral_name: str | None = None
    return_date: str | None = Field(default=None, description="ISO date YYYY-MM-DD when the person is back (out of office)")
    follow_up_date: str | None = Field(default=None, description="ISO date YYYY-MM-DD when they asked to be contacted again")
    proposed_meeting: str | None = Field(default=None, description="Verbatim proposed time, if any")
    company_size: int | None = None
    current_tool: str | None = None
    qualification_notes: list[str] = Field(default_factory=list)


class ReplyInterpretation(BaseModel):
    """Structured output schema sent to the model (JSON schema) and validated on return."""

    intent: Intent
    confidence: float = Field(ge=0.0, le=1.0, description="0-1. Be conservative; below 0.6 means you are guessing.")
    language: Literal["es", "pt", "en", "other"]
    evidence: list[str] = Field(description="Verbatim quotes from the reply that support the intent. Must appear literally in the text.")
    extracted: ExtractedFacts
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    summary: str = Field(description="One sentence for the SDR, in English.")


class AIResult(BaseModel):
    """What the pipeline gets back from the interpreter: the interpretation plus how it was produced."""

    interpretation: ReplyInterpretation | None
    valid: bool
    validation_errors: list[str] = Field(default_factory=list)
    mode: Literal["live", "offline"]
    model: str
    prompt_version: str
    attempts: int = 1
    latency_ms: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    raw_output: str | None = None
    refused: bool = False
    ai_call_id: int | None = None
