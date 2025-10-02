# 22. Internationalization & Style

**Core Principle:** Prompts should be adaptable to different languages, regions, and stylistic needs. PromptLang allows for the parameterization of locale-specific information and the use of reusable style modules to separate content logic from presentational rules.

This enables the creation of a single, core prompt that can be adapted for a global audience and various contexts without duplicating the main logic.

## Why it Matters

*   **Global Reach (Internationalization - i18n):** Allows a single prompt to generate responses in multiple languages and formats (e.g., dates, currencies), drastically reducing the effort needed to build global applications.
*   **Consistency (Styling):** Reusable style modules ensure a consistent tone, voice, and persona across many different prompts.
*   **Separation of Concerns:** Separates the core task of the prompt (the `GOAL`) from the specifics of its presentation (the `STYLE`). This makes prompts cleaner and easier to maintain.
*   **Flexibility:** Allows for easy swapping of styles. You can take a single prompt and have it generate a `friendly` response, a `formal` legal response, or a `technical` response just by changing a parameter.

## Practical Application & Examples

### Internationalization (i18n)

i18n is achieved by treating language and locale as input variables.

```
PROMPT:
GOAL: Send a shipping confirmation to the user.

INPUTS:
  user_name: string
  product_name: string
  estimated_arrival: string # ISO 8601 date, e.g., "2024-11-10"
  locale: string? = "en-US" # e.g., "en-US", "fr-FR", "ja-JP"

CONTEXT:
  """
  - User Name: {{user_name}}
  - Product: {{product_name}}
  - Estimated Arrival: {{estimated_arrival}}
  - Target Locale: {{locale}}
  """

STYLE:
  - Language: Generate the response in the language corresponding to the {{locale}} code.
  - Date Formatting: Format the {{estimated_arrival}} date according to the conventions of the {{locale}}.

OUTPUT:
  - A string containing the notification message.
```

**How it Works:**

When this prompt is run, the `locale` input variable controls the output.

*   `run_prompt(..., locale: "en-US")` might produce:
    > "Hello John, your order for the 'SuperWidget' has shipped! It is expected to arrive on **November 10, 2024**."

*   `run_prompt(..., locale: "fr-FR")` might produce:
    > "Bonjour John, votre commande pour le 'SuperWidget' a été expédiée ! La livraison est prévue pour le **10 novembre 2024**."

*   `run_prompt(..., locale: "ja-JP")` might produce:
    > "ジョン様、ご注文の「スーパーウィジェット」が発送されました。配送予定日は**2024年11月10日**です。"

The core logic of the prompt remains the same; only the output language and date format change based on the `locale` parameter.

### Reusable Style Modules

Just like functions, styles can be defined in separate files and imported. This is a powerful application of [Composition & Modules](./composition_modules.md).

**File: `/styles/legal.prompt`**
```
# STYLE: For formal, legal communication.
STYLE:
  - Persona: "A corporate lawyer."
  - Tone: "Formal, precise, and unambiguous."
  - Language: "Use formal legal terminology where appropriate."
  - Formatting: "Reference specific clauses and definitions."
```

**File: `/styles/friendly.prompt`**
```
# STYLE: For casual, friendly customer interaction.
STYLE:
  - Persona: "A helpful and cheerful friend."
  - Tone: "Enthusiastic and positive."
  - Language: "Use simple, everyday language. Emojis are okay! 😊"
```

Now, you can write a prompt that can adopt either style.

```
PROMPT:
@import "/styles/{{style_name}}.prompt"

GOAL: Explain the consequence of a specific action.

INPUTS:
  action: string
  consequence: string
  style_name: string # "legal" or "friendly"

CONTEXT:
  """
  Action: {{action}}
  Consequence: {{consequence}}
  """

OUTPUT:
  - A string containing the explanation.
```

**How it Works:**

1.  The `@import` statement itself contains a variable: `{{style_name}}`.
2.  When the prompt is run with `style_name: "legal"`, it will import `/styles/legal.prompt`, and the model will adopt the persona of a lawyer.
3.  When run with `style_name: "friendly"`, it will import `/styles/friendly.prompt` and produce a much more casual response.

This powerful combination of i18n parameters and modular styling allows a small number of core prompts to serve a wide variety of use cases and audiences, making the entire system more efficient and maintainable.
