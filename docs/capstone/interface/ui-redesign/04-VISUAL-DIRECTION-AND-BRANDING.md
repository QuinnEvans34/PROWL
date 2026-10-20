# 04 — Visual direction and branding

> Approval update: Quinton approved the rendered Concept 01 direction on October 18. Use its graphite/silver/violet treatment and actual black-panther asset as the implementation baseline. Contrast and real-layer checks remain implementation acceptance work.


Status: Concept 01 visual direction approved; validate accessibility and scientific-layer distinctions during implementation.

## Direction: quiet, precise, recognizable

Use neutral graphite instead of the existing blue-green wash. Imaging provides the visual interest.
Silver typography and restrained violet accents create distinction without covering the app in color.
The palette is inspired by the user's description of a sleek black panther, not sampled from an asset.

| Token | Proposed starting value | Role |
|---|---|---|
| background | `#0D0F12` | App background |
| surface | `#15181D` | Panels |
| raised | `#1D2128` | Menus, selected surfaces |
| border | `#343A46` | Functional boundaries |
| text | `#F0F2F6` | Primary text |
| text-muted | `#A8B0BE` | Secondary labels |
| accent | `#B7A4FF` | Active control, focus, primary action |
| accent-ink | `#171223` | Text on bright accent |

Contrast and overlay distinguishability still need measurement; these are draft tokens, not a pass.
Do not use brand accent as a substitute for scientific layer or semantic-status colors. Preserve
existing anatomy encodings until a deliberate, tested palette migration. Always pair colors with labels.

## Panther placement

1. Welcome/import empty state: the full prowling silhouette gets space to read, above a concise
   instruction and Import CT action. This is the primary expressive brand moment.
2. Assistant header: a small silhouette in a contrasting neutral badge identifies the companion.
3. Global shell: compact PROWL wordmark with a modest mark where the silhouette remains legible.
4. Loading: subtle halo/pulse around the assistant badge; no walking mascot over the scan.

Use an appropriate contrasting backing for the black artwork. Do not recolor or crop the original
before inspecting it. No logo watermark on CTs, masks, measurement graphics, or exported evidence.
At tiny sizes prefer a wordmark or approved simplified mark over an illegible panther.

## Typography, surfaces, motion

- Start with the existing sans-serif or system stack; decide typography through the visual draft.
- Body/control labels typically 14–16px; reserve small text for secondary metadata.
- Tabular numerals for measurements; monospaced text only where identifiers benefit.
- Consistent 4/8px spacing rhythm; modest 8–12px panel radii; no pill around every label.
- Use hierarchy and borders rather than pervasive gradients, glow, glass, and nested cards.
- Short transitions around 120–180ms; no animation that delays an action. Honor reduced motion.
- Focus visibility and selected state must be independently identifiable.

## Approved visual deliverable

The populated desktop workbench, assistant, findings, summary, import and no-reference flows are implemented in `prototype/` and were approved by Quinton. Use that reference for implementation. Use the supplied repository-root `PROWL_LOGO.png`; do not synthesize a substitute. The initial image preview rendered black against a dark background, so verify silhouette visibility on a pale silver backing in the prototype. Preserve the source file.
