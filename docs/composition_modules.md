# 3. Composition & Modules

**Core Principle:** Prompts can import and reuse other prompt files or blocks. This allows for a modular, scalable, and maintainable prompt architecture.

Think of it like functions in a programming language. Instead of copying and pasting the same logic in multiple places, you define it once and import it wherever it's needed.

## Why it Matters

*   **Reusability (DRY):** Don't Repeat Yourself. Common instructions, styles, policies, or constraints can be defined once and reused across many prompts.
*   **Maintainability:** When a shared piece of logic needs to be updated (e.g., a change in your company's legal disclaimer), you only need to edit one file, and the change propagates everywhere.
*   **Scalability:** Makes it manageable to have a large library of prompts. You can build complex prompts by composing smaller, simpler ones.
*   **Consistency:** Ensures that all prompts adhere to the same styles, policies, and output formats where required.

## Practical Application & Examples

ProML uses an `@import` directive to include content from other files. You can import a whole file or specific named blocks.

### Example: Reusing a Style Guide

Let's say you have a standard style for all your AI-generated customer emails.

**File: `/styles/customer_email.proml`**
```
STYLE:
- Tone: Friendly, helpful, and slightly formal.
- Language: Use clear, simple English. Avoid technical jargon.
- Formatting: Start with a greeting (e.g., "Hello [Customer Name],"). End with "Best regards, The Support Team."
- Persona: Act as a knowledgeable and patient customer support agent.
```

Now, any prompt that needs to generate a customer email can simply import this style.

**File: `/prompts/password_reset_email.proml`**
```
@import "/styles/customer_email.proml"

GOAL: Write an email to a customer explaining how to reset their password.

INPUT:
- customer_name: string
- reset_link: string

OUTPUT:
- A string containing the full email body.
```

### Example: Overriding Imported Blocks

Composition also allows for overrides. Imagine you need a slightly more urgent tone for a fraud alert email, but still want to keep the rest of the standard email style.

**File: `/prompts/fraud_alert_email.proml`**
```
@import "/styles/customer_email.proml"

GOAL: Write an email to a customer alerting them to suspicious activity on their account.

INPUT:
- customer_name: string
- activity_details: string

// Override the imported style with a more specific instruction
STYLE:
- Tone: Urgent and serious, while still being reassuring.

OUTPUT:
- A string containing the full email body.
```

In this case, the local `STYLE` block overrides the `Tone` instruction from the imported file, but the other style rules (Language, Formatting, Persona) are still inherited. This provides a powerful combination of reusability and flexibility.
