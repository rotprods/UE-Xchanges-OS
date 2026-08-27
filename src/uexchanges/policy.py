from __future__ import annotations
import re
from .models import AIPolicy

_PROHIBITED=[r"applications? written with chatgpt.*will not be considered",r"do not use (?:chatgpt|ai|artificial intelligence)",r"ai[- ]generated (?:answers?|applications?).*(?:not accepted|not considered|prohibited)",r"must be written in your own words.*(?:without|no) (?:ai|chatgpt)"]
_ASSIST_ONLY=[r"use of ai.*(?:disclose|declare)",r"ai may be used.*(?:research|proofread|assist)"]

def detect_ai_policy(text:str)->AIPolicy:
    normalized=" ".join(text.lower().split())
    if any(re.search(p,normalized) for p in _PROHIBITED): return AIPolicy.FINAL_TEXT_PROHIBITED
    if any(re.search(p,normalized) for p in _ASSIST_ONLY): return AIPolicy.ASSIST_ONLY
    return AIPolicy.UNKNOWN

def final_text_generation_allowed(policy:AIPolicy)->bool:
    return policy in {AIPolicy.ALLOWED,AIPolicy.ASSIST_ONLY}
