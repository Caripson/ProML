# ProML CLI

The `proml` command provides a lightweight developer experience for working with `.proml` modules.

## Commands

| Command | Description |
|---------|-------------|
| `proml init` | Scaffold a new prompt skeleton with all mandatory blocks. |
| `proml lint` | Parse and validate one or more `.proml` files. |
| `proml fmt` | Format `.proml` files using the schema-aware formatter (idempotent, preserves block comments). |
| `proml test` | Run `TEST` blocks via the reference runner. |
| `proml run` | Execute a prompt via the configured engine profile (schema & policy enforced, optional `--provider stub`). |
| `proml bench` | Run several iterations (default: 3) to gather latency statistics without using the cache. |
| `proml publish` | Add a prompt to the local registry (`proml_registry.yaml`). |
| `proml import` | Resolve a prompt version from the registry. |

Example:

```bash
python3 -m proml.cli lint test_prompts
python3 -m proml.cli publish test_prompts/sentiment_analysis.proml
python3 -m proml.cli import com.example.sentiment --version ^1.0.0
python3 -m proml.cli run test_prompts/sentiment_analysis.proml --input comment="I love this" --provider stub
```
