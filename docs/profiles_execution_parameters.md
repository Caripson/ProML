# 4. Profiles & Execution Parameters

**Core Principle:** A prompt should declare its execution requirements, such as the model, temperature, and resource budgets. This allows for predictable, repeatable, and fine-tuned model behavior.

By embedding these parameters directly into the prompt file, you version control not just the prompt text, but also the configuration under which it was designed to run.

## Why it Matters

*   **Reproducibility:** Guarantees that a prompt will produce similar results over time by locking it to a specific model and settings. This is crucial for testing and debugging.
*   **Performance Tuning:** Allows you to optimize prompts for specific use cases. A creative task might need a high temperature, while a factual extraction task needs a low one.
*   **Cost & Latency Control:** You can set explicit budgets for how much a prompt is allowed to cost or how long it can take, preventing runaway generation and ensuring a good user experience.
*   **Flexibility:** Profiles allow you to define different sets of parameters for different environments (e.g., a `cheap` profile for development, a `fast` profile for production, and a `powerful` profile for batch processing).

## Practical Application & Examples

Execution parameters are defined in a `PROFILE` block. You can define multiple named profiles, and one will be chosen at runtime.

### Example: A Single Default Profile

This prompt is designed to run with a specific model and a low temperature to ensure factual, non-creative answers.

```
PROMPT:
GOAL: Extract the name of the CEO from the provided article.

CONTEXT:
"""
[Article text here...]
"""

OUTPUT_SCHEMA:
{
  "type": "object",
  "properties": {
    "ceo_name": { "type": "string" }
  }
}

PROFILE:
  default:
    engine: "gpt-4-turbo-2024-04-09"
    temperature: 0.1
    max_tokens: 50
```

### Example: Multiple Profiles for Different Needs

This prompt for summarizing articles has three different profiles for different scenarios.

```
PROMPT:
GOAL: Provide a summary of the given article.

INPUT:
- article_text: string

OUTPUT:
- A one-paragraph summary.

PROFILE:
  # The standard profile: balances cost and quality
  default:
    engine: "claude-3-sonnet-20240229"
    temperature: 0.5
    max_tokens: 500
    cost_budget: 0.05 // Max $0.05 per run

  # A faster, cheaper profile for quick previews
  fast:
    engine: "claude-3-haiku-20240307"
    temperature: 0.7
    max_tokens: 300
    latency_budget: "2s" // Must respond within 2 seconds

  # A high-quality profile for deep analysis
  powerful:
    engine: "gpt-4-turbo-2024-04-09"
    temperature: 0.3
    max_tokens: 2000
```

When executing this prompt, the user or system could specify which profile to use:

*   `run_prompt("summarize.prompt", profile="default")` would use Claude 3 Sonnet.
*   `run_prompt("summarize.prompt", profile="fast")` would use the cheaper and faster Haiku model.
*   `run_prompt("summarize.prompt", profile="powerful")` would use GPT-4 for the highest quality summary, assuming the cost and latency are acceptable.

This provides enormous flexibility, allowing the same prompt logic to be used in different contexts without modification.
