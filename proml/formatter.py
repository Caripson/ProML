"""Schema-aware formatter for .proml documents."""

from __future__ import annotations

import io
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from .parser import PromlDocument, parse_proml


@dataclass
class FormattingOptions:
    indent: int = 2
    sort_keys: bool = True


def format_proml_content(source: str, *, filename: str = "<string>", options: Optional[FormattingOptions] = None) -> str:
    document = parse_proml(source, filename=filename)
    opts = options or FormattingOptions()
    leading_comments, block_comments, block_bodies = _extract_section_metadata(source)
    return _format_document(document, opts, leading_comments, block_comments, block_bodies)


def _format_document(
    document: PromlDocument,
    options: FormattingOptions,
    leading_comments: List[str],
    block_comments: Dict[str, List[str]],
    block_bodies: Dict[str, str],
) -> str:
    lines: List[str] = []
    writer = _SectionWriter(lines, options, leading_comments, block_comments, block_bodies)

    writer.section("META", _meta_to_mapping(document), block_bodies.get("META"))
    writer.section("INPUT", _inputs_to_mapping(document.inputs), block_bodies.get("INPUT"))
    writer.section("OUTPUT", _output_to_mapping(document), block_bodies.get("OUTPUT"))

    if document.policy is not None:
        writer.section("POLICY", _policy_to_mapping(document.policy), block_bodies.get("POLICY"))
    if document.pipeline is not None:
        writer.section("PIPELINE", _pipeline_to_mapping(document.pipeline), block_bodies.get("PIPELINE"))
    if document.tests:
        writer.section("TEST", _tests_to_sequence(document.tests), block_bodies.get("TEST"))

    return "\n".join(lines) + "\n"


class _SectionWriter:
    def __init__(
        self,
        lines: List[str],
        options: FormattingOptions,
        leading_comments: List[str],
        block_comments: Dict[str, List[str]],
        block_bodies: Dict[str, str],
    ) -> None:
        self.lines = lines
        self.options = options
        self.block_comments = block_comments
        self.block_bodies = block_bodies
        if leading_comments:
            self.lines.extend(leading_comments)
            if leading_comments[-1].strip() != "":
                self.lines.append("")

    def section(self, title: str, data: Any, original_body: Optional[str]) -> None:
        if self.lines:
            if self.lines[-1] != "":
                self.lines.append("")
        comments = self.block_comments.get(title, [])
        if comments:
            self.lines.extend(comments)
            if comments[-1].strip() != "":
                self.lines.append("")
        self.lines.append(f"{title}:")
        body = _render_block(data, original_body, self.options)
        indented = _indent(body.splitlines(), self.options.indent)
        self.lines.extend(indented)


def _indent(lines: List[str], indent: int) -> List[str]:
    prefix = " " * indent
    return [prefix + line if line else "" for line in lines]


def _meta_to_mapping(document: PromlDocument) -> Dict[str, Any]:
    data = {
        "id": document.meta.identifier,
        "version": document.meta.version,
        "repro": document.meta.repro,
    }
    if document.meta.description:
        data["description"] = document.meta.description
    if document.meta.owners:
        data["owners"] = document.meta.owners
    if document.meta.tags:
        data["tags"] = document.meta.tags
    if document.meta.profiles:
        data["profiles"] = {
            name: _profile_to_dict(profile)
            for name, profile in sorted(document.meta.profiles.items())
        }
    return data


def _profile_to_dict(profile) -> Dict[str, Any]:
    payload = {
        "provider": profile.provider,
        "model": profile.model,
        "temperature": profile.temperature,
        "max_output_tokens": profile.max_output_tokens,
    }
    if profile.cost_budget is not None:
        payload["cost_budget"] = profile.cost_budget
    if profile.cache is not None:
        cache = {
            "strategy": profile.cache.strategy,
            "scope": profile.cache.scope,
        }
        if profile.cache.ttl_seconds is not None:
            cache["ttl"] = _format_ttl(profile.cache.ttl_seconds)
        payload["cache"] = cache
    return payload


