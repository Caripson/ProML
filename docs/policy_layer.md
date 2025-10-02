# 5. Policy Layer (Security & Ethics)

**Core Principle:** Prompts must be able to declare and enforce rules related to security, safety, and ethics. This provides a built-in mechanism for responsible AI development.

A policy is a rule that the model's output must adhere to. These can be imported from a central repository or defined locally within a prompt.

## Why it Matters

*   **Safety & Security:** Automatically prevents the model from generating harmful, inappropriate, or sensitive content. This is a critical guardrail.
*   **Privacy:** Enforces rules like PII (Personally Identifiable Information) masking, protecting user data and helping with compliance (e.g., GDPR).
*   **Compliance:** Ensures that model outputs meet legal or organizational requirements, such as including disclaimers or requiring citations for factual claims.
*   **Consistency:** Guarantees that all prompts adhere to the same set of ethical and safety standards, reducing risk and simplifying audits.

## Practical Application & Examples

Policies are defined in a `POLICIES` block. They can be simple flags, or more complex rules with parameters. Policies can often be imported from a central, managed source.

### Example: Enforcing Privacy and Disclaimers

Imagine a prompt that summarizes medical articles for a general audience. It's crucial that it doesn't leak personal data and that it includes a medical disclaimer.

**File: `/policies/standard_safety.prompt`**
```
POLICIES:
  # This policy instructs the runtime to find and replace PII.
  - pii_masking: true

  # This policy forbids the model from generating content on a list of topics.
  - forbidden_topics: ["hate_speech", "self_harm", "graphic_violence"]
```

**File: `/prompts/medical_summary.prompt`**
```
@import "/policies/standard_safety.prompt"

GOAL: Summarize the provided medical study for a non-technical audience.

INPUT:
- study_text: string

OUTPUT:
- A one-paragraph summary.

POLICIES:
  # Local policy: ensure the output includes a specific disclaimer.
  - must_include:
      text: "This summary is for informational purposes only and is not a substitute for professional medical advice."
      position: "append"

  # Local policy: require the model to cite the source of its claims.
  - require_citation: {
      source: "{{INPUT.study_text}}"
    }
```

### How it Works

1.  **Imported Policies:** The prompt first imports the `standard_safety.prompt` file. The PromptLang runtime now knows it must apply `pii_masking` and check for `forbidden_topics`.
2.  **Local Policies:** The prompt then adds its own specific policies.
    *   `must_include`: The runtime will check the model's final output. If the disclaimer is missing, it will either reject the output or automatically append it.
    *   `require_citation`: This is a more complex policy. It might instruct the model to generate a citation, or it could be a post-processing step where another model call verifies that the summary's claims are supported by the source text.

This layered approach allows for a powerful and flexible system:

*   **Central Governance:** An organization can define a set of mandatory base policies (`standard_safety.prompt`) that all developers must use.
*   **Local Customization:** Individual prompt authors can add specific, context-aware policies (`must_include`, `require_citation`) as needed.

This makes building safe and ethical AI systems a systematic and enforceable part of the development process, rather than an afterthought.
