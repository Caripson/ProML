# 13. Assertions & Validation

**Core Principle:** While a [Strict I/O](./strict_io.md) schema defines the *shape* of the output, assertions define its *semantic correctness*. Assertions are rules and invariance requirements that go beyond simple type checking, enabling a deeper level of validation.

Assertions can be used as both pre-conditions (checking inputs) and post-conditions (checking outputs), ensuring that the prompt operates within expected boundaries.

## Why it Matters

*   **Semantic Correctness:** Catches errors that a schema can't. A schema can verify that an `email` field is a string, but an assertion can verify that it actually contains an `@` symbol.
*   **Business Logic:** Allows you to embed critical business rules directly into the prompt (e.g., `order_total must be greater than 0`).
*   **Guardrails:** Prevents the model from producing outputs that are structurally valid but logically flawed (e.g., a summary that is longer than the original text).
*   **Enhanced Testing:** Provides a more powerful mechanism for [Testability & Verification](./testability_verification.md), allowing for richer, more meaningful tests.

## Practical Application & Examples

Assertions are defined in a `CONSTRAINTS` block for outputs or within the `INPUTS` block for inputs. They are also used heavily in the `assert` block of `TEST` cases.

### Example: Output Assertions in a `CONSTRAINTS` Block

This prompt generates a short biography and uses assertions to enforce quality standards.

```
PROMPT:
GOAL: Generate a short, one-paragraph biography for a given person.

INPUTS:
  person_name: string
  achievements: array

OUTPUT_SCHEMA:
{
  "type": "object",
  "properties": {
    "biography": { "type": "string" }
  }
}

CONSTRAINTS:
  - path: "$.biography"
    type: "string_length"
    max: 500 // The biography must be under 500 characters

  - path: "$.biography"
    type: "contains_all"
    values: "{{INPUT.achievements}}" // Must mention all achievements

  - path: "$.biography"
    type: "not_contains"
    values: ["in conclusion", "to summarize"] // Avoid clichéd phrases
```

**How it Works:**

After the model generates an output, but before it is returned, the PromptLang runtime validates it against these constraints:
1.  It checks if the `biography` string is longer than 500 characters.
2.  It verifies that all the strings from the input `achievements` array are present in the generated `biography`.
3.  It ensures that the biography doesn't contain lazy, clichéd phrases.

If any of these assertions fail, the runtime can take action, such as automatically re-running the prompt with feedback, returning a default error, or logging the failure.

### Example: Input Assertions

Assertions can also validate inputs before the prompt is even sent to the model.

```
PROMPT:
GOAL: Compare two products.

INPUTS:
  product_a: string
  product_b: string {
    assert:
      - type: "not_equals"
        value: "{{INPUT.product_a}}" // Ensure products are different
        message: "Product A and Product B cannot be the same."
  }

# ...
```

Here, the assertion in the `INPUTS` block ensures that the prompt is never run with two identical products, preventing a nonsensical request from being sent to the model and wasting resources.

### Common Assertion Types

PromptLang supports a rich set of assertion types, including:

*   **Equality:** `equals`, `not_equals`
*   **Numeric:** `greater_than`, `less_than`, `in_range`
*   **String:** `string_length`, `matches_regex`, `contains`, `not_contains`
*   **Array:** `array_length`, `contains_all`, `contains_any`, `is_unique`
*   **Logical:** `all_of`, `any_of`, `not` (for combining other assertions)

By combining a structural schema with semantic assertions, PromptLang provides a comprehensive framework for ensuring the quality, correctness, and safety of model outputs.
