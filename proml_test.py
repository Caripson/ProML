"""Proof-of-concept ProML test runner with strict I/O validation."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from proml.constraints import ConstraintEngine
from proml.policy import PolicyEvaluator
from proml.runtime import PromptCache, build_cache_key, select_profile
from proml.parser import (
    PromlDocument,
    PromlParseError,
    TestAssertion,
    TestCase,
    TestStep,
    parse_proml_file,
)


def get_from_dict(data: Any, path: str) -> Any:
    """Access a nested value using a simplified JSONPath (`$.field.sub`)."""
    if not path.startswith("$."):
        return None
    parts = path[2:].split(".")
    current = data
    for part in parts:
        if isinstance(current, list):
            try:
                index = int(part)
            except ValueError:
                return None
            if index < 0 or index >= len(current):
                return None
            current = current[index]
        elif isinstance(current, dict):
            if part not in current:
                return None
            current = current[part]
        else:
            return None
    return current


def ensure_json_output(payload: Any, step: TestStep) -> Tuple[str, Any]:
    """Return (raw_json_string, parsed_value)."""
    if isinstance(payload, str):
        raw = payload
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AssertionError(
                f"Step '{step.name or 'anonymous'}' mock_output is not valid JSON: {exc}"
            ) from exc
    else:
        parsed = payload
        try:
            raw = json.dumps(parsed, separators=(",", ":"), sort_keys=True)
        except (TypeError, ValueError) as exc:
            raise AssertionError(
                f"Step '{step.name or 'anonymous'}' mock_output is not JSON-serialisable: {exc}"
            ) from exc
    return raw, parsed


def run_tests(document: PromlDocument) -> int:
    if not document.tests:
        print("No TEST block found in the prompt file.")
        return 0

    total = 0
    passed = 0
    engine = ConstraintEngine(document.output)
    shared_cache = PromptCache()

    policy_warnings = PolicyEvaluator(document.policy).validate()
    for warning in policy_warnings:
        print(f"Policy warning: {warning.message}")

    default_inputs = {
        field.name: field.default
        for field in document.inputs
        if not field.required and field.default is not None
    }

    for case in document.tests:
        total += 1
        print(f"Running test: \"{case.name}\"")
        case_passed = _run_test_case(document, case, default_inputs, engine, shared_cache)
        if case_passed:
            passed += 1
        print("-" * 20)

    failed = total - passed
    print("\n--- Test Summary ---")
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("--------------------")
    return 0 if failed == 0 else 1


def _run_test_case(
    document: PromlDocument,
    case: TestCase,
    default_inputs: Dict[str, Any],
    engine: ConstraintEngine,
    shared_cache: PromptCache,
) -> bool:
    resolved_input = dict(default_inputs)
    resolved_input.update(case.input)
    profile = select_profile(document.meta)
    if profile and profile.cache and profile.cache.scope == "shared":
        cache_manager = shared_cache
    else:
        cache_manager = PromptCache()
    case_failed = False

    for step in case.steps:
        step_name = step.name or case.name
        if len(case.steps) > 1:
            print(f"  -> Step: {step_name}")

        combined_input = dict(resolved_input)
        combined_input.update(step.input)
        prompt_signature = f"{document.meta.identifier}:{case.name}"
        cache_key = build_cache_key(document.meta, profile, prompt_signature, combined_input)

        cached_value = cache_manager.fetch(cache_key)
        is_cache_hit = cached_value is not None
        if not is_cache_hit:
            cache_manager.store(cache_key, step.mock_output, profile.cache if profile else None)

        try:
            raw_output, parsed_output = ensure_json_output(step.mock_output, step)
        except AssertionError as exc:
            print(f"    ! ERROR: {exc}")
            case_failed = True
            break

        schema_errors = engine.validate_schema(parsed_output)
        if schema_errors:
            print("    - Schema validation: FAIL")
            for error in schema_errors:
                print(f"      - {error}")
            case_failed = True
            break
        else:
            print("    - Schema validation: PASS")

        regex_errors = engine.validate_regex(raw_output)
        if regex_errors:
            print("    - Regex constraint: FAIL")
            for error in regex_errors:
                print(f"      - {error}")
            case_failed = True
            break
        elif document.output.regex:
            print("    - Regex constraint: PASS")

        context = {
            "is_cache_hit": is_cache_hit,
            "raw_output": raw_output,
            "parsed_output": parsed_output,
            "input": combined_input,
            "cache_key": cache_key,
            "profile": profile,
        }

        if not _run_assertions(step.assertions, parsed_output, raw_output, context, engine):
            case_failed = True
            break

    if case_failed:
        print(f"Result: FAIL ({case.name})")
        return False
    print(f"Result: PASS ({case.name})")
    return True


def _run_assertions(
    assertions: List[TestAssertion],
    parsed_output: Any,
    raw_output: str,
    context: Dict[str, Any],
    engine: ConstraintEngine,
) -> bool:
    all_passed = True
    for assertion in assertions:
        assertion_type = assertion.type
        if assertion_type == "equals":
            path = assertion.path
            if not path:
                print("    - ASSERT [equals]: FAIL (path missing)")
                all_passed = False
                continue
            actual = get_from_dict(parsed_output, path)
            expected = assertion.value
            if actual == expected:
                print(f"    - ASSERT [equals] {path}: PASS")
            else:
                print(f"    - ASSERT [equals] {path}: FAIL")
                print(f"      - Expected: {expected!r}")
                print(f"      - Got: {actual!r}")
                all_passed = False
        elif assertion_type == "schema":
            errors = engine.validate_schema(parsed_output)
            if errors:
                print("    - ASSERT [schema]: FAIL")
                for error in errors:
                    print(f"      - {error}")
                all_passed = False
            else:
                print("    - ASSERT [schema]: PASS")
        elif assertion_type == "matches_regex":
            pattern = assertion.value
            if not isinstance(pattern, str):
                print("    - ASSERT [matches_regex]: FAIL (pattern missing)")
                all_passed = False
                continue
            if re.fullmatch(pattern, raw_output):
                print(f"    - ASSERT [matches_regex]: PASS ({pattern!r})")
            else:
                print(f"    - ASSERT [matches_regex]: FAIL ({pattern!r})")
                print(f"      - Output: {raw_output!r}")
                all_passed = False
        elif assertion_type == "was_cached":
            expected = bool(assertion.value)
            actual = bool(context.get("is_cache_hit"))
            if actual == expected:
                print(f"    - ASSERT [was_cached]: PASS (was_cached={actual})")
            else:
                print("    - ASSERT [was_cached]: FAIL")
                print(f"      - Expected: {expected}")
                print(f"      - Got: {actual}")
                all_passed = False
        else:
            print(f"    - ASSERT [{assertion_type}]: SKIPPED (unsupported type)")
    return all_passed


def main(argv: Iterable[str]) -> int:
    parser = argparse.ArgumentParser(description="Run ProML test cases")
    parser.add_argument("path", help="Path to the .proml file")
    args = parser.parse_args(list(argv))

    target = Path(args.path)
    if not target.exists():
        print(f"Error: File not found at {target}")
        return 1

    try:
        document = parse_proml_file(target)
    except PromlParseError as exc:
        print(f"Parse error: {exc}")
        return 1

    return run_tests(document)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
