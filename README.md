# Battal

Open-source AI Safety & Agent Security platform — Turkish-first.

Battal is a security service that AI gateways, code studios/IDEs and agent runtimes call to evaluate
what flows through them: user input, model output (including streaming), RAG content, tool calls and
tool results. It combines pluggable detectors (Turkish and Turkish–English mixed text, PII and
secrets, prompt injection, content safety) with deterministic policy enforcement, behind one
evaluation API.

- **Not a proxy.** Gateways such as LiteLLM stay the gateway; Battal is the guard they call.
- **Swappable components.** Models, scanners and policy engines plug in behind stable interfaces.
- **Self-hosted.** Designed to run inside your own infrastructure; sensitive content never needs to
  leave it.
- **Explainable decisions.** Detector scores, policy decision and rationale are separate, versioned
  and auditable.

Planned distribution: a Python SDK (`pip install battal`) and Battal Server (container/Helm).

> **Status:** early research & design phase. No usable release yet.

## Licensing

Apache-2.0. See [LICENSING.md](LICENSING.md) for models, datasets and trademark.

## Contributing & security

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).
