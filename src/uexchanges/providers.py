from __future__ import annotations

import urllib.parse
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from .discovery import (
    DiscoveredURL,
    canonicalize_url,
    dedupe_discovered,
    discover_from_html,
    opportunity_fingerprint,
)
from .source_state import SourceStateStore


class AccessMode(str, Enum):
    STATIC_PAGINATED_HTML = "static_paginated_html"
    DYNAMIC_INDEX = "dynamic_index"
    AUTH_INDEX_PUBLIC_DETAILS = "auth_index_public_details"
    EXTERNAL_CANDIDATES = "external_candidates"


@dataclass(frozen=True)
class ProviderSpec:
    source_id: str
    index_url: str
    access_mode: AccessMode
    page_size: int = 10
    max_pages: int = 20


@dataclass(frozen=True)
class PagePayload:
    url: str
    status: int
    text: str
    content_hash: str
    etag: str | None = None
    last_modified: str | None = None


@dataclass
class ScanReport:
    source_id: str
    access_mode: AccessMode
    pages_fetched: int = 0
    pages_changed: int = 0
    candidates_found: int = 0
    new_candidates: int = 0
    candidates: list[DiscoveredURL] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blocked_reason: str | None = None


def salto_page_url(base_url: str, offset: int, limit: int = 10) -> str:
    """Build deterministic SALTO pagination while preserving caller filters."""
    parts = urllib.parse.urlsplit(base_url)
    q = dict(urllib.parse.parse_qsl(parts.query, keep_blank_values=True))
    q["b_limit"] = str(limit)
    q["b_offset"] = str(offset)
    q.setdefault("b_order", "applicationDeadline")
    return urllib.parse.urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urllib.parse.urlencode(q), "")
    )


class ProviderScanner:
    """Provider-aware discovery scanner.

    `fetch_page` is injected so network code, tests and agentic/browser discovery
    share the same deterministic processing layer.
    """

    def __init__(self, state: SourceStateStore) -> None:
        self.state = state

    def scan(
        self,
        spec: ProviderSpec,
        fetch_page: Callable[[str, dict[str, str]], PagePayload],
    ) -> ScanReport:
        report = ScanReport(spec.source_id, spec.access_mode)
        if spec.access_mode is AccessMode.DYNAMIC_INDEX:
            report.blocked_reason = (
                "Index content is client-rendered/dynamic. Use a browser/API/search-backed "
                "collector and feed discovered detail URLs through ingest_external_candidates()."
            )
            return report
        if spec.access_mode is AccessMode.AUTH_INDEX_PUBLIC_DETAILS:
            report.blocked_reason = (
                "Index requires authentication while detail pages may be public. Do not bypass "
                "access controls; use authorised login or search-backed public-detail discovery."
            )
            return report
        if spec.access_mode is not AccessMode.STATIC_PAGINATED_HTML:
            report.blocked_reason = "This source is candidate-fed rather than index-scanned."
            return report

        found: list[DiscoveredURL] = []
        for page_no in range(spec.max_pages):
            offset = page_no * spec.page_size
            page_url = salto_page_url(spec.index_url, offset, spec.page_size)
            headers = self.state.conditional_headers(spec.source_id, page_url)
            payload = fetch_page(page_url, headers)
            report.pages_fetched += 1
            changed = self.state.record_fetch(
                spec.source_id,
                canonicalize_url(payload.url),
                status=payload.status,
                content_hash=payload.content_hash,
                etag=payload.etag,
                last_modified=payload.last_modified,
            )
            report.pages_changed += int(changed)
            if payload.status == 304:
                continue
            if payload.status < 200 or payload.status >= 300:
                report.warnings.append(f"Non-success status {payload.status} for {payload.url}")
                break
            candidates = discover_from_html(spec.source_id, payload.text, payload.url)
            if not candidates:
                break
            found.extend(candidates)
            if len(candidates) < spec.page_size:
                break

        report.candidates = dedupe_discovered(found)
        report.candidates_found = len(report.candidates)
        for item in report.candidates:
            fp = opportunity_fingerprint(canonical_url=item.canonical_url)
            if self.state.mark_candidate_seen(fp, spec.source_id, item.canonical_url):
                report.new_candidates += 1
        return report

    def ingest_external_candidates(self, source_id: str, urls: list[str]) -> ScanReport:
        report = ScanReport(source_id, AccessMode.EXTERNAL_CANDIDATES)
        seen: set[str] = set()
        for raw in urls:
            canonical = canonicalize_url(raw)
            if canonical in seen:
                continue
            seen.add(canonical)
            item = DiscoveredURL(source_id, raw, canonical, None)
            report.candidates.append(item)
            fp = opportunity_fingerprint(canonical_url=canonical)
            if self.state.mark_candidate_seen(fp, source_id, canonical):
                report.new_candidates += 1
        report.candidates_found = len(report.candidates)
        return report


DEFAULT_PROVIDER_SPECS = {
    "salto_calendar": ProviderSpec(
        source_id="salto_calendar",
        index_url="https://www.salto-youth.net/tools/european-training-calendar/browse/",
        access_mode=AccessMode.STATIC_PAGINATED_HTML,
        page_size=10,
        max_pages=20,
    ),
    "salto_trainers": ProviderSpec(
        source_id="salto_trainers",
        index_url="https://www.salto-youth.net/tools/call-for-trainers/",
        access_mode=AccessMode.AUTH_INDEX_PUBLIC_DETAILS,
    ),
    "eyp_esc": ProviderSpec(
        source_id="eyp_esc",
        index_url="https://youth.europa.eu/go-abroad/volunteering/opportunities_en",
        access_mode=AccessMode.DYNAMIC_INDEX,
    ),
    "eurodesk": ProviderSpec(
        source_id="eurodesk",
        index_url="https://programmes.eurodesk.eu/en",
        access_mode=AccessMode.DYNAMIC_INDEX,
    ),
}
