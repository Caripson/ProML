# 2. Strict I/O

**Core Principle:** All output must follow a validatable schema. This makes the prompt's output predictable, machine-readable, and reliable.

By enforcing a strict output contract, you transform the language model from a creative text generator into a dependable component in an automated system.

## Why it Matters

*   **Reliability:** Guarantees that the output will have a consistent structure, preventing errors in downstream applications that consume the data.
*   **Automation:** Enables seamless chaining of prompts. The output of one prompt can be safely fed as the input to another, or used by other software, without manual intervention.
*   **Validation:** Allows for automated testing and validation. You can programmatically check if the model's output conforms to the expected schema.
*   **Clarity:** Defining an output schema forces you to think clearly about the exact data you need, which often improves the quality of the prompt itself.

## Practical Application & Examples

JSON Schema is the standard for defining output structure in PromptLang, but other formats could be used.

### Bad Example: Unstructured Output

This prompt leaves the output format open to interpretation.

```
PROMPT:
GOAL: Summarize the user's request and extract their contact information.

INPUT:
"""
Hi, I need to reset my password. My username is @testuser and my email is test@example.com. Please help!
"""

OUTPUT:
- A summary of the user's problem.
- The user's contact details.
```

The model might produce:
`The user wants to reset their password. You can reach them at test@example.com.`

Or it might produce:
`Problem: Password Reset. Contact: test@example.com (@testuser)`

This ambiguity makes it impossible to reliably parse the output in an automated workflow.

### Good Example: Schema-Enforced Output

This prompt uses a JSON Schema to define the exact output structure.

```
PROMPT:
GOAL: Summarize the user's request and extract their contact information.

INPUT:
"""
Hi, I need to reset my password. My username is @testuser and my email is test@example.com. Please help!
"""

OUTPUT:
- A JSON object that validates against the following schema.

OUTPUT_SCHEMA:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "summary": {
      "type": "string",
      "description": "A brief, one-sentence summary of the user's request."
    },
    "contact": {
      "type": "object",
      "properties": {
        "username": {
          "type": "string",
          "description": "The user's @username, if provided."
        },
        "email": {
          "type": "string",
          "format": "email",
          "description": "The user's email address."
        }
      },
      "required": ["email"]
    }
  },
  "required": ["summary", "contact"]
}
```

This guarantees a predictable JSON output that can be easily parsed and validated:

```json
{
  "summary": "The user needs to reset their password.",
  "contact": {
    "username": "@testuser",
    "email": "test@example.com"
  }
}
```

This structured output can be directly used by another function, an API call, or a subsequent prompt without any fragile string parsing.
