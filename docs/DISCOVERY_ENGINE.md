# Discovery Engine

## Objective
High recall without application spam. Discovery may be broad; verification and hard gates must be strict.

## Tiering
- Tier 0: official programme/agency portals and SALTO/Eurodesk ecosystem.
- Tier 1: organisations with recurring verified Erasmus/ESC/training history.
- Tier 2: discovery/search/social signals. These may create candidates but never authoritative facts.

## Incremental loop
`source registry -> fetch -> content hash -> candidate links -> canonical URLs -> fingerprint -> dedupe -> provider adapter -> raw evidence -> verify -> canonical record`.

## Identity hierarchy
1. Provider project/call ID.
2. Canonical application/opportunity URL.
3. Fallback `(host, normalised title, start date, country)` fingerprint.

Never dedupe by title alone.

## Change detection
Persist `(source URL, ETag/Last-Modified if available, sha256, fetched_at)`. If unchanged, skip downstream extraction. If changed, emit a graph event and re-verify eligibility-critical facts.

## Search strategy
Use official indexes first; then organisation graph watchers; then search-engine/social discovery for new publishers. Newly discovered organisations begin with low trust and earn source quality through repeated verified calls/outcomes.

## Mass application constraint
The mass part is discovery, parsing, triage, evidence retrieval and dossier preparation. Submission volume is capped by eligibility, fit, policy and human review.
