# 6. Testability & Verification

**Core Principle:** Prompts must be testable. PromptLang provides a framework for defining unit tests and evaluation datasets (fixtures) directly within the prompt file, enabling automated testing and quality assurance.

This treats prompts as code, applying the same principles of continuous integration and regression testing that are standard in software engineering.

## Why it Matters

*   **Regression Prevention:** When you modify a prompt or update a model, you can run tests to ensure that its behavior hasn't broken for known edge cases.
*   **Quality Assurance:** Provides a systematic way to measure and enforce the quality of a prompt's output.
*   **Development Aid:** Writing tests helps clarify the prompt's requirements and can guide its development (a form of Test-Driven Development for prompts).
*   **CI/CD Integration:** Test suites can be run automatically in a CI/CD pipeline, preventing a faulty prompt from being deployed to production.

## Practical Application & Examples

PromptLang supports two main forms of testing defined in a `TEST` or `EVAL` block: **Unit Tests** and **Evaluation Sets (Fixtures)**.

### Example: Unit Tests

Unit tests are simple, inline tests that check for specific input/output behavior. They are useful for verifying core logic and handling edge cases.

```
PROMPT:
GOAL: Extract the ISO 8601 date from a given string.

INPUT:
- text: string

OUTPUT_SCHEMA:
{
  "type": "object",
  "properties": {
    "date": { "type": "string", "format": "date" }
  }
}

TEST:
  - name: "Handles standard date format"
    input: { text: "The meeting is on 2024-08-15." }
    assert:
      - type: "json_schema"
      - type: "equals"
        path: "$.date"
        value: "2024-08-15"

  - name: "Handles month name format"
    input: { text: "Please join us on September 5th, 2025." }
    assert:
      - type: "equals"
        path: "$.date"
        value: "2025-09-05"

  - name: "Returns null for no date"
    input: { text: "There is no date here." }
    assert:
      - type: "equals"
        path: "$.date"
        value: null
```

In this example:
1.  Each test case has a `name`, an `input` object, and a set of `assert` conditions.
2.  The `assert` block defines what must be true about the output.
    *   `json_schema`: Asserts that the output validates against the `OUTPUT_SCHEMA`.
    *   `equals`: Asserts that a specific field in the JSON output (using JSONPath) is equal to a given value.

A test runner can execute these tests and report which ones pass or fail.

### Example: Evaluation Sets (Fixtures)

For more comprehensive testing, you can link to an external file containing a larger set of test cases. This is useful for regression testing on real-world data.

**File: `/prompts/sentiment.prompt`**
```
PROMPT:
GOAL: Classify the sentiment of the user's comment.

INPUT:
- comment: string

OUTPUT_SCHEMA:
{
  "type": "object",
  "properties": {
    "sentiment": { "enum": ["positive", "negative", "neutral"] }
  }
}

EVAL:
  - name: "Customer feedback regression suite"
    fixtures: "/evals/customer_feedback.jsonl"
```

**File: `/evals/customer_feedback.jsonl`** (JSON Lines format)
```json
{"input": {"comment": "I love this product, it works perfectly!"}, "expected": {"sentiment": "positive"}}
{"input": {"comment": "The app keeps crashing, I am very frustrated."}, "expected": {"sentiment": "negative"}}
{"input": {"comment": "The delivery was on time."}, "expected": {"sentiment": "neutral"}}
```

The `EVAL` block points to this dataset. A test runner would then execute the prompt for each entry in `customer_feedback.jsonl` and compare the actual output to the `expected` output, generating a report with accuracy metrics.

By integrating testing directly into the prompt's definition, PromptLang makes it easy to build reliable, high-quality, and maintainable AI systems.
