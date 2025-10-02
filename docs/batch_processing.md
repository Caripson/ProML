# 26. Batch Processing

**Core Principle:** A prompt should be runnable on a large dataset of inputs in a single, efficient operation. PromptLang should provide a standard way to define batch execution, allowing the runtime to optimize calls to the underlying model.

This is crucial for data processing, analysis, and evaluation tasks where a prompt needs to be applied to thousands or millions of items.

## Why it Matters

*   **Efficiency:** Instead of a slow, sequential loop of one-by-one API calls, a batch-aware runtime can process inputs in parallel, manage rate limits intelligently, and potentially use model-specific batching endpoints that offer better performance.
*   **Cost Reduction:** Some model providers offer discounts for batch jobs or have specific APIs (like the OpenAI Batch API) that are cheaper for large, asynchronous tasks.
*   **Simplicity:** The developer only needs to specify the prompt and the dataset. The runtime handles the complexity of execution, parallelization, and error handling.
*   **Scalability:** Provides a clear path to scale a prompt from a single-input test case to a massive production dataset.

## Practical Application & Examples

Batch processing would not be a block within a prompt, but rather a mode of the **PromptLang execution engine**. The engine would take a prompt and a dataset as input.

### Example: Running a Batch Job from the Command Line

Imagine you have a CSV file with thousands of customer reviews, and you want to classify the sentiment of each one using a prompt.

**File: `/data/reviews.csv`**
```csv
comment_id,text
101,"I love this product, it works perfectly!"
102,"The app keeps crashing, I am very frustrated."
103,"The delivery was on time."
...
```

**File: `/prompts/sentiment.prompt`**
```
PROMPT:
GOAL: Classify the sentiment of the user's comment.

INPUTS:
  # The input name 'text' matches the column header in the CSV
  text: string

OUTPUT_SCHEMA:
{
  "type": "object",
  "properties": {
    "sentiment": { "enum": ["positive", "negative", "neutral"] }
  }
}
```

A developer could then initiate the batch job with a command:

```bash
# The command to run a prompt over a dataset
promptlang-run --prompt /prompts/sentiment.prompt \
               --dataset /data/reviews.csv \
               --output /results/sentiments.jsonl \
               --input-mapping '{"comment": "text"}' # Maps prompt input to dataset column
```

**How it Works:**

1.  **`--prompt`:** Specifies the prompt to be used.
2.  **`--dataset`:** Points to the source data file (CSV, JSONL, etc.).
3.  **`--output`:** Specifies where to write the results.
4.  **`--input-mapping`:** A crucial argument that tells the runner how to map columns from the dataset to the prompt's `INPUTS`. In this case, it maps the `text` column from `reviews.csv` to the `comment` input variable of the `sentiment.prompt`.

**The `promptlang-run` engine would then:**

a.  Read the dataset.
b.  For each row, create an input object for the prompt (e.g., `{ "comment": "I love this product..." }`).
c.  Group these inputs into optimal batches (e.g., 100 at a time).
d.  Send these batches to the model provider, potentially in parallel, while respecting rate limits.
e.  Collect the results from the model.
f.  Combine the original input data with the model's output and write it to the output file `/results/sentiments.jsonl`.

**Output File: `/results/sentiments.jsonl`**
```json
{"comment_id": 101, "text": "I love this product...", "output": {"sentiment": "positive"}}
{"comment_id": 102, "text": "The app keeps crashing...", "output": {"sentiment": "negative"}}
{"comment_id": 103, "text": "The delivery was on time.", "output": {"sentiment": "neutral"}}
...
```

By standardizing the concept of batch processing, PromptLang provides a powerful, scalable way to apply language models to large-scale data analysis tasks, moving beyond single, interactive executions.
