from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_ALLOWED_FRESHNESS = {"HISTORICAL_ONLY", "CURRENT_EXACT_SOURCE", "STALE", "SUPERSEDED"}
_ALLOWED_RESTORE = {"UNVERIFIED", "RESTORE_PASS", "AIR_GAPPED_RESTORE_PASS", "FAILED"}
_DERIVED_AUTHORITY = "DERIVED_RECONSTRUCTIBLE_ONLY"


class ArtifactRegistryError(ValueError):
    pass


def _sha256(value: str, field_name: str) -> None:
    if not _SHA256_RE.fullmatch(value):
        raise ArtifactRegistryError(f"{field_name} must be a lowercase sha256 hex digest")


@dataclass(frozen=True, slots=True)
class SemanticArtifactRecord:
    artifact_id: str
    source_repo: str
    source_sha: str
    created_at: str
    model: str
    model_sha256: str
    embedding_dimensions: int
    chunk_contract: str
    points: int
    paths: int
    snapshot_sha256: str
    vectors_sha256: str
    graph_sha256: str
    baseline_id: str
    delta_parent: str | None
    freshness: str
    authority: str
    benchmark_ref: str | None
    backup_locations: tuple[str, ...]
    restore_status: str
    cos_dimensions: int = 20
    mutation_authority: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self, *, observed_main_sha: str | None = None) -> None:
        if not self.artifact_id or not self.source_repo or not self.model or not self.chunk_contract:
            raise ArtifactRegistryError("identity/model/chunk fields cannot be blank")
        if not _GIT_SHA_RE.fullmatch(self.source_sha):
            raise ArtifactRegistryError("source_sha must be a 40-char git sha")
        for name in ("model_sha256", "snapshot_sha256", "vectors_sha256", "graph_sha256"):
            _sha256(getattr(self, name), name)
        if self.embedding_dimensions != 1024:
            raise ArtifactRegistryError("UEX semantic embedding contract is 1024D")
        if self.cos_dimensions != 20:
            raise ArtifactRegistryError("COS topology contract is 20D")
        if self.points < 1 or self.paths < 1 or self.paths > self.points:
            raise ArtifactRegistryError("invalid point/path counts")
        if self.freshness not in _ALLOWED_FRESHNESS:
            raise ArtifactRegistryError(f"unsupported freshness {self.freshness!r}")
        if self.restore_status not in _ALLOWED_RESTORE:
            raise ArtifactRegistryError(f"unsupported restore_status {self.restore_status!r}")
        if self.authority != _DERIVED_AUTHORITY or self.mutation_authority:
            raise ArtifactRegistryError("semantic artifacts must remain non-mutating derived state")
        if not self.backup_locations:
            raise ArtifactRegistryError("at least one durable backup location is required")
        if self.freshness == "CURRENT_EXACT_SOURCE":
            if observed_main_sha is None:
                raise ArtifactRegistryError("CURRENT_EXACT_SOURCE requires observed_main_sha")
            if self.source_sha != observed_main_sha:
                raise ArtifactRegistryError("CURRENT_EXACT_SOURCE source_sha does not match main")


