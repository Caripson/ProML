# 23. Reproducibility & Determinism

**Core Principle:** A prompt execution should be reproducible. By specifying an execution profile and a random seed, you should be able to get the exact same output for the same input, especially when using the same model version.

This is fundamental for reliable testing, debugging, and auditing. While large language models have inherent randomness, PromptLang provides the mechanisms to control it.

## Why it Matters

*   **Reliable Testing:** When a [Unit Test](./testability_verification.md) fails, you need to be sure it failed because of a logic error, not random chance. Reproducibility ensures that your tests are deterministic.
*   **Debugging:** If a prompt produces a faulty output in production, you need to be able to reproduce that exact output in a development environment to diagnose the problem.
*   **Auditing & Compliance:** For many applications (e.g., in finance or healthcare), it's a requirement to be able to demonstrate exactly why a particular output was generated. This is only possible if the generation process is reproducible.
*   **Change Management:** When you revise a prompt, you can run it with the same seed as the previous version to see a direct, deterministic comparison of the outputs, making it easier to evaluate the impact of your change.

## Practical Application & Examples

Reproducibility is achieved by controlling the parameters defined in the `PROFILE` block. The two most important parameters are the `engine` version and the `seed`.

### Example: A Reproducible Prompt Profile

This prompt for generating creative text includes parameters to ensure it can be run deterministically.

```
PROMPT:
GOAL: Write a short, creative story about a robot who discovers music.

PROFILE:
  default:
    # Lock to a specific model version. "gpt-4-turbo" is an alias and can change,
    # but the versioned name is static.
    engine: "gpt-4-turbo-2024-04-09"
    temperature: 0.8

    # The seed is the key to deterministic output.
    seed: 12345

  # A profile for creative, non-deterministic generation
  creative_mode:
    engine: "gpt-4-turbo-2024-04-09"
    temperature: 0.9
    seed: null # Explicitly setting seed to null allows for randomness
```

**How it Works:**

1.  **`engine`:** The prompt specifies the exact version of the model (`gpt-4-turbo-2024-04-09`). This is crucial because different model versions can produce different results even with the same seed.
2.  **`seed`:** The `seed` is an integer that initializes the model's random number generator. When the `temperature` is greater than 0, the model makes random choices about which words to pick. The `seed` ensures that it makes the *same* random choices every time.

*   If you run this prompt with the `default` profile 100 times, you will get the **exact same story** every single time.
*   If you change the `seed` to `54321`, you will get a *different* story, but it will be the *same* different story every time you run it with that new seed.
*   If you run it with the `creative_mode` profile, where `seed` is `null`, you will get a new, unpredictable story on each run.

### How it's Used in Practice

*   **During Testing:** A CI/CD pipeline would always run tests with a fixed seed. This ensures that a test failure is a real signal of a problem, not a random fluctuation.
    ```bash
    # In a CI/CD script
    promptlang-test --profile="default" --seed=999
    ```
*   **During Debugging:** When a production system logs an error, it should also log the `seed` and `engine` version that were used. A developer can then copy these values into their local environment to reproduce the problematic output exactly.
    ```json
    // From a production error log
    {
      "prompt_id": "story-generator@1.0.0",
      "error": "Output contained forbidden words.",
      "execution_params": {
        "engine": "gpt-4-turbo-2024-04-09",
        "seed": 8675309
      }
    }
    ```
    A developer can now use `seed: 8675309` to debug the issue locally.

By providing mechanisms to control determinism, PromptLang makes working with inherently stochastic models a more predictable and reliable engineering discipline.
