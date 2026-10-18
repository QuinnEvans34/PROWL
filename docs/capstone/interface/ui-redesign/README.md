# PROWL UI redesign — approved design and implementation handoff

Version: 1.0 · October 18, 2026 (America/Denver).
Owner: Quinton Evans. Implementation branch: `codex/prowl-ui-redesign`.
Status: **Concept 01 approved by Quinton; ready for Claude implementation.**

Quinton approved the prototype's direction and requested the full specification/handoff package.
This supersedes earlier draft-only / do-not-dispatch wording within this package. It does not
assert backend capabilities that do not exist or authorize unrelated scientific work.

## Start here

1. Read [01 — Product brief and decisions](01-PRODUCT-BRIEF-AND-DECISIONS.md).
2. Open [the approved interactive reference](prototype/index.html) in a browser. Its editable source
   is `prototype/prowl-workbench.html`; see [preview instructions](prototype/README.md).
3. Read [03 — Workbench and workflow](03-WORKBENCH-AND-WORKFLOW.md),
   [04 — Visual direction](04-VISUAL-DIRECTION-AND-BRANDING.md), and
   [05 — Assistant and evidence](05-AI-ASSISTANT-AND-EVIDENCE.md).
4. Implement using [08 — Component and integration specification](08-COMPONENT-AND-INTEGRATION-SPEC.md).
5. Use [09 — Acceptance and delivery checklist](09-ACCEPTANCE-AND-DELIVERY-CHECKLIST.md).
6. Consult [10 — Baseline and transfer](10-BASELINE-AND-TRANSFER.md) before touching existing work.

Supporting context: [02 — Live audit](02-LIVE-INTERFACE-AUDIT.md) and
[06 — Implementation sequence](06-IMPLEMENTATION-AND-ACCEPTANCE.md).
The copy/paste assignment is [07 — Claude implementation prompt](07-CLAUDE-IMPLEMENTATION-PROMPT.md).
The old `07-CLAUDE-HANDOFF-PROMPT-DRAFT.md` is a retired prototype assignment, not the active prompt.

## What is approved

- Radiologist-centered, study-centered workbench; optional reference annotations.
- Concept 01 graphite/silver/violet visual direction and restrained original panther branding.
- Persistent Studies / Workbench / Research shell; integrated Findings / Ask PROWL / Summary panel.
- DICOM series-selection experience as an initial product requirement.
- Editable, source-aware review summary as the workflow endpoint.
- Implement progressively in the existing React/NiiVue app, preserving its working integrations.

## What the reference means

The prototype is the visual and interaction baseline, not a clinical implementation or a source of
measurements. Use real viewer data and validated services where they exist. Synthetic anatomy,
scripted responses, simulated conversion, and in-memory draft retention remain demonstrator behavior.
Do not copy these shortcuts into live modes. Do not reinterpret design approval as clinical readiness.

Use this precedence: latest explicit user direction → this approved packet's UX decisions → existing
scientific/data contracts and current validated service behavior. These apply to different concerns:
the visual redesign supersedes historical layout-preservation preferences, not scientific validation.
When a proposed UI requires a missing backend, implement its explicit capability boundary and keep
working on independent UI tasks; report the dependency instead of fabricating a success.

## Scope and handback

The initial read-only audit began at `5a86f27b7d5b36784f8ed4a4e557886e24ffa86a`. Concurrent literature
work advanced this same branch; the pre-package baseline is recorded in 10. Preserve those commits.
The packet includes the original root `PROWL_LOGO.png` and an integrity manifest for the approved
reference. No production UI change, model run, or service mutation is part of this packet preparation.

Claude should deliver implemented milestones, screenshots, actual validation results, and explicit
remaining dependencies. No public push, deployment, merge, model training, or corpus changes are implied.
