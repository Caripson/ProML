"""Command line interface for ProML developer workflows."""

from __future__ import annotations

import argparse
import dataclasses
import json
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import yaml

from .formatter import format_proml_content
from .parser import PromlParseError, parse_proml_file
from .registry import REGISTRY_FILENAME, Registry
from .runtime import PromptExecutor

PROMPT_TEMPLATE = """META:
  id: "{module_id}"
  version: "{version}"
  repro: "strict"
  description: "{description}"
  profiles:
    default:
      provider: "openai"
      model: "gpt-4.1-mini"
      temperature: 0.2
      max_output_tokens: 512
      cost_budget: 0.02
      cache:
        strategy: "simple"
        scope: "shared"
        ttl: 15m

INPUT:
  input_text:
    type: string
    description: "Primary user input."
    required: true

OUTPUT:
  json_schema:
    $id: "schema:{module_id}:output"
    version: "{version}"
    schema:
      type: object
      additionalProperties: false
      required: [result]
      properties:
        result:
          type: string
  regex: null
  grammar: null

POLICY:
  imports: []
  local: {}

PIPELINE:
  steps:
    - id: main
      uses: module.com.example@^1.0.0
      inputs:
        text: $input.input_text
      outputs:
        result: string
      expects:
        result: string
  edges: []

TEST:
  - name: "smoke test"
    input:
      input_text: "Hello"
    mock_output:
      result: "Hello"
    assert:
      - type: schema
      - type: equals
        path: $.result
        value: "Hello"
"""


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="proml", description="ProML developer tooling")
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init", help="Create a new ProML prompt skeleton")
    init_parser.add_argument("path", help="Target path for the new .proml file")
    init_parser.add_argument("--id", dest="module_id", default="com.example.prompt", help="Module identifier")
    init_parser.add_argument("--version", default="0.1.0", help="Initial semantic version")
    init_parser.add_argument("--description", default="Describe the prompt here.", help="Short description")
    init_parser.add_argument("--force", action="store_true", help="Overwrite if the file already exists")

    lint_parser = subparsers.add_parser("lint", help="Validate .proml structure")
    lint_parser.add_argument("paths", nargs="+", help="Files or directories to lint")

    fmt_parser = subparsers.add_parser("fmt", help="Format .proml files")
    fmt_parser.add_argument("paths", nargs="+", help="Files or directories to format")

    test_parser = subparsers.add_parser("test", help="Execute TEST blocks via the reference runner")
    test_parser.add_argument("paths", nargs="+", help=".proml files to test")

    run_parser = subparsers.add_parser("run", help="Execute a prompt using the default profile")
    run_parser.add_argument("path", help="Path to the .proml file")
    run_parser.add_argument("--input", action="append", default=[], help="Input key=value pairs (value parsed as JSON when possible)")
    run_parser.add_argument("--profile", help="Profile name override")
    run_parser.add_argument("--provider", help="Override provider (e.g. stub)")
    run_parser.add_argument("--no-cache", action="store_true", help="Disable cache usage for this run")

    bench_parser = subparsers.add_parser("bench", help="Collect latency statistics across runs")
    bench_parser.add_argument("path", help="Path to the .proml file")
    bench_parser.add_argument("--input", action="append", default=[], help="Input key=value pairs (value parsed as JSON when possible)")
    bench_parser.add_argument("--profile", help="Profile name override")
    bench_parser.add_argument("--provider", help="Override provider (e.g. stub)")
    bench_parser.add_argument("--repeat", type=int, default=3, help="Number of iterations to run (default: 3)")

    publish_parser = subparsers.add_parser("publish", help="Publish a .proml into the local registry")
    publish_parser.add_argument("path", help="Path to the .proml file")
    publish_parser.add_argument("--registry", default=REGISTRY_FILENAME, help="Registry filename")

    import_parser = subparsers.add_parser("import", help="Resolve a module from the local registry")
    import_parser.add_argument("module_id", help="Module identifier")
    import_parser.add_argument("--version", dest="version", help="Version or range (e.g. ^1.0.0)")
    import_parser.add_argument("--registry", default=REGISTRY_FILENAME, help="Registry filename")

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "init":
        return _cmd_init(args)
    if args.command == "lint":
        return _cmd_lint(args)
    if args.command == "fmt":
        return _cmd_fmt(args)
    if args.command == "test":
        return _cmd_test(args)
    if args.command == "run":
        return _cmd_run(args)
    if args.command == "bench":
        return _cmd_bench(args)
    if args.command == "publish":
        return _cmd_publish(args)
    if args.command == "import":
        return _cmd_import(args)

    parser.print_help()
    return 1


def _cmd_init(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if path.exists() and not args.force:
        print(f"Refusing to overwrite existing file: {path}")
        return 1
    path.parent.mkdir(parents=True, exist_ok=True)
    content = PROMPT_TEMPLATE.format(
        module_id=args.module_id,
        version=args.version,
        description=args.description,
    )
    path.write_text(content, encoding="utf-8")
    print(f"Created {path}")
    return 0


def _iter_proml_paths(paths: List[str]) -> List[Path]:
    collected: List[Path] = []
    for raw in paths:
        candidate = Path(raw)
        if candidate.is_dir():
            collected.extend(sorted(candidate.glob("**/*.proml")))
        elif candidate.suffix == ".proml" and candidate.exists():
            collected.append(candidate)
        else:
            print(f"Warning: skipping {candidate} (not found or not a .proml file)")
    return collected


def _parse_input_pairs(pairs: List[str]) -> Dict[str, Any]:
    inputs: Dict[str, Any] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"Invalid input pair '{pair}'. Use key=value format.")
        key, raw_value = pair.split("=", 1)
        if not key:
            raise ValueError("Input key cannot be empty.")
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError:
            value = raw_value
        inputs[key] = value
    return inputs


