# 24. Secure Distribution & License

**Core Principle:** Prompts, especially when shared or distributed, must carry metadata about their usage rights, distribution terms, and emergency control mechanisms. This includes licensing information, data handling rules, and a "kill switch" to disable a prompt if a critical vulnerability is found.

This framework provides the trust and safety layer necessary for creating a healthy ecosystem of shared and distributed prompts.

## Why it Matters

*   **Legal Clarity (License):** A standard license (like MIT, Apache 2.0, or a custom EULA) clarifies how others can use, modify, and distribute your prompt. This is essential for both open-source and commercial prompt libraries.
*   **Risk Management:** The `risk_class` and `data_handling` rules inform consumers of the prompt about its intended use and how it handles data, helping them make informed decisions about whether to trust it.
*   **Emergency Control (Kill Switch):** If a severe vulnerability is discovered in a prompt (e.g., a prompt injection that allows an attacker to take over a system), a kill switch provides a mechanism for a central authority to remotely disable it, protecting all downstream users.
*   **Trust & Safety:** This metadata provides the signals needed for a central registry or marketplace to curate and manage prompts, flagging malicious content and promoting high-quality, safe prompts.

## Practical Application & Examples

This information is defined in the `META` block, alongside other governance and documentation data.

### Example: An Open-Source Prompt

This prompt is intended for free and open distribution.

```
PROMPT:
META:
  id: "com.opensource.prompts.markdown-formatter"
  version: "1.0.0"
  owner: "@community-dev"

  # Distribution & License Metadata
  license: "MIT"
  distribution: "public"
  risk_class: "low"
  data_handling: "ephemeral" # Indicates data is not stored or logged
```

*   **`license`:** `MIT`. This is a standard, permissive open-source license identifier.
*   **`distribution`:** `public`. This indicates it can be freely shared.
*   **`risk_class`:** `low`. It performs a safe, well-understood task.
*   **`data_handling`:** `ephemeral`. This is a promise to the user that the prompt and its runtime will not store or log the input data, which is important for privacy.

### Example: A Commercial, High-Risk Prompt

This prompt is part of a commercial product and handles sensitive financial data.

```
PROMPT:
META:
  id: "com.mycorp.prompts.financial-analyzer"
  version: "3.5.0"
  owner: "@finance-ai-team"

  # Distribution & License Metadata
  license: "Proprietary - See EULA at https://mycorp.com/eula"
  distribution: "restricted"
  risk_class: "high"
  data_handling: "audited_and_encrypted"

  # Emergency Control
  kill_switch_id: "mycorp-fin-analyzer-v3"
  kill_switch_authority: "https://pki.mycorp.com/authorities/kill-switch"
```

*   **`license`:** `Proprietary`. It points to an external End User License Agreement.
*   **`distribution`:** `restricted`. It should not be shared outside the company.
*   **`risk_class`:** `high`. It works with sensitive data.
*   **`data_handling`:** `audited_and_encrypted`. This signals to the user and the runtime that data is stored, but only in a secure, audited, and encrypted manner.
*   **`kill_switch_id` & `kill_switch_authority`:** This is the emergency kill switch mechanism.

### How the Kill Switch Works

1.  The `kill_switch_id` is a unique identifier for this family of prompts.
2.  The `kill_switch_authority` is a URL pointing to a trusted server that maintains a list of revoked prompt IDs.
3.  Before a PromptLang runtime executes this prompt, it **must** first contact the `kill_switch_authority` (respecting caching rules to avoid performance issues).
4.  The runtime asks the authority: "Is `mycorp-fin-analyzer-v3` on the revoked list?"
5.  If the authority responds with "yes", the runtime **must refuse to execute the prompt** and should return an error indicating that the prompt has been disabled for security reasons.

This mechanism allows a developer or company to instantly disable a dangerous or vulnerable prompt across their entire user base, even after it has been distributed and installed, providing a powerful final layer of safety for a distributed prompt ecosystem.
