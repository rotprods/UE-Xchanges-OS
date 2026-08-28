# Portfolio Conflict Graph

## Purpose

Preserve option value while preventing impossible double commitments.

A date overlap is **not** an application blocker. It creates a graph edge:

`Opportunity A -[MUTUALLY_EXCLUSIVE_IF_ACCEPTED]-> Opportunity B`

The edge becomes an execution gate only when the applicant tries to move an overlapping accepted opportunity into `COMMITTED`.

## Interval rule

Activity date ranges are inclusive:

- A ends 16 Oct, B starts 16 Oct -> overlap.
- A ends 16 Oct, B starts 17 Oct -> no overlap.

Missing or disputed dates do not silently disappear. They create verification debt; conflict edges derived from disputed dates must be marked provisional in operational projections.

## Allowed state behaviour

| Existing state | Overlapping new APPLIED | Overlapping new ACCEPTED | Commit target |
|---|---:|---:|---:|
| CANDIDATE | allowed | allowed | n/a |
| APPLIED | allowed | allowed | allowed |
| ACCEPTED | allowed | allowed | `PORTFOLIO_RESOLUTION` |
| COMMITTED | allowed to apply | acceptance may be recorded | `PORTFOLIO_RESOLUTION` |
| WITHDRAWN/REJECTED/EXPIRED | ignored | ignored | ignored |

Receiving two acceptances is allowed because it preserves the human owner's choice. Confirming/committing to incompatible mobilities is not.

## Mandatory transition

Before `ACCEPTED -> COMMITTED`:

1. Build current conflict edges from verified inclusive date intervals.
2. Find overlapping nodes in `ACCEPTED` or `COMMITTED`.
3. If none exist: `COMMIT_NO_ACTIVE_PORTFOLIO_CONFLICT`.
4. If any exist: route to `PORTFOLIO_RESOLUTION` with code `RESOLVE_MUTUALLY_EXCLUSIVE_ACCEPTANCE`.
5. Human owner chooses which opportunity to keep.
6. Other accepted alternative(s) must move to a resolved state such as `WITHDRAWN` before commitment continues.

## Calendar evidence

Google Calendar is a separate evidence source, not the portfolio graph itself.

- A calendar busy window can establish a concrete availability conflict.
- An empty calendar does **not** prove full real-world availability.
- Long-term ESC commitments require explicit private availability confirmation even if Calendar is empty.

## Current autumn-2026 examples

The current portfolio contains these meaningful edges:

- `CTRL+REAL` <-> `Building With Our Hands`
- `Building With Our Hands` <-> `Game of Nature`
- `Game of Nature` <-> `Unleashing Creativity`
- long-term `A Cu’ AppARTeni` and `Solsona` overlap with many short autumn opportunities and therefore carry high option cost.

`Digi-Hack` (18-25 Sep) currently has no overlap with the principal P0 autumn calls.

## Deterministic implementation

`src/uexchanges/portfolio.py`

Public primitives:

- `intervals_overlap()`
- `build_conflict_edges()`
- `evaluate_commitment()`

Regression coverage lives in `tests/test_portfolio.py`.
