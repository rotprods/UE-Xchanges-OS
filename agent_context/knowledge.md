# UE-Xchanges-OS — Knowledge / Evidence Map

> Public, non-sensitive recovery summary. Private applicant facts/answers remain in Drive and authorised sources.

## Knowledge classes

### A — Authoritative external evidence
Examples:
- official call page;
- authorised form;
- organiser email/thread;
- contract;
- payment/submission receipt;
- portal confirmation.

These can change domain truth.

### B — Canonical private operational evidence
Drive CRM, Event Bus, application rows, opportunity rows, evidence refs, receipts, sessions and leases.

### C — Versioned public system knowledge
GitHub policies, schemas, code, tests, architecture and non-sensitive recovery projections.

### D — Derived execution knowledge
RuntimeGraph, Command Center, Notion, Todoist, HubSpot relationship projections.

D never overrides A/B.

## Known domain facts at snapshot

### COMPASS
- Historical application existence is proven by organiser outcome sequence.
- #1 waitlist → selected after withdrawal.
- Acceptance reply sent.
- Confirmation still requires human payment/receipt/Tally.
- Original submit timestamp/receipt remains unrecovered.

### Step Into Paralympics
- Normal participants can be disabled or non-disabled.
- Normal participant route does not require youth-work experience.
- Organiser extended deadline date to 1 Sep.
- Official form was still live during 23:35 dispatcher scan.
- Exact closing time remained unknown.
- Human Frontier promoted to READY; no receipt yet.

### CIVIS LAB
- Current youth-sector employment not mandatory.
- Spanish route eligible.
- Human payment/proof gate precedes participant-list inclusion.
- Travel booking only after host authorisation.

### SABER / Soilpunk
- Official deadline passed historically.
- Host explicitly authorised late application after Spanish cancellation.
- Form/receipt state unresolved.

### Game of Nature
- Strong participant invitation.
- Group-leader suggestion exists, but GL duties/requirements remain separate unresolved evidence.

### I-PLAY
- Sending organisation reported open places.
- Current exact route/deadline/details require reconciliation.

### CONVIVIAL FOODSCAPES
- Canonical row: `non_salto-convivial-foodscapes-2026`.
- Priority P1.
- Deadline 2026-09-15.
- `AI_UNKNOWN` hard gate.
- Full-November availability unconfirmed.
- Not enqueued to Mass Apply while those gates remain open.

## Known infrastructure facts

- Drive is canonical CRM/event authority.
- `goal.md` carries canonical mission/policy but its numeric scale is historic.
- Root `STATE.md/HANDOFF.md` were stale at the start of this snapshot; another active continuity session owns their refresh.
- Current GitHub main: `d1d82b0dbb8d5712888cef7d247b2487f9fd7514`.
- Browser Stack main CI: `33565691506` and `33565691512`, both SUCCESS.
- Browser Worker bearer is memory-only.
- Browser Relay local prefill uses plan/request-bound HMAC capability.
- Browser Stack persists only a local 0600 capability-signing key; external targets and Submit remain unavailable.

## Unknown / verification debt

- Exact current deadline hour for Step unless a newer organiser/source event resolves it.
- Submission receipts for current Human Frontier actions.
- Original COMPASS receipt/submission time.
- 60 Telegram post bodies.
- CONVIVIAL AI policy.
- CONVIVIAL full-November availability.
- Some profile hard gates for professional/trainer calls.
- HubSpot write reauthorisation if relationship projection is resumed.

## Forbidden inference

Never infer:
- disability/health;
- youth-worker/trainer status;
- education;
- safeguarding/first aid;
- work rights beyond explicit legal/profile evidence;
- submission success from prepared form/email/task;
- payment success from payment instructions;
- acceptance from invitation to apply.

## Knowledge update protocol

Every material new fact should carry:
- source/evidence ref;
- fetched/received timestamp;
- entity/opportunity/application ID;
- previous state;
- new state;
- confidence/authority class;
- next gate;
- idempotency/event ref.

If the fact changes domain truth, persist Drive first, then recompute RuntimeGraph/projections.