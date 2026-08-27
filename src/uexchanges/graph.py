from __future__ import annotations
import hashlib,json
from dataclasses import asdict,dataclass,field
from datetime import datetime,timezone
from typing import Any,Iterable

def stable_id(kind:str,natural_key:str)->str:
    return f"{kind.lower()}_{hashlib.sha256(f'{kind}:{natural_key}'.encode()).hexdigest()[:20]}"

@dataclass(frozen=True)
class GraphEvent:
    event_id:str; event_type:str; occurred_at:str; subject_id:str; payload:dict[str,Any]=field(default_factory=dict); source:str|None=None
    @classmethod
    def create(cls,event_type:str,subject_id:str,payload:dict[str,Any],source:str|None=None)->"GraphEvent":
        occurred_at=datetime.now(timezone.utc).isoformat(); raw=json.dumps([event_type,subject_id,occurred_at,payload,source],sort_keys=True,default=str)
        return cls("evt_"+hashlib.sha256(raw.encode()).hexdigest()[:24],event_type,occurred_at,subject_id,payload,source)

def events_to_jsonl(events:Iterable[GraphEvent])->str:
    return "\n".join(json.dumps(asdict(e),sort_keys=True) for e in events)

class GraphProjection:
    def __init__(self)->None:
        self.nodes:dict[str,dict[str,Any]]={}; self.edges:set[tuple[str,str,str]]=set()
    def apply(self,event:GraphEvent)->None:
        if event.event_type=="NODE_UPSERTED": self.nodes.setdefault(event.subject_id,{}).update(event.payload)
        elif event.event_type=="EDGE_ADDED": self.edges.add((event.payload["from"],event.payload["type"],event.payload["to"]))
        elif event.event_type=="EDGE_REMOVED": self.edges.discard((event.payload["from"],event.payload["type"],event.payload["to"]))
    @classmethod
    def rebuild(cls,events:Iterable[GraphEvent])->"GraphProjection":
        p=cls()
        for e in events: p.apply(e)
        return p
