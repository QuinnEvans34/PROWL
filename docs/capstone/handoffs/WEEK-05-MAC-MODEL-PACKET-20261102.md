# Mac model packet prepared — November 2

The laptop reported its verifier complete, backups/MLflow/cleanup verified and no
training active. Its separate branch codex/week05-cuda-readiness contains the
physical-region bridge and Windows access guard (8a0dfb3, d37bafc);42 tests passed,
one Unix-specific test skipped. These are reported laptop results, not rerun here.
Do not duplicate that adapter work. Windows supervisor integration remains open.

## Completed on the Mac

Added scripts/prepare_week5_model_handoff.py: a CPU-only selected-control exporter.
It checks pinned primary/independent checkpoint bytes, selected native report and
backup, step20000, zero-KD identity, architecture, cohort roles, finite float32
tensors and strict inference-only loading. It creates fresh private outputs outside
the repository and compares every exported tensor exactly. No optimizer is exported,
model forward run, training state altered or GPU initialized by this operation.

Six tests passed across the new boundary checks and existing inference-weight loader.
The real export also passed strict loading and tensor equality. No source images or
masks were read. Current KD continued advancing (177→178 observed during closeout).

| Identity | SHA256 |
| --- | --- |
| Original localizer inference weights | 46417801f3d3c37e618d06823027e84f0ce84343f469f24124537167d40198d5 |
| Selected control step20000 checkpoint | 919ebd4c18e72aece8b47299b3a1ccc8a1f392be53e229d0921a04f74e6651ad |
| Selected native report | 8fbefc60b0d2da0ec951713ed9e15f58f12fc19ea571cdd3389135eb17d0a1bf |
| Exported segmenter inference weights | 8b2a104f9830776da7011a759f5dfddbc9750725380bf244f7d292f02aadcd63 |

The checkpoint/report hashes were checked against the frozen November2 control
closeout, not merely computed and accepted from arbitrary files. Selected
provided-region development Dice remains0.383592868; no new performance measured.

## Private transfer inventory

Archive on Mac external drive:
`/Volumes/PROWL-Data/PROWL/artifacts/week05-cuda-handoff-20261102/week05-models-provenance.tar.gz`

Size34,975,283bytes. SHA256
`90b1f308de6be6e3abe38992d463a393798111798bdec74d5506bde0a887fec2`.
17 files including the manifest; every archived payload was rehashed against it.
No CT/mask arrays, original training checkpoint or optimizer state are included.
Weights and private provenance remain outside Git. Pushing this report does not
transfer the archive. Private delivery and destination readback remain pending.

Includes localizer.pt, segmenter-control-020000.pt, localizer recipe and historical
lineage review, control provenance and frozen design,70-case development identities
with source hashes, explicit inference contract and eight relevant source snapshots.
The old checkpoint-review.json describes the historical segmenter; the new
control-provenance.json is authoritative for the supplied current segmenter.

## Evaluation exposure and remaining gates

No recorded localizer training member overlaps the current70-case development set.
Three current development cases were in the localizer's earlier development set:
PanTS_00002514, PanTS_00005194 and PanTS_00007687. They remain in the packet with
exposure flags; no cases were excluded/reassigned. All70 were also used for control
checkpoint selection. This is exposed development evidence, not untouched evaluation.
Case-ID reconciliation does not prove biological independence or resolve unknown
pretraining membership. The laptop must reconcile its own identities before freezing.

Preserve current-control HU[-100,250] normalization, physical144 windows/72stride,
source-index margin expansion and native probability reconstruction. The old
localizer uses its own bound recipe; do not conflate their normalization rules.
All-support remains the historical localizer default; largest-component remains an
experimental option, not a silently selected new policy. The packet is NOT launch-ready.

Next: private delivery/hash readback, laptop supervisor/physical executor integration,
eligible frozen cohort/policy/budget review, and retained cross-device reference.
No current-checkpoint cross-device inference reference was generated while KD owns
the Mac GPU. A suitable existing reference must be verified or a bounded reference
run scheduled before that gate can pass. No new training or GPU evaluation dispatched.

## Private delivery verified — November 2, 21:00 UTC

Magic Wormhole transferred the archive through its encrypted transit relay; the
Mac sender received confirmation and exited successfully. The laptop checked the
34,975,283-byte archive against the SHA256 above before extraction, rejected unsafe
archive paths/types and verified all 16 manifest payloads both before and after
extraction (17 files including the manifest). Its retained receipt records VERIFIED
at 2026-11-02T21:00:52.145333+00:00:
`E:/PROWL/transfer/week05-cuda-baseline-20261102-a01/receipt.json`.
Payload destination: the same directory's `extracted/week05-models-provenance`.
These are laptop command results inspected from its chat, not Mac filesystem reads.

Private delivery is complete. The laptop is continuing CPU strict model loading,
cohort reconciliation and Windows physical-executor preparation. The unresolved
cross-device reference and admission gates remain; delivery does not establish
scientific readiness or authorize a new evaluation/training launch. Mac KD was not
interrupted, and no model forward was run on the Mac for this transfer.
