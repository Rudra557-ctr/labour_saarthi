"""Terminology guardrails against publication drift (Step 7.1 §1.3, rules T-1..T-4).

Scope is deliberate. The lint inspects **published** labels, interpretations and
envelope-level strings. It does NOT inspect internal table or column names, because
those may legitimately say `vacancy` - an observed concept the project really does
hold - or appear in an internal coverage table named `supply_coverage_summary`.
Banning the vocabulary outright would flag honest fields and teach everyone to
suppress the check. The target is unsupported *interpretation*.

Three rules:

1. `shortage`, `deficit`, `skill gap`, `supply gap`, `demand-supply gap` are
   forbidden in any published label, for every output. Nothing in the system is one.
2. `supply` may not describe a training measure or an occupation-grain quantity.
3. An output whose unit marks it a relative signal may not be labelled with
   `vacancies`, `jobs`, `openings`, `demand volume` or similar count language, and
   its confidence may not be numeric.

Step 7.3.1 adds two rules:

4. **Ranking labels.** Phrasings that assert an *observed* ranking - "district demand
   ranking", "highest-demand districts", "top occupations by vacancies",
   "occupation shortage ranking" - are forbidden everywhere, because outputs B and C
   are derived allocation signals whose within-group ordering is an input's ordering.
5. **Corroboration labels.** A derivation input may never be framed as "independent
   validation" or "corroborating demand data" for the output it is a factor in.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from lmis.publish.contract import PublicationContract

_NUMERIC = re.compile(r"\d")


@dataclass(frozen=True)
class TerminologyViolation:
    output_id: str
    rule: str
    term: str
    where: str
    text: str

    def __str__(self) -> str:  # pragma: no cover - diagnostic
        return (
            f"{self.output_id}: [{self.rule}] forbidden term {self.term!r} "
            f"in {self.where}: {self.text!r}"
        )


# Dashes are normalised before matching. A label written "demand-supply gap" with
# an en dash must not slip past a rule written with a hyphen - that would be a hole
# in the lint, not a feature of the label.
_DASHES = str.maketrans({"\u2010": "-", "\u2011": "-", "\u2012": "-",
                         "\u2013": "-", "\u2014": "-", "\u2212": "-"})

# A forbidden term immediately preceded by one of these is a negation - the
# guardrail itself, not a breach of it. "no demand-supply gap is published" is
# exactly what the product must be able to say.
_NEGATORS = re.compile(
    r"(?:\bno\b|\bnot\b|\bnever\b|\bwithout\b|\bcannot\b|\bnone\b|"
    r"\bneither\b|\bnor\b|\bwhy\s+no\b)[\s\w,'\u2019-]{0,34}$",
    re.IGNORECASE,
)
_NEGATION_WINDOW = 46


def _normalise(text: str) -> str:
    return text.translate(_DASHES)


def _strip_negations(text: str, permitted: list[str]) -> str:
    """Remove explicitly permitted negating phrases before matching.

    `RELATIVE_RANKING_SIGNAL_NOT_A_VACANCY_COUNT` contains "vacancy", but it is the
    guardrail itself. Stripping an explicit allowlist keeps the check deterministic:
    an un-negated "vacancy count" on a relative signal still fails, because only the
    listed phrases are removed.
    """
    out = _normalise(text)
    for phrase in permitted:
        out = re.sub(re.escape(_normalise(phrase)), " ", out, flags=re.IGNORECASE)
    return out


def _is_negated(haystack: str, start: int) -> bool:
    """True when the occurrence at `start` sits just after a negating word."""
    window = haystack[max(0, start - _NEGATION_WINDOW):start]
    return bool(_NEGATORS.search(window))


def _hits(text: str, terms: list[str], permitted: list[str] | None = None) -> list[str]:
    """Forbidden terms actually ASSERTED in `text` (negated uses do not count)."""
    low = _strip_negations(text, permitted or []).lower()
    found: list[str] = []
    for term in terms:
        needle = _normalise(term).lower()
        pos = low.find(needle)
        while pos != -1:
            if not _is_negated(low, pos):
                found.append(term)
                break
            pos = low.find(needle, pos + 1)
    return found


def _is_relative_signal(spec_or_env: dict[str, Any], rel_units: list[str]) -> bool:
    return str(spec_or_env.get("unit") or "") in rel_units


def lint_label_catalogue(
    labels: dict[str, str], contract: PublicationContract, catalogue: str = "ui"
) -> list[TerminologyViolation]:
    """Lint a UI label catalogue or export header set (Step 7.3 §18 item 8).

    Translation files are where terminology drifts most easily, because a label is
    written once and then read by everyone. The same three rules apply as to
    contract labels: nothing may assert a shortage or gap, nothing may call a
    training measure supply, and nothing may assert an observed ranking.
    """
    t = contract.terminology
    everywhere = t["reserved_everywhere"]
    quantities = t["reserved_for_quantities"]
    rankings = t.get("forbidden_ranking_labels", [])
    corrob = t.get("forbidden_corroboration_labels", [])
    # Explanatory prose that must be able to NAME what the system does not publish.
    # Held in the contract, not hard-coded here, so every exemption is reviewable.
    neg = (
        t.get("permitted_negations", [])
        + t.get("permitted_explanatory_phrases", [])
    )
    v: list[TerminologyViolation] = []
    for key, text in labels.items():
        if not isinstance(text, str):
            continue
        for term in _hits(text, everywhere, neg):
            v.append(TerminologyViolation(catalogue, "reserved_everywhere", term, key, text))
        for term in _hits(text, quantities, neg):
            v.append(TerminologyViolation(
                catalogue, "reserved_for_quantities", term, key, text))
        for term in _hits(text, rankings, neg):
            v.append(TerminologyViolation(catalogue, "forbidden_ranking_label", term, key, text))
        for term in _hits(text, corrob, neg):
            v.append(TerminologyViolation(catalogue, "corroboration_label", term, key, text))
    return v


def lint_derivation_labels(
    contract: PublicationContract, section_labels: dict[str, str] | None = None
) -> list[TerminologyViolation]:
    """Lint how a derivation input is framed (Step 7.3.1 circularity rule).

    `section_labels` maps an input table to the UI section label it would be shown
    under. With no argument the declared contract rules are checked for internal
    consistency; Step 7.4 passes its real label catalogue.
    """
    v: list[TerminologyViolation] = []
    global_bad = contract.terminology.get("forbidden_corroboration_labels", [])
    for rule in contract.derivation_inputs:
        inp = rule["input"]
        permitted = [p.lower() for p in rule.get("permitted_section_labels", [])]
        banned = list({*rule.get("prohibited_labels", []), *global_bad})
        # the rule must not permit a label it also bans
        for allowed in permitted:
            for term in banned:
                if term.lower() in allowed:
                    v.append(TerminologyViolation(
                        inp, "corroboration_label", term, "permitted_section_labels", allowed))
        if section_labels and inp in section_labels:
            label = section_labels[inp]
            for term in _hits(label, banned):
                v.append(TerminologyViolation(
                    inp, "corroboration_label", term, "section_label", label))
            if label.lower() not in permitted:
                v.append(TerminologyViolation(
                    inp, "derivation_disclosure_only", label, "section_label", label))
    return v


def lint_contract(contract: PublicationContract) -> list[TerminologyViolation]:
    """Lint the declared labels in the contract itself."""
    t = contract.terminology
    everywhere = t["reserved_everywhere"]
    quantities = t["reserved_for_quantities"]
    rel_terms = t["forbidden_for_relative_signals"]
    rel_units = t["relative_signal_units"]
    rankings = t.get("forbidden_ranking_labels", [])
    neg = t.get("permitted_negations", [])
    v: list[TerminologyViolation] = []

    for spec in contract.outputs:
        oid = spec["output_id"]
        label = str(spec.get("allowed_label") or "")
        for term in _hits(label, everywhere, neg):
            v.append(TerminologyViolation(oid, "reserved_everywhere", term,
                                          "allowed_label", label))
        for term in _hits(label, rankings, neg):
            v.append(TerminologyViolation(oid, "forbidden_ranking_label", term,
                                          "allowed_label", label))
        # 'supply' in a label is permitted only where the label is about the
        # ABSENCE of supply evidence (a coverage table), never as a measure.
        if spec.get("unit") != "mixed":
            for term in _hits(label, quantities, neg):
                v.append(TerminologyViolation(oid, "reserved_for_quantities", term,
                                              "allowed_label", label))
        if _is_relative_signal(spec, rel_units):
            for term in _hits(label, rel_terms, neg):
                v.append(TerminologyViolation(oid, "relative_signal_not_a_count",
                                              term, "allowed_label", label))
    return v


def lint_envelopes(
    envelopes: list[dict[str, Any]], contract: PublicationContract
) -> list[TerminologyViolation]:
    """Lint the built envelopes: labels, interpretation, and confidence shape."""
    t = contract.terminology
    everywhere = t["reserved_everywhere"]
    quantities = t["reserved_for_quantities"]
    rel_terms = t["forbidden_for_relative_signals"]
    rel_units = t["relative_signal_units"]
    allowed_conf = set(t["allowed_confidence_values"])
    rankings = t.get("forbidden_ranking_labels", [])
    corrob = t.get("forbidden_corroboration_labels", [])
    neg = t.get("permitted_negations", [])
    v: list[TerminologyViolation] = []

    for env in envelopes:
        oid = env["output_id"]
        for where in ("allowed_label", "interpretation"):
            text = str(env.get(where) or "")
            for term in _hits(text, everywhere, neg):
                v.append(TerminologyViolation(oid, "reserved_everywhere", term,
                                              where, text))
            for term in _hits(text, rankings, neg):
                v.append(TerminologyViolation(oid, "forbidden_ranking_label", term,
                                              where, text))
            for term in _hits(text, corrob, neg):
                v.append(TerminologyViolation(oid, "corroboration_label", term,
                                              where, text))
            if env.get("unit") != "mixed":
                for term in _hits(text, quantities, neg):
                    v.append(TerminologyViolation(oid, "reserved_for_quantities",
                                                  term, where, text))
            if _is_relative_signal(env, rel_units):
                for term in _hits(text, rel_terms, neg):
                    v.append(TerminologyViolation(
                        oid, "relative_signal_not_a_count", term, where, text))

        # Rule T-1: a relative signal may not advertise a count-like unit.
        if _is_relative_signal(env, rel_units):
            for term in _hits(str(env.get("unit")), rel_terms, neg):
                v.append(TerminologyViolation(oid, "relative_signal_not_a_count",
                                              term, "unit", str(env["unit"])))

        # Confidence stays categorical - never a probability or percentage.
        for c in env.get("confidence") or []:
            cs = str(c)
            if _NUMERIC.search(cs) or cs not in allowed_conf:
                v.append(TerminologyViolation(oid, "confidence_must_be_categorical",
                                              cs, "confidence", cs))
    return v
