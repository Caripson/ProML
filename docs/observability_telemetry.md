# 14. Observability & Telemetry

**Core Principle:** Every prompt execution should be an observable event. The PromptLang runtime must automatically capture and structure key telemetry data, such as cost, latency, tool calls, and errors, making it easy to monitor, debug, and optimize prompt performance.

This brings standard DevOps and MLOps practices to prompt engineering, treating prompt performance as a critical metric to be tracked.

## Why it Matters

*   **Performance Monitoring:** Tracking latency allows you to identify and fix slow prompts, ensuring a good user experience.
*   **Cost Management:** Monitoring token usage and cost per prompt run is essential for managing budgets and preventing unexpected expenses.
*   **Debugging:** Detailed logs, including the exact prompt version, inputs, and any errors, are invaluable for diagnosing and fixing problems.
*   **Optimization & A/B Testing:** Structured telemetry is the foundation for systematically improving prompts. You can A/B test two different versions of a prompt, and use the telemetry data to determine which one performs better in terms of cost, latency, and output quality.

## Practical Application & Examples

Observability is not something you typically define in the prompt file itself. Rather, it's a feature of the **PromptLang runtime environment**. The runtime automatically wraps every prompt execution and emits a structured log event.

### Example: Standard Telemetry Event

When you execute a prompt, the runtime should generate a log (e.g., in JSON format) that looks something like this:

```json
{
  "timestamp": "2024-10-26T10:00:05Z",
  "event_type": "prompt_execution",
  "prompt_id": "com.mycompany.prompts.sentiment-analysis@1.3.0",
  "execution_id": "exec_abc123",
  "profile_used": "default",
  "status": "success",

  "metrics": {
    "latency_ms": 850,
    "cost_usd": 0.0025,
    "tokens": {
      "input": 520,
      "output": 15
    }
  },

  "model": {
    "engine": "gpt-4-turbo-2024-04-09",
    "temperature": 0.2
  },

  "trace": {
    "input": {
      "comment": "I am incredibly happy with the service!"
    },
    "output": {
      "sentiment": "positive"
    },
    "errors": null
  },

  "metadata": {
    "customer_id": "cust_xyz789",
    "environment": "production"
  }
}
```

**Key Fields Explained:**

*   `prompt_id`: The unique ID and version of the prompt that was run. Crucial for traceability.
*   `metrics.latency_ms`: Total time taken for the execution.
*   `metrics.cost_usd`: The calculated cost for this specific run.
*   `metrics.tokens`: The number of input and output tokens, which is used to calculate cost and monitor complexity.
*   `trace`: Contains the actual inputs, outputs, and any errors that occurred. This is vital for debugging but may be sanitized or omitted in production logs to protect privacy.
*   `metadata`: Custom tags that allow you to slice and dice the data (e.g., filter by customer, environment, or A/B test group).

### Example: A/B Testing

Observability is the key to effective A/B testing. Imagine you want to see if a new version of a prompt is better than the old one.

1.  **Deployment:** You configure your application to send 90% of traffic to `prompt@1.3.0` (the control) and 10% of traffic to `prompt@1.4.0` (the challenger). You add a `version_group` tag to your telemetry metadata (`"version_group": "challenger"`).

2.  **Data Collection:** You let the system run and collect thousands of the telemetry events described above.

3.  **Analysis:** You can now run queries on your logging platform to compare the two versions:

    *   `AVG(latency_ms) WHERE prompt_id = 'prompt@1.3.0'` vs. `AVG(latency_ms) WHERE prompt_id = 'prompt@1.4.0'`
    *   `SUM(cost_usd) WHERE prompt_id = 'prompt@1.3.0'` vs. `SUM(cost_usd) WHERE prompt_id = 'prompt@1.4.0'`
    *   You can also perform more advanced analysis on the quality of the outputs.

Based on this data, you can make a confident, evidence-based decision on whether to roll out the new version to all users.

By making every prompt run an observable event, PromptLang turns prompt engineering from a craft into a measurable and optimizable engineering discipline.
