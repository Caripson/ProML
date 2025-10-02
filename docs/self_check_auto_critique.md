# 17. Self-Check & Auto-Critique

**Core Principle:** A prompt can instruct a model to review and validate its own output before finalizing it. This internal feedback loop helps the model catch and correct its own mistakes, improving the quality and reliability of the final response.

This is a powerful technique that can be implemented as a simple instruction or as a more formal step in a [Pipeline](./pipelines_steps.md).

## Why it Matters

*   **Improved Accuracy:** The model can double-check its work against the prompt's original requirements, correcting factual errors, logical inconsistencies, or formatting mistakes.
*   **Better Adherence to Constraints:** By explicitly asking the model to verify its output against the stated rules, you significantly increase the chances that it will follow them.
*   **Reduced Hallucinations:** Forcing the model to "show its work" or verify claims against a source text can reduce the likelihood of it inventing facts.
*   **More Robust Outputs:** It acts as a final line of defense against simple errors that might otherwise require a separate validation step or a re-run.

## Practical Application & Examples

Self-critique can range from a simple instruction to a formal, multi-step process.

### Example: Simple In-Prompt Instruction

This is the easiest way to implement self-check. You add an instruction at the end of your prompt telling the model to review its work.

```
PROMPT:
GOAL: Generate a JSON object representing a user, based on the input text.

CONTEXT:
"""
John Doe is a 35-year-old software engineer from New York.
"""

OUTPUT_SCHEMA:
{
  "type": "object",
  "properties": {
    "name": { "type": "string" },
    "age": { "type": "number" },
    "city": { "type": "string" }
  },
  "required": ["name", "age", "city"]
}

CONSTRAINTS:
  - The output MUST be a valid JSON object that conforms to the schema.
  - Before you output the final JSON, take a moment to review your work. Check that all fields are present and that the types are correct (e.g., age must be a number, not a string). If you find any errors, correct them before providing the final output.
```

**How it Works:**

By adding that final paragraph to the `CONSTRAINTS`, you are priming the model to perform an internal check. Modern models are capable of following this meta-instruction. They will generate the JSON, then internally "look" at it, compare it to the rules, and fix it if necessary, all within a single generation pass. For instance, if it first generated `"age": "35"` (a string), the self-check instruction encourages it to correct this to `"age": 35` (a number) before giving the final answer.

### Example: Formal Auto-Critique using a Pipeline

For more critical tasks, a formal, multi-step pipeline provides a more robust implementation of auto-critique. This is often called a "Reflect and Revise" pattern.

```
PROMPT:
PIPELINE:
  - name: "draft"
    prompt: "/prompts/generate_legal_clause.prompt"
    input: { context: "{{INPUT.context}}" }

  - name: "critique"
    prompt: "/prompts/critique_legal_clause.prompt"
    input: {
      clause: "{{STEPS.draft.output.clause}}",
      requirements: "The clause must be unambiguous, mention the governing law of California, and have a term of 3 years."
    }

  - name: "revise"
    prompt: "/prompts/revise_legal_clause.prompt"
    input: {
      original_clause: "{{STEPS.draft.output.clause}}",
      critique: "{{STEPS.critique.output.feedback}}"
    }

INPUTS:
  context: string
```

**How it Works:**

1.  **Draft:** The first prompt generates an initial version of a legal clause. This draft might be imperfect.
2.  **Critique:** The second prompt's sole purpose is to act as a critic. It receives the draft and a list of explicit requirements. Its goal is to find flaws. It might output: `{"feedback": "The clause is well-written but fails to mention the governing law."}`.
3.  **Revise:** The third prompt receives the original draft and the critique. Its goal is to generate a final, improved version that incorporates the feedback.

This structured process is more explicit and reliable than a simple instruction. It forces the system to dedicate a full generation pass to finding and correcting errors, leading to significantly higher quality outputs for complex tasks.

Whether implemented as a simple instruction or a formal pipeline, self-critique is a powerful technique for making language models more reliable and accurate.