@dataclass(slots=True)
class SemanticArtifactRegistry:
    schema_version: str = "1.0.0"
    baseline_id: str | None = None
    current_id: str | None = None
    artifacts: dict[str, SemanticArtifactRecord] = field(default_factory=dict)

    def add(self, record: SemanticArtifactRecord, *, observed_main_sha: str | None = None) -> None:
        record.validate(observed_main_sha=observed_main_sha if record.freshness == "CURRENT_EXACT_SOURCE" else None)
        if record.artifact_id in self.artifacts:
            raise ArtifactRegistryError(f"duplicate artifact_id {record.artifact_id}")
        if record.delta_parent is not None and record.delta_parent not in self.artifacts:
            raise ArtifactRegistryError("delta_parent must already exist")
        if record.baseline_id != record.artifact_id and record.baseline_id not in self.artifacts:
            raise ArtifactRegistryError("baseline_id must reference self or an existing artifact")
        self.artifacts[record.artifact_id] = record
        if record.artifact_id == record.baseline_id and self.baseline_id is None:
            self.baseline_id = record.artifact_id
        self._validate_graph()

    def set_current(self, artifact_id: str, *, observed_main_sha: str) -> None:
        record = self.artifacts.get(artifact_id)
        if record is None:
            raise ArtifactRegistryError("unknown current artifact")
        record.validate(observed_main_sha=observed_main_sha if record.freshness == "CURRENT_EXACT_SOURCE" else None)
        if record.freshness != "CURRENT_EXACT_SOURCE":
            raise ArtifactRegistryError("current pointer requires CURRENT_EXACT_SOURCE freshness")
        self.current_id = artifact_id

    def _validate_graph(self) -> None:
        for artifact_id in self.artifacts:
            seen: set[str] = set()
            cursor: str | None = artifact_id
            while cursor is not None:
                if cursor in seen:
                    raise ArtifactRegistryError("delta lineage cycle detected")
                seen.add(cursor)
                record = self.artifacts.get(cursor)
                if record is None:
                    raise ArtifactRegistryError("broken delta lineage")
                cursor = record.delta_parent

    def validate(self, *, observed_main_sha: str | None = None) -> None:
        self._validate_graph()
        for record in self.artifacts.values():
            record.validate(
                observed_main_sha=observed_main_sha
                if record.freshness == "CURRENT_EXACT_SOURCE"
                else None
            )
        if self.baseline_id is not None and self.baseline_id not in self.artifacts:
            raise ArtifactRegistryError("unknown baseline pointer")
        if self.current_id is not None:
            if observed_main_sha is None:
                raise ArtifactRegistryError("registry current pointer validation requires main sha")
            current = self.artifacts.get(self.current_id)
            if current is None:
                raise ArtifactRegistryError("unknown current pointer")
            current.validate(observed_main_sha=observed_main_sha)
            if current.freshness != "CURRENT_EXACT_SOURCE":
                raise ArtifactRegistryError("current pointer is not current-exact")

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "authority": _DERIVED_AUTHORITY,
            "mutation_authority": False,
            "baseline_id": self.baseline_id,
            "current_id": self.current_id,
            "artifacts": [asdict(self.artifacts[key]) for key in sorted(self.artifacts)],
        }

    def digest(self) -> str:
        payload = json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(payload).hexdigest()

    def dump(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    @classmethod
    def load(
        cls, path: str | Path, *, observed_main_sha: str | None = None
    ) -> "SemanticArtifactRegistry":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("authority") != _DERIVED_AUTHORITY or data.get("mutation_authority") is not False:
            raise ArtifactRegistryError("registry authority boundary violated")
        registry = cls(
            schema_version=str(data.get("schema_version", "")),
            baseline_id=data.get("baseline_id"),
            current_id=data.get("current_id"),
        )
        records: dict[str, SemanticArtifactRecord] = {}
        for raw in data.get("artifacts", []):
            raw = dict(raw)
            raw["backup_locations"] = tuple(raw.get("backup_locations", ()))
            record = SemanticArtifactRecord(**raw)
            record.validate(
                observed_main_sha=observed_main_sha
                if record.freshness == "CURRENT_EXACT_SOURCE"
                else None
            )
            if record.artifact_id in records:
                raise ArtifactRegistryError(f"duplicate artifact_id {record.artifact_id}")
            records[record.artifact_id] = record
        registry.artifacts = records
        registry._validate_graph()
        for record in records.values():
            if record.baseline_id not in records:
                raise ArtifactRegistryError("broken baseline reference")
        if registry.baseline_id is not None and registry.baseline_id not in records:
            raise ArtifactRegistryError("unknown baseline pointer")
        if registry.current_id is not None:
            if observed_main_sha is None:
                raise ArtifactRegistryError("current registry load requires observed_main_sha")
            registry.set_current(registry.current_id, observed_main_sha=observed_main_sha)
        return registry
