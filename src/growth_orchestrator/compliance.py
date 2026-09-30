"""Compliance rules that run BEFORE the model and never depend on it.

Opt-out detection is a legal obligation (LFPDPPP in MX, LGPD in BR, Ley 1581 in CO).
A regulator will not accept "the model missed it", so this is deterministic and boring on purpose.
The model also sees the text and may flag `unsubscribe_request`; when both agree it is a nice
consistency check, when they disagree the rule wins.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

OPT_OUT_PATTERNS: dict[str, list[str]] = {
    "es": [
        r"\bno (me|nos) (vuelvan|vuelva|vuelvas) a (escribir|contactar|llamar|molestar)\b",
        r"\bno (me|nos) (escriban|escriba|contacten|contacte|llamen|llame) (mas|más)\b",
        r"\b(quitenme|quítenme|quitame|quítame|sacame|sáquenme|saquenme|eliminenme|elimíneme|borrenme|bórrenme) de (la|su|sus|esta) (lista|base|listas)\b",
        r"\bdar(me|nos)? de baja\b",
        r"\b(quiero|solicito|deseo) (la )?baja\b",
        r"\bbaja de (la|su) (lista|base)\b",
        r"\bborr(en|ar|a) mis datos\b",
        r"\belimin(en|ar|a) mis datos\b",
        r"\bdejen de (escribir|contactar|molestar|llamar)\b",
        r"\bno deseo recibir\b",
        r"\bcancelar (la )?suscripci[oó]n\b",
    ],
    "pt": [
        r"\bn[aã]o (me|nos) (contate|contatem|escreva|escrevam|liguem|ligue) (mais)?\b",
        r"\bn[aã]o quero (mais )?receber\b",
        r"\b(me )?(remova|removam|retire|retirem|tire|tirem) da (lista|base)\b",
        r"\bdescadastr(ar|e|em|o)\b",
        r"\bcancelar (a )?(inscri[cç][aã]o|assinatura)\b",
        r"\bparem de (me )?(enviar|contatar|escrever)\b",
        r"\bexclu(a|am|ir) meus dados\b",
    ],
    "en": [
        r"\bunsubscribe\b",
        r"\bopt[- ]?out\b",
        r"\b(remove|take) me (off|from) (your|this|the) (list|mailing list|database)\b",
        r"\bstop (emailing|contacting|messaging|calling) (me|us)\b",
        r"\bdo not (contact|email|message|call) (me|us) (again|anymore)\b",
        r"\bdon'?t (contact|email|message|call) (me|us) (again|anymore)\b",
        r"\bdelete my (data|information)\b",
        r"\b(please,? )?no (further|more) (emails|contact|messages)[.!,]?\s*(please|thanks|thank you)?[.!]?\s*$",
    ],
}

# "I don't want to unsubscribe, keep sending" must not read as an opt-out.
NEGATED_OPT_OUT = re.compile(r"\b(don'?t|do not|not|never|no) (want to |wish to |need to |quiero |queremos |quero )?(unsubscribe|opt[- ]?out|dar(me|nos)? de baja|descadastrar)")

# Text that tries to talk to the model instead of to the SDR.
# Text that tries to talk to the model instead of to the SDR. Kept narrow on purpose: a false positive here
# sends an interested prospect to a human, which is safe but costs speed; so patterns must not match normal sales talk.
INJECTION_PATTERNS = [
    r"\bignore (all |the |your )?(previous|prior|above) (instructions|prompts?)\b",
    r"\bignora (todas )?(las )?instrucciones (anteriores|previas)\b",
    r"\bignore (as )?instru[cç][oõ]es (anteriores|acima)\b",
    r"\b(you are now|from now on you are|act as|pretend to be|pretend you are) (a |an |the )?(helpful |sales |ai |virtual )?(assistant|bot|ai|model|system|agent)\b",
    r"\bsystem prompt\b",
    r"\b(classify|mark|label|set|tag) (this|it|the (reply|intent|message)) as\b",
    r"\b(clasifica|marca|etiqueta) (esto|este mensaje|la respuesta) como\b",
    r"\b(intent|confidence|action)\s*[:=]\s*[\"']?\w+",
    r"\b(schedule|book|create) (a|the) (demo|meeting|deal) (automatically|immediately|without asking)\b",
    r"\[\s*(system|assistant|instruction)\s*\]",
    r"\b(output|return|respond with) (only )?(json|the following)\b",
]


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


@dataclass
class ComplianceResult:
    opt_out: bool = False
    opt_out_matches: list[str] = field(default_factory=list)
    injection_suspected: bool = False
    injection_matches: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "opt_out": self.opt_out,
            "opt_out_matches": self.opt_out_matches,
            "injection_suspected": self.injection_suspected,
            "injection_matches": self.injection_matches,
        }


def check_reply(text: str) -> ComplianceResult:
    norm = _normalize(text)
    result = ComplianceResult()
    negated = NEGATED_OPT_OUT.search(norm) is not None
    for lang, patterns in OPT_OUT_PATTERNS.items():
        for pat in patterns:
            m = re.search(pat, norm)
            if m and not (negated and NEGATED_OPT_OUT.search(norm).end() >= m.start()):
                result.opt_out = True
                result.opt_out_matches.append(f"{lang}: {m.group(0)}")
    for pat in INJECTION_PATTERNS:
        m = re.search(pat, norm)
        if m:
            result.injection_suspected = True
            result.injection_matches.append(m.group(0))
    return result
