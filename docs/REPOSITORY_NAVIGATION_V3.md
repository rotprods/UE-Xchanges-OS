# Repository navigation V3 — truthful, offline qualification

Status: CANDIDATE_ONLY. No production promotion or current-main index is claimed.

The public RETR02 candidate at 8f6bded9b62b82086418ce9d8bdea34f13c4fcc8 contains 60 newly authored Gold V2 queries (30 paired EN/ES intents). They are not the lost historical gold fixture and are not 60 independent topics. Their questions and expected paths are unchanged here.

## Reproduced defects and repair

1. Published shards 03/04 had byte hashes different from their manifest. The donor exact-file test run had 21 passing tests and one checksum error. The two manifest hashes now name the actual unchanged published bytes; checksum enforcement remains active.
2. The original surface called hybrid protected the first ten dense paths in their original order. Its top-10 was therefore identical to dense in all 60 queries. It cannot establish hybrid improvement. The best existing default is retained as `dense_protected`; true RRF is explicitly `strategy="hybrid_rrf"`, experimental only.
3. The benchmark now gates the true RRF result, never the protected dense surrogate. The original numeric thresholds are unchanged: minimum Recall@10 .70, MRR@10 .40, nDCG@10 .40, and maximum regression against dense .02. Invalid metric ranges and mismatched query counts fail closed.
4. The replay runner uses checksummed real query vectors; it makes no network/model calls. A corpus manifest binds the two allowed historical embedding source commits rather than relabelling every chunk as newly embedded at the snapshot source commit.

## Measured decision

On 60 frozen queries and 676 historical chunks / 397 paths, instructed dense Recall@10 is 56/60 = .933333; true RRF is 51/60 = .85. The -8.33 percentage-point regression fails the existing 2-point allowance. Dense MRR@10 is .617956; RRF MRR@10 is .400681. No tuning, relabelling, or threshold weakening was used to manufacture a pass.

The legacy `recall_at_k` metric is query-level hit rate; all frozen queries have one expected path so it equals recall here. The legacy `mrr` field is explicitly truncated at rank 10. Per-query raw rankings are retained in the private replay package. Independent holdout validation is still required before recommending a new retrieval strategy.

## Offline replay

Retrieve the RETR03 recovery package through private EventBus / Mission Control. Verify its SHA-256 and every RELEASE_MANIFEST entry, then use its `source/` directory:

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python scripts/run_repository_navigation_benchmark.py \
  --gold-manifest benchmarks/semantic/repository_navigation_gold_v2.manifest.json \
  --vectors ../inputs/recovered-vectors.jsonl \
  --corpus-manifest ../inputs/snapshot-manifest.json \
  --expected-corpus-manifest-sha256 148a4ac7e17f47acb4a8884c856798d951df36aed78cee26ca78b842b6ebcfc9 \
  --query-cache ../evidence/query-embeddings.json \
  --expected-query-cache-sha256 b14adfc612a0dfdb98b572d6a0ee4523cf066db91377ef706f771d835843dc48 \
  --source-sha 5bd92696e3b9d04be9eda0c2a6e5dcb929235870 \
  --output /tmp/uex-replay.json
```

Expected replay exit status is **2**: benchmark executed, hybrid promotion failed. Exit 3 means invalid input or runtime failure, not a measured regression. Exit 0 alone never certifies repository integration, eligibility, application receipt, or payment. The new runner intentionally removes implicit live-service calls from qualification; live inference capture is a separate evidenced preparation.

`semantic-artifacts/registry.json` records the historical baseline with `current_id=null`. It is not an incremental current-main release. Offline replay proves ranking reproducibility of saved real model outputs, not bit-exact new inference on another CPU or OS-enforced air-gap isolation.

## Remaining boundary

Focused local Python 3.13 tests are not a complete checkout qualification on the supported 3.11/3.12 matrix. No Actions/CI was activated, no PR opened and no merge authorized in this wave. Full repository integration needs an authorized capable checkout/runner. Keep the hybrid production gate blocked regardless of infrastructure availability until a separately designed and independently evaluated repair beats the unchanged gate.