def _inputs_to_mapping(inputs) -> Dict[str, Any]:
    result = {}
    for field in inputs:
        entry = {
            "type": field.type,
            "required": field.required,
        }
        if field.description:
            entry["description"] = field.description
        if field.default is not None:
            entry["default"] = field.default
        result[field.name] = entry
    return result


def _output_to_mapping(document: PromlDocument) -> Dict[str, Any]:
    return {
        "json_schema": {
            "$id": document.output.schema_id,
            "version": document.output.schema_version,
            "schema": document.output.json_schema,
        },
        "regex": document.output.regex,
        "grammar": document.output.grammar,
    }


def _policy_to_mapping(policy) -> Dict[str, Any]:
    data = {}
    if policy.imports:
        data["imports"] = [
            {"id": entry.identifier, "version": entry.version}
            for entry in policy.imports
        ]
    if policy.local:
        data["local"] = policy.local
    return data


def _pipeline_to_mapping(pipeline) -> Dict[str, Any]:
    steps = []
    for step in pipeline.steps:
        steps.append(
            {
                "id": step.identifier,
                "uses": step.uses,
                "inputs": step.inputs,
                "outputs": step.outputs,
                "expects": step.expects,
            }
        )
    edges = [
        {"from": edge.source, "to": edge.target}
        for edge in pipeline.edges
    ]
    payload = {"steps": steps}
    if edges:
        payload["edges"] = edges
    return payload


def _tests_to_sequence(test_cases) -> List[Any]:
    cases: List[Any] = []
    for case in test_cases:
        entry: Dict[str, Any] = {
            "name": case.name,
        }
        if case.input:
            entry["input"] = case.input
        if case.expect:
            entry["expect"] = case.expect

        if len(case.steps) == 1 and case.steps[0].name == case.name:
            step = case.steps[0]
            entry["mock_output"] = step.mock_output
            if step.assertions:
                entry["assert"] = _assertions_to_list(step.assertions)
        else:
            entry["steps"] = []
            for step in case.steps:
                step_entry = {}
                if step.name:
                    step_entry["name"] = step.name
                if step.input:
                    step_entry["input"] = step.input
                step_entry["mock_output"] = step.mock_output
                if step.assertions:
                    step_entry["assert"] = _assertions_to_list(step.assertions)
                entry["steps"].append(step_entry)
        cases.append(entry)

    return cases


def _assertions_to_list(assertions) -> List[Any]:
    result = []
    for assertion in assertions:
        payload = {"type": assertion.type}
        if assertion.path is not None:
            payload["path"] = assertion.path
        if assertion.value is not None:
            payload["value"] = assertion.value
        payload.update(assertion.options)
        result.append(payload)
    return result


def _format_ttl(ttl_seconds: int) -> Any:
    if ttl_seconds % 86400 == 0:
        return f"{ttl_seconds // 86400}d"
    if ttl_seconds % 3600 == 0:
        return f"{ttl_seconds // 3600}h"
    if ttl_seconds % 60 == 0:
        return f"{ttl_seconds // 60}m"
    return ttl_seconds


def _render_block(data: Any, original_body: Optional[str], options: FormattingOptions) -> str:
    if isinstance(data, str):
        return data
    return _merge_with_original(original_body, data, options)


def _merge_with_original(original_body: Optional[str], data: Any, options: FormattingOptions) -> str:
    yaml = _make_yaml(options)
    if not original_body or not original_body.strip():
        return _serialize_data(data, yaml)
    try:
        existing = yaml.load(original_body)
    except Exception:  # pragma: no cover - malformed original
        existing = None

    merged = _update_structure(existing, data, yaml)
    return _dump_ruamel(merged, yaml)


