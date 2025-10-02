"""Constraint enforcement utilities for ProML outputs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Protocol, runtime_checkable

from .parser import OutputConstraints


@runtime_checkable
class GenerationAdapter(Protocol):
    """Adapter interface for decoder-time constraint enforcement."""

    def supports_regex(self) -> bool: ...

    def apply_regex(self, pattern: str) -> None: ...

    def supports_json_schema(self) -> bool: ...

    def apply_json_schema(self, schema: Dict[str, Any]) -> None: ...

    def supports_grammar(self) -> bool: ...

    def apply_grammar(self, grammar: Dict[str, Any]) -> None: ...


@dataclass
class ConstraintReport:
    passed: bool
    errors: List[str]


class ConstraintEngine:
    """Centralises regex, grammar, and schema enforcement."""

    def __init__(self, constraints: OutputConstraints) -> None:
        self._constraints = constraints
        self._regex = re.compile(constraints.regex) if constraints.regex else None
        self._schema = constraints.json_schema
        self._grammar = constraints.grammar

    @property
    def constraints(self) -> OutputConstraints:
        return self._constraints

    def configure(self, adapter: GenerationAdapter) -> List[str]:
        """Attempt to configure decoder-time constraints on the adapter.

        Returns a list of warnings for constraints that could not be applied
        proactively and must be validated post-hoc.
        """

        warnings: List[str] = []
        if self._regex:
            if adapter.supports_regex():
                adapter.apply_regex(self._constraints.regex)  # type: ignore[arg-type]
            else:
                warnings.append("Adapter does not support regex constraints; will validate after generation.")
        if self._schema:
            if adapter.supports_json_schema():
                adapter.apply_json_schema(self._schema)
            else:
                warnings.append("Adapter cannot enforce JSON Schema; falling back to validation.")
        if self._grammar:
            if adapter.supports_grammar():
                adapter.apply_grammar(self._grammar)
            else:
                warnings.append("Grammar constraints require a compatible adapter (e.g. guidance/llguidance).")
        return warnings

    def validate_schema(self, value: Any) -> List[str]:
        if not self._schema:
            return []
        return validate_schema(value, self._schema)

    def validate_regex(self, raw: str) -> List[str]:
        if not self._regex:
            return []
        if self._regex.fullmatch(raw):
            return []
        return [f"Output does not match regex {self._constraints.regex!r}."]

    def validate_grammar(self, raw: str, parsed: Any) -> List[str]:
        if not self._grammar:
            return []
        return [
            "Grammar constraints are defined but no runtime enforcer is configured yet; "
            "consider integrating a Guidance-compatible adapter."
        ]

    def validate_all(self, raw: str, parsed: Any) -> ConstraintReport:
        errors: List[str] = []
        errors.extend(self.validate_schema(parsed))
        errors.extend(self.validate_regex(raw))
        errors.extend(self.validate_grammar(raw, parsed))
        return ConstraintReport(passed=not errors, errors=errors)


def validate_schema(value: Any, schema: Dict[str, Any], path: str = "$") -> List[str]:
    errors: List[str] = []
    schema_type = schema.get("type")
    if schema_type:
        if isinstance(schema_type, list):
            if not any(_is_instance(value, t) for t in schema_type):
                errors.append(f"{path}: expected type {schema_type}, got {type(value).__name__}")
                return errors
        else:
            if not _is_instance(value, schema_type):
                errors.append(f"{path}: expected type {schema_type}, got {type(value).__name__}")
                return errors

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value {value!r} not in enum {schema['enum']!r}")
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: value {value!r} does not match const {schema['const']!r}")

    if schema.get("type") in ("object", None) or "properties" in schema or "required" in schema:
        if not isinstance(value, dict):
            errors.append(f"{path}: expected object")
            return errors
        required = schema.get("required", [])
        for field in required:
            if field not in value:
                errors.append(f"{path}: missing required property '{field}'")
        properties = schema.get("properties", {})
        for name, subschema in properties.items():
            if name in value:
                errors.extend(validate_schema(value[name], subschema, f"{path}.{name}"))
        additional = schema.get("additionalProperties")
        if additional is False:
            allowed = set(properties.keys())
            for name in value:
                if name not in allowed:
                    errors.append(f"{path}: additional property '{name}' not allowed")

    if schema.get("type") == "array" or "items" in schema:
        if not isinstance(value, list):
            errors.append(f"{path}: expected array")
            return errors
        items = schema.get("items")
        if isinstance(items, dict):
            for idx, item in enumerate(value):
                errors.extend(validate_schema(item, items, f"{path}[{idx}]"))
        elif isinstance(items, list):
            for idx, (item, subschema) in enumerate(zip(value, items)):
                errors.extend(validate_schema(item, subschema, f"{path}[{idx}]"))
            if len(value) > len(items):
                errors.append(f"{path}: array longer than tuple schema of length {len(items)}")

    if "allOf" in schema:
        for subschema in schema["allOf"]:
            errors.extend(validate_schema(value, subschema, path))

    if "anyOf" in schema:
        subschemas = schema["anyOf"]
        if not any(not validate_schema(value, subschema, path) for subschema in subschemas):
            errors.append(f"{path}: does not satisfy anyOf clause")

    if "pattern" in schema and isinstance(value, str):
        pattern = schema["pattern"]
        if not re.fullmatch(pattern, value):
            errors.append(f"{path}: string does not match pattern {pattern!r}")

    return errors


def _is_instance(value: Any, schema_type: str) -> bool:
    if schema_type == "object":
        return isinstance(value, dict)
    if schema_type == "array":
        return isinstance(value, list)
    if schema_type == "string":
        return isinstance(value, str)
    if schema_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if schema_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if schema_type == "boolean":
        return isinstance(value, bool)
    if schema_type == "null":
        return value is None
    return False
