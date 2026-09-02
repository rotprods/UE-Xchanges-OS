#!/usr/bin/env bash
set -euo pipefail

repo="${1:-.}"
cd "$repo"

command -v ollama >/dev/null || { echo "ollama is required" >&2; exit 2; }
command -v docker >/dev/null || { echo "docker is required for local Qdrant" >&2; exit 2; }

ollama pull "${OLLAMA_EMBED_MODEL:-qwen3-embedding:0.6b}"
docker compose -f compose.semantic.yml up -d
python -m pip install -e .
uex-semantic --repo . doctor
uex-semantic --repo . index
uex-semantic --repo . benchmark --live
cos-graph-engine --repo . --output artifacts/semantic/cos20-graph.json
