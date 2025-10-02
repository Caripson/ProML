# 11. Safe Tool Usage

**Core Principle:** Language models can be granted access to external tools, but this access must be strictly defined and controlled. Every tool must be exposed to the model via a formal contract, specifying its inputs, outputs, and side effects.

This turns tools into a secure, predictable, and observable part of the prompt execution, preventing the model from taking unexpected or harmful actions.

## Why it Matters

*   **Safety & Security:** A strict contract is the primary defense against prompt injection and misuse of tools. The model can only call a tool with parameters that match the defined schema.
*   **Reliability:** By defining the tool's signature, you ensure the model provides the correct inputs, and you know exactly what kind of data to expect in return.
*   **Clarity:** The tool contract serves as clear documentation for the model (and for human developers), explaining what the tool does and how to use it.
*   **Error Handling:** The contract can specify how to handle tool failures, allowing the prompt to degrade gracefully instead of failing completely.

## Practical Application & Examples

Tools are declared in a `TOOLS` block. Each tool definition includes its name, a description, and a JSON Schema for its parameters.

### Example: A Simple, Read-Only Tool

This prompt uses a tool to get the current weather.

```
PROMPT:
GOAL: Answer questions about the current weather.

TOOLS:
  - name: "get_weather"
    description: "Gets the current weather for a specific location."
    side_effects: false
    parameters:
      type: "object"
      properties:
        city: {
          type: "string",
          description: "The city, e.g., San Francisco"
        }
      required: ["city"]

INPUT:
- question: string

CONTEXT:
  "{{question}}"
```

When the user asks, "What's the weather like in London?", the model doesn't answer directly. Instead, it generates a request to use the tool:

**Model's desired action:**
```json
{
  "tool_call": {
    "name": "get_weather",
    "parameters": {
      "city": "London"
    }
  }
}
```

The PromptLang runtime intercepts this request.
1.  It **validates** the call against the schema. The `name` is correct, and the `parameters` object has the required `city` property of type `string`. The call is valid.
2.  It checks the `side_effects` flag. It is `false`, meaning this tool only reads data and doesn't change any state.
3.  The runtime then executes the actual `get_weather` function in the application code with the parameter `city: "London"`.
4.  The function returns a result (e.g., `{"temperature": "15°C", "conditions": "Cloudy"}`).
5.  This result is fed back into the model, which then formulates the final answer: "The current weather in London is 15°C and cloudy."

### Example: A Tool with Side Effects and Error Handling

This prompt uses a tool to send an email. This is a sensitive action.

```
PROMPT:
GOAL: Send an email based on the user's request.

TOOLS:
  - name: "send_email"
    description: "Sends an email to a recipient."
    side_effects: true
    parameters:
      type: "object"
      properties:
        recipient: { type: "string", format: "email" }
        subject: { type: "string" }
        body: { type: "string" }
      required: ["recipient", "subject", "body"]
    error_handling:
      - strategy: "retry"
        max_attempts: 2
      - strategy: "feedback_to_model"
        message: "The email failed to send. Inform the user and ask them to verify the recipient's address."

# ...
```

*   `side_effects: true`: This is a critical flag. It tells the runtime that this tool changes state in the real world. The runtime might require additional user confirmation or stricter logging for this tool call.
*   `error_handling`: This block tells the runtime what to do if the `send_email` function fails.
    *   First, it will `retry` the call up to 2 times.
    *   If it still fails, it will follow the `feedback_to_model` strategy, feeding the error message back to the model so it can generate a helpful response to the user.

By defining tools with these explicit, machine-readable contracts, PromptLang enables the creation of powerful and safe AI agents that can interact with the world beyond simple text generation.
