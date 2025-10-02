# 18. Human-Readability

**Core Principle:** Prompts are code, and they should be as easy for humans to read and write as possible. PromptLang's syntax is designed to be clean, intuitive, and familiar, drawing inspiration from formats like YAML and Markdown.

If a prompt is difficult for a human to understand, it will be difficult to maintain, debug, and improve.

## Why it Matters

*   **Low Barrier to Entry:** A simple, readable syntax makes it easier for everyone, including non-developers like product managers or domain experts, to contribute to and understand prompts.
*   **Maintainability:** Clean, well-commented prompts are easier to come back to and modify weeks or months later.
*   **Collaboration:** Readability is key to effective team collaboration. It allows for easier code reviews and a shared understanding of the prompt's logic.
*   **Reduced Errors:** A clear and unambiguous syntax reduces the chance of making simple mistakes during editing.

## Practical Application & Examples

PromptLang achieves readability through several key features:

1.  **YAML-like Block Structure:** Using clear, indented blocks with simple key-value pairs.
2.  **Markdown for Content:** Allowing for the use of Markdown in text-heavy blocks for formatting and clarity.
3.  **Support for Comments:** Providing a standard way to add explanatory notes that are ignored by the parser.

### Example: A Well-Structured and Commented Prompt

This example demonstrates how syntax elements come together to create a highly readable prompt.

```
# PROMPT: com.mycompany.prompts.email-generator
# VERSION: 1.2.0
# AUTHOR: @jane.doe
# CHANGELOG:
#   1.2.0 - Added support for 'urgent' tone.
#   1.1.0 - Improved clarity of the goal.
#   1.0.0 - Initial version.

# GOAL: Generate a professional email based on a set of key points.
# This prompt is used by the internal sales team.

GOAL: Generate a professional email.

INPUTS:
  recipient_name: string
  key_points: array # An array of strings to be included in the email.
  tone: string? = "neutral" # Can be "neutral" or "urgent"

STYLE:
  - Persona: A helpful and professional sales associate.
  - Formatting: Use short paragraphs. Start with "Hi {{recipient_name}},".

# The main context block where we assemble the core message.
# Using Markdown here for the list makes it easy to read.
CONTEXT:
  """
  Please write an email that incorporates the following key points:

  - {{#each key_points}}- {{this}}
  {{/each}}
  The tone of the email should be {{tone}}.
  """

OUTPUT:
  OUTPUT_SCHEMA: { "type": "string" } # The final email body.

# PROFILE: Use a fast and cheap model for this common task.
PROFILE:
  default:
    engine: "claude-3-haiku-20240307"
```

**Readability Features in this Example:**

*   **File Header Comments:** The block of comments at the top provides a human-readable changelog and metadata. The `#` syntax is instantly recognizable to anyone familiar with shell scripts, Python, or YAML.
*   **Inline Comments:** Comments like `# The final email body.` explain the purpose of specific blocks or lines.
*   **Clear Block Structure:** The use of capitalized block names (`GOAL`, `INPUTS`, `STYLE`, etc.) makes the prompt easy to scan.
*   **Indentation:** The YAML-like indentation clearly shows the hierarchy of the information.
*   **Markdown in `CONTEXT`:** The `CONTEXT` block uses a multiline string (`"""`) and includes a Markdown-style list. This is much clearer than putting everything on one line.
*   **Familiar Templating:** The `{{variable}}` syntax is widely used in many popular templating languages (Handlebars, Jinja, etc.), making it immediately familiar to many developers.

By prioritizing human-readability, PromptLang ensures that prompts remain manageable and maintainable as they grow in complexity and number, fostering a more robust and collaborative development environment.
