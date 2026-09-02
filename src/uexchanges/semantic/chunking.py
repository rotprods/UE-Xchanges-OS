from __future__ import annotations

import hashlib
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


_SECRET_FILE_NAMES = {
    ".env",
    "private.json",
    "credentials.json",
    "secrets.json",
    "id_rsa",
    "id_ed25519",
}
_SECRET_PARTS = {".git", ".venv", "node_modules", "private"}
_BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".heic", ".ico",
    ".mp4", ".mov", ".avi", ".mkv", ".mp3", ".wav", ".aiff",
    ".zip", ".gz", ".tar", ".7z", ".rar", ".woff", ".woff2", ".ttf",
    ".otf", ".sqlite", ".sqlite3", ".db", ".pyc",
}
_NAMESPACE = uuid.UUID("aebd867d-afb0-4e7e-9b6d-0ad96628d5ce")


@dataclass(frozen=True, slots=True)
class RepoChunk:
    point_id: str
    path: str
    chunk_index: int
    line_start: int
    line_end: int
    text: str
    sha256: str

    def payload(self) -> dict[str, object]:
        return {
            "path": self.path,
            "chunk_index": self.chunk_index,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "chunk_sha256": self.sha256,
            "text": self.text,
        }


@dataclass(frozen=True, slots=True)
class ScanStats:
    tracked_candidates: int
    indexed_files: int
    skipped_binary: int
    skipped_secret: int
    skipped_large: int
    skipped_decode: int


def _is_secret_path(relative: Path) -> bool:
    lowered = [part.lower() for part in relative.parts]
    if any(part in _SECRET_PARTS for part in lowered):
        return True
    name = relative.name.lower()
    if name in _SECRET_FILE_NAMES:
        return True
    if name.startswith(".env") and name != ".env.example":
        return True
    if name.endswith((".pem", ".key", ".p12", ".pfx")):
        return True
    if len(relative.parts) >= 2 and relative.parts[0].lower() in {"applications", "data"}:
        return True
    if relative.as_posix().lower() == "profile/private.json":
        return True
    return False


def tracked_paths(repo_root: Path) -> list[Path]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "-z"],
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        proc = None
    if proc and proc.returncode == 0:
        return [Path(p.decode("utf-8")) for p in proc.stdout.split(b"\0") if p]
    if (repo_root / ".git").exists():
        stderr = proc.stderr.decode("utf-8", errors="replace")[:300] if proc else "git unavailable"
        raise RuntimeError(f"git ls-files failed for repository: {stderr}")
    return [path.relative_to(repo_root) for path in repo_root.rglob("*") if path.is_file()]


def _read_pdf_text(path: Path) -> str | None:
    try:
        from pypdf import PdfReader  # type: ignore[import-not-found]
    except ImportError:
        return None
    try:
        reader = PdfReader(str(path))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return None


def _read_text(path: Path) -> tuple[str | None, str | None]:
    if path.suffix.lower() == ".pdf":
        text = _read_pdf_text(path)
        return (text, None if text is not None else "decode")
    if path.suffix.lower() in _BINARY_SUFFIXES:
        return None, "binary"
    try:
        raw = path.read_bytes()
    except OSError:
        return None, "decode"
    if b"\x00" in raw[:8192]:
        return None, "binary"
    try:
        return raw.decode("utf-8"), None
    except UnicodeDecodeError:
        return None, "decode"


def chunk_text(
    *, path: str, text: str, target_chars: int = 3600, overlap_chars: int = 420
) -> Iterator[RepoChunk]:
    lines = text.splitlines(keepends=True)
    if not lines and text:
        lines = [text]
    start = 0
    chunk_index = 0
    while start < len(lines):
        size = 0
        end = start
        while end < len(lines) and (size < target_chars or end == start):
            size += len(lines[end])
            end += 1
            if size >= target_chars:
                break
        chunk = "".join(lines[start:end]).strip()
        if chunk:
            digest = hashlib.sha256(chunk.encode("utf-8")).hexdigest()
            identity = f"{path}:{chunk_index}:{start + 1}:{end}:{digest}"
            yield RepoChunk(
                point_id=str(uuid.uuid5(_NAMESPACE, identity)),
                path=path,
                chunk_index=chunk_index,
                line_start=start + 1,
                line_end=end,
                text=chunk,
                sha256=digest,
            )
            chunk_index += 1
        if end >= len(lines):
            break
        overlap_size = 0
        next_start = end
        while next_start > start and overlap_size < overlap_chars:
            next_start -= 1
            overlap_size += len(lines[next_start])
        if next_start <= start:
            next_start = max(start + 1, end - 1)
        start = next_start


def scan_repository(
    repo_root: Path,
    *,
    target_chars: int = 3600,
    overlap_chars: int = 420,
    max_file_bytes: int = 2_000_000,
) -> tuple[list[RepoChunk], ScanStats]:
    chunks: list[RepoChunk] = []
    candidates = tracked_paths(repo_root)
    indexed_files = skipped_binary = skipped_secret = skipped_large = skipped_decode = 0
    for relative in sorted(candidates, key=lambda item: item.as_posix()):
        if _is_secret_path(relative):
            skipped_secret += 1
            continue
        absolute = repo_root / relative
        try:
            size = absolute.stat().st_size
        except OSError:
            skipped_decode += 1
            continue
        if size > max_file_bytes and relative.suffix.lower() != ".pdf":
            skipped_large += 1
            continue
        text, reason = _read_text(absolute)
        if text is None:
            if reason == "binary":
                skipped_binary += 1
            else:
                skipped_decode += 1
            continue
        if not text.strip():
            continue
        file_chunks = list(
            chunk_text(
                path=relative.as_posix(),
                text=text,
                target_chars=target_chars,
                overlap_chars=overlap_chars,
            )
        )
        if file_chunks:
            indexed_files += 1
            chunks.extend(file_chunks)
    return chunks, ScanStats(
        tracked_candidates=len(candidates),
        indexed_files=indexed_files,
        skipped_binary=skipped_binary,
        skipped_secret=skipped_secret,
        skipped_large=skipped_large,
        skipped_decode=skipped_decode,
    )
