"""Content-addressed recovery manifest for UE-Xchanges-OS.

The manifest is a value-safe inventory of public recovery artifacts and private
control-plane availability.  It contains no applicant values, credentials or
provider secrets and never substitutes for the underlying authorities.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Mapping

_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _aware(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value


def sha256_text(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("text must be str")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RecoveryArtifactDigest:
    path: str
    sha256: str
    role: str
    required: bool = True

    def __post_init__(self) -> None:
        if not self.path or self.path.startswith("/") or ".." in self.path.split("/"):
            raise ValueError("artifact path must be a relative repository path")
        if not _SHA256.fullmatch(self.sha256):
            raise ValueError("artifact sha256 must be lowercase 64-char hex")
        if not self.role:
            raise ValueError("artifact role is required")

    def as_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "role": self.role,
            "required": self.required,
        }


@dataclass(frozen=True)
class PrivateRecoverySource:
    name: str
    available: bool
    watermark: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("private source name is required")
        if any(token in self.name.lower() for token in ("password", "cookie", "token", "secret")):
            raise ValueError("private source names cannot encode secret material")
        if "\n" in self.watermark or "\r" in self.watermark:
            raise ValueError("watermark must be single-line")

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "available": self.available,
            "watermark": self.watermark,
        }


@dataclass(frozen=True)
class RecoveryManifest:
    generated_at: datetime
    current_main_sha: str
    event_watermark: str
    bootstrap_manifest_version: str
    command_center_ref: str
    command_center_watermark: str
    public_artifacts: tuple[RecoveryArtifactDigest, ...]
    private_sources: tuple[PrivateRecoverySource, ...]
    bundle_hash: str

    def __post_init__(self) -> None:
        _aware(self.generated_at, "generated_at")
        if not _SHA40.fullmatch(self.current_main_sha):
            raise ValueError("current_main_sha must be lowercase 40-char hex")
        if not self.event_watermark:
            raise ValueError("event_watermark is required")
        if not self.bootstrap_manifest_version:
            raise ValueError("bootstrap_manifest_version is required")
        if not self.command_center_ref or not self.command_center_watermark:
            raise ValueError("command center ref/watermark are required")
        paths = [item.path for item in self.public_artifacts]
        if len(paths) != len(set(paths)):
            raise ValueError("public artifact paths must be unique")
        names = [item.name for item in self.private_sources]
        if len(names) != len(set(names)):
            raise ValueError("private source names must be unique")
        if not _SHA256.fullmatch(self.bundle_hash):
            raise ValueError("bundle_hash must be lowercase 64-char hex")
        if self.bundle_hash != compute_bundle_hash(
            current_main_sha=self.current_main_sha,
            event_watermark=self.event_watermark,
            bootstrap_manifest_version=self.bootstrap_manifest_version,
            command_center_ref=self.command_center_ref,
            command_center_watermark=self.command_center_watermark,
            public_artifacts=self.public_artifacts,
            private_sources=self.private_sources,
        ):
            raise ValueError("bundle_hash does not match manifest content")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "UEX_RECOVERY_MANIFEST",
            "version": "1.0.0",
            "generated_at": self.generated_at.isoformat(),
            "current_main_sha": self.current_main_sha,
            "event_watermark": self.event_watermark,
            "bootstrap_manifest_version": self.bootstrap_manifest_version,
            "command_center_ref": self.command_center_ref,
            "command_center_watermark": self.command_center_watermark,
            "public_artifacts": [item.as_dict() for item in self.public_artifacts],
            "private_sources": [item.as_dict() for item in self.private_sources],
            "bundle_hash": self.bundle_hash,
            "authority": "INVENTORY_ONLY_NOT_DOMAIN_AUTHORITY",
        }


def _identity_payload(
    *,
    current_main_sha: str,
    event_watermark: str,
    bootstrap_manifest_version: str,
    command_center_ref: str,
    command_center_watermark: str,
    public_artifacts: Iterable[RecoveryArtifactDigest],
    private_sources: Iterable[PrivateRecoverySource],
) -> dict[str, object]:
    artifacts = tuple(sorted(public_artifacts, key=lambda item: item.path))
    sources = tuple(sorted(private_sources, key=lambda item: item.name))
    return {
        "contract": "UEX_RECOVERY_MANIFEST",
        "version": "1.0.0",
        "current_main_sha": current_main_sha,
        "event_watermark": event_watermark,
        "bootstrap_manifest_version": bootstrap_manifest_version,
        "command_center_ref": command_center_ref,
        "command_center_watermark": command_center_watermark,
        "public_artifacts": [item.as_dict() for item in artifacts],
        "private_sources": [item.as_dict() for item in sources],
    }


def compute_bundle_hash(**kwargs: object) -> str:
    payload = _identity_payload(**kwargs)  # type: ignore[arg-type]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_recovery_manifest(
    *,
    generated_at: datetime,
    current_main_sha: str,
    event_watermark: str,
    bootstrap_manifest_version: str,
    command_center_ref: str,
    command_center_watermark: str,
    public_artifacts: Iterable[RecoveryArtifactDigest],
    private_sources: Iterable[PrivateRecoverySource],
) -> RecoveryManifest:
    _aware(generated_at, "generated_at")
    artifacts = tuple(sorted(public_artifacts, key=lambda item: item.path))
    sources = tuple(sorted(private_sources, key=lambda item: item.name))
    bundle_hash = compute_bundle_hash(
        current_main_sha=current_main_sha,
        event_watermark=event_watermark,
        bootstrap_manifest_version=bootstrap_manifest_version,
        command_center_ref=command_center_ref,
        command_center_watermark=command_center_watermark,
        public_artifacts=artifacts,
        private_sources=sources,
    )
    return RecoveryManifest(
        generated_at=generated_at,
        current_main_sha=current_main_sha,
        event_watermark=event_watermark,
        bootstrap_manifest_version=bootstrap_manifest_version,
        command_center_ref=command_center_ref,
        command_center_watermark=command_center_watermark,
        public_artifacts=artifacts,
        private_sources=sources,
        bundle_hash=bundle_hash,
    )


def digest_public_artifacts(contents: Mapping[str, tuple[str, str, bool]]) -> tuple[RecoveryArtifactDigest, ...]:
    """Build artifact digests from `{path: (content, role, required)}` input."""

    return tuple(
        sorted(
            (
                RecoveryArtifactDigest(path=path, sha256=sha256_text(content), role=role, required=required)
                for path, (content, role, required) in contents.items()
            ),
            key=lambda item: item.path,
        )
    )
