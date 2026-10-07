"""Weakest-link confidence, per the Step 3.1 methodology.

Overall confidence is the WORST of its dimensions, never an average: averaging
lets a strong term mask a fatal one, which is exactly how a historical prior or a
national proxy gets laundered into a confident-looking district number.

No numeric probabilities are produced. There is no statistical basis for saying
"83% confident" about a product of a survey share and a 2011 census share, so the
output is an ordinal category, and the dimensions that produced it are stored
alongside it so the verdict stays explainable.

REFINEMENT MADE DURING IMPLEMENTATION (Step 4.0): the Step 3.1 draft had no way
to say "this dimension does not apply to this output". Output B has no occupation
dimension BY DESIGN, and scoring that as NOT_AVAILABLE wrongly drove it to LOW -
penalising a deliberate design choice as if it were missing evidence. Hence
NOT_APPLICABLE, which is excluded from all triggers. NOT_AVAILABLE now means only
what it should: we wanted this evidence and do not have it.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

HIGH, MEDIUM, LOW = "HIGH", "MEDIUM", "LOW"
NOT_APPLICABLE = "NOT_APPLICABLE"

SOURCE_CONFIDENCE = {"OBSERVED", "SURVEY_ESTIMATE", "ADMINISTRATIVE"}
TEMPORAL = {"CURRENT", "RECENT", "STALE", "HISTORICAL", NOT_APPLICABLE}
GEOGRAPHY = {"DIRECT", "ALLOCATED", "NATIONAL_PROXY", NOT_APPLICABLE}
OCCUPATION = {"DIRECT", "DIVISION_MAPPED", "NATIONAL_PROXY", "NOT_AVAILABLE", NOT_APPLICABLE}
STATISTICAL = {
    "CENSUS",
    "ADMINISTRATIVE_FULL_COVERAGE",
    "SURVEY_WITH_N",
    "SURVEY_WITHOUT_N",
    "NONE",
    NOT_APPLICABLE,
}

# A dimension drives the result to LOW when it is actively disqualifying.
_LOW_TRIGGERS = {
    "temporal_confidence": {"HISTORICAL"},
    "geography_coverage": {"NATIONAL_PROXY"},
    "occupation_coverage": {"NATIONAL_PROXY", "NOT_AVAILABLE"},
}
_MEDIUM_TRIGGERS = {
    "temporal_confidence": {"STALE"},
    "geography_coverage": {"ALLOCATED"},
    "occupation_coverage": {"DIVISION_MAPPED"},
    "statistical_support": {"SURVEY_WITHOUT_N"},
}

VALID = {
    "source_confidence": SOURCE_CONFIDENCE,
    "temporal_confidence": TEMPORAL,
    "geography_coverage": GEOGRAPHY,
    "occupation_coverage": OCCUPATION,
    "statistical_support": STATISTICAL,
}


@dataclass(frozen=True)
class Confidence:
    source_confidence: str
    mapping_confidence: float | None   # measured purity 0-1, or None if no mapping used
    temporal_confidence: str
    geography_coverage: str
    occupation_coverage: str
    statistical_support: str
    transformation_depth: int          # number of multiplicative derivations

    def __post_init__(self) -> None:
        for field, allowed in VALID.items():
            value = getattr(self, field)
            if value not in allowed:
                raise ValueError(f"{field}={value!r} not in {sorted(allowed)}")
        if self.mapping_confidence is not None and not 0.0 <= self.mapping_confidence <= 1.0:
            raise ValueError(f"mapping_confidence out of range: {self.mapping_confidence}")
        if self.transformation_depth < 0:
            raise ValueError("transformation_depth must be >= 0")

    def overall(self) -> str:
        d = asdict(self)
        for field, triggers in _LOW_TRIGGERS.items():
            if d[field] in triggers:
                return LOW
        if self.mapping_confidence is not None and self.mapping_confidence < 0.85:
            return LOW
        if self.transformation_depth >= 3:
            return LOW
        for field, triggers in _MEDIUM_TRIGGERS.items():
            if d[field] in triggers:
                return MEDIUM
        if self.mapping_confidence is not None and self.mapping_confidence < 0.95:
            return MEDIUM
        if self.transformation_depth > 1:
            return MEDIUM
        return HIGH

    def as_columns(self) -> dict:
        out = asdict(self)
        out["overall_confidence"] = self.overall()
        return out
