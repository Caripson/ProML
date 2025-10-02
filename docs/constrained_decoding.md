# Constrained Decoding Framework

ProML supports constrained decoding to ensure that model outputs respect the declarative invariants declared in the `OUTPUT` block. Constraints can be enforced proactively during generation (decoder-time) or validated post-hoc.

## Constraint Engine Overview

The reference implementation exposes a `ConstraintEngine` located in `proml/constraints.py`. The engine centralises three categories of constraints:

- **Regex constraints** (`OUTPUT.regex`): The model output must match the supplied regular expression.
- **JSON Schema constraints** (`OUTPUT.json_schema`): The structured output must satisfy the embedded JSON Schema fragment.
- **Grammar constraints** (`OUTPUT.grammar`): A placeholder for context-free grammars used by specialised decoders (e.g. Guidance, llguidance).

```python
from proml.constraints import ConstraintEngine
engine = ConstraintEngine(document.output)
errors = engine.validate_all(raw_text, parsed_json)
if errors:
    raise RuntimeError(errors)
```

`validate_all` aggregates schema, regex, and grammar checks. Individual helper methods (`validate_schema`, `validate_regex`, `validate_grammar`) are also available so that tooling can emit granular diagnostics.

## Decoder Adapters

The engine can attempt decoder-time enforcement through a `GenerationAdapter` protocol:

```python
from proml.constraints import GenerationAdapter

class GuidanceAdapter:
    def supports_regex(self) -> bool: ...
    def apply_regex(self, pattern: str) -> None: ...
    def supports_json_schema(self) -> bool: ...
    def apply_json_schema(self, schema: dict) -> None: ...
    def supports_grammar(self) -> bool: ...
    def apply_grammar(self, grammar: dict) -> None: ...
```

Adapters are responsible for wiring constraints into the target runtime (OpenAI function calling, Anthropic tool choice, llguidance grammars, etc.). The engine’s `configure` method returns warnings when a constraint cannot be applied up-front, allowing the caller to decide whether to continue with post-hoc validation or abort early.

### Guidance

`proml.adapters.guidance_adapter.GuidanceGenerationAdapter` implements the protocol for the [Guidance](https://github.com/microsoft/guidance) library. When Guidance is available the adapter collects regex/grammar/schema constraints and exposes them via `gen_kwargs()` so that template authors can write::

    adapter = GuidanceGenerationAdapter()
    warnings = engine.configure(adapter)
    program += adapter.gen_call()

If Guidance is not installed the adapter raises a descriptive `RuntimeError`, signalling that the caller should fall back to post-hoc validation.

## Grammar Constraints

The grammar pathway is intentionally conservative: when a grammar is present but no compatible adapter is configured, validation produces an actionable warning. Future iterations will add native support for emitting PEG/CFG grammars to adapters such as Guidance and llguidance.

## Integration with the Test Runner

`proml_test.py` now instantiates a `ConstraintEngine` for each document. Schema validation is mandatory for every step, regex validation is optional and runs when a pattern is provided, and individual assertions (`type: schema`, `type: matches_regex`) reuse the engine helpers to stay aligned with the spec.

This architecture separates constraint definition from execution, making it possible to plug in new enforcement strategies without changing the ProML parser or the authored prompts.
