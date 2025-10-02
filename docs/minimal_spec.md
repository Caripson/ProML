# Minimal ProML Specification

This document captures the first converged version of the Prompt Markup Language (ProML) document format. It defines the required blocks, their ordering, and the structural invariants that every `.proml` file must respect.

## Document Layout

A valid ProML document SHALL contain the following top-level blocks in order:

1. `META`
2. `INPUT`
3. `OUTPUT`
4. `POLICY` (optional)
5. `PIPELINE` (optional)
6. `TEST` (optional)

The `META` and `POLICY` blocks are immutable at runtime; only the `INPUT` values vary between executions.

Blank lines MAY appear between blocks. Lines beginning with `#` are treated as comments and ignored by the parser.

## Formal Grammar (EBNF)

The grammar below uses an indentation-aware `yaml_block` non-terminal to denote an indented YAML mapping. All terminals are case-sensitive.

```
document        = ws*, meta_block, input_block, output_block,
                  policy_block?, pipeline_block?, test_block?, ws*, EOF ;

meta_block      = "META", ":", newline, yaml_block(meta_mapping) ;
input_block     = "INPUT", ":", newline, yaml_block(input_mapping) ;
output_block    = "OUTPUT", ":", newline, yaml_block(output_mapping) ;
policy_block    = "POLICY", ":", newline, yaml_block(policy_mapping) ;
pipeline_block  = "PIPELINE", ":", newline, yaml_block(pipeline_mapping) ;
test_block      = "TEST", ":", newline, yaml_block(test_sequence) ;

yaml_block(X)   = INDENT, X, DEDENT ;

meta_mapping        = meta_entry, { newline, meta_entry } ;
meta_entry          = indent_line ;  (* parsed as YAML key/value *)

input_mapping       = input_entry, { newline, input_entry } ;
input_entry         = indent_line ;

output_mapping      = output_entry, { newline, output_entry } ;
output_entry        = indent_line ;

policy_mapping      = policy_entry, { newline, policy_entry } ;
policy_entry        = indent_line ;

pipeline_mapping    = pipeline_entry, { newline, pipeline_entry } ;
pipeline_entry      = indent_line ;

test_sequence       = "-", ws+, test_case, { newline, "-", ws+, test_case } ;
test_case           = yaml_inline_or_block ;

yaml_inline_or_block = indent_line | (newline, deeper_yaml_block) ;

indent_line         = INDENTED_TEXT ;
deep_yaml_block     = yaml_block(arbitrary_yaml) ;
arbitrary_yaml      = indent_line, { newline, indent_line } ;

ws              = " " | "\t" ;
newline         = "\r\n" | "\n" ;
```

> **Note:** `yaml_block` content is interpreted by the reference parser using a YAML 1.2 compliant loader. The grammar enforces the presence and ordering of blocks; YAML parsing enforces key/value structure inside each block.

## Block Semantics

### META

The `META` block defines immutable, descriptive metadata for the prompt module.

Required keys:

- `id` (string): unique identifier (`reverse.dns` recommended).
- `version` (string): semantic version (`MAJOR.MINOR.PATCH`).
- `repro` (string): determinism tier, one of `"strict" | "loose"`.

Optional keys:

- `description` (string)
- `owners` (sequence of strings)
- `tags` (sequence of strings)
- `profiles` (mapping): engine-specific execution profiles.

Each entry in `profiles` is a mapping with the following shape:

```yaml
profiles:
  default:
    provider: "openai"          # one of openai|anthropic|local|ollama|stub|...
    model: "gpt-4.1-mini"
    temperature: 0.2            # 0.0 – 2.0
    max_output_tokens: 512      # upper bound for decoder output tokens
    cost_budget: 0.02           # optional per-call USD budget ceiling
    cache:
      strategy: "simple"        # implementation-defined strategy
      scope: "shared"           # shared|local
      ttl: 15m                  # duration string or integer seconds
```

If multiple profiles are defined, the runtime defaults to the `default` profile unless another profile name is explicitly chosen at invocation time. Cache TTL values accept human-friendly suffixes (`s`, `m`, `h`, `d`).

When `repro: "strict"` the following constraints apply:

- `temperature` MUST be ≤ 0.3.
- `max_output_tokens` MUST be ≤ 1024.
- `cost_budget` MUST be provided, ensuring a hard cap per invocation.

The runtime MUST NOT mutate any values from `META`.

### INPUT

Defines a typed, declarative interface for runtime inputs.

Each entry is a mapping from input name to a specification object:

```yaml
INPUT:
  comment:
    type: string
    description: >-
      The end-user text to classify.
    required: true
    default: null
```

Recognised fields:

- `type` (string): primary type name (`string`, `integer`, `number`, `boolean`, `object`, `array`).
- `description` (string): human-readable description.
- `required` (boolean, default `true`).
- `default` (any YAML scalar/object): applied when `required` is `false` and no explicit value is provided.

