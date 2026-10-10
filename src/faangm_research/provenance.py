"""Snapshot manifest creation and integrity verification."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_manifest(data_dir: Path, output_path: Path) -> dict[str, object]:
    files = []
    for path in sorted(data_dir.rglob("*")):
        if path.is_file() and path != output_path:
            files.append(
                {
                    "path": str(path.relative_to(data_dir.parent)),
                    "bytes": path.stat().st_size,
                    "sha256": file_sha256(path),
                }
            )
    manifest: dict[str, object] = {
        "created_at": datetime.now(UTC).isoformat(),
        "file_count": len(files),
        "files": files,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def verify_manifest(root: Path, manifest_path: Path) -> list[str]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for record in manifest["files"]:
        path = root / record["path"]
        if not path.exists():
            errors.append(f"Missing: {record['path']}")
        elif file_sha256(path) != record["sha256"]:
            errors.append(f"Hash mismatch: {record['path']}")
    return errors
