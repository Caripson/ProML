"""Reference parser for the Prompt Markup Language (ProML)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import yaml

BLOCK_ORDER = ["META", "INPUT", "OUTPUT", "POLICY", "PIPELINE", "TEST"]
REQUIRED_BLOCKS = ["META", "INPUT", "OUTPUT"]
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z-.]+)?(?:\+[0-9A-Za-z-.]+)?$")
REPRO_TIERS = {"strict", "loose"}
STRICT_TEMP_MAX = 0.3
STRICT_MAX_TOKENS = 1024


class PromlParseError(ValueError):
    """Raised when parsing or validation fails."""

    def __init__(self, message: str, filename: str, line: Optional[int] = None) -> None:
        location = f"{filename}:{line}" if line is not None else filename
        super().__init__(f"{location}: {message}")
        self.filename = filename
        self.line = line


@dataclass
class SourceSpan:
    filename: str
    start_line: int
    end_line: int


@dataclass
class CacheConfig:
    strategy: str
    scope: str
    ttl_seconds: Optional[int]


@dataclass
class EngineProfile:
    name: str
    provider: str
    model: str
    temperature: float
    max_output_tokens: int
    cost_budget: Optional[float]
    cache: Optional[CacheConfig]


@dataclass
class MetaBlock:
    span: SourceSpan
    identifier: str
    version: str
    repro: str
    description: Optional[str] = None
    owners: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    profiles: Dict[str, EngineProfile] = field(default_factory=dict)


@dataclass
class InputField:
    name: str
    type: str
    span: SourceSpan
    description: Optional[str] = None
    required: bool = True
    default: Any = None


@dataclass
class OutputConstraints:
    span: SourceSpan
    json_schema: Dict[str, Any]
    schema_id: str
    schema_version: str
    regex: Optional[str] = None
    grammar: Optional[Dict[str, Any]] = None


@dataclass
class PolicyImport:
    identifier: str
    version: str
    span: SourceSpan


@dataclass
class PolicyBlock:
    span: SourceSpan
    imports: List[PolicyImport] = field(default_factory=list)
    local: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineStep:
    span: SourceSpan
    identifier: str
    uses: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    expects: Dict[str, Any]


@dataclass
class PipelineEdge:
    span: SourceSpan
    source: str
    target: str


@dataclass
class PipelineBlock:
    span: SourceSpan
    steps: List[PipelineStep]
    edges: List[PipelineEdge]


@dataclass
class TestAssertion:
    type: str
    span: SourceSpan
    path: Optional[str] = None
    value: Any = None
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestStep:
    span: SourceSpan
    name: Optional[str]
    input: Dict[str, Any]
    mock_output: Any
    assertions: List[TestAssertion]


@dataclass
class TestCase:
    span: SourceSpan
    name: str
    input: Dict[str, Any]
    expect: Dict[str, Any]
    steps: List[TestStep]


@dataclass
class PromlDocument:
    filename: str
    span: SourceSpan
    meta: MetaBlock
    inputs: List[InputField]
    output: OutputConstraints
    policy: Optional[PolicyBlock]
    pipeline: Optional[PipelineBlock]
    tests: List[TestCase]


def parse_proml_file(path: str | Path) -> PromlDocument:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    return parse_proml(text, filename=str(path))


def parse_proml(text: str, filename: str = "<string>") -> PromlDocument:
    lines = text.replace("\r\n", "\n").split("\n")
    blocks = _extract_blocks(lines, filename)

    for block_name in REQUIRED_BLOCKS:
        if block_name not in blocks:
            raise PromlParseError(f"Missing required block '{block_name}'.", filename)

    meta = _parse_meta(blocks["META"].content, blocks["META"].span)
    inputs = _parse_inputs(blocks["INPUT"].content, blocks["INPUT"].span)
    output = _parse_output(blocks["OUTPUT"].content, blocks["OUTPUT"].span)
    policy = _parse_policy(blocks["POLICY"].content, blocks["POLICY"].span) if "POLICY" in blocks else None
    pipeline = _parse_pipeline(blocks["PIPELINE"].content, blocks["PIPELINE"].span) if "PIPELINE" in blocks else None
    tests = _parse_tests(blocks["TEST"].content, blocks["TEST"].span) if "TEST" in blocks else []

    document_span = SourceSpan(filename, 1, len(lines))
    return PromlDocument(
        filename=filename,
        span=document_span,
        meta=meta,
        inputs=inputs,
        output=output,
        policy=policy,
        pipeline=pipeline,
        tests=tests,
    )


@dataclass
class _RawBlock:
    name: str
    content: str
    span: SourceSpan


def _extract_blocks(lines: List[str], filename: str) -> Dict[str, _RawBlock]:
    blocks: Dict[str, _RawBlock] = {}
    current_index = -1
    i = 0
    total = len(lines)

    while i < total:
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        header_match = re.match(r"^([A-Z_]+):\s*$", stripped)
        if not header_match:
            raise PromlParseError("Expected block header (e.g., 'META:').", filename, i + 1)

        block_name = header_match.group(1)
        if block_name not in BLOCK_ORDER:
            raise PromlParseError(f"Unknown block '{block_name}'.", filename, i + 1)

        block_position = BLOCK_ORDER.index(block_name)
        if block_position < current_index:
            previous = BLOCK_ORDER[current_index]
            raise PromlParseError(
                f"Block '{block_name}' must appear after '{previous}'.",
                filename,
                i + 1,
            )
        if block_name in blocks:
            raise PromlParseError(f"Block '{block_name}' declared more than once.", filename, i + 1)

        start_line = i + 1
        i += 1

        body_lines: List[str] = []
        while i < total:
            candidate = lines[i]
            candidate_stripped = candidate.strip()
            if candidate_stripped and re.match(r"^[A-Z_]+:\s*$", candidate_stripped) and not candidate.startswith(" "):
                break
            body_lines.append(candidate)
            i += 1

        if not body_lines:
            raise PromlParseError(f"Block '{block_name}' is empty.", filename, start_line + 1)

        _ensure_block_indentation(body_lines, filename, start_line + 1)
        block_text = _dedent_block(body_lines)
        if not block_text.strip():
            raise PromlParseError(f"Block '{block_name}' has no content.", filename, start_line + 1)
        end_line = start_line + len(body_lines)

        blocks[block_name] = _RawBlock(
            name=block_name,
            content=block_text,
            span=SourceSpan(filename, start_line, end_line),
        )
        current_index = block_position

    return blocks


def _ensure_block_indentation(body_lines: List[str], filename: str, start_line: int) -> None:
    for offset, raw in enumerate(body_lines):
        if not raw.strip():
            continue
        if raw.lstrip().startswith("#"):
            if raw.startswith("#"):
                raise PromlParseError(
                    "Comments inside a block must be indented by at least one space.",
                    filename,
                    start_line + offset,
                )
            continue
        if raw.startswith(" "):
            continue
        raise PromlParseError(
            "Block content must be indented.",
            filename,
            start_line + offset,
        )


def _dedent_block(body_lines: List[str]) -> str:
    indents: List[int] = []
    for raw in body_lines:
        stripped = raw.strip()
        if not stripped:
            continue
        leading_spaces = len(raw) - len(raw.lstrip(" "))
        if leading_spaces == 0:
            continue
        indents.append(leading_spaces)
    indent_level = min(indents) if indents else 0
    dedented_lines = [line[indent_level:] if len(line) >= indent_level else "" for line in body_lines]
    return "\n".join(dedented_lines).rstrip()


def _yaml_load(content: str, span: SourceSpan) -> Any:
    try:
        return yaml.safe_load(content)
    except yaml.YAMLError as exc:  # pragma: no cover - PyYAML formatting
        message = str(exc).strip()
        raise PromlParseError(f"YAML error: {message}", span.filename, span.start_line) from exc


def _parse_meta(content: str, span: SourceSpan) -> MetaBlock:
    data = _yaml_load(content, span)
    if not isinstance(data, dict):
        raise PromlParseError("META block must be a mapping.", span.filename, span.start_line)

    missing = [key for key in ("id", "version", "repro") if key not in data]
    if missing:
        raise PromlParseError(
            f"META block missing required keys: {', '.join(missing)}.",
            span.filename,
            span.start_line,
        )

    identifier = data["id"]
    version = data["version"]
    repro = data["repro"]
    description = data.get("description")
    owners = data.get("owners", [])
    tags = data.get("tags", [])
    profiles_data = data.get("profiles", {})

    if not isinstance(identifier, str) or not identifier:
        raise PromlParseError("META.id must be a non-empty string.", span.filename, span.start_line)
    if not isinstance(version, str) or not SEMVER_RE.match(version):
        raise PromlParseError("META.version must be a semantic version string.", span.filename, span.start_line)
    if repro not in REPRO_TIERS:
        raise PromlParseError("META.repro must be one of 'strict' or 'loose'.", span.filename, span.start_line)
    if description is not None and not isinstance(description, str):
        raise PromlParseError("META.description must be a string if provided.", span.filename, span.start_line)
    if not isinstance(owners, list) or not all(isinstance(item, str) for item in owners):
        raise PromlParseError("META.owners must be a list of strings.", span.filename, span.start_line)
    if not isinstance(tags, list) or not all(isinstance(item, str) for item in tags):
        raise PromlParseError("META.tags must be a list of strings.", span.filename, span.start_line)
    if profiles_data and not isinstance(profiles_data, dict):
        raise PromlParseError("META.profiles must be a mapping of profile names.", span.filename, span.start_line)

    profiles = _parse_engine_profiles(profiles_data or {}, span, repro)

    return MetaBlock(
        span=span,
        identifier=identifier,
        version=version,
        repro=repro,
        description=description,
        owners=owners,
        tags=tags,
        profiles=profiles,
    )


def _parse_engine_profiles(data: Dict[str, Any], span: SourceSpan, repro: str) -> Dict[str, EngineProfile]:
    profiles: Dict[str, EngineProfile] = {}
    for name, spec in data.items():
        if not isinstance(name, str) or not name:
            raise PromlParseError("Profile names must be non-empty strings.", span.filename, span.start_line)
        if not isinstance(spec, dict):
            raise PromlParseError("Each profile entry must be a mapping.", span.filename, span.start_line)

        provider = spec.get("provider")
        model = spec.get("model")
        temperature = spec.get("temperature", 0.0)
        max_tokens = spec.get("max_output_tokens")
        cost_budget = spec.get("cost_budget")
        cache_data = spec.get("cache")

        if not isinstance(provider, str) or not provider:
            raise PromlParseError("Profile provider must be a non-empty string.", span.filename, span.start_line)
        if not isinstance(model, str) or not model:
            raise PromlParseError("Profile model must be a non-empty string.", span.filename, span.start_line)
        if not isinstance(temperature, (int, float)):
            raise PromlParseError("Profile temperature must be numeric.", span.filename, span.start_line)
        temperature_value = float(temperature)
        if temperature_value < 0.0 or temperature_value > 2.0:
            raise PromlParseError("Profile temperature must be between 0.0 and 2.0.", span.filename, span.start_line)
        if not isinstance(max_tokens, int) or max_tokens <= 0:
            raise PromlParseError("Profile max_output_tokens must be a positive integer.", span.filename, span.start_line)
        if cost_budget is not None and not isinstance(cost_budget, (int, float)):
            raise PromlParseError("Profile cost_budget must be numeric when provided.", span.filename, span.start_line)

        if repro == "strict":
            if temperature_value > STRICT_TEMP_MAX:
                raise PromlParseError(
                    f"Strict repro profiles must use temperature <= {STRICT_TEMP_MAX}.",
                    span.filename,
                    span.start_line,
                )
            if max_tokens > STRICT_MAX_TOKENS:
                raise PromlParseError(
                    f"Strict repro profiles must set max_output_tokens <= {STRICT_MAX_TOKENS}.",
                    span.filename,
                    span.start_line,
                )
            if cost_budget is None:
                raise PromlParseError(
                    "Strict repro profiles must declare a cost_budget ceiling.",
                    span.filename,
                    span.start_line,
                )

        cache_config = _parse_cache_config(cache_data, span) if cache_data is not None else None

        profiles[name] = EngineProfile(
            name=name,
            provider=provider,
            model=model,
            temperature=temperature_value,
            max_output_tokens=max_tokens,
            cost_budget=float(cost_budget) if cost_budget is not None else None,
            cache=cache_config,
        )

    return profiles


def _parse_cache_config(data: Any, span: SourceSpan) -> CacheConfig:
    if not isinstance(data, dict):
        raise PromlParseError("Profile cache configuration must be a mapping.", span.filename, span.start_line)

    strategy = data.get("strategy", "simple")
    scope = data.get("scope", "local")
    ttl = data.get("ttl")

    if not isinstance(strategy, str) or not strategy:
        raise PromlParseError("Cache.strategy must be a non-empty string.", span.filename, span.start_line)
    if not isinstance(scope, str) or not scope:
        raise PromlParseError("Cache.scope must be a non-empty string.", span.filename, span.start_line)

    ttl_seconds = _parse_duration(ttl, span) if ttl is not None else None

    return CacheConfig(
        strategy=strategy,
        scope=scope,
        ttl_seconds=ttl_seconds,
    )


def _parse_duration(value: Any, span: SourceSpan) -> int:
    if isinstance(value, int):
        if value < 0:
            raise PromlParseError("Cache.ttl must be non-negative.", span.filename, span.start_line)
        return value
    if isinstance(value, str):
        match = re.fullmatch(r"^(\d+)([smhd])$", value)
        if not match:
            raise PromlParseError("Cache.ttl must use format <number><s|m|h|d>.", span.filename, span.start_line)
        amount = int(match.group(1))
        unit = match.group(2)
        multiplier = {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
        return amount * multiplier
    raise PromlParseError("Cache.ttl must be an integer or duration string.", span.filename, span.start_line)


def _parse_inputs(content: str, span: SourceSpan) -> List[InputField]:
    data = _yaml_load(content, span)
    if not isinstance(data, dict):
        raise PromlParseError("INPUT block must be a mapping.", span.filename, span.start_line)

    inputs: List[InputField] = []
    for name, spec in data.items():
        if not isinstance(name, str) or not name:
            raise PromlParseError("Input names must be non-empty strings.", span.filename, span.start_line)
        if not isinstance(spec, dict):
            raise PromlParseError(
                f"INPUT.{name} must be a mapping describing the field.",
                span.filename,
                span.start_line,
            )

        field_type = spec.get("type")
        if not isinstance(field_type, str) or not field_type:
            raise PromlParseError(
                f"INPUT.{name}.type is required and must be a string.",
                span.filename,
                span.start_line,
            )

        description = spec.get("description")
        if description is not None and not isinstance(description, str):
            raise PromlParseError(
                f"INPUT.{name}.description must be a string if provided.",
                span.filename,
                span.start_line,
            )

        required = spec.get("required", True)
        if not isinstance(required, bool):
            raise PromlParseError(
                f"INPUT.{name}.required must be a boolean if provided.",
                span.filename,
                span.start_line,
            )

        default = spec.get("default")
        if not required and "default" not in spec:
            default = None

        inputs.append(
            InputField(
                name=name,
                type=field_type,
                description=description,
                required=required,
                default=default,
                span=span,
            )
        )

    if not inputs:
        raise PromlParseError("INPUT block must declare at least one field.", span.filename, span.start_line)

    return inputs


def _parse_output(content: str, span: SourceSpan) -> OutputConstraints:
    data = _yaml_load(content, span)
    if not isinstance(data, dict):
        raise PromlParseError("OUTPUT block must be a mapping.", span.filename, span.start_line)

    json_schema = data.get("json_schema")
    if not isinstance(json_schema, dict):
        raise PromlParseError("OUTPUT.json_schema must be a mapping.", span.filename, span.start_line)

    schema_id = json_schema.get("$id")
    schema_version = json_schema.get("version")
    schema_body = json_schema.get("schema")
    if not isinstance(schema_id, str) or not schema_id:
        raise PromlParseError("OUTPUT.json_schema.$id must be a non-empty string.", span.filename, span.start_line)
    if not isinstance(schema_version, str) or not schema_version:
        raise PromlParseError("OUTPUT.json_schema.version must be a non-empty string.", span.filename, span.start_line)
    if not isinstance(schema_body, dict):
        raise PromlParseError("OUTPUT.json_schema.schema must be a mapping.", span.filename, span.start_line)

    regex_value = data.get("regex")
    if regex_value is not None and not isinstance(regex_value, str):
        raise PromlParseError("OUTPUT.regex must be a string when provided.", span.filename, span.start_line)

    grammar_value = data.get("grammar")
    if grammar_value is not None and not isinstance(grammar_value, dict):
        raise PromlParseError("OUTPUT.grammar must be a mapping when provided.", span.filename, span.start_line)

    return OutputConstraints(
        span=span,
        json_schema=schema_body,
        schema_id=schema_id,
        schema_version=schema_version,
        regex=regex_value,
        grammar=grammar_value,
    )


def _parse_policy(content: str, span: SourceSpan) -> PolicyBlock:
    data = _yaml_load(content, span)
    if not isinstance(data, dict):
        raise PromlParseError("POLICY block must be a mapping.", span.filename, span.start_line)

    imports_raw = data.get("imports", [])
    if not isinstance(imports_raw, list):
        raise PromlParseError("POLICY.imports must be a list if provided.", span.filename, span.start_line)

    imports: List[PolicyImport] = []
    for item in imports_raw:
        if not isinstance(item, dict):
            raise PromlParseError("POLICY.imports entries must be mappings.", span.filename, span.start_line)
        policy_id = item.get("id")
        version = item.get("version")
        if not isinstance(policy_id, str) or not policy_id:
            raise PromlParseError("POLICY.imports[].id must be a non-empty string.", span.filename, span.start_line)
        if not isinstance(version, str) or not version:
            raise PromlParseError("POLICY.imports[].version must be a non-empty string.", span.filename, span.start_line)
        imports.append(PolicyImport(identifier=policy_id, version=version, span=span))

    local = data.get("local", {})
    if local is None:
        local = {}
    if not isinstance(local, dict):
        raise PromlParseError("POLICY.local must be a mapping if provided.", span.filename, span.start_line)

    return PolicyBlock(span=span, imports=imports, local=local)


def _parse_pipeline(content: str, span: SourceSpan) -> PipelineBlock:
    data = _yaml_load(content, span)
    if not isinstance(data, dict):
        raise PromlParseError("PIPELINE block must be a mapping.", span.filename, span.start_line)

    steps_data = data.get("steps", [])
    edges_data = data.get("edges", [])

    if not isinstance(steps_data, list) or not steps_data:
        raise PromlParseError("PIPELINE.steps must be a non-empty list.", span.filename, span.start_line)
    if not isinstance(edges_data, list):
        raise PromlParseError("PIPELINE.edges must be a list if provided.", span.filename, span.start_line)

    steps: List[PipelineStep] = []
    seen_ids: set[str] = set()
    for item in steps_data:
        if not isinstance(item, dict):
            raise PromlParseError("PIPELINE.steps entries must be mappings.", span.filename, span.start_line)
        step_id = item.get("id")
        uses = item.get("uses")
        inputs_map = item.get("inputs", {})
        outputs_map = item.get("outputs", {})
        expects_map = item.get("expects", {})
        if not isinstance(step_id, str) or not step_id:
            raise PromlParseError("PIPELINE.steps[].id must be a non-empty string.", span.filename, span.start_line)
        if step_id in seen_ids:
            raise PromlParseError(f"Duplicate pipeline step id '{step_id}'.", span.filename, span.start_line)
        if not isinstance(uses, str) or not uses:
            raise PromlParseError("PIPELINE.steps[].uses must be a non-empty string.", span.filename, span.start_line)
        if not isinstance(inputs_map, dict):
            raise PromlParseError("PIPELINE.steps[].inputs must be a mapping.", span.filename, span.start_line)
        if not isinstance(outputs_map, dict):
            raise PromlParseError("PIPELINE.steps[].outputs must be a mapping.", span.filename, span.start_line)
        if not isinstance(expects_map, dict):
            raise PromlParseError("PIPELINE.steps[].expects must be a mapping if provided.", span.filename, span.start_line)

        steps.append(
            PipelineStep(
                span=span,
                identifier=step_id,
                uses=uses,
                inputs=inputs_map,
                outputs=outputs_map,
                expects=expects_map,
            )
        )
        seen_ids.add(step_id)

    edges: List[PipelineEdge] = []
    for item in edges_data:
        if not isinstance(item, dict):
            raise PromlParseError("PIPELINE.edges entries must be mappings.", span.filename, span.start_line)
        source = item.get("from")
        target = item.get("to")
        if not isinstance(source, str) or not isinstance(target, str):
            raise PromlParseError("PIPELINE.edges entries require 'from' and 'to' strings.", span.filename, span.start_line)
        if source not in seen_ids or target not in seen_ids:
            raise PromlParseError("PIPELINE.edges references unknown step id.", span.filename, span.start_line)
        edges.append(PipelineEdge(span=span, source=source, target=target))

    _ensure_acyclic(seen_ids, edges, span)

    return PipelineBlock(span=span, steps=steps, edges=edges)


def _ensure_acyclic(step_ids: Iterable[str], edges: List[PipelineEdge], span: SourceSpan) -> None:
    adjacency: Dict[str, List[str]] = {step_id: [] for step_id in step_ids}
    indegree: Dict[str, int] = {step_id: 0 for step_id in step_ids}
    for edge in edges:
        adjacency[edge.source].append(edge.target)
        indegree[edge.target] += 1

    queue: List[str] = [step for step, deg in indegree.items() if deg == 0]
    visited = 0

    while queue:
        node = queue.pop()
        visited += 1
        for neighbor in adjacency[node]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)

    if visited != len(step_ids):
        raise PromlParseError("PIPELINE graph must be acyclic.", span.filename, span.start_line)


def _parse_tests(content: str, span: SourceSpan) -> List[TestCase]:
    data = _yaml_load(content, span)
    if data is None:
        return []
    if not isinstance(data, list):
        raise PromlParseError("TEST block must be a list of test cases.", span.filename, span.start_line)

    cases: List[TestCase] = []
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise PromlParseError("Each test case must be a mapping.", span.filename, span.start_line)
        name = item.get("name") or f"Test Case #{index + 1}"
        if not isinstance(name, str):
            raise PromlParseError("Test case name must be a string.", span.filename, span.start_line)

        input_data = item.get("input", {})
        if not isinstance(input_data, dict):
            raise PromlParseError("Test case 'input' must be a mapping.", span.filename, span.start_line)

        expect_data = item.get("expect", {})
        if expect_data is None:
            expect_data = {}
        if not isinstance(expect_data, dict):
            raise PromlParseError("Test case 'expect' must be a mapping if provided.", span.filename, span.start_line)

        steps_data = item.get("steps")
        steps: List[TestStep]
        if steps_data is None:
            mock_output = item.get("mock_output", {})
            assertions = item.get("assert", [])
            step_input = input_data
            steps = [
                TestStep(
                    span=span,
                    name=name,
                    input=step_input,
                    mock_output=mock_output,
                    assertions=_parse_assertions(assertions, span),
                )
            ]
        else:
            if not isinstance(steps_data, list) or not steps_data:
                raise PromlParseError("Test case 'steps' must be a non-empty list.", span.filename, span.start_line)
            steps = []
            for step in steps_data:
                if not isinstance(step, dict):
                    raise PromlParseError("Each test step must be a mapping.", span.filename, span.start_line)
                step_name = step.get("name")
                if step_name is not None and not isinstance(step_name, str):
                    raise PromlParseError("Test step 'name' must be a string if provided.", span.filename, span.start_line)
                step_input = step.get("input", {})
                if not isinstance(step_input, dict):
                    raise PromlParseError("Test step 'input' must be a mapping if provided.", span.filename, span.start_line)
                mock_output = step.get("mock_output", {})
                assertions = _parse_assertions(step.get("assert", []), span)
                steps.append(
                    TestStep(
                        span=span,
                        name=step_name,
                        input=step_input,
                        mock_output=mock_output,
                        assertions=assertions,
                    )
                )

        cases.append(
            TestCase(
                span=span,
                name=name,
                input=input_data,
                expect=expect_data,
                steps=steps,
            )
        )

    return cases


def _parse_assertions(raw_assertions: Any, span: SourceSpan) -> List[TestAssertion]:
    if raw_assertions is None:
        return []
    if not isinstance(raw_assertions, list):
        raise PromlParseError("'assert' must be a list of assertion objects.", span.filename, span.start_line)

    assertions: List[TestAssertion] = []
    for item in raw_assertions:
        if not isinstance(item, dict):
            raise PromlParseError("Assertion entries must be mappings.", span.filename, span.start_line)
        assertion_type = item.get("type")
        if not isinstance(assertion_type, str) or not assertion_type:
            raise PromlParseError("Assertion 'type' must be a non-empty string.", span.filename, span.start_line)
        path = item.get("path")
        if path is not None and not isinstance(path, str):
            raise PromlParseError("Assertion 'path' must be a string if provided.", span.filename, span.start_line)
        value = item.get("value")

        extra = {k: v for k, v in item.items() if k not in {"type", "path", "value"}}
        assertions.append(TestAssertion(type=assertion_type, span=span, path=path, value=value, options=extra))
    return assertions
