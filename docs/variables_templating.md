# 9. Variables & Templating

**Core Principle:** Prompts must have a clear, standardized way to declare input variables, specify their types, and define default values. This makes prompts reusable and ensures that they receive the data they need in the correct format.

PromptLang uses an `INPUTS` block for explicit variable declaration and a `{{variable_name}}` syntax for templating.

## Why it Matters

*   **Clarity & Readability:** Explicitly declaring inputs at the top of the prompt makes it immediately clear what data the prompt requires.
*   **Type Safety:** Specifying types (e.g., `string`, `number`, `boolean`, `array`) allows for static analysis and runtime validation, catching errors before they reach the model.
*   **Reusability:** A prompt with well-defined inputs is a reusable component. It can be called with different data, just like a function in a programming language.
*   **User Experience:** Default values allow for optional inputs, making prompts more flexible. Required flags ensure that critical information is never missing.

## Practical Application & Examples

Variables are defined in the `INPUTS` block and used elsewhere in the prompt with double curly braces.

### Example: Basic Input Declaration

```
PROMPT:
GOAL: Write a personalized welcome email.

INPUTS:
  customer_name: string
  product_name: string

CONTEXT:
  """
  The customer {{customer_name}} has just purchased {{product_name}}.
  """

STYLE:
  - Start the email with "Hello {{customer_name}},".

OUTPUT:
  - A string containing the email body.
```

Before execution, a runtime would inject the actual values for `customer_name` and `product_name` into the `CONTEXT` and `STYLE` blocks.

### Example: Typed Variables, Defaults, and Required Flags

PromptLang extends simple declarations with more powerful features.

```
PROMPT:
GOAL: Generate a search query for a product catalog.

INPUTS:
  query: string
  category: string? = "all"
  limit: number = 10
  include_out_of_stock: boolean = false

CONTEXT:
  """
  User is searching for "{{query}}".
  Filter by category: {{category}}.
  Return at most {{limit}} results.
  Include out-of-stock items: {{include_out_of_stock}}.
  """

# ... rest of prompt
```

Let's break down the `INPUTS` block:

*   `query: string`: This declares a variable named `query` of type `string`. Since there is no `?` and no default value, this input is **required**. An error will be thrown if it's not provided at runtime.
*   `category: string? = "all"`: This declares a `category` variable of type `string`.
    *   The `?` indicates that this is an **optional** input.
    *   `= "all"` provides a **default value**. If no `category` is provided at runtime, it will automatically be set to `"all"`.
*   `limit: number = 10`: A `number` input with a default value of `10`.
*   `include_out_of_stock: boolean = false`: A `boolean` input that defaults to `false`.

### How it Works

1.  **Static Analysis:** Before running the prompt, a linter or compiler can check for errors.
    *   It can warn you if you use a variable `{{undefined_variable}}` that wasn't declared in the `INPUTS` block.
    *   It can check that the types of default values match their declared types (e.g., `limit: number = "ten"` would be an error).
2.  **Runtime Validation:** When the prompt is executed:
    *   The runtime checks that all required inputs (like `query`) have been provided.
    *   It validates that the provided values match the declared types (e.g., `limit="ten"` would throw a type error).
    *   It applies default values for any optional inputs that were not provided.

This systematic approach to handling variables makes prompts more robust, easier to debug, and simpler to integrate into larger applications.
