# 16. Fallback & Degradation

**Core Principle:** Systems should be resilient. A prompt can define a strategy for graceful degradation, specifying fallback models or simpler, canned responses to use if the primary execution fails, exceeds its budget, or takes too long.

This ensures that the user always gets a response, even if it's not the ideal one, preventing system failures and improving the user experience.

## Why it Matters

*   **Resilience:** Protects against API outages or model failures. If your primary model provider is down, the system can automatically switch to a backup.
*   **Performance Guarantees:** Ensures that your application meets its latency requirements. If the powerful primary model is too slow, the system can fall back to a faster, simpler one.
*   **Cost Control:** Prevents budget overruns. If a prompt is about to exceed its cost limit, it can be aborted and a cheaper fallback can be used instead.
*   **User Experience:** Avoids showing the user a hard error message. A degraded response (e.g., "I can't generate a full summary right now, but I can extract the key topics.") is better than no response at all.

## Practical Application & Examples

Fallback strategies are typically defined within the `PROFILE` block, as they are closely tied to execution parameters like latency and cost budgets.

### Example: Falling Back to a Cheaper Model

This prompt uses a powerful model by default but will fall back to a cheaper, faster model if the primary one fails or is too slow.

```
PROMPT:
GOAL: Generate a detailed, multi-paragraph summary of the provided article.

INPUTS:
  article: string

PROFILE:
  default:
    engine: "gpt-4-turbo-2024-04-09"
    latency_budget: "5s"
    fallback:
      - on: ["timeout", "api_error"]
        strategy: "rerun_with_profile"
        profile: "fast_fallback"

  fast_fallback:
    engine: "claude-3-haiku-20240307"
    # This profile has a different, simpler goal
    GOAL: "Generate a three-bullet-point summary of the provided article."
```

**How it Works:**

1.  The runtime first attempts to execute the prompt using the `default` profile with GPT-4.
2.  It starts a timer. If the API call to GPT-4 takes longer than 5 seconds (`latency_budget`), the runtime aborts the request.
3.  The `fallback` rule is triggered by the `timeout` event.
4.  The `strategy` is `rerun_with_profile`, so the runtime re-executes the entire prompt, but this time it uses the `fast_fallback` profile.
5.  This new execution uses the much faster Haiku model. Crucially, it also uses a **different `GOAL`** defined within the fallback profile. Instead of trying to generate a detailed summary (which might be too slow for any model), it now attempts a much simpler task: creating a bullet-point summary.

This ensures the user gets a useful, albeit less detailed, response quickly, rather than waiting a long time or getting an error.

### Example: Degrading to a Canned Response

Sometimes, the safest fallback is not another model, but a simple, predetermined answer.

```
PROMPT:
GOAL: Answer a complex user question.

PROFILE:
  default:
    engine: "claude-3-opus-20240229"
    cost_budget: 0.25 // Max $0.25 per run
    fallback:
      - on: ["cost_limit"]
        strategy: "return_static_response"
        response: {
          "error": "Query too complex",
          "message": "I am unable to process this request as it is too complex. Please try simplifying your question."
        }
```

**How it Works:**

1.  The prompt is run with the powerful Opus model.
2.  The runtime monitors the token usage. If the number of tokens generated would cause the `cost_budget` of $0.25 to be exceeded, it stops the generation.
3.  The `fallback` rule is triggered by the `cost_limit` event.
4.  The `strategy` is `return_static_response`, so the runtime doesn't call another model. Instead, it immediately returns the predefined JSON `response`.

This provides a clear and immediate feedback loop to the user, preventing runaway costs and managing expectations.

By defining fallback and degradation paths, ProML allows you to build robust, production-ready applications that can handle the inherent unpredictability of working with large language models.