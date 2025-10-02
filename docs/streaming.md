# 27. Streaming

**Core Principle:** For real-time and interactive use cases, waiting for a model to generate a complete response is too slow. A prompt should be able to specify that its output should be streamed token-by-token, allowing the user to see the response as it's being generated.

This is essential for creating engaging chatbots, code assistants, and other applications where perceived latency is a critical factor.

## Why it Matters

*   **Improved User Experience:** Streaming significantly reduces *perceived* latency. Users start seeing a response almost instantly, which makes the application feel much more responsive, even if the total generation time is the same.
*   **Enables Long-Form Generation:** For tasks that generate long articles, code files, or stories, streaming is the only practical way to deliver the content without long, frustrating waits.
*   **Better Interactivity:** Allows for more dynamic interactions. For example, a user could interrupt a streaming response midway through if they see it's going in the wrong direction.

## Practical Application & Examples

Streaming would be a property of an execution `PROFILE`, as it governs how the response is delivered by the runtime.

### Example: A Streaming Chatbot Prompt

This prompt is for a chatbot that should stream its answers back to the user.

```
PROMPT:
GOAL: Act as a helpful AI assistant and answer the user's question.

INPUTS:
  user_question: string
  conversation_history: array

PROFILE:
  default:
    engine: "claude-3-sonnet-20240229"
    temperature: 0.7
    # Enable streaming for this profile
    STREAM: true

OUTPUT:
  # Even when streaming, you can still have a schema for the final, complete object.
  # The runtime can assemble the streamed chunks into this final object.
  OUTPUT_SCHEMA:
  {
    "type": "object",
    "properties": {
      "response_text": { "type": "string" }
    }
  }
```

**How it Works:**

1.  The `STREAM: true` flag in the `PROFILE` instructs the PromptLang runtime to make a streaming request to the underlying language model API.
2.  Instead of waiting for the full response, the model provider's API will send back a sequence of small chunks (events).

    *   `chunk 1: {"delta": "Hello"}`
    *   `chunk 2: {"delta": "! I can"}`
    *   `chunk 3: {"delta": " certainly"}`
    *   `chunk 4: {"delta": " help"}`
    *   `chunk 5: {"delta": " with that."}`
    *   `...`

3.  The PromptLang runtime doesn't wait for the end. It immediately forwards these chunks to the client application (e.g., a web browser or a terminal).
4.  The client application is responsible for appending these chunks together and displaying them to the user in real-time, creating the familiar typing effect.
5.  Simultaneously, the runtime can be assembling the chunks internally. When the stream is finished, it can construct the final, complete JSON object (`{"response_text": "Hello! I can certainly help with that."}`) and validate it against the `OUTPUT_SCHEMA`.

This provides the best of both worlds: the user gets the low-latency experience of streaming, while the developer still gets the reliability of a final, schema-validated object.

### Controlling Streaming Behavior

The `STREAM` block could be extended with more granular controls.

```
PROFILE:
  streaming_profile:
    engine: "gpt-4-turbo-2024-04-09"
    STREAM:
      # A more advanced option where you only stream a specific field
      # from the final JSON object.
      field: "response_text"
      # An option to control how often chunks are sent (e.g., word by word)
      granularity: "word"
```

By making streaming a first-class citizen in the prompt specification, PromptLang allows developers to easily build the fast, interactive experiences that users have come to expect from modern AI applications.
