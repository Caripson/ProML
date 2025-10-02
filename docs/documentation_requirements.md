# 21. Documentation Requirements

**Core Principle:** A prompt is not complete without documentation. Every prompt must include metadata that describes its purpose, provides clear examples, and lists any known limitations. A changelog should also be maintained within the prompt file.

This ensures that prompts are easy to understand, use, and maintain, even for developers who were not their original authors.

## Why it Matters

*   **Discoverability & Usability:** Good documentation makes it easy for other developers to find the prompt they need and understand how to use it correctly.
*   **Maintainability:** When an author returns to a prompt months later, the documentation serves as a crucial reminder of its purpose, design choices, and edge cases.
*   **Trust & Transparency:** Listing known limitations builds trust. It helps users understand when a prompt is suitable for a task and when it might not be, preventing misuse and managing expectations.
*   **Collaboration:** Documentation is a form of communication. It allows teams to build a shared understanding of their prompt library.

## Practical Application & Examples

ProML encourages embedding documentation directly into the prompt file using comments and dedicated metadata blocks. This keeps the documentation and the code in sync.

### Example: A Well-Documented Prompt

This example shows how documentation is woven into the fabric of a prompt file.

```
# ===================================================================
# PROMPT: com.mycompany.prompts.text-summarizer
# ===================================================================

# -------------------------------------------------------------------
# METADATA & GOVERNANCE
# -------------------------------------------------------------------
META:
  id: "com.mycompany.prompts.text-summarizer"
  version: "1.5.2"
  status: "stable"
  owner: "@content-team"

  # --- Documentation ---
  description: "Generates a concise, three-bullet-point summary of a given text. Designed for articles up to 2000 words."
  tags: ["summarization", "text-generation", "content"]
  examples:
    - input: { text: "... (a long article) ..." }
      output: { summary: ["First point.", "Second point.", "Third point."] }
  known_limitations:
    - "May not perform well on highly technical or scientific papers."
    - "Does not currently support languages other than English."
    - "Summaries of texts over 3000 words may lose significant nuance."

# -------------------------------------------------------------------
# CHANGELOG
# -------------------------------------------------------------------
# 1.5.2 (2024-10-26): Fixed bug where empty text caused an error.
# 1.5.1 (2024-10-20): Improved handling of lists in the source text.
# 1.5.0 (2024-09-15): Increased summary length to three bullet points.
# 1.4.0 (2024-08-01): Migrated to claude-3-sonnet for better quality.
# 1.0.0 (2024-05-10): Initial release.
# -------------------------------------------------------------------

GOAL: Generate a concise, three-bullet-point summary of the provided text.

# ... (rest of the prompt definition)
```

**Key Documentation Components:**

1.  **Header Comments & Changelog:** The file starts with a clear header and a detailed, reverse-chronological changelog. This immediately tells a reader the prompt's history and what has changed recently.

2.  **`META.description`:** A concise, one-sentence summary of what the prompt does. This is the most important piece of documentation, as it's often displayed in search results in a prompt registry.

3.  **`META.tags`:** A list of keywords that make the prompt discoverable. A developer could search for `"summarization"` and find this prompt.

4.  **`META.examples`:** Provides a concrete example of the expected input and output. This is often faster to understand than reading the full prompt logic.

5.  **`META.known_limitations`:** This is crucial for setting expectations. It honestly communicates what the prompt *cannot* or *should not* be used for. This prevents other developers from using it in an inappropriate context and then being surprised by a poor result.

### How This is Used

*   **IDE Integration:** An IDE extension could parse this metadata and display it in a formatted way when a developer hovers over the prompt file.
*   **Prompt Registry UI:** A central web UI for all prompts could use this data to generate a beautiful, searchable documentation page for each prompt, complete with its description, tags, examples, and limitations.
*   **Automated Linting:** A linter can enforce documentation requirements. For example, it could throw an error if a prompt with `status: "stable"` is missing the `description` or `known_limitations` fields, thus enforcing a documentation standard before prompts are published.

By making documentation a required, first-class citizen, ProML ensures that the prompt library remains a valuable, understandable, and maintainable asset as it grows.
