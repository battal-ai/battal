# ADR 0001: Product shape and licensing

- Status: accepted
- Date: 2026-11-16

## Context

Battal should be usable as open source and also support a paid commercial edition later. It
targets organizations running LLMs on their own infrastructure, with Turkish as the primary
language. Adoption is the main early risk; a large vendor cloning the core is a lesser one.

## Decisions

1. **Shape.** Battal is a security service and SDK that gateways and agent runtimes call. It is not
   an LLM proxy. One evaluation API fronts swappable detectors and policy components.
2. **Distribution.** Python SDK (in-process) and Battal Server (container/Helm).
3. **Fully open source for now.** The whole repository is Apache-2.0. A commercial enterprise
   edition is deferred to a later stage. When it comes, it will follow the open-core pattern, with
   new code in a separately licensed `enterprise/` directory and production use requiring a
   license key. Code already released stays Apache-2.0.
4. **Future open/paid boundary.** The security floor stays open (engine, API/SDK, adapters,
   baseline Turkish detectors, deterministic policy, eval harness, public benchmark). Candidates for
   the future paid edition are scale, governance and sector expertise (multi-tenant control plane,
   SSO/RBAC, audit-evidence packs, policy canary/rollback, premium and sector models, support).
5. **Contributions.** A CLA is required for code contributions, which keeps a future dual-licensing
   option open. Code PRs are not merged until the CLA is in place.
6. **Models and data.** Licensed separately from code. A baseline Turkish safety model is open;
   higher-accuracy and sector-specific models are commercial. Third-party models with their own
   licenses are not redistributed; adapters support them.
7. **Trademark.** The name is protected separately from the code license. Forks must rename.
8. **Languages.** Code and contributor docs are in English; research reports are in Turkish.

## Alternatives rejected

- **AGPL core + commercial license:** stronger protection against cloning, but slows enterprise
  adoption and conflicts with embedding the SDK and adapters, including upstream in LiteLLM.
  It remains reachable later, because Apache-2.0 code can be included in AGPLv3 works and the CLA
  allows relicensing.
- **Source-available core (BSL/FSL/ELv2):** not open source, so it contradicts a core goal.
- **Separate private repos for paid features:** more CI and release overhead, and customers cannot
  audit the code.

## Consequences

- Anyone may fork the core. The commercial advantage rests on enterprise features, models,
  trademark and support, not on the code license.
- Features earmarked for the future paid edition should not be built into the open core early,
  because released code cannot be pulled back. Keep extension points so that they can be added later
  as separate modules.
- Final legal review is required before the first commercial sale.
