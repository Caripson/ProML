# ProML VS Code Extension (Skeleton)

This folder contains the scaffolding for a lightweight VS Code extension that adds:

- Syntax highlighting for `.proml` files (delegating to YAML with custom block headers).
- Snippets for the core block structure and engine profiles.
- Basic language configuration (comments, bracket matching).

To develop locally:

1. Install dependencies with `npm install`.
2. Run `vsce package` to build the extension bundle or launch the VS Code extension host with `F5`.

Future enhancements:

- Schema-aware autocomplete for `OUTPUT.json_schema`.
- Hover documentation sourced from the registry.
- Diagnostics backed by the ProML parser (via language server).
