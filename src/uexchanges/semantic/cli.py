from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from .benchmark import run_projection_benchmark
from .config import SemanticConfig
from .cos20 import Cos20Projector
from .graphify import CosGraphEngine
from .indexer import SemanticIndexer, _repo_identity
from .ollama import OllamaEmbedder, OllamaError
from .qdrant import QdrantError, QdrantRESTClient


def _json(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def _clients(config: SemanticConfig) -> tuple[OllamaEmbedder, QdrantRESTClient]:
    return (
        OllamaEmbedder(config.ollama_url, config.ollama_model),
        QdrantRESTClient(
            config.qdrant_url,
            config.qdrant_collection,
            api_key=config.qdrant_api_key,
        ),
    )


def command_doctor(args: argparse.Namespace) -> int:
    config = SemanticConfig.from_env(args.repo)
    ollama, qdrant = _clients(config)
    report: dict[str, object] = {"config": {
        "repo_root": str(config.repo_root),
        "ollama_url": config.ollama_url,
        "ollama_model": config.ollama_model,
        "qdrant_url": config.qdrant_url,
        "qdrant_collection": config.qdrant_collection,
        "semantic_vector": config.semantic_vector_name,
        "cos_vector": config.cos_vector_name,
        "cos_dimensions": config.cos_dimensions,
        "remote_allowed": config.allow_remote,
    }}
    ok = True
    try:
        report["ollama"] = ollama.doctor()
        ok = ok and bool(report["ollama"].get("model_present"))  # type: ignore[union-attr]
    except OllamaError as exc:
        report["ollama"] = {"reachable": False, "error": str(exc)}
        ok = False
    try:
        report["qdrant"] = qdrant.doctor()
    except QdrantError as exc:
        report["qdrant"] = {"reachable": False, "error": str(exc)}
        ok = False
    _json(report)
    return 0 if ok else 2


def command_index(args: argparse.Namespace) -> int:
    config = SemanticConfig.from_env(args.repo)
    report = SemanticIndexer(config).sync(recreate=args.recreate, clear_repo=not args.keep_existing)
    _json(report.to_dict())
    return 0


def command_search(args: argparse.Namespace) -> int:
    config = SemanticConfig.from_env(args.repo)
    ollama, qdrant = _clients(config)
    semantic = ollama.embed([args.query])[0]
    if args.space == "cos20":
        vector = Cos20Projector(seed=config.projection_seed).project(semantic)
        using = config.cos_vector_name
    else:
        vector = semantic
        using = config.semantic_vector_name
    repo_id, _ = _repo_identity(config.repo_root)
    filter_ = None if args.all_repos else {"must": [{"key": "repo", "match": {"value": repo_id}}]}
    hits = qdrant.query(vector, using=using, limit=args.limit, filter_=filter_)
    _json({"query": args.query, "space": args.space, "repo": None if args.all_repos else repo_id, "hits": hits})
    return 0


def command_graphify(args: argparse.Namespace) -> int:
    config = SemanticConfig.from_env(args.repo)
    repo_id, _ = _repo_identity(config.repo_root)
    graph = CosGraphEngine(config).build(
        repo_id=None if args.all_repos else repo_id,
        top_k=args.top_k,
        min_score=args.min_score,
        max_nodes=args.max_nodes,
        query_batch_size=args.query_batch,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(graph, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    _json({"output": str(output), "node_count": graph["node_count"], "edge_count": graph["edge_count"], "dimensions": 20})
    return 0


def command_benchmark(args: argparse.Namespace) -> int:
    report: dict[str, object] = {"projection": run_projection_benchmark(source_dimensions=args.source_dimensions, vectors=args.vectors).to_dict()}
    if args.live:
        config = SemanticConfig.from_env(args.repo)
        ollama, qdrant = _clients(config)
        samples = [
            "RuntimeGraph lease fencing and deterministic idempotency",
            "Erasmus opportunity evidence and Spain eligibility",
            "submission receipt authority and human frontier",
            "Qdrant semantic repository search",
        ]
        started = time.perf_counter()
        vectors = ollama.embed(samples)
        embed_seconds = max(time.perf_counter() - started, 1e-9)
        qdrant_info = qdrant.doctor()
        report["live"] = {
            "ollama_model": config.ollama_model,
            "embedding_dimensions": len(vectors[0]),
            "embedding_batch_seconds": round(embed_seconds, 6),
            "texts_per_second": round(len(samples) / embed_seconds, 3),
            "qdrant": qdrant_info,
            "note": "full index/query latency is reported by the index command and can be sampled after sync",
        }
    _json(report)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="uex-semantic", description="Local semantic retrieval + COS-20D graph projection")
    parser.add_argument("--repo", default=".", help="repository root")
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="verify loopback Ollama/Qdrant and model presence")
    doctor.set_defaults(func=command_doctor)

    index = sub.add_parser("index", help="vectorize all indexable Git-tracked repository text")
    index.add_argument("--recreate", action="store_true", help="recreate incompatible/rebuildable Qdrant collection")
    index.add_argument("--keep-existing", action="store_true", help="do not delete prior points for this repository")
    index.set_defaults(func=command_index)

    search = sub.add_parser("search", help="semantic repository search")
    search.add_argument("query")
    search.add_argument("--space", choices=("semantic", "cos20"), default="semantic")
    search.add_argument("--limit", type=int, default=8)
    search.add_argument("--all-repos", action="store_true")
    search.set_defaults(func=command_search)

    graph = sub.add_parser("graphify", help="materialize the COS-20D neighbour graph")
    graph.add_argument("--output", default="artifacts/semantic/cos20-graph.json")
    graph.add_argument("--top-k", type=int, default=6)
    graph.add_argument("--min-score", type=float, default=0.72)
    graph.add_argument("--max-nodes", type=int, default=5000)
    graph.add_argument("--query-batch", type=int, default=64)
    graph.add_argument("--all-repos", action="store_true")
    graph.set_defaults(func=command_graphify)

    bench = sub.add_parser("benchmark", help="benchmark the deterministic 20D projection; optionally probe live services")
    bench.add_argument("--source-dimensions", type=int, default=1024)
    bench.add_argument("--vectors", type=int, default=72)
    bench.add_argument("--live", action="store_true")
    bench.set_defaults(func=command_benchmark)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (ValueError, RuntimeError, OllamaError, QdrantError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _graph_alias_argv(argv: list[str]) -> list[str]:
    prefix: list[str] = []
    rest: list[str] = []
    index = 0
    while index < len(argv):
        if argv[index] == "--repo":
            if index + 1 >= len(argv):
                return ["--repo", "", "graphify"]
            prefix.extend([argv[index], argv[index + 1]])
            index += 2
            continue
        rest.append(argv[index])
        index += 1
    return [*prefix, "graphify", *rest]


def graphify_main() -> int:
    return main(_graph_alias_argv(sys.argv[1:]))


def cos_graph_main() -> int:
    return main(_graph_alias_argv(sys.argv[1:]))


if __name__ == "__main__":
    raise SystemExit(main())
