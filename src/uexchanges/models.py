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

    # Historical youth-sector experience and CURRENT youth-work context are different facts.
    # Historical participation may improve fit/selection evidence but must never auto-satisfy
    # a call that explicitly requires present involvement in youth work.
    youth_sector_experience_verified: bool | None = None
    youth_sector_last_activity_date: date | None = None
    completed_erasmus_youth_staff_mobilities: int = 0
    completed_erasmus_youth_exchanges: int = 0

    # True only when private evidence demonstrates CURRENT involvement in youth work
    # (or another explicitly accepted current youth-work-context target). None = unverified.
    youth_work_context_verified: bool | None = None

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
    # Platform/call-level CURRENT-context requirement. Historical youth-sector
    # participation is evidence, but it cannot silently satisfy this gate.
    requires_youth_work_context: bool = False
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
