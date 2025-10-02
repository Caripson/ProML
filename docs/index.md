# ProML (Prompt Markup Language)

Welcome to the official documentation for the ProML (Prompt Markup Language). This wiki provides a comprehensive guide to the principles and features of ProML, a language designed for creating powerful, reliable, and maintainable prompts.

## 🏛️ Core Principles

1.  [Declarative First](./declarative_first.md): Describe the task, not the step-by-step reasoning.
2.  [Strict I/O](./strict_io.md): All output must follow a validatable schema.
3.  [Composition & Modules](./composition_modules.md): Import and reuse prompt blocks.
4.  [Profiles & Execution Parameters](./profiles_execution_parameters.md): Specify engine, temperature, and other parameters in the prompt.
5.  [Policy Layer (Security & Ethics)](./policy_layer.md): Built-in rules for privacy, citations, and more.
6.  [Testability & Verification](./testability_verification.md): Enable unit tests and evaluation datasets.
7.  [Versioning & Semver](./versioning_semver.md): Track prompt versions and changes.
8.  [Clear Block Structure](./clear_block_structure.md): A fixed order for prompt sections.
9.  [Variables & Templating](./variables_templating.md): Clear rules for variable declaration and typing.
10. [Import & Inheritance](./import_inheritance.md): Import pre-built policies, styles, and patterns.
11. [Safe Tool Usage](./safe_tool_usage.md): Define tools with JSON Schema contracts.
12. [Pipelines & Steps](./pipelines_steps.md): Describe multi-step workflows.
13. [Assertions & Validation](./assertions_validation.md): Define invariance requirements for outputs.
14. [Observability & Telemetry](./observability_telemetry.md): Standard fields for cost, latency, and other metrics.
15. [Security & Privacy Scopes](./security_privacy_scopes.md): Define trust levels for inputs.
16. [Fallback & Degradation](./fallback_degradation.md): Specify fallback engines or simpler responses.
17. [Self-Check & Auto-Critique](./self_check_auto_critique.md): Prompts can validate their own output.
18. [Human-Readability](./human_readability.md): YAML/Markdown-like syntax for easy editing.
19. [Governance & Roles](./governance_roles.md): Metadata for owners, reviewers, and risk class.
20. [CI/CD-Friendly](./ci_cd_friendly.md): Easy to lint, build, and test in pipelines.
21. [Documentation Requirements](./documentation_requirements.md): Prompts have a README with metadata.
22. [Internationalization & Style](./internationalization_style.md): Definable language and date formats.
23. [Reproducibility & Determinism](./reproducibility_determinism.md): Seed and execution profiles for reproducible outputs.
24. [Secure Distribution & License](./secure_distribution_license.md): Specify license, risk class, and a "kill switch".
25. [Caching](./caching.md): Cache responses for identical requests to improve performance and reduce cost.
26. [Batch Processing](./batch_processing.md): Define how to efficiently run a prompt over a large dataset.
27. [Streaming](./streaming.md): Enable real-time, token-by-token output generation.
28. [Human-in-the-Loop](./human_in_the_loop.md): Define points in a pipeline that require manual human approval.
29. [Interactive Debugging](./interactive_debugging.md): Support for breakpoints and step-through debugging of prompts and pipelines.
