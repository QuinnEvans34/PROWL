# PROWL architecture set

**Status:** Active architecture baseline  
**Approved:** Quinton Evans, 2026-09-08

This directory contains the human-readable architecture views. Machine-readable boundary contracts
live under [`../contracts/`](../contracts/).

The inherited current-state view is dated September 8. For implemented capstone slices and
remaining gaps, use the [October 12 evidence overlay](../weeks/WEEK-01-CLOSEOUT-2026-10-12.md).

## Views

| View | Question answered |
|---|---|
| [`current-state.md`](current-state.md) | What does the inherited repository actually do today? |
| [`system-context.md`](system-context.md) | Who and what exists outside PROWL, and where are the trust boundaries? |
| [`component-map.md`](component-map.md) | Which internal component owns each responsibility? |
| [`data-flow.md`](data-flow.md) | How do training, inference, retrieval, review, and release artifacts move? |

## Governing choices

1. Single-user research workstation.
2. File-first, versioned artifacts; a database requires a measured need.
3. One case-package schema for static files and FastAPI.
4. Append-only review events tied to immutable prediction versions; `edit` means correction required.

These choices are recorded as D-017 through D-020 in [`../DECISIONS.md`](../DECISIONS.md).

## Reading order

Read current state first, then context, component map, and data flow. The contrast between current and
target is deliberate: it identifies the adapters and new work without describing the inherited
system as more mature than it is.
