# UE-Xchanges-OS — Semantic Brain Durability Seal

Checkpoint: `2026-09-15`  
Context: `CTX-UEX-GLOBAL-EXPANSION-INCOME-V1`  
Baseline main before this wave: `c5fd939617cb28f8af90d5ac39907564804ee925`  
Writer session: `SES-UEX-CHATGPT-20260915T110528-SEM01`  
Writer agent: `AGT-SEMANTIC-BRAIN-DURABILITY-SEALER`

## Purpose

Make the semantic/vector brain death-safe and discoverable by every compliant cold-start agent, rather than leaving it as hidden chat/sandbox knowledge.

This checkpoint is public/sanitised. Private correspondence, applicant data and live-evidence overlays remain outside public GitHub.

## Finding that triggered the seal

The semantic collection was not a forever-running service. On 2026-09-15 no Qdrant/Ollama daemon was relied on as persistent state. The durable value lived in reconstruction artifacts and recovery evidence.

The previous architecture had already externalised substantial state, but the mandatory UE-Xchanges bootstrap did **not** yet require a cold agent to read a semantic-brain restore contract. A new agent could therefore waste work by re-embedding/rebuilding after sandbox death.

This wave closes that discovery gap.

## Durable semantic state already proven

Recovery assurance in Rot.Knowledge records:

- historical source commit: `5bd92696e3b9d04be9eda0c2a6e5dcb929235870`;
- model: `qwen3-embedding:0.6b`;
- native width: `1024D`;
- model blob SHA256: `06507c7b42688469c4e7298b0a1e16deff06caf291cf0a5b278c308249c3e439`;
- Qdrant: `v1.19.0`;
- points: `676`;
- paths/files: `397`;
- graph nodes/edges: `676 / 2729`;
- COS dimensions: `20`;
- restart persistence: `PASS`;
- isolated snapshot restore: `PASS`;
- snapshot guard tests: `12` passing;
- byte-exact recovered source validation: `PASS`;
- external recovery backup SHA256: `60aa24625d3e1da981c71f67520d580544846a8cc2666c3900847178a7b54ed5`;
- snapshot SHA256: `2c52722941a7a23abec205103db11f27b5affd0ae47f912d8e962159128aa388`.

Current private federated-brain v2 package:

- SHA256: `7fe7ff75db16a089fce5645d22d91343540561c837fb2e5c1a6caafeb988e2f5`;
- private Drive pointer recorded in canonical EventBus/session evidence;
- live/private evidence is intentionally not copied into this checkpoint.

## Durability boundary

What is durable now:

- validated vector/snapshot/graph/manifest recovery state;
- content hashes and model identity;
- public Rot.Knowledge recovery assurance + snapshot guard;
- private federated-brain package;
- versioned UE-Xchanges restore contract;
- bootstrap-required discovery;
- EventBus/session/lease provenance.

What is **not yet** fully air-gapped:

- the 2026-09-07 recovery assurance explicitly records `weights_and_runtime_binaries_in_backup=false`;
- exact model/runtime blobs may still need upstream re-fetch or current local caches;
- therefore `FOREVER`, `AIR_GAPPED_RESTORE_COMPLETE` and `BIT_EXACT_RUNTIME_REPLICATION` are not claimed.

## Architecture law promoted by this wave

```text
service liveness != persistence
service death != brain loss
restore validated artifacts before regeneration
historical semantic source != current source
semantic retrieval != mutation authority
projection existence != projection freshness
```

`docs/SEMANTIC_BRAIN_DURABILITY.md` is now the canonical public restore/authority contract.

`agent_context/bootstrap_manifest.json` now requires every compliant cold-start writer to read it.

`MEMORY.md` now stores the slow-changing semantic-brain invariants.

`agent_context/README.md`, `knowledge.md` and `recovery.md` route zero-context agents through the restore-before-regenerate flow.

## Retrieval evidence

The later strict bilingual exact-path benchmark superseded the optimistic interpretation of the first small probe set:

