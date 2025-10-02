# 19. Governance & Roles

**Core Principle:** Prompts in a production system require clear ownership, review processes, and risk assessment. PromptLang provides a metadata framework for embedding governance information directly into the prompt file.

This makes governance an explicit, auditable part of the prompt lifecycle, rather than an external, ad-hoc process.

## Why it Matters

*   **Accountability:** Clearly defines who is responsible for maintaining a prompt (`owner`) and who has approved it (`reviewers`).
*   **Risk Management:** Assigning a `risk_class` allows the system to apply different levels of scrutiny. A `high_risk` prompt might require more reviewers or be subject to stricter policies.
*   **Auditability:** All governance information is version-controlled along with the prompt itself, providing a clear audit trail for compliance and security reviews.
*   **Automated Workflows:** This metadata can be used by CI/CD pipelines to automate the review and deployment process. For example, a change to a `high_risk` prompt could automatically trigger a notification to the legal and security teams.

## Practical Application & Examples

Governance information is defined in the `META` block, alongside versioning data.

### Example: A Low-Risk Prompt

This prompt generates creative marketing slogans. It's considered low-risk because it doesn't handle sensitive data or perform critical actions.

```
PROMPT:
META:
  id: "com.mycompany.prompts.slogan-generator"
  version: "2.1.0"
  status: "stable"

  # Governance Metadata
  owner: "@marketing-team"
  reviewers:
    - "@jane.doe"
    - "@product-manager"
  risk_class: "low"
  last_reviewed: "2024-10-20"

GOAL: Generate a catchy slogan for a new product.
# ...
```

*   **owner:** The `@marketing-team` is responsible for this prompt.
*   **reviewers:** Two individuals have signed off on the current version.
*   **risk_class:** `low`. This might mean it can be deployed with a less stringent review process.
*   **last_reviewed:** A timestamp indicating when the last formal review took place.

### Example: A High-Risk Prompt

This prompt interacts with customer data and has the ability to modify it via a tool. It is therefore classified as high-risk.

```
PROMPT:
META:
  id: "com.mycompany.prompts.customer-data-updater"
  version: "1.0.0"
  status: "stable"

  # Governance Metadata
  owner: "@backend-services-team"
  reviewers:
    - "@lead-engineer"
    - "@security-officer"
    - "@legal-compliance"
  risk_class: "high"
  last_reviewed: "2024-09-15"

GOAL: Update customer information based on user requests.

TOOLS:
  - name: "update_customer_record"
    side_effects: true
    # ...

POLICIES:
  - pii_masking: true
# ...
```

*   **owner:** A core engineering team owns this critical prompt.
*   **reviewers:** Note the inclusion of `@security-officer` and `@legal-compliance`. The `high` risk class likely mandates their approval.
*   **risk_class:** `high`. This signals to the entire system that this prompt requires special handling.

### How Governance Metadata is Used

1.  **Code Review:** When a developer submits a change to a prompt, the `reviewers` field provides a clear checklist of who needs to approve the pull request.
2.  **CI/CD Pipeline:** The pipeline can read the `risk_class` and adjust its behavior:
    *   If `risk_class` is `low`, the tests might run, and on success, it might be deployed automatically.
    *   If `risk_class` is `high`, the pipeline might run additional security scans, require manual approval from the listed reviewers, and log the deployment event to a special audit trail.
3.  **Prompt Registry:** A central registry of all prompts could display this governance data, allowing anyone in the organization to see who owns a prompt, how risky it is, and when it was last reviewed.
4.  **Automated Alerts:** A script could periodically scan all prompts and flag any `high_risk` prompts that haven't been reviewed in the last 6 months, creating a ticket for the `owner` to address.

By embedding governance directly into the prompt file, PromptLang helps organizations manage their AI systems responsibly and at scale.
