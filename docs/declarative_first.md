# 1. Declarative First

**Core Principle:** Describe *what* the task is, not *how* the model should reason step-by-step. Make your intent and requirements clear, but avoid hardcoding the thinking process.

This approach treats the language model as a goal-oriented engine. You provide the destination, and the model figures out the best path to get there. This leads to more robust, flexible, and future-proof prompts.

## Why it Matters

*   **Robustness:** Models change and improve. A prompt that dictates a specific reasoning path might fail with a newer, smarter model that has a better internal logic. A declarative prompt remains compatible.
*   **Simplicity:** It's easier to state a goal than to micromanage a complex reasoning process. This makes prompts shorter, clearer, and easier to maintain.
*   **Flexibility:** The model can adapt its "thinking" to the specific input it receives, rather than being locked into a single, predefined path.

## Practical Application & Examples

The key is to focus on the final output and the constraints that define success.

### Bad Example: Imperative (Step-by-Step)

This prompt tells the model exactly *how* to think.

```
PROMPT:
GOAL: Extract the key topics from the following text.

CONTEXT:
"""
The new law, which takes effect next month, will require all tech companies to disclose their data retention policies. It is expected to face legal challenges from major corporations.
"""

INSTRUCTIONS:
1. First, read the text and identify the main subject.
2. Then, identify the key action being taken.
3. Finally, identify the potential consequences.
4. Combine these three points into a list of topics.
```

This is brittle. If the model's internal reasoning is different, it might get confused or produce a suboptimal result.

### Good Example: Declarative

This prompt describes the desired output, leaving the "how" to the model.

```
PROMPT:
GOAL: Extract the key topics from the provided text.

CONTEXT:
"""
The new law, which takes effect next month, will require all tech companies to disclose their data retention policies. It is expected to face legal challenges from major corporations.
"""

OUTPUT:
- A JSON array of strings.
- Each string should be a distinct topic mentioned in the text.
- Topics should be concise and high-level.

EXAMPLE_OUTPUT:
["New Tech Law", "Data Retention Policies", "Legal Challenges"]
```

Here, we've defined the *what* (key topics) and the *shape* of the output (a JSON array of strings) without dictating the cognitive process. The model is free to use its own advanced understanding to achieve the goal, making the prompt more resilient and effective.
