# ProML (Prompt Markup Language)

*Author: Johan Caripson*

ProML is a structured markup language for Large Language Model prompts. The project now ships a full toolchain: a formal specification, a production-ready parser and runtime, a CLI, a local registry, a constrained-decoding adapter layer, and developer ergonomics such as formatting, documentation, and editor support.

## ✨ Highlights

- **Formal spec & docs** — `docs/` contains the language guide, minimal grammar, and 29 governing principles for prompt engineering.
- **Reference parser** — `proml/parser.py` builds an AST, validates block order, semver, repro tiers, policies, pipelines, and test definitions.
- **Strict I/O test runner** — `proml_test.py` parses `.proml` files, enforces JSON Schema/regex/grammar constraints, and runs caching-aware assertions.
- **Constraint engine** — pluggable validators for regex, JSON Schema, and CFG grammar; ships with a Guidance-compatible adapter for decoder-time enforcement.
- **Engine profiles & caching** — structured metadata for model, temperature, token limits, and cost budgets with hash-based cache keys and adapter registry (OpenAI, Anthropic, Local, Ollama, Stub).
- **CLI & registry** — `proml` command (init, lint, fmt, test, run, bench, publish, import) plus a YAML registry for semver-aware module discovery.
- **Developer experience** — schema-aware formatter, VS Code extension skeleton, MkDocs plugin, and example prompts under `test_prompts/`.

## 🚀 Quick Start

Clone the repo and ensure dependencies are installed (Python 3.10+ recommended). The CLI runs directly via `python3 -m proml.cli`.

Install locally in editable mode:

```bash
python3 -m pip install -e .
```

For full tooling (docs, tests, Guidance adapter) use the dev extras:

```bash
python3 -m pip install -e .[dev]
```

### Format & Lint

```bash
python3 -m proml.cli fmt test_prompts/sentiment_analysis.proml
python3 -m proml.cli lint test_prompts
```

The formatter is schema-aware and preserves inline comments thanks to `ruamel.yaml`.

### Run Tests

```bash
python3 proml_test.py test_prompts/sentiment_analysis.proml
python3 proml_test.py test_prompts/caching_example.proml
```

### Execute a Prompt

```bash
python3 -m proml.cli run test_prompts/sentiment_analysis.proml \
  --input comment="I love this product" --provider stub
```

Use `--provider stub` for offline evaluation; registered adapters handle OpenAI, Anthropic, Local backends, and more.

### Registry Workflow

```bash
python3 -m proml.cli publish test_prompts/sentiment_analysis.proml
python3 -m proml.cli import com.example.sentiment --version ^1.0.0
```

Published modules are tracked in `proml_registry.yaml` with integrity hashes and reproducibility metadata.

## 🧰 Developer Tooling

- **Formatting & comments:** schema-aware formatter retains inline annotations across blocks.
- **Guidance adapter:** `proml.adapters.GuidanceGenerationAdapter` lets you enforce regex/grammar/schema constraints inside Guidance programs.
- **MkDocs plugin:** `mkdocs_proml_plugin.py` renders `.proml` modules into documentation pages automatically.
- **VS Code extension:** `tools/vscode/` provides syntax highlighting and snippets for `.proml` files.

## 📚 Documentation

Browse the specification and principles in the [docs index](./docs/index.md). The minimal spec includes a formal EBNF grammar, block invariants, determinism tiers, policy semantics, pipelines, and testing requirements.

## 🔬 Tests

The repository includes targeted tests for the parser, formatter, and adapters under `tests/`. Run them with:

```bash
PYTHONPATH=. python3 tests/test_formatter.py
PYTHONPATH=. python3 tests/test_guidance_adapter.py
```

## 🌐 Publishing Docs

The project is preconfigured for MkDocs out of the box. After installing `mkdocs` and `mkdocs-material`, run `mkdocs serve` to preview the docs site locally. A Hugo configuration is also included for alternative static site generation.

## 🙌 Contributing & Next Ideas

Issues and PRs are welcome! Impactful directions include:

- Package the CLI as a distributable (`pip install proml`).
- Build richer adapters (Guidance grammar, OpenAI function-calling integration).
- Expand formatter lint rules (comment style, schema normalization hints).
- Publish example modules and tutorials demonstrating real-world prompt workflows.

Have fun building reproducible, testable LLM workflows with ProML.
