# Critical Fact Correction — Triglav Deadline — 2026-08-28

## Incident

The operational state temporarily promoted `2026-09-05 15:00` as the application deadline for European Youth Portal opportunity `53491` (Guardians of Triglav National Park).

A fresh fetch of the official detail page at approximately 14:27 Europe/Madrid on 2026-08-28 showed:

- application deadline: **28/08/2026 15:00**;
- activity: 21/09/2026–05/10/2026;
- Spain listed as eligible;
- authenticated European Youth Portal sign-in required to apply.

The 05 September fact was erroneous and is revoked.

## Immediate remediation

- Drive application dossier corrected.
- CRM Opportunity and Application nodes corrected.
- Todoist task escalated to deadline-critical.
- `LIVE-STATE-OVERRIDE.json` created to supersede stale `goal-state.json` fields until integrated.
- User explicitly alerted that manual authenticated portal action is required.

## Root failure

A same-provider result interpreted as a newer official crawl was promoted without preserving the exact source-page text and fetch timestamp strongly enough. The system then treated that interpretation as authoritative.

## Mandatory prevention rules

1. Deadline changes require exact quoted/source-located evidence from the canonical detail page.
2. Search snippets, cached previews and inferred crawl recency may not supersede a canonical detail page.
3. A later fetch timestamp does not prove the underlying deadline changed.
4. Material deadline extensions require two-source verification when practical: canonical detail page plus form/provider confirmation.
5. Any deadline shortening inside 24 hours triggers `DEADLINE_CRITICAL` and immediate user escalation.
6. A fact-resolution event must preserve `observed_value`, `observed_at`, `source_url`, `source_locator` and `superseded_value`.
7. Do not describe an inferred date as “current official” unless the exact canonical page contains it.

## State

`FRESH_OFFICIAL_DETAIL_PAGE_CONTROLS`

Official deadline: `2026-08-28T15:00:00+02:00`.