- dense 1024D Recall@5: about `0.60`;
- dense 1024D Recall@10: about `0.64`;
- COS-20D Recall@5: about `0.26`;
- COS-20D Recall@10: about `0.42`;
- instruction-aware Qwen query encoding: about `0.70` Recall@10;
- local dense + lexical/BM25 fusion: about `0.74` Recall@10, MRR about `0.464`.

These metrics justify:

- native semantic retrieval remaining primary;
- COS-20D remaining topology only;
- a separate hybrid `repository_navigation` candidate surface;
- promotion of the raw >=50-query gold set as a future reproducible benchmark gate.

Aggregate metrics are recorded here as wave evidence; raw gold fixtures still require explicit durable promotion before becoming a release criterion.

## Safety bugs found by brain testing

The federated-brain gauntlet found and corrected:

1. vague temporal query preferring an older semantically close item;
2. authority sort allowing an authoritative but irrelevant item to hijack a query;
3. display limits hiding a lower-ranked authoritative reply behind a semantically close draft;
4. unsent draft text ranking strongly without being allowed to become external evidence;
5. prompt-injection text inside retrieved content;
6. incorrect embedding dimension acceptance.

Safe decision policy:

```text
semantic candidate generation
→ topical/entity relevance gate
→ authority/freshness within the same topic
→ preserve raw semantic result for transparency
→ mutation_authority=false
```

## Freshness finding outside the brain

On 2026-09-15 RuntimeGraph still exposed generated state from `2026-09-07T19:32:00+02:00` with watermark `EVT-20260907T193100-DSP2-A189-005`, while the canonical EventBus had materially later events. This proves the durable rule: **projection available does not mean projection fresh**.

This documentation wave does not repair RuntimeGraph/domain state; that requires a separate exact-ID authority/fence.

## Writer protocol for this seal

- `SESSION_STARTED`: `EVT-20260915T110528-SEMDUR-001`;
- `BOOTSTRAP_CONTEXT_LOADED`: `EVT-20260915T110837-SEMDUR-002`;
- writer lifecycle activation heartbeat: `EVT-20260915T111042-SEMDUR-003`;
- WriterAuthorizationReceipt: `WAZ-715b9f3b565060ba34641b90`;
- authorization event: `EVT-20260915T111525-SEMDUR-004`;
- exact VERSIONED_CODE lease: `LSE-UEX-SEMANTIC-BRAIN-DURABILITY-20260915T111526-SEM01`;
- lease event: `EVT-20260915T111526-SEMDUR-005`;
- exact lease read-back: `ACTIVE` before versioned writes;
- bounded health scope: `CURRENT_WRITER_AND_UNEXPIRED_LEASES`;
- historical hygiene evaluated: `false`;
- domain authority: `false`;
- external capability: `false`.

No canonical opportunity/application state, payment, booking, form submission, provider authentication or RuntimeGraph projection is changed by this wave.

## Why this work survives where sandbox-only agents fail

The difference is the operating method:

- externalise state before chat death;
- content-address artifacts;
- pin model/runtime identity;
- shard expensive vector outputs;
- persist incremental deltas;
- keep public contracts and private evidence separate;
- test destructive restore, not only happy-path query;
- make recovery files machine-discoverable through bootstrap;
- record sessions/leases/events/read-backs;
- distinguish authority from derived retrieval;
- distinguish freshness from mere existence;
- never use chat as the only continuity system.

## Next hardening frontier

1. replicate exact model/runtime blobs to a second durable external store and checksum them;
2. perform a destructive cold-sandbox restore with **no reliance on pre-existing `/mnt/data`**;
3. persist the raw bilingual >=50-query gold set + deterministic benchmark runner;
4. implement/document hybrid dense+lexical `repository_navigation` as a separate derived surface;
5. formalise changed-file incremental indexing and stale-point deletion;
6. add a semantic-artifact registry with latest/baseline/delta pointers and hashes;
7. independently reconcile stale RuntimeGraph/control-plane projections under their own exact leases;
8. optional always-on Qdrant deployment only after reconstructibility remains the primary durability mechanism.

## Handoff rule

A successor must be able to continue from GitHub + Drive/Rot.Knowledge + EventBus without this chat. If any later source contradicts this checkpoint, the later authoritative source wins; the contradiction is preserved rather than silently rewritten.
