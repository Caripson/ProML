# 25. Caching

**Core Principle:** Identical prompt executions should not be wastefully repeated. The ProML runtime should support caching, allowing it to store and instantly retrieve responses for previously seen requests, saving significant time and cost.

This principle treats prompt execution like a pure function: for the same input, you should get the same output.

## Why it Matters

*   **Cost Reduction:** Caching is one of the most effective ways to reduce API costs. For high-volume applications with repetitive requests (e.g., classifying common user queries), caching can eliminate the vast majority of LLM calls.
*   **Latency Improvement:** Retrieving a result from a local or distributed cache is orders of magnitude faster than making a round-trip API call to a large language model. This leads to a much better user experience.
*   **Reduced Load on Services:** Caching reduces the number of requests sent to the underlying model provider, which can help avoid rate limiting and reduce overall system load.
*   **Consistency:** Caching ensures that users receive the exact same answer for the same query, which can be desirable for informational or navigational queries.

## Practical Application & Examples

Caching strategies would be defined in a `CACHE` block within a prompt's `PROFILE`. This allows for fine-grained control over how caching is applied.

### Example: Simple Time-Based Caching

This prompt for translating common UI elements uses a simple cache that stores results for 24 hours.

```
PROMPT:
GOAL: Translate a short UI string to a target language.

INPUTS:
  ui_string: string
  language: string

PROFILE:
  default:
    engine: "claude-3-haiku-20240307"
    # This prompt is highly cacheable
    CACHE:
      strategy: "simple"
      ttl: "24h" # Time-to-live: how long to keep an item in the cache
      scope: "shared" # 'shared' means all users share the same cache
```

**How it Works:**

1.  The first time the prompt is run with `ui_string: "Hello, World!"` and `language: "Spanish"`, the runtime sends the request to the model.
2.  It receives the response `{"translation": "Hola, Mundo!"}`.
3.  Before returning the response, the runtime stores it in a cache (e.g., Redis, Memcached, or a local dictionary). The cache key would be a hash of the prompt ID, version, and the specific input values (`"Hello, World!"`, `"Spanish"`).
4.  The next time the *exact same request* comes in within 24 hours, the runtime finds the entry in the cache and returns the stored response immediately, without ever calling the language model.
5.  After 24 hours (`ttl`), the cache entry expires and the next request will go to the model again.

### Example: User-Specific Caching

For prompts that are personalized, the cache scope can be restricted.

```
PROMPT:
GOAL: Summarize the user's recent activity.

INPUTS:
  user_id: string
  user_activity_log: string

PROFILE:
  default:
    engine: "gpt-4-turbo-2024-04-09"
    CACHE:
      strategy: "simple"
      ttl: "1h"
      scope: "user" # Cache results on a per-user basis
```

**How it Works:**

*   The `scope: "user"` flag tells the runtime to include the `user_id` (or another designated user identifier) in the cache key.
*   When a request for `user_id: "alice"` is cached, it is stored separately from a request for `user_id: "bob"`.
*   This prevents Bob from accidentally seeing a cached summary of Alice's activity, ensuring data privacy while still providing performance benefits for individual users who might re-run the same prompt.

By providing a declarative way to control caching, ProML allows developers to easily optimize their applications for performance and cost without writing complex caching logic in their application code.