Additional keys are reserved for future extensions and MUST be ignored by the parser with a warning.

### OUTPUT

Declares strict output constraints. The block is immutable and applies to every execution.

Required fields:

```yaml
OUTPUT:
  json_schema:
    $id: "schema:com.example.sentiment:output"
    version: "2024-05-01"
    schema:
      type: object
      required: [sentiment]
      properties:
        sentiment:
          enum: [positive, negative, neutral]
  regex: null
  grammar: null
```

- `json_schema` (mapping):
  - `$id` (URI string) identifying the schema.
  - `version` (string) describing schema release.
  - `schema` (mapping): embedded JSON Schema (draft 2020-12 subset).
- `regex` (string | null): optional ECMAScript-compatible regular expression that the entire model output MUST match when provided.
- `grammar` (mapping | null): optional context-free grammar expressed in Extended Backus–Naur form for constrained decoding.

### POLICY

Optional block describing policy layers that guard prompt execution.

Example:

```yaml
POLICY:
  imports:
    - id: policy.global.pii
      version: ">=1.2.0"
  local:
    safety_checks:
      - ensure: no_personal_data
        message: "Strip PII before returning output."
```

Semantics:

- `imports` (sequence): references to registered policy modules, resolved through the registry.
- `local` (mapping): inline policy rules evaluated prior to returning the final output. Policy evaluation failures MUST abort execution.

`POLICY` is immutable and evaluated by the runtime before returning an answer. The helper `proml.policy.PolicyEvaluator` inspects local safety checks and can emit warnings or block responses when invariants fail.

### PIPELINE

Optional declarative DAG describing multi-step execution. Each step is immutable.

```yaml
PIPELINE:
  steps:
    - id: detect_language
      uses: module.com.detect_language@^1.0.0
      inputs:
        text: $input.comment
      outputs:
        language: $.language
    - id: classify_sentiment
      uses: module.com.sentiment@^2.1.0
      inputs:
        text: $input.comment
        language: $step.detect_language.language
      expects:
        sentiment: string
  edges:
    - from: detect_language
      to: classify_sentiment
```

Semantics:

- `steps` (sequence): order-independent definitions of DAG nodes.
  - `id` (string): unique within the document.
  - `uses` (string): reference to another ProML module + semver range.
  - `inputs` (mapping): bindings from parameter name to selectors (input, step outputs, constants).
  - `outputs` (mapping): declares the shape of produced values.
  - `expects` (mapping): optional runtime assertions on the step output types.
- `edges` (sequence): adjacency list describing dependencies. The DAG MUST be acyclic.

Selectors follow the syntax:

- `$input.<name>`: resolve from the `INPUT` block instance values.
- `$step.<step-id>.<field>`: resolve from outputs of previous steps.
- Scalar literals: YAML scalars interpreted as constants.

Use `proml.pipeline.PipelineGraph` to obtain a stable topological order and dependency sets, keeping execution declarative and side-effect free.

### TEST

Optional block containing executable test cases. Tests are immutable and run against the reference runner.

Structure:

```yaml
TEST:
  - name: "classifies positive comments"
    input:
      comment: "I love this product!"
    expect:
      schema: true
      fields:
        sentiment: equals: positive
      regex: null
    steps:
      - name: "primary"
        mock_output:
          sentiment: positive
        assert:
          - type: equals
            path: $.sentiment
            value: positive
```

Recognised keys:

- `name` (string): human-readable identifier.
- `input` (mapping): overrides for runtime inputs.
- `expect` (mapping): high-level expectations (`schema`, `regex`, `fields`).
- `steps` (sequence): optional multi-step tests validating caching or stateful behaviour.
- `mock_output` (mapping): stubbed model output for the step.
- `assert` (sequence): list of assertions. Supported assertion types will be extended in the test runner upgrade phase (`equals`, `schema`, `matches_regex`, `was_cached`, etc.).

## AST Expectations

The reference parser will generate an abstract syntax tree with the following top-level shape:

```json
{
  "type": "Document",
  "meta": { ... },
  "inputs": [ ... ],
  "output": { ... },
  "policy": { ... },
  "pipeline": { ... },
  "tests": [ ... ]
}
```

- Missing optional blocks are represented as `null` or empty collections.
- Each node retains source span metadata (`start_line`, `end_line`) to support linting, formatting, and IDE tooling.

## Determinism and Runtime Contract

- Prompts tagged with `repro: "strict"` MUST set low-temperature engine profiles and pass schema validation without retries.
- `POLICY` imports are resolved and executed before model output is released. Failures block the response.
- The runtime MUST reject documents that deviate from this spec (e.g., missing mandatory blocks, malformed YAML, invalid semver).

This minimal spec will evolve, but the parser and tooling implemented in subsequent tasks SHALL treat this document as the authoritative baseline.
