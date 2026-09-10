# UE-Xchanges-OS — CGEV2 + COS integration map

Seal: `2026-09-10T14:46:00+02:00`

## CGEV2 in this repository

CGEV2 is the project's continuity/control discipline, not a second database product. The existing repo history already uses the term for the zero-context survival layer established on 2026-09-01.

CGEV2 responsibilities:

- reconstruct authority from current main + private Drive + provider evidence;
- persist session identity, leases, EventBus provenance and recovery checkpoints;
- distinguish canonical facts from projections;
- preserve exact IDs, causal parents, source versions and idempotency;
- provide zero-context `STATE/HANDOFF/checkpoint/agent_context` recovery;
- run reconciliation rather than silently overwriting contradictions;
- keep human/external/irreversible gates explicit;
- make every agent able to answer `where are we, why, under what authority, and what is next?` without chat history.

CGEV2 does **not** make a stale projection canonical and does not grant browser/payment/submission capability.

## COS in this repository

The repo implements a local semantic/COS graph layer under `src/uexchanges/semantic/**`:

- deterministic COS-20D projection (`COS_DIMENSIONS = 20`);
- semantic vector + `cos20` named-vector topology;
- Qdrant-backed retrieval when configured;
- `graphify` / `cos-graph-engine` CLI entrypoints;
- reconstructible graph artifacts and neighbour topology;
- provenance-aware local semantic navigation.

`ARCHITECTURE.md` intentionally describes the system as evidence-first with a small deterministic event/graph core and COS-style provenance rather than making a generic graph platform the source of truth.

## Authority split

```text
                           AUTHORITATIVE EVIDENCE
        official / organiser / receipt / private Drive canonical state
                                      |
                                      v
                                  CGEV2
              identity · provenance · sessions · leases · events
                     state reconstruction · reconciliation
                     /                              \
                    v                                v
          RuntimeGraph RG2.x                  COS semantic layer
    exact-ID deterministic reducer       retrieval / neighbour topology
    frontiers / cursors / projections    discovery / graph navigation
                    \                                /
                     +--------------+---------------+
                                    v
                         decisions / work selection
```

### Mutation law

A COS result may say “these records appear related”. It may **not** say “mutate application X”. A state-changing route requires exact `application_id` or exact `opportunity_id` mapping plus evidence allowed by the relevant adapter/domain contract.

Embeddings, title similarity, cosine neighbourhoods and semantic retrieval are candidate-generation tools only.

## COS + RuntimeGraph

Good uses:

- find likely relevant source documents for a known exact entity;
- navigate architecture/docs during cold start;
- discover related organisations/opportunities for later exact-ID verification;
- surface duplicate candidates for deterministic identity resolution;
- build non-authoritative contextual neighbourhoods for agent reasoning;
- reconstruct knowledge topology across public repo artifacts.

Forbidden uses:

- deciding that two applications are identical solely from vector similarity;
- marking a submission/receipt/eligibility gate from an embedding result;
- advancing Source_Cursors because semantic search found nothing;
- promoting youth-worker/trainer/profile claims from related text;
- using COS as a replacement for `Context_Registry`, `Agent_Event_Bus`, canonical CRM or provider evidence.

## CGEV2 + RuntimeGraph

RuntimeGraph is where canonical, explicit evidence becomes deterministic execution state.

```text
Source delta
→ explicit adapter contract
→ exact application/opportunity ID
→ NormalizedIngress
→ deterministic idempotency
→ affected subgraph
→ Claim/Frontier/Projection recompute
```

CGEV2 surrounds this with the control plane:

```text
NEW SESSION
→ BOOTSTRAP
→ BOUNDED HEALTH
→ WRITER AUTHORIZATION
→ RECEIPT
→ LEASE
→ BOUNDED RUNTIME WORK
→ READBACK
→ EVENTS
→ RELEASE
→ SESSION TERMINAL
→ CHECKPOINT/NEXT
```

## Current architectural learning

The healthiest split is:

- **CGEV2:** continuity + governance + audit + coordination.
- **COS:** semantic retrieval + graph topology.
- **RuntimeGraph:** exact-ID deterministic state/execution projection.
- **Provider/domain authority:** original truth.
- **RG2.3:** reversible action execution.
- **Human:** irreversible/sensitive decisions/actions.

The system becomes unsafe when one layer is allowed to impersonate another.

## Regression rule

Any future feature connecting COS to RuntimeGraph must include a negative test proving that fuzzy/semantic evidence alone cannot produce a state-changing mutation.
