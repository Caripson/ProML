# 10. Import & Inheritance

**Core Principle:** Prompts can import and build upon other prompts, inheriting their properties and overriding them where necessary. This enables a powerful, hierarchical, and DRY (Don't Repeat Yourself) approach to prompt management.

This is a more advanced form of [Composition & Modules](./composition_modules.md), focusing on how imported blocks are merged and customized.

## Why it Matters

*   **Hierarchy & Specialization:** You can create a generic base prompt (e.g., a base `character` prompt) and then create more specific versions (e.g., `helpful_assistant`, `sarcastic_teenager`) that inherit from it and modify its behavior.
*   **Scalability:** Manages complexity in large prompt libraries. Instead of duplicating code, you create a clear inheritance chain.
*   **Maintainability:** Changes to a base prompt automatically propagate to all the prompts that inherit from it, simplifying updates.
*   **Flexibility:** Allows for fine-grained control. You can inherit a complex set of rules and then override just one or two specific instructions to suit a new context.

## Practical Application & Examples

ProML uses an `@import` statement. When one prompt imports another, its blocks are merged. By default, local blocks override imported blocks.

### Example: Inheriting and Overriding a Style

Let's define a base style for a chatbot.

**File: `/styles/base_chatbot.proml`**
```
STYLE:
  - persona: "A helpful AI assistant."
  - tone: "Friendly and informative."
  - language: "Use clear, simple English."
  - safety: "Do not engage with harmful requests."
```

Now, we can create a new prompt for a more specialized chatbot that handles technical support. It will inherit the base style but override the `persona`.

**File: `/prompts/tech_support_bot.proml`**
```
@import "/styles/base_chatbot.proml"

GOAL: Help users troubleshoot technical issues with our software.

INPUTS:
  user_question: string

# The local STYLE block is merged with the imported one.
STYLE:
  # This overrides the imported 'persona'
  - persona: "A patient and knowledgeable technical support specialist."
  # This adds a new instruction
  - formatting: "Use code blocks for commands and error messages."

OUTPUT:
  - A string containing the support response.
```

**Resulting Merged Style:**

When the `tech_support_bot.proml` is executed, the runtime engine effectively sees the following merged `STYLE` block:

```
STYLE:
  - persona: "A patient and knowledgeable technical support specialist." // Overridden
  - tone: "Friendly and informative."                               // Inherited
  - language: "Use clear, simple English."                          // Inherited
  - safety: "Do not engage with harmful requests."                  // Inherited
  - formatting: "Use code blocks for commands and error messages." // Added
```

### Example: Extending Policies

Inheritance is also powerful for managing policies. You can have a strict, company-wide policy file and then a slightly more relaxed version for internal tools.

**File: `/policies/strict.proml`**
```
POLICIES:
  - pii_masking: { level: "high" }
  - forbidden_topics: ["finance", "legal_advice", "medical_advice"]
```

An internal summarization tool might be allowed to handle financial documents.

**File: `/prompts/internal_quarterly_report_summarizer.proml`**
```
@import "/policies/strict.proml"

GOAL: Summarize an internal financial report.

# This prompt is for internal use only and is allowed to handle financial topics.
POLICIES:
  # Override the imported policy by setting the list of forbidden topics
  # to a new list that omits "finance".
  - forbidden_topics: ["legal_advice", "medical_advice"]
```

Here, the local `POLICIES` block completely replaces the imported `forbidden_topics` rule, while still inheriting the `pii_masking` rule. This allows for granular control over security and safety rules in a manageable, hierarchical way.

This mechanism of importing, inheriting, and overriding is fundamental to building sophisticated and scalable prompt-based applications.
