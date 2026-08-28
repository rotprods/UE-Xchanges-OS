# Fact Resolution Protocol

## Why

Opportunity calls change. A live listing can be updated after an infopack PDF, cached page, newsletter or social post was produced. The system must preserve contradictions without letting an LLM choose the convenient value.

## Claim model

Each material fact may have one or more claims:

- `fact_key`
- `value`
- `source_id`
- `authority_rank`
- `observed_at`
- `live_current`

Material facts include deadlines, dates, eligible countries, age, fees, funding, participant profile and application/AI policy.

## Deterministic resolution

1. No claim -> `VERIFY_MISSING_FACT`.
2. All claims agree -> `RESOLVE_CONSISTENT_FACT` using the highest-authority/newest claim for provenance.
3. Conflicting claims are unresolved by default -> `VERIFY_CONFLICTING_FACT`.
4. Automatic supersession is allowed only when exactly one claim:
   - is marked `live_current`;
   - is at the highest authority level among the claims;
   - is strictly newer than every conflicting claim at that authority level.
5. That narrow case yields `LIVE_SOURCE_SUPERSEDES_STALE_ARTIFACT`.
6. Lower-authority freshness can never override a higher-authority contradictory source automatically.

## Digi-Hack fixture

Observed 28 Aug 2026:

- a stale downloadable infopack contained an older August application date;
- older cached SALTO detail text also contained an earlier date;
- the fresh current SALTO index/listing exposed deadline 28 Aug 2026 and continued to route `Apply now` to the external form.

The operational record therefore preserves all claims and uses the current live claim for execution, with supersession provenance rather than silently rewriting history.

## Safety invariant

If authority/freshness dominance is not explicit, the application remains in `VERIFICATION_DEBT` whenever the conflict can affect eligibility, deadline, dates, fee, funding or policy.

## Implementation

- `src/uexchanges/facts.py`
- `tests/test_facts.py`
