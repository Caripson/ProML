# ProML Registry

The local registry (`proml_registry.yaml`) keeps track of published ProML modules and their versions. Each entry stores:

- `module_id`: the globally unique identifier.
- `version`: semantic version of the module.
- `path`: filesystem location of the `.proml` file.
- `sha256`: integrity hash for reproducibility.
- `repro`: the declared determinism tier (`strict`/`loose`).
- `metadata`: owners and tags mirrored from the `META` block.

## Publishing

Use the CLI to publish modules into the registry:

```bash
python3 -m proml.cli publish test_prompts/sentiment_analysis.proml
```

The registry enforces unique versions per module and records the hash of the file at publish time.

## Resolving Modules

Resolve a module/version pair via the registry:

```bash
python3 -m proml.cli import com.example.sentiment --version ^1.0.0
```

Version constraints support exact matches (`1.0.0`), caret ranges (`^1.0.0`), and basic comparison operators (`>=1.2.0`). The command returns the registry metadata, including the path that can be imported into another project.
