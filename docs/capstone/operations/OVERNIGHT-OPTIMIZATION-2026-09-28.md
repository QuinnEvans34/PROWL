# Overnight optimization work — D-277

Quinton authorized continued implementation and investigation without checking back. The immediate
work is the [CAP-EXP-002 proposal](CAP-EXP-002-PROPOSAL-2026-09-28.md): change only CE class balance,
keep the remaining two-case recipe fixed. This authorization supersedes the proposal's earlier
awaiting-approval wording. It does not authorize unbounded training or bypass verification.

Implement version4 objective-bound identities/configuration with legacy checkpoint readability;
verify objective arithmetic, extreme logits, empty cases, class-duplication invariance, objective
mismatch rejection and complete synthetic persistence. Add original/new objective and probability/
fixed-patch telemetry at0/25/50/75/100. Preserve native masks and backup restore checks. Check that
scratch parameters match the original step0 digest without loading its weights. Run one short native
synthetic rehearsal before preparing a concrete real request. Write the authorization only after its
pins and evidence are verified. Then execute one100-update balanced run within the existing limits.

Use the result to choose the next useful action. Do not automatically launch a second recipe, extend
failed runs, tune thresholds, or expand the dataset. Any follow-up must first have a concrete question,
changed/retained factors, bounded budget and pre-run notebook entry. Stop for the night when the next
step requires a substantive scope/design choice or when further work would be less reliable.