def _cmd_lint(args: argparse.Namespace) -> int:
    paths = _iter_proml_paths(args.paths)
    if not paths:
        print("No .proml files to lint.")
        return 1
    exit_code = 0
    for path in paths:
        try:
            parse_proml_file(path)
            print(f"OK  {path}")
        except PromlParseError as exc:
            print(f"ERR {path}: {exc}")
            exit_code = 1
    return exit_code


def _cmd_fmt(args: argparse.Namespace) -> int:
    paths = _iter_proml_paths(args.paths)
    if not paths:
        print("No .proml files to format.")
        return 1

    for path in paths:
        original = Path(path).read_text(encoding="utf-8")
        try:
            formatted = format_proml_content(original, filename=str(path))
        except PromlParseError as exc:
            print(f"ERR {path}: {exc}")
            return 1
        if formatted != original:
            Path(path).write_text(formatted, encoding="utf-8")
            print(f"FMT {path}")
        else:
            print(f"OK  {path}")
    return 0


def _cmd_test(args: argparse.Namespace) -> int:
    # Defer import to avoid circular dependency at module load time.
    import proml_test as test_runner  # type: ignore

    exit_code = 0
    for path in args.paths:
        code = test_runner.main([path])
        exit_code = exit_code or code
    return exit_code


def _cmd_run(args: argparse.Namespace) -> int:
    try:
        document = parse_proml_file(Path(args.path))
    except PromlParseError as exc:
        print(f"Parse error: {exc}")
        return 1

    try:
        inputs = _parse_input_pairs(args.input)
    except ValueError as exc:
        print(f"Input error: {exc}")
        return 1

    executor = PromptExecutor()
    try:
        result = executor.execute(
            document,
            inputs,
            profile_name=args.profile,
            override_provider=args.provider,
            use_cache=not args.no_cache,
        )
    except RuntimeError as exc:
        print(f"Run failed: {exc}")
        return 1

    for warning in result.warnings:
        print(f"Warning: {warning}")

    formatted = json.dumps(result.parsed_output, indent=2, sort_keys=True)
    print(formatted)

    cache_status = "hit" if result.from_cache else "miss"
    print(
        f"Profile {result.profile_name} ({result.provider}) | cache={cache_status} | "
        f"duration={result.duration:.3f}s | cost≤{result.estimated_cost:.4f} USD"
    )
    return 0


def _cmd_bench(args: argparse.Namespace) -> int:
    try:
        document = parse_proml_file(Path(args.path))
    except PromlParseError as exc:
        print(f"Parse error: {exc}")
        return 1

    try:
        inputs = _parse_input_pairs(args.input)
    except ValueError as exc:
        print(f"Input error: {exc}")
        return 1

    repeats = max(1, args.repeat)
    executor = PromptExecutor()
    durations: List[float] = []
    warnings: List[str] = []
    last_result: Optional[Any] = None

    for _ in range(repeats):
        try:
            result = executor.execute(
                document,
                inputs,
                profile_name=args.profile,
                override_provider=args.provider,
                use_cache=False,
            )
        except RuntimeError as exc:
            print(f"Bench failed: {exc}")
            return 1
        durations.append(result.duration)
        warnings.extend(result.warnings)
        last_result = result

    avg = statistics.mean(durations)
    min_duration = min(durations)
    max_duration = max(durations)

    if last_result is not None:
        print(
            f"Benchmarked {repeats} iteration(s) via {last_result.profile_name} ({last_result.provider})."
        )
        print(
            f"Latency: avg={avg:.3f}s min={min_duration:.3f}s max={max_duration:.3f}s"
        )
        if last_result.estimated_cost:
            print(
                f"Estimated cost per call ≤ {last_result.estimated_cost:.4f} USD (profile budget)."
            )

    for warning in sorted(set(warnings)):
        print(f"Warning: {warning}")

    return 0


def _cmd_publish(args: argparse.Namespace) -> int:
    root = Path.cwd()
    registry = Registry.load(root, args.registry)
    try:
        entry = registry.add_document(Path(args.path))
    except (ValueError, FileNotFoundError, PromlParseError) as exc:
        print(f"Publish failed: {exc}")
        return 1
    registry.save()
    print(f"Published {entry.module_id}@{entry.version} → {entry.path}")
    return 0


def _cmd_import(args: argparse.Namespace) -> int:
    root = Path.cwd()
    registry = Registry.load(root, args.registry)
    try:
        entry = registry.resolve(args.module_id, args.version)
    except KeyError as exc:
        print(f"Import failed: {exc}")
        return 1
    print(yaml.safe_dump(dataclasses.asdict(entry), sort_keys=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
