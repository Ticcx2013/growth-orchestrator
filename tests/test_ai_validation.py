"""The model's output is a claim until our validators make it evidence."""

from datetime import date

from growth_orchestrator.ai.interpreter import validate
from growth_orchestrator.models import Action, ExtractedFacts, Intent, ReplyInterpretation, RiskFlag

from .conftest import INTERESTED_ES, reply

REPLY_DATE = date(2026, 9, 30)


def _interp(**kw):
    base = dict(intent=Intent.INTERESTED, confidence=0.9, language="es", evidence=["sí me interesa"], extracted=ExtractedFacts(), risk_flags=[], summary="s")
    base.update(kw)
    return ReplyInterpretation(**base)


def test_valid_interpretation_passes():
    assert validate(_interp(), INTERESTED_ES, REPLY_DATE) == []


def test_evidence_must_be_verbatim():
    errs = validate(_interp(evidence=["the prospect is interested"]), INTERESTED_ES, REPLY_DATE)
    assert any("not found verbatim" in e for e in errs)


def test_evidence_matching_is_tolerant_to_case_and_whitespace():
    assert validate(_interp(evidence=["SÍ  me interesa"]), INTERESTED_ES, REPLY_DATE) == []


def test_invented_referral_email_is_rejected():
    interp = _interp(intent=Intent.REFERRAL, extracted=ExtractedFacts(referral_email="alguien@empresa.mx"))
    errs = validate(interp, "Habla con mi socio Roberto.", REPLY_DATE)
    assert any("does not appear" in e for e in errs)


def test_dates_must_be_in_the_future_and_parseable():
    past = _interp(intent=Intent.OUT_OF_OFFICE, extracted=ExtractedFacts(return_date="2026-01-05"), evidence=["fuera"])
    bad = _interp(intent=Intent.OUT_OF_OFFICE, extracted=ExtractedFacts(return_date="next monday"), evidence=["fuera"])
    assert any("not after" in e for e in validate(past, "Estoy fuera", REPLY_DATE))
    assert any("not an ISO date" in e for e in validate(bad, "Estoy fuera", REPLY_DATE))


def test_company_size_must_appear_in_text():
    interp = _interp(intent=Intent.PRICING_QUESTION, extracted=ExtractedFacts(company_size=400), evidence=["¿Cuánto cuesta?"])
    assert any("company_size" in e for e in validate(interp, "¿Cuánto cuesta? Somos 40 personas.", REPLY_DATE))


def test_unsubscribe_intent_requires_the_flag():
    interp = _interp(intent=Intent.UNSUBSCRIBE, evidence=["No me vuelvan a escribir"], risk_flags=[])
    assert any("unsubscribe_request" in e for e in validate(interp, "No me vuelvan a escribir", REPLY_DATE))
    ok = _interp(intent=Intent.UNSUBSCRIBE, evidence=["No me vuelvan a escribir"], risk_flags=[RiskFlag.UNSUBSCRIBE_REQUEST])
    assert validate(ok, "No me vuelvan a escribir", REPLY_DATE) == []


def test_unclear_intent_may_have_no_evidence():
    assert validate(_interp(intent=Intent.UNCLEAR, confidence=0.2, evidence=[]), "Ok", REPLY_DATE) == []


def test_unavailable_model_output_escalates_instead_of_guessing(rt):
    # Offline mode with a reply that has no recorded response == the API is down.
    out = reply(rt, "c_lucia", "Un texto que jamás fue grabado como fixture, sí me interesa mucho.")
    assert out["action"] == Action.ESCALATE_TO_HUMAN.value and out["requires_review"]
    assert rt.crm.records == {}
    ai = rt.db.one("SELECT valid, validation_errors_json FROM ai_calls")
    assert ai["valid"] == 0 and "no recorded response" in ai["validation_errors_json"]