def _extract_section_metadata(source: str) -> tuple[List[str], Dict[str, List[str]], Dict[str, str]]:
    lines = source.replace("\r\n", "\n").split("\n")
    leading: List[str] = []
    block_comments: Dict[str, List[str]] = {}
    block_bodies: Dict[str, List[str]] = {}
    pending: List[str] = []
    seen_block = False
    i = 0
    total = len(lines)

    header_pattern = re.compile(r"^([A-Z_]+):\s*$")

    while i < total:
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("#"):
            pending.append(line)
            i += 1
            continue
        header = header_pattern.match(stripped)
        if header:
            block = header.group(1)
            if pending:
                if not seen_block and not leading:
                    leading = pending.copy()
                else:
                    block_comments[block] = pending.copy()
                pending.clear()
            seen_block = True
            body_lines: List[str] = []
            i += 1
            while i < total:
                candidate = lines[i]
                stripped_candidate = candidate.strip()
                if header_pattern.match(stripped_candidate) and not candidate.startswith(" "):
                    break
                body_lines.append(candidate)
                i += 1
            block_bodies[block] = "\n".join(body_lines)
            continue
        if stripped == "":
            if pending:
                pending.append(line)
            else:
                if not seen_block and (not leading or leading[-1] != ""):
                    leading.append("")
            i += 1
            continue
        pending.clear()
        i += 1

    cleaned_bodies = {
        name: _dedent_block(body)
        for name, body in block_bodies.items()
    }
    return leading, block_comments, cleaned_bodies


def _dedent_block(body: str) -> str:
    lines = body.split("\n")
    if not lines:
        return ""
    # find minimum indent for non-empty, non-comment lines
    indent = None
    for line in lines:
        if not line.strip():
            continue
        leading = len(line) - len(line.lstrip(" "))
        if indent is None or leading < indent:
            indent = leading
    indent = indent or 0
    return "\n".join(line[indent:] if len(line) >= indent else line for line in lines).strip("\n")


def _make_yaml(options: FormattingOptions) -> YAML:
    yaml = YAML(typ="rt")
    yaml.indent(mapping=options.indent, sequence=options.indent, offset=0)
    yaml.width = 80
    yaml.sort_base_mapping_type_on_output = options.sort_keys
    return yaml


def _serialize_data(data: Any, yaml: YAML) -> str:
    buffer = io.StringIO()
    yaml.dump(data, buffer)
    return buffer.getvalue().rstrip()


def _dump_ruamel(node: Any, yaml: YAML) -> str:
    buffer = io.StringIO()
    yaml.dump(node, buffer)
    return buffer.getvalue().rstrip()


def _update_structure(existing: Any, desired: Any, yaml: YAML) -> Any:
    if isinstance(desired, dict):
        if not isinstance(existing, CommentedMap):
            return _to_ruamel(desired, yaml)
        keys_to_remove = [key for key in existing if key not in desired]
        for key in keys_to_remove:
            del existing[key]
        for key, value in desired.items():
            if isinstance(value, dict):
                existing[key] = _update_structure(existing.get(key), value, yaml)
            elif isinstance(value, list):
                existing_value = existing.get(key)
                if isinstance(existing_value, CommentedSeq):
                    _update_sequence(existing_value, value, yaml)
                    existing[key] = existing_value
                else:
                    existing[key] = _to_ruamel(value, yaml)
            else:
                existing[key] = value
        return existing
    elif isinstance(desired, list):
        if not isinstance(existing, CommentedSeq):
            existing = CommentedSeq()
        _update_sequence(existing, desired, yaml)
        return existing
    else:
        return desired


def _update_sequence(sequence: CommentedSeq, desired: List[Any], yaml: YAML) -> None:
    while len(sequence) > len(desired):
        sequence.pop(len(desired))
    for idx, value in enumerate(desired):
        if idx < len(sequence):
            current = sequence[idx]
            if isinstance(value, dict):
                sequence[idx] = _update_structure(current, value, yaml)
            elif isinstance(value, list):
                if isinstance(current, CommentedSeq):
                    _update_sequence(current, value, yaml)
                    sequence[idx] = current
                else:
                    sequence[idx] = _to_ruamel(value, yaml)
            else:
                sequence[idx] = value
        else:
            sequence.append(_to_ruamel(value, yaml))


def _to_ruamel(value: Any, yaml: YAML) -> Any:
    if isinstance(value, (dict, list)):
        return yaml.load(json.dumps(value))
    return value


__all__ = ["format_proml_content", "FormattingOptions"]
