"""MkDocs plugin that renders documentation from .proml modules."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

try:  # pragma: no cover - only executed when MkDocs is installed
    from mkdocs.config import config_options
    from mkdocs.plugins import BasePlugin
except ImportError:  # pragma: no cover - plugin not active outside MkDocs
    BasePlugin = object  # type: ignore
    config_options = None  # type: ignore

from proml.parser import PromlDocument, parse_proml_file


def _render_document(doc: PromlDocument) -> str:
    lines: List[str] = []
    lines.append(f"# {doc.meta.identifier}")
    lines.append("")
    lines.append(f"Version: **{doc.meta.version}**  ")
    lines.append(f"Repro tier: **{doc.meta.repro}**")
    if doc.meta.description:
        lines.append("")
        lines.append(doc.meta.description)
    if doc.meta.owners:
        owners = ", ".join(doc.meta.owners)
        lines.append("")
        lines.append(f"**Owners:** {owners}")
    if doc.meta.tags:
        tags = ", ".join(doc.meta.tags)
        lines.append(f"**Tags:** {tags}")

    if doc.meta.profiles:
        lines.append("")
        lines.append("## Engine Profiles")
        for profile in doc.meta.profiles.values():
            lines.append(f"- **{profile.name}** → {profile.provider}/{profile.model} (temp={profile.temperature}, max_tokens={profile.max_output_tokens})")

    lines.append("")
    lines.append("## Inputs")
    for field in doc.inputs:
        default_text = f" (default={field.default!r})" if field.default is not None else ""
        required = "required" if field.required else "optional"
        lines.append(f"- `{field.name}`: {field.type} ({required}){default_text}")
        if field.description:
            lines.append(f"  - {field.description}")

    lines.append("")
    lines.append("## Output Schema")
    lines.append("```json")
    import json

    schema_payload: Dict[str, Any] = {
        "$id": doc.output.schema_id,
        "version": doc.output.schema_version,
        "schema": doc.output.json_schema,
    }
    lines.append(json.dumps(schema_payload, indent=2, sort_keys=True))
    lines.append("```")

    if doc.tests:
        lines.append("")
        lines.append("## Tests")
        for case in doc.tests:
            lines.append(f"- **{case.name}**: {len(case.steps)} step(s)")
    return "\n".join(lines) + "\n"


class ProMLDocsPlugin(BasePlugin):  # type: ignore[misc]
    if config_options is not None:
        config_scheme = (
            ("glob", config_options.Type(str, default="test_prompts/**/*.proml")),
            ("output_dir", config_options.Type(str, default="docs/generated")),
        )

    def on_config(self, config):  # pragma: no cover - executed by MkDocs
        project_dir = Path(config["config_file_path"]).parent
        self.project_dir = project_dir
        self.output_dir = project_dir / self.config.get("output_dir", "docs/generated")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return config

    def on_files(self, files, config):  # pragma: no cover - executed by MkDocs
        if BasePlugin is object:
            return files
        pattern = self.config.get("glob", "test_prompts/**/*.proml")
        for path in self.project_dir.glob(pattern):
            doc = parse_proml_file(path)
            output_path = self.output_dir / f"{doc.meta.identifier}.md"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(_render_document(doc), encoding="utf-8")
        return files
