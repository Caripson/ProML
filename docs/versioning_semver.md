# 7. Versioning & Semver

**Core Principle:** Every prompt is a versioned artifact. Each prompt file must contain a unique ID, a semantic version (SemVer), and a status, enabling proper dependency management, traceability, and lifecycle control.

This treats prompts like software packages, bringing a critical layer of engineering discipline to prompt management.

## Why it Matters

*   **Traceability:** When you have a model's output, you can trace it back to the exact version of the prompt that produced it. This is invaluable for debugging, auditing, and analyzing results.
*   **Dependency Management:** Systems can declare dependencies on specific versions of prompts (e.g., `my-app requires prompt/summarize@^1.2.0`). This prevents breaking changes from unexpectedly affecting production systems.
*   **Lifecycle Management:** The `status` field (e.g., `draft`, `stable`, `deprecated`) communicates the prompt's readiness and intended use, helping developers choose the right one and plan for migrations.
*   **Collaboration:** Provides a shared understanding of a prompt's history and compatibility, making it easier for teams to collaborate on large prompt libraries.

## Practical Application & Examples

This information is stored in a `META` block, typically at the top of the prompt file.

### Example: A Stable Prompt

This is a well-tested, production-ready prompt.

```
PROMPT:
META:
  id: "com.mycompany.prompts.sentiment-analysis"
  version: "1.3.0"
  status: "stable"
  owner: "@ml-team"

GOAL: Classify the sentiment of a user's comment.

# ... rest of the prompt definition
```

*   **id:** A globally unique identifier. Using a reverse domain name convention is a good practice.
*   **version:** `1.3.0` follows Semantic Versioning (MAJOR.MINOR.PATCH).
    *   `MAJOR` (1): Incremented for incompatible API changes (e.g., changing the output schema).
    *   `MINOR` (3): Incremented for adding functionality in a backward-compatible manner.
    *   `PATCH` (0): Incremented for backward-compatible bug fixes.
*   **status:** `stable` indicates it's safe for production use.

### Example: A Draft Prompt

This is a new prompt still under development.

```
PROMPT:
META:
  id: "com.mycompany.prompts.entity-extraction-v2"
  version: "0.1.0-alpha.2"
  status: "draft"
  owner: "@jane.doe"

GOAL: Extract entities (people, places, organizations) from text.

# ... rest of the prompt definition
```

*   **version:** `0.1.0-alpha.2` clearly indicates this is a pre-release version and not yet stable.
*   **status:** `draft` warns other users that this prompt is experimental and may change at any time.

### How it's Used in a System

A prompt execution engine or a CI/CD pipeline can use this metadata:

1.  **Linting:** A linter can enforce that all prompts have a valid `META` block and that version numbers are incremented correctly.
2.  **Dependency Resolution:** An application might have a manifest file that specifies its prompt dependencies:
    ```json
    {
      "dependencies": {
        "sentiment_prompt": "com.mycompany.prompts.sentiment-analysis@^1.0.0",
        "extraction_prompt": "com.mycompany.prompts.entity-extraction-v2@~0.1.0"
      }
    }
    ```
    The system would then ensure it loads compatible prompt versions, preventing a `MAJOR` version bump from breaking the application.
3.  **Auditing and Logging:** When a prompt is executed, the runtime logs the full prompt ID and version (`com.mycompany.prompts.sentiment-analysis@1.3.0`). If a problem is discovered later, you know exactly which version of which prompt was responsible.
4.  **Deprecation Warnings:** If a developer tries to use a prompt marked as `deprecated`, the system can issue a warning, pointing them to the newer version.

By formalizing versioning, PromptLang enables the creation of robust, enterprise-scale systems built on top of language models.
