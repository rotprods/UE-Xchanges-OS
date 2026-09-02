# UE-Xchanges-OS — Local Semantic Graph Engine

## Contract

This layer is a **reconstructible projection** of the public/versioned repository. It never becomes a second source of opportunity, application, receipt, eligibility or RuntimeGraph truth.

Pipeline:

```text
Git-tracked repository text
  → deterministic safety scan + line-aware chunks
  → Ollama `/api/embed`
  → Qdrant collection `uexchanges_repo_semantic`
       ├─ named vector `semantic` (native model dimension; default Qwen3 0.6B = 1024D)
       └─ named vector `cos20` (deterministic signed-hash 20D projection)
  → semantic search (native vector)
  → COS-GRAPH-ENGINE (20D neighbour topology)
  → reconstructible JSON graph artifact
```

`semantic` is the retrieval vector. `cos20` is a compact topology/graph vector only. A 20D projection is deliberately **not** allowed to replace native semantic retrieval because dimensionality reduction at that scale can reorder nearest neighbours.

## Privacy / authority invariants

- Ollama and Qdrant default to loopback only. Non-loopback endpoints fail closed unless `SEMANTIC_ALLOW_REMOTE=1` is explicitly set.
- Indexing starts from `git ls-files`, not arbitrary home-directory files.
- Known secret/private paths, key/certificate formats, `.env*` runtime files (while retaining `.env.example`), `private/`, `applications/`, `data/` and `profile/private.json` are excluded even if accidentally present.
- Binary media is not embedded. Tracked PDFs are extracted only when the existing `pypdf` optional dependency is installed; otherwise they are reported as skipped.
- Qdrant payload contains public repository chunk text and provenance only. Do not point this indexer at private Drive exports or applicant-private working directories.
- The Qdrant collection and graph artifact are projections; deleting and rebuilding them must not lose canonical state.

## Local bootstrap

Prerequisites: Ollama, Docker with Compose, Python 3.11+. The Compose file pins Qdrant `v1.19.0` (current stable release observed on 2026-09-02) rather than a mutable `latest` tag.

```bash
ollama pull qwen3-embedding:0.6b
docker compose -f compose.semantic.yml up -d
python -m pip install -e .
uex-semantic --repo . doctor
uex-semantic --repo . index
uex-semantic --repo . search "RuntimeGraph lease fencing and idempotency"
cos-graph-engine --repo . --output artifacts/semantic/cos20-graph.json
uex-semantic --repo . benchmark --live --iterations 12
```

One-command equivalent:

```bash
./scripts/semantic_bootstrap.sh .
```

## Commands

`uex-semantic doctor` checks loopback connectivity and verifies that the configured Ollama model is installed.

`uex-semantic index` scans all indexable Git-tracked repository text, embeds it in batches, creates/validates named Qdrant vector spaces, upserts the complete new build first, and only then deletes stale points from the previous build. A failed embedding run therefore does not intentionally erase the last complete snapshot.

`uex-semantic search "..."` uses native semantic embeddings. Add `--space cos20` only to inspect the compact projection.

`graphify` and `cos-graph-engine` are aliases for materialising the 20D neighbour graph from Qdrant. Graph construction uses Qdrant's batch query endpoint rather than one network request per node.

`uex-semantic benchmark` runs a deterministic offline projection benchmark. `--live` additionally warms the local services and measures real Ollama embedding latency plus native-semantic and COS-20D Qdrant query latency with mean/p50/p95/min/max, throughput-at-mean and top-5 native↔COS overlap. `--iterations N` controls the live sample count (default 8, minimum 3).

## Environment

```dotenv
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_EMBED_MODEL=qwen3-embedding:0.6b
QDRANT_URL=http://127.0.0.1:6333
QDRANT_COLLECTION=uexchanges_repo_semantic
QDRANT_API_KEY=
SEMANTIC_VECTOR_NAME=semantic
COS_VECTOR_NAME=cos20
COS_DIMENSIONS=20
COS_PROJECTION_SEED=uexchanges-cos20-v1
SEMANTIC_CHUNK_CHARS=3600
SEMANTIC_CHUNK_OVERLAP_CHARS=420
SEMANTIC_EMBED_BATCH=16
SEMANTIC_UPSERT_BATCH=64
SEMANTIC_MAX_FILE_BYTES=2000000
SEMANTIC_ALLOW_REMOTE=0
SEMANTIC_BENCH_ITERATIONS=12  # bootstrap-script live benchmark sample count
```

## Qdrant collection contract

Default model contract:

```json
{
  "vectors": {
    "semantic": {"size": 1024, "distance": "Cosine"},
    "cos20": {"size": 20, "distance": "Cosine"}
  },
  "on_disk_payload": true
}
```

The indexer infers the actual native embedding width from Ollama and refuses an incompatible existing collection unless `--recreate` is explicitly requested. This prevents silent mixed-model corruption.

## Benchmark interpretation

The offline benchmark measures deterministic projection throughput, cosine mean absolute error, cosine correlation and recall@5 on clustered synthetic 1024D vectors. It is a regression guard for the COS projection implementation, **not proof of semantic relevance for the repository**.

Production acceptance requires a local live run after indexing:

```bash
uex-semantic --repo . benchmark --live --iterations 12
uex-semantic --repo . search "evidence hierarchy and submission receipt"
uex-semantic --repo . search "multi-agent lease fencing"
uex-semantic --repo . search "RuntimeGraph dead letter source cursor"
```

For retrieval quality, judge the native `semantic` space. The live `semantic_cos20_overlap_at_5` metric is diagnostic only—not relevance ground truth. COS-20D quality is topological; lower recall/overlap there does not justify replacing native retrieval or changing domain truth. Inspect `probe_hits` to see the top repository paths returned by both spaces for canonical architecture/evidence queries.
