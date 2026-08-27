from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any

class Role(str, Enum):
    PARTICIPANT = "participant"
    YOUTH_WORKER = "youth_worker"
    FACILITATOR = "facilitator"
    TRAINER = "trainer"
    EXPERT = "expert"

class GateResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"

class AIPolicy(str, Enum):
    ALLOWED = "ai_allowed"
    ASSIST_ONLY = "ai_assist_only"
    FINAL_TEXT_PROHIBITED = "ai_final_text_prohibited"
    UNKNOWN = "ai_unknown"

@dataclass(frozen=True)
class Provenance:
    source: str
    fetched_at: datetime | None = None
    locator: str | None = None
    method: str = "source"
    confidence: float = 1.0

@dataclass
class ApplicantProfile:
    residence_country: str | None = None
    age: int | None = None
    languages: set[str] = field(default_factory=set)
    roles: set[Role] = field(default_factory=set)
    topics: set[str] = field(default_factory=set)
    available_from: date | None = None
    available_to: date | None = None
    previous_programme_months: dict[str, float] = field(default_factory=dict)
    evidence_ids: set[str] = field(default_factory=set)

@dataclass
class Opportunity:
    opportunity_id: str
    title: str
    programme: str
    role: Role
    source_url: str
    deadline: datetime | None = None
    start_date: date | None = None
    end_date: date | None = None
    eligible_countries: set[str] | None = None
    age_min: int | None = None
    age_max: int | None = None
    required_languages: set[str] = field(default_factory=set)
    required_topics: set[str] = field(default_factory=set)
    requires_support_org: bool | None = None
    ai_policy: AIPolicy = AIPolicy.UNKNOWN
    facts: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Provenance] = field(default_factory=dict)

@dataclass(frozen=True)
class GateDecision:
    name: str
    result: GateResult
    reason: str

@dataclass
class EligibilityDecision:
    result: GateResult
    gates: list[GateDecision]
    @property
    def failed(self) -> bool:
        return any(g.result is GateResult.FAIL for g in self.gates)

@dataclass(frozen=True)
class ScoreComponent:
    name: str
    score: float
    weight: float

@dataclass
class ScoreCard:
    total: float
    band: str
    components: list[ScoreComponent]
    blocked_reason: str | None = None
