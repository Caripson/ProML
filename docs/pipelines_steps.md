# 12. Pipelines & Steps

**Core Principle:** Complex tasks can be broken down into a pipeline of smaller, sequential steps. Each step can be a call to a language model (a prompt) or a call to a tool, allowing for sophisticated, multi-stage reasoning and workflows.

This brings the power of workflow orchestration directly into the prompt language, enabling patterns like generation, evaluation, and revision.

## Why it Matters

*   **Modularity:** Breaks down a complex problem into simpler, manageable parts. Each step has a clear purpose, making the overall workflow easier to design, debug, and maintain.
*   **Improved Quality:** Mimics human problem-solving. Instead of trying to get a perfect answer in one shot, you can generate a draft, critique it, and then revise it, leading to higher-quality results.
*   **State Management:** A pipeline can manage state, passing the output of one step as the input to the next, enabling a coherent chain of thought.
*   **Efficiency:** Allows for using different models or tools for different steps. You could use a fast, cheap model for an initial draft and a more powerful, expensive model for a final review.

## Practical Application & Examples

A pipeline is defined as an ordered list of steps in a `PIPELINE` block. This block typically replaces the simple `GOAL` block for more complex prompts.

### Example: A Simple Generate-and-Translate Pipeline

This pipeline first generates a marketing slogan in English and then translates it into French.

```
PROMPT:
PIPELINE:
  - name: "generate_slogan"
    prompt: "/prompts/slogan_generator.proml"
    input: {
      product: "{{INPUT.product}}"
    }

  - name: "translate_to_french"
    prompt: "/prompts/translator.proml"
    input: {
      text: "{{STEPS.generate_slogan.output.slogan}}",
      target_language: "French"
    }

INPUTS:
  product: string

OUTPUT:
  - The final translated slogan from the 'translate_to_french' step.
```

**How it Works:**

1.  The pipeline takes an initial `INPUT` (`product`).
2.  **Step 1 (`generate_slogan`):** It calls the `slogan_generator.prompt`, passing the product name. The output of this step (e.g., `{ "slogan": "The future of speed." }`) is stored internally.
3.  **Step 2 (`translate_to_french`):** It calls the `translator.prompt`. The `input.text` for this step is dynamically populated from the output of the previous step using the `{{STEPS.generate_slogan.output.slogan}}` variable.
4.  The final output of the entire pipeline is the result of the last step.

### Example: A Reflect-and-Revise Pipeline

This is a more advanced pattern where the AI critiques its own work.

```
PROMPT:
PIPELINE:
  - name: "draft_summary"
    prompt: "/prompts/basic_summarizer.proml"
    input: { article: "{{INPUT.article}}" }

  - name: "critique_summary"
    prompt: "/prompts/summary_critic.proml"
    input: {
      summary: "{{STEPS.draft_summary.output.summary}}",
      article: "{{INPUT.article}}"
    }

  - name: "revise_summary"
    prompt: "/prompts/summary_reviser.proml"
    input: {
      original_summary: "{{STEPS.draft_summary.output.summary}}",
      critique: "{{STEPS.critique_summary.output.critique}}",
      article: "{{INPUT.article}}"
    }

INPUTS:
  article: string

OUTPUT:
  - The revised summary from the 'revise_summary' step.
```

**How it Works:**

1.  **`draft_summary`:** Generates an initial, potentially flawed summary.
2.  **`critique_summary`:** A different prompt is used to evaluate the draft. Its goal is to find flaws, such as inaccuracies, missing key points, or poor phrasing. Its output might be: `{ "critique": "The summary misses the key financial data mentioned in the last paragraph." }`.
3.  **`revise_summary`:** A third prompt receives the original summary, the critique, and the source article. Its goal is to generate a new, improved summary that addresses the feedback from the critique step.

This structured, multi-step process allows the AI to perform more complex and nuanced tasks, producing results that are far superior to what a single prompt could achieve.
