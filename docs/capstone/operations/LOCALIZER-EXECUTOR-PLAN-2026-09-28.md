# Bounded smoke executor implementation and verification

D-274: Quinton explicitly requested completion of the bounded training loop, before/after evaluation
and necessary supporting work, plus Claude P2 review. Scope includes implementation, synthetic tests,
retained synthetic end-to-end verification and preparation of a concrete launch request. Actual
CAP-EXP-001 real-data training remains unlaunched until the specific prepared request is approved.

Implement the existing CAP-EXP-001 design: alternating qualified members, scratch-only MPS, fixed
budget/cadence, full-volume image-only before/after evaluation, native masks and contact sheets,
non-overwriting checkpoints, terminal bundle and independent backup/consumer restore. Every failed
attempt is retained. A launch authorization must bind the prepared request's exact controls and
permission; a file marked pending is rejected before source payloads or model work.

Synthetic verification runs the same executor on two invented volumes with a shorter explicit horizon,
not the real cohort, preserving honest synthetic identity. CPU fixtures cover numerical metric oracles,
budgets, order, checkpoint cadence, wrong identity, pending approvals, exports and failed persistence.
A bounded native MPS two-update rehearsal may use the existing D-273 primary/backup/restore areas:
600s,16GiB,1GiB new bytes per domain, existing quota/floors, AC and cooperative accelerator lock.
Do not reuse its weights for the real smoke. Review Claude's files read-only and write a separate
Codex handback; no literature download, search, email, signature or new seed approval is implied.
