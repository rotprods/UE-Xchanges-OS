from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class EvidenceItem:
    evidence_id:str; fact:str; topics:frozenset[str]; externally_usable:bool=True
@dataclass(frozen=True)
class CriterionMatch:
    criterion:str; evidence_ids:tuple[str,...]; gap:bool

def map_criteria_to_evidence(criteria:list[str],evidence:list[EvidenceItem])->list[CriterionMatch]:
    matches=[]
    for criterion in criteria:
        words={w.lower().strip(".,:;()[]") for w in criterion.split() if len(w)>3}; candidates=[]
        for item in evidence:
            if not item.externally_usable: continue
            haystack=item.fact.lower()+" "+" ".join(item.topics).lower()
            if any(word in haystack for word in words): candidates.append(item.evidence_id)
        matches.append(CriterionMatch(criterion,tuple(candidates[:5]),gap=not candidates))
    return matches
