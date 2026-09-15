# UE-Xchanges-OS — Zero-Context Recovery Procedure

Semantic-durability seal: `2026-09-15`

Use this when a new agent starts with no trusted chat memory.

## 1. Establish current Git authority

Read current `main` first. Historical baselines in recovery docs are not assumed current.

Then read:

1. `../goal.md`
2. `../AGENTS.md`
3. `../MEMORY.md`
4. `bootstrap_manifest.json`
5. `../docs/SEMANTIC_BRAIN_DURABILITY.md`
6. `../LIVE-STATE-OVERRIDE.json`
7. `../STATE.md`
8. `../HANDOFF.md`
9. `../checkpoints/2026-09-15-semantic-brain-durability-seal.md`
10. this directory's current navigation files, ending with `NEXT.md`
11. current writer-authorization/bootstrap/runbook files required by the manifest and by the intended operation.

The semantic-brain durability contract is a mandatory bootstrap read. A cold agent must not regenerate embeddings simply because Qdrant/Ollama is absent.

## 2. Reconstruct private control plane

Read:

- `Context_Registry`;
- exact/new `Agent_Sessions`;
- currently **UNEXPIRED** `Work_Leases` only for live fencing;
- `Agent_Event_Bus` after the live watermark;
- RuntimeGraph `Command_Center`, `Human_Now`, `Agent_Next`, `Source_Cursors`, `Dead_Letters`.

Do not assume a historical seal watermark is the current tail. Read every later event.

## 3. Check derived-view freshness before using it

Compare RuntimeGraph/projection generated timestamps and watermarks against the current EventBus/source evidence.

A projection can exist and still be stale. If stale, use it only as navigation and rebuild/reconcile it through the correct exact-ID authority path. Never patch canonical truth to make it agree with a stale projection.

The 2026-09-15 semantic-durability audit observed RuntimeGraph watermark `EVT-20260907T193100-DSP2-A189-005` while the canonical EventBus had materially later events; therefore the current domain/frontier must be reconstructed fresh before acting.

## 4. Restore the semantic brain when needed

Follow `docs/SEMANTIC_BRAIN_DURABILITY.md`:

1. resolve latest semantic recovery pointers from the checkpoint/EventBus/Rot.Knowledge;
2. verify package/snapshot SHA256;
3. verify model identity + expected **1024D** width, Qdrant version and COS dimensions;
4. restore the validated historical collection/vector/graph state in an isolated runtime;
5. apply only explicit incremental deltas after the baseline;
6. run point/path/dimension/finite-vector/graph checks;
7. run the adversarial brain gauntlet;
8. compare artifact source SHA with current `main`;
9. mark stale partitions `HISTORICAL_ONLY`;
10. add a separate current-code/fresh-evidence overlay rather than rewriting history;
11. keep every semantic result `mutation_authority=false`.

Known recovery assurance records a private external backup for snapshot/vector/graph/manifest/log state, but not all exact model/runtime binaries. Treat local `/mnt/data` blobs as acceleration only until a later air-gapped replication checkpoint proves otherwise.

## 5. Reconstruct domain state fresh

Do not assert current opportunities, applications, Human Frontier, receipts, deadlines or source cursors from old semantic or RuntimeGraph snapshots.

Read canonical Drive and fresh provider evidence before any domain/frontier claim.

Semantic retrieval may identify which exact records/files to inspect; it never supplies mutation authority.

## 6. Normal writer authorization

Use the current versioned WriterAuthorization architecture:

```text
exact new current session rows
+ exact BootstrapGuard evidence
+ currently-unexpired leases
+ exact live lease owners/bootstrap evidence
→ bounded writer health
→ WriterAuthorization
→ canonical receipt
→ immediate exact lease acquisition
```

`historical_hygiene_evaluated=false` means exactly that. Do not pretend it is a global-green report.

## 7. Execute RG2.2 only within its current runbook

For scheduled canary/initial production when still applicable:

- one adapter slice;
- <=5 new/late-unique candidates;
- <=2 exact application/opportunity subgraphs;
- no second adapter in the same activation;
- preserve continuation boundary;
- never advance cursor beyond unprocessed evidence.

Exact-ID explicit adapter facts only.

## 8. Preserve authority boundaries

- Gmail cannot directly become receipt.
- COS/fuzzy/title/embedding similarity cannot authorise mutation.
- RuntimeGraph cannot self-heal canonical domain state.
- RG2.2 cannot execute Agent_Next.
- Todoist mutation requires exact persisted binding.
- payments/auth/credentials/OTP/cookies/external PREFILL/Submit remain outside generic execution.
- a running semantic daemon is not durable state.
- a stopped semantic daemon is not evidence the brain is lost.

## 9. Closure is mandatory

Reserve activation budget for:

- exact read-back;
- release all own leases by stable ID;
- verify `RELEASED`;
- close session terminally;
- emit terminal event evidence;
- persist changed STATE/HANDOFF/NEXT/checkpoint only when state materially changed;
- persist semantic restore/benchmark artifacts outside the ephemeral runtime before claiming death-safe completion.

## 10. Promotion sequence

Operational RuntimeGraph promotion remains governed by current live state/runbooks rather than this historical sequence. For semantic durability, the next independent hardening gates are:

```text
validated external snapshot/vector restore
→ exact model/runtime blob replication to durable store
→ destructive cold-sandbox restore drill
→ raw >=50-query bilingual gold-set persistence
→ dense/instruction/hybrid reproducible benchmark
→ changed-file incremental index contract
→ current-main freshness overlay
→ optional always-on Qdrant service (never sole persistence)
```

## 11. End every session durably

Before exit, persist exact main SHA, private watermark, own session/lease lifecycle, tests/read-backs, blockers, next transition and handoff. Chat text and sandbox process state are never the sole continuity layer.
