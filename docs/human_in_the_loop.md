# 28. Human-in-the-Loop

**Core Principle:** Not all decisions should be fully automated. For critical or ambiguous tasks, a workflow should be able to pause and request explicit approval from a human before proceeding. PromptLang should provide a way to define these human approval steps within a pipeline.

This principle is essential for building safe, reliable, and practical AI-powered workflows in enterprise environments.

## Why it Matters

*   **Safety & Control:** For actions with real-world consequences (e.g., deleting data, sending money, publishing content), a human approval step is a critical safety-net to prevent costly mistakes.
*   **Handling Ambiguity:** When a model is uncertain about a user's intent or the correct course of action, it can escalate to a human for clarification instead of making a potentially wrong guess.
*   **Building Trust:** Users and stakeholders are more likely to trust and adopt an AI system if they know there are human checks and balances at critical points.
*   **Regulatory Compliance:** In many domains (like healthcare and finance), regulations may mandate human oversight for certain automated decisions.

## Practical Application & Examples

A `human-in-the-loop` step would be a special type of step within a [Pipeline](./pipelines_steps.md).

### Example: Approving a Social Media Post

This pipeline drafts a social media post and then sends it to a marketing manager for approval before publishing it with a tool.

```
PROMPT:
PIPELINE:
  - name: "draft_post"
    prompt: "/prompts/social_media_writer.prompt"
    input: { topic: "{{INPUT.topic}}" }

  - name: "human_approval"
    type: "human_in_the_loop"
    description: "Review the drafted social media post for tone, accuracy, and brand safety."
    # Data to present to the human reviewer
    ui_payload: {
      "title": "Approve Social Media Post",
      "draft_text": "{{STEPS.draft_post.output.text}}",
      "suggested_hashtags": "{{STEPS.draft_post.output.hashtags}}"
    }
    # Who should approve this? Can be a specific user or a role.
    assignee: "@marketing-manager"
    # What actions can the human take?
    actions: ["approve", "reject", "edit_and_approve"]

  - name: "publish_post"
    # This step only runs if the previous step was approved
    run_if: "{{STEPS.human_approval.result.action}} == 'approve' or {{STEPS.human_approval.result.action}} == 'edit_and_approve'"
    tool: "social_media_publisher"
    parameters: {
      # Use the (potentially edited) text from the approval step
      "text_to_publish": "{{STEPS.human_approval.result.edited_payload.draft_text}}"
    }
```

**How it Works:**

1.  **`draft_post`:** The pipeline starts by calling a prompt to generate the text for a social media post.
2.  **`human_approval`:** The workflow pauses here. The PromptLang runtime or orchestration engine would now:
    a.  Identify the `assignee` (`@marketing-manager`).
    b.  Send a notification to that user (e.g., via Slack, email, or a custom dashboard).
    c.  The notification would contain the `ui_payload` data, rendered in a user-friendly interface with buttons for `approve`, `reject`, and `edit_and_approve`.
3.  **Human Action:** The marketing manager reviews the draft. They might fix a typo and click "edit_and_approve". Their decision and the edited text are captured.
4.  **Conditional Execution:** The pipeline resumes. It checks the `run_if` condition for the `publish_post` step. Since the action was `edit_and_approve`, the condition is true.
5.  **`publish_post`:** The `social_media_publisher` tool is called, but it uses the final, human-approved text from the output of the `human_approval` step.

This creates a powerful, auditable workflow that combines the speed of AI-powered generation with the safety and judgment of human oversight.
