from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "mc_cid", "mc_eid"
}

SOURCE_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    "eyp_esc": (re.compile(r"/solidarity/opportunity/\d+", re.I),),
    "salto_calendar": (re.compile(r"/tools/european-training-calendar/training/[^/?#]+", re.I),),
    "salto_trainers": (
        re.compile(r"/tools/call-for-trainers/call/[^/?#]+", re.I),
        re.compile(r"/tools/call-for-trainers/[^/?#]+", re.I),
    ),
    "eurodesk": (re.compile(r"programmes\.eurodesk\.eu", re.I),),
    "eurodesk_es": (re.compile(r"/oportunidades/", re.I),),
}

@dataclass(frozen=True)
class SourceConfig:
    source_id: str
    name: str
    tier: int
    source_type: str
    url: str | None
    cadence_hours: int
    enabled: bool = True

@dataclass(frozen=True)
class DiscoveredURL:
    source_id: str
    url: str
    canonical_url: str
    anchor_text: str | None = None

@dataclass(frozen=True)
class FetchResult:
    url: str
    final_url: str
    status: int
    content_type: str | None
    fetched_at_epoch: float
    content: bytes
    sha256: str

class _LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        if tag.lower() == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data: str):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str):
        if tag.lower() == "a" and self._href is not None:
            self.links.append((self._href, " ".join("".join(self._text).split())))
            self._href = None
            self._text = []

def canonicalize_url(url: str) -> str:
    p = urllib.parse.urlsplit(url.strip())
    scheme = p.scheme.lower() or "https"
    netloc = p.netloc.lower()
    if netloc.endswith(":80") and scheme == "http": netloc = netloc[:-3]
    if netloc.endswith(":443") and scheme == "https": netloc = netloc[:-4]
    path = re.sub(r"/{2,}", "/", p.path or "/")
    if path != "/": path = path.rstrip("/")
    query = urllib.parse.parse_qsl(p.query, keep_blank_values=True)
    query = [(k, v) for k, v in query if k.lower() not in TRACKING_PARAMS]
    query.sort()
    return urllib.parse.urlunsplit((scheme, netloc, path, urllib.parse.urlencode(query), ""))

def content_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def opportunity_fingerprint(*, provider_id: str | None = None, canonical_url: str | None = None,
                            host: str | None = None, title: str | None = None,
                            start_date: str | None = None, country: str | None = None) -> str:
    if provider_id:
        basis = f"provider:{provider_id.strip().lower()}"
    elif canonical_url:
        basis = f"url:{canonicalize_url(canonical_url)}"
    else:
        parts = [host or "", title or "", start_date or "", country or ""]
        basis = "fallback:" + "|".join(re.sub(r"\s+", " ", p.strip().lower()) for p in parts)
    return "opp_" + hashlib.sha256(basis.encode()).hexdigest()[:24]

def extract_links(html: str, base_url: str) -> list[tuple[str, str]]:
    parser = _LinkExtractor(); parser.feed(html)
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for href, text in parser.links:
        if not href or href.startswith(("mailto:", "tel:", "javascript:")): continue
        absolute = urllib.parse.urljoin(base_url, href)
        canonical = canonicalize_url(absolute)
        if canonical in seen: continue
        seen.add(canonical); out.append((canonical, text))
    return out

def is_candidate_link(source_id: str, url: str) -> bool:
    patterns = SOURCE_PATTERNS.get(source_id)
    if not patterns: return True
    return any(p.search(url) for p in patterns)

def discover_from_html(source_id: str, html: str, base_url: str) -> list[DiscoveredURL]:
    results=[]
    for url, text in extract_links(html, base_url):
        if is_candidate_link(source_id, url):
            results.append(DiscoveredURL(source_id=source_id, url=url, canonical_url=url, anchor_text=text or None))
    return results

def dedupe_discovered(items: Iterable[DiscoveredURL]) -> list[DiscoveredURL]:
    out=[]; seen=set()
    for item in items:
        key=item.canonical_url
        if key in seen: continue
        seen.add(key); out.append(item)
    return out

def load_sources(path: str | Path) -> list[SourceConfig]:
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    out=[]
    for s in data.get("sources",[]):
        out.append(SourceConfig(
            source_id=s["id"], name=s["name"], tier=int(s.get("tier",1)),
            source_type=s.get("type","unknown"), url=s.get("url"),
            cadence_hours=int(s.get("cadence_hours",24)), enabled=bool(s.get("enabled",True))
        ))
    return out

def fetch_url(url: str, *, timeout: float = 20.0, max_bytes: int = 5_000_000,
              user_agent: str = "UE-Xchanges-OS/0.1 (+https://github.com/rotprods/UE-Xchanges-OS)") -> FetchResult:
    req=urllib.request.Request(url, headers={"User-Agent":user_agent, "Accept":"text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.5"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        content=response.read(max_bytes+1)
        if len(content)>max_bytes: raise ValueError(f"Response exceeds max_bytes={max_bytes}")
        return FetchResult(
            url=url, final_url=response.geturl(), status=getattr(response,"status",200),
            content_type=response.headers.get("Content-Type"), fetched_at_epoch=time.time(),
            content=content, sha256=content_hash(content)
        )
