"""Local registry management for ProML modules."""

from __future__ import annotations

import dataclasses
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .parser import parse_proml_file

REGISTRY_FILENAME = "proml_registry.yaml"


@dataclass
class RegistryEntry:
    module_id: str
    version: str
    path: str
    sha256: str
    repro: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class Registry:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.modules: Dict[str, List[RegistryEntry]] = {}

    @classmethod
    def load(cls, root: Path, filename: str = REGISTRY_FILENAME) -> "Registry":
        registry_path = root / filename
        registry = cls(registry_path)
        if registry_path.exists():
            data = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
            modules = data.get("modules", {})
            for module_id, entries in modules.items():
                registry.modules[module_id] = [RegistryEntry(**entry) for entry in entries]
        return registry

    def save(self) -> None:
        payload = {
            "modules": {
                module_id: [dataclasses.asdict(entry) for entry in sorted(entries, key=lambda e: _version_key(e.version))]
                for module_id, entries in self.modules.items()
            }
        }
        self.path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")

    def add_document(self, document_path: Path) -> RegistryEntry:
        document = parse_proml_file(document_path)
        module_id = document.meta.identifier
        version = document.meta.version
        sha256_hash = _compute_sha256(document_path)
        entry = RegistryEntry(
            module_id=module_id,
            version=version,
            path=str(document_path),
            sha256=sha256_hash,
            repro=document.meta.repro,
            metadata={
                "owners": document.meta.owners,
                "tags": document.meta.tags,
            },
        )
        entries = self.modules.setdefault(module_id, [])
        for existing in entries:
            if existing.version == version:
                raise ValueError(f"Version {version} for module {module_id} already exists in the registry.")
        entries.append(entry)
        self.modules[module_id] = entries
        return entry

    def resolve(self, module_id: str, version_spec: Optional[str] = None) -> RegistryEntry:
        if module_id not in self.modules:
            raise KeyError(f"Module '{module_id}' not found in registry.")
        entries = sorted(self.modules[module_id], key=lambda e: _version_key(e.version), reverse=True)
        if version_spec is None:
            return entries[0]
        for entry in entries:
            if _version_satisfies(entry.version, version_spec):
                return entry
        raise KeyError(f"No version matching '{version_spec}' for module '{module_id}'.")


def _compute_sha256(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def _version_key(version: str) -> tuple[int, int, int, str]:
    major, minor, patch, suffix = _split_version(version)
    return (major, minor, patch, suffix or "")


def _version_satisfies(version: str, spec: str) -> bool:
    if spec.startswith("^"):
        base = spec[1:]
        major, _, _, _ = _split_version(base)
        v_major, _, _, _ = _split_version(version)
        return v_major == major and _compare_versions(version, base) >= 0
    if spec.startswith(">="):
        base = spec[2:]
        return _compare_versions(version, base) >= 0
    if spec.startswith("<="):
        base = spec[2:]
        return _compare_versions(version, base) <= 0
    if spec.startswith(">"):
        base = spec[1:]
        return _compare_versions(version, base) > 0
    if spec.startswith("<"):
        base = spec[1:]
        return _compare_versions(version, base) < 0
    # exact match
    return version == spec


def _compare_versions(lhs: str, rhs: str) -> int:
    lhs_parts = _version_key(lhs)
    rhs_parts = _version_key(rhs)
    if lhs_parts == rhs_parts:
        return 0
    return 1 if lhs_parts > rhs_parts else -1


def _split_version(version: str) -> tuple[int, int, int, Optional[str]]:
    parts = version.split("-")
    core = parts[0]
    suffix = parts[1] if len(parts) > 1 else None
    major_str, minor_str, patch_str = core.split(".")
    return int(major_str), int(minor_str), int(patch_str), suffix
