# Lenovo check-in metadata snapshot

Observed 2026-11-09T19:24:02.184170+00:00; journal source event 2026-11-09T19:23:59.522000+00:00. Saved metadata, not a live feed. No trainer, dashboard, tracking, source, cache or frozen producing file changed.

Training-session total: **1,161,405.344 seconds = 322.612595556 hours** across eleven unique Lenovo scientific sessions. Arithmetic: prior nine 964,509.828 + original STU-Net 105,530.110 + continuation 91,365.406. The original and continuation appear exactly once. Continuation: 10,571 new/global22,571 updates, phase-local25.379279444 hours. MLflow is a mapping to the same work, not additional time. All nine historical journal hashes were rechecked unchanged; current journal hash covers only the complete-line prefix at the observation.

Latest complete70-case native validation22k: raw lesion Dice0.4121723662348846,35/36positive cases detected,26/34empty scans with alarms. Best18k: Dice0.43051696723124094. No fixed5mm filter applied. Progress export uses phase-local steps2k..10k and target12k, with global steps separately recorded. Parent curve remains separate. Additive ancestry sidecar supplies starting_step12000 because the snapshot was already written when that refinement arrived.

These are scientific session hours including in-loop validation/checkpoint/I/O, not GPU-busy, optimizer-only, human work or calendar hours. Engineering, failed preupdate qualification, standalone inference, downloads and Mac runs are excluded. Older first-five-weeks records remain unavailable per the November3 ledger. This is not a certified exhaustive all-time or combined-machine total; Mac must reconcile its own records and deduplicate copies. No new exhaustive historical inventory was performed. Historical untimed tails remain uncounted. Existing first-six figures are a subset, never additive.

## Export hashes

- `docs/capstone/coordination/WINDOWS-TRAINING-HOURS-20261109.json`: `6acb7d445e8a8c771f181295e2bc4c2a8a542d33f6f19ad1add469df3389730f`
- `configs/training-progress/lenovo-stunet-corrected-20261109.json`: `9959f678d93123a30f4b1cbe1acd5dfb9d8e30e75dc4cf58f2d43a688d64193a`
- `docs/capstone/coordination/STUNET-PROGRESS-ANCESTRY-20261109.json`: `5b7c9c6f567a1c34eb61cbcc6e80f2a6a9b478db8449439eb261456276dd90cb`

All exports contain aggregate metadata only, no patient identifiers or imaging arrays. All new paths checked outside500ready pins. JSON parse, distinct11run/MLflow keys, historical hashes, contiguous new update counts, phase/global arithmetic, complete70case validation counts, aggregate hours and identifier absence checked. Original November3 export and original progress config untouched.
