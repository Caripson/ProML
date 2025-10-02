# 20. CI/CD-Friendly

**Core Principle:** Prompts are a form of code and should be integrated into standard software development lifecycle processes. The PromptLang format and tooling are designed to be seamlessly integrated into Continuous Integration and Continuous Deployment (CI/CD) pipelines.

This allows for the automated testing, validation, and deployment of prompts, ensuring quality and reliability at scale.

## Why it Matters

*   **Automation:** Automating the testing and deployment process reduces manual effort and human error.
*   **Quality Gatekeeping:** A CI/CD pipeline acts as a quality gate, preventing poorly written, untested, or non-compliant prompts from reaching production.
*   **Rapid Iteration:** Automation enables faster, more confident iteration on prompts. You can push a change and get immediate feedback from the automated test suite.
*   **Reproducible Builds:** The use of manifests and lockfiles ensures that a prompt that works today will continue to work tomorrow by freezing its dependencies.

## Practical Application & Examples

A typical CI/CD pipeline for a PromptLang project would consist of several stages that run automatically whenever a change is made to a prompt file.

### Example CI/CD Pipeline Workflow

Imagine a developer pushes a change to the `sentiment-analysis@1.4.0.prompt` file.

**1. Linting Stage:**

The pipeline first runs a `promptlang-lint` command.
*   **Action:** The linter statically analyzes the prompt file.
*   **Checks:**
    *   Is the syntax valid?
    *   Is the [Block Structure](./clear_block_structure.md) in the correct order?
    *   Are all [Variables](./variables_templating.md) used in the prompt declared in the `INPUTS` block?
    *   Does the [Metadata](./governance_roles.md) contain an owner and a valid version number?
*   **Outcome:** If any check fails, the pipeline stops and reports an error to the developer.

**2. Testing Stage:**

If linting passes, the pipeline runs the `promptlang-test` command.
*   **Action:** The test runner executes all the [Unit Tests](./testability_verification.md) and [Evaluation Sets](./testability_verification.md) defined in the prompt's `TEST` and `EVAL` blocks.
*   **Checks:**
    *   Does the prompt produce the correct output for given inputs?
    *   Does the output consistently validate against the `OUTPUT_SCHEMA`?
    *   Does it pass all defined `assert` conditions?
*   **Outcome:** If any test fails, the pipeline stops. The developer can review the test results to debug the issue.

**3. Compliance & Security Scan Stage:**

Next, the pipeline can run checks related to governance and security.
*   **Action:** A custom script or tool scans the prompt's `POLICIES` and `META` blocks.
*   **Checks:**
    *   Does the prompt import the mandatory company-wide `base-policies.prompt`?
    *   If `risk_class` is `high`, has a user with the `@security-officer` role approved the change?
    *   Does the prompt use any deprecated or forbidden tools?
*   **Outcome:** Failure stops the pipeline and may notify the security team.

**4. Build & Package Stage:**

If all checks pass, the prompt is ready to be "built".
*   **Action:** The `promptlang-build` command compiles the prompt and its dependencies into a single, deployable artifact. It also generates a `promptlang.lock` file.
*   **`promptlang.lock` (Lockfile):** This file freezes the exact versions of all dependencies:
    *   The specific version of the engine used (e.g., `gpt-4-turbo-2024-04-09`).
    *   The exact versions (`@1.2.0`) of any imported prompts, styles, or policies.
*   **Outcome:** This process creates a versioned, self-contained prompt package (e.g., `sentiment-analysis-1.4.0.pkg`) and the `promptlang.lock` file.

**5. Deployment Stage:**

Finally, the packaged prompt is deployed.
*   **Action:** The pipeline pushes the prompt package to a central prompt registry or directly to the application servers.
*   **Zero-Downtime:** The application can now load and start using the new prompt version (`@1.4.0`) without any service interruption.
*   **Rollback:** Because the packages are versioned, if the new prompt causes unforeseen issues in production, the system can be instantly rolled back to the previous version (`@1.3.0`).

By making PromptLang inherently CI/CD-friendly, it elevates prompt engineering from a manual, ad-hoc activity to a mature, automated, and reliable engineering discipline.
