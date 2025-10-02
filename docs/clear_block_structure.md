# 8. Clear Block Structure

**Core Principle:** A prompt's components should be organized into a standardized, logical sequence of blocks. This makes prompts easier to read, write, and parse for both humans and machines.

PromptLang enforces a consistent structure, which acts as a mental scaffold for the prompt author and a predictable format for tooling.

## Why it Matters

*   **Readability:** A fixed order means you always know where to find a specific piece of information (e.g., the output schema, the style guide, the tests).
*   **Maintainability:** When everyone on a team organizes prompts the same way, it's much easier to understand and modify someone else's work.
*   **Tooling:** A consistent structure is essential for tools like linters, compilers, and IDE extensions that need to parse and understand the prompt file.
*   **Cognitive Load:** It reduces the mental effort required to write a prompt. Instead of a blank page, you have a clear template to fill in, guiding you through the process of creating a high-quality prompt.

## The Standard Block Order

PromptLang recommends the following order. While not all blocks are required for every prompt, they should appear in this sequence if present.

1.  `META`: Versioning, ID, status, owner. (Not in the original list, but essential)
2.  `GOAL`: The primary objective of the prompt.
3.  `INPUTS`: Declaration of input variables.
4.  `CONTEXT`: Background information or data the model needs.
5.  `CONSTRAINTS`: Rules the output must follow.
6.  `STYLE`: Guidelines for tone, persona, and formatting.
7.  `TOOLS`: Definitions of tools the model can use.
8.  `OUTPUT`: The desired output format and schema.
9.  `PROFILE`: Execution parameters (model, temperature, etc.).
10. `POLICIES`: Security, safety, and ethical rules.
11. `TEST`/`EVAL`: Unit tests and evaluation datasets.

## Practical Application & Example

A linter or IDE extension would validate this structure.

### Bad Example: Disorganized Prompt

```
PROMPT:
OUTPUT:
- A JSON object with a "summary" field.

GOAL: Summarize the article.

PROFILE:
  default:
    engine: "claude-3-haiku-20240307"

INPUT:
- article: string

STYLE:
- Write in a neutral, journalistic tone.
```

This prompt is hard to read. The `OUTPUT` is defined before the `GOAL`, and the `PROFILE` is mixed in with the core logic. A human has to hunt for information, and a machine would struggle to parse it reliably.

### Good Example: Correct Block Structure

```
PROMPT:
# (META block would be here)

GOAL: Summarize the provided article in a neutral tone.

INPUTS:
  article: string

STYLE:
  - Tone: Neutral, journalistic.
  - Complexity: Accessible to a general audience.

OUTPUT:
  OUTPUT_SCHEMA:
    {
      "type": "object",
      "properties": {
        "summary": { "type": "string" }
      },
      "required": ["summary"]
    }

PROFILE:
  default:
    engine: "claude-3-haiku-20240307"
    temperature: 0.4

TEST:
  - name: "Handles short article"
    input: { article: "This is a short test article." }
    assert:
      - type: "json_schema"
      - type: "not_equals"
        path: "$.summary"
        value: ""
```

This version is clean, logical, and predictable.

*   You start with the high-level **goal**.
*   You see the required **inputs**.
*   You understand the desired **style** and **output** format.
*   You can check the **execution profile** for performance details.
*   Finally, you can review the **tests** to understand the expected behavior.

A linter would approve this structure. If a developer tried to place the `STYLE` block after the `OUTPUT` block, the linter would flag it with a warning and suggest the correct ordering, enforcing consistency across the entire project.
