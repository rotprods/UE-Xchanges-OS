from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .runtime_graph import RuntimeGraph, compile_mass_apply_rows


def _read_json(path: str) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str, payload: object) -> None:
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def compile_command(rows_path: str, output_path: str, source_revision: str) -> int:
    rows = _read_json(rows_path)
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("rows JSON must be a list of objects")
    graph = compile_mass_apply_rows(rows)
    snapshot = graph.to_snapshot(
        generated_at=datetime.now(timezone.utc),
        source_revision=source_revision,
    )
    _write_json(output_path, snapshot)
    return 0


def recover_command(snapshot_path: str) -> int:
    snapshot = _read_json(snapshot_path)
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot JSON must be an object")
    graph = RuntimeGraph.from_snapshot(snapshot)
    now = datetime.now(timezone.utc)
    graph.recompute(now)
    print(
        json.dumps(
            {
                "actions": len(graph.actions),
                "gates": len(graph.gates),
                "human_frontier": len(graph.human_frontier(now)),
                "agent_frontier": len(graph.agent_frontier(now)),
                "system_frontier": len(graph.system_frontier(now)),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="UE-Xchanges RuntimeGraph v1")
    sub = parser.add_subparsers(dest="command", required=True)

    compile_parser = sub.add_parser("compile")
    compile_parser.add_argument("rows_json")
    compile_parser.add_argument("snapshot_json")
    compile_parser.add_argument("--source-revision", required=True)

    recover_parser = sub.add_parser("recover")
    recover_parser.add_argument("snapshot_json")

    args = parser.parse_args()
    if args.command == "compile":
        return compile_command(args.rows_json, args.snapshot_json, args.source_revision)
    return recover_command(args.snapshot_json)


if __name__ == "__main__":
    raise SystemExit(main())
