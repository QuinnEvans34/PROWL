# Current training output → measurement viewer handoff

**Status:** Input discovery complete; current saved prediction and producer schema pending.
**Owner:** AI-05 / DAG-RAG integration; training artifacts remain owned by the training chat.

## Finding and correction

The latest inspected history of **Plan capstone experiment workflow** identifies
`pants_pancreas_region_24k_20261019` on the Windows laptop. Quinton explicitly approved using
provided pancreas masks to define its region. That is pancreas-assisted inference. Training
coverage checks reported complete pancreas/lesion support across overlapping windows; they do
not certify the accuracy or completeness of each predicted outline.

The existing `saved-prediction-view-v2` adapter accepts only the retained CT-only autonomous
cascade contract. It must continue rejecting reference-assisted results. The prior instruction
to admit the current run through v2 was too broad: inspect its producer records, then implement
a separately versioned assisted adapter. Never manufacture autonomous provenance or mark
`reference_inputs_used=false` for this run.

Read-only evidence: training chat `01a12c40-1490-7cf2-8e20-6498c71bf685`, turns
`01a155b8-cead-72e0-89e3-59657bda4fd4` (human approval and launch report) and
`01a15a8d-1752-7cd2-a2aa-838548a60719` (interim report). These are historical snapshots,
not a current training-health check. Native reports were recorded under
`E:/PROWL/artifacts/pants_pancreas_region_24k_20261019/execution/native-*.json`.
Whether the current evaluator retains its native prediction arrays is still unknown.

Fetched training branch `codex/windows-training-readiness` at
`1e427dd66d9eb85e2eb31e760eb972ae05744b27` without changing the checkout.
Its older `scripts/diagnostics/evaluate_pants_native.py` writes native NIfTI files,
but it does not establish what the newer running physical-window producer retains. Do not
execute that older evaluator, infer paths, or reconstruct an outline from aggregate metrics.

## Requested handoff, before any transfer

Ask the training owner for a metadata-only inventory of an **already retained**, completed
development prediction. Choose the first case by sorted case ID from the latest completed
evaluation that retained masks, before inspecting case quality. Freeze that case/checkpoint in
the receipt. If it fails intake, retain the failure; do not silently search for a better example.
This is an exposed development integration case, not an independent evaluation sample.

| Required record | What it must establish |
|---|---|
| Producer | Exact code revision plus uncommitted producer hashes if applicable; run/config, evaluation step, checkpoint SHA-256, ordinary/EMA identity and completed evaluation receipt |
| Input identity | CT file SHA-256/bytes, case and development membership; native shape, affine, explicit spatial units and voxel dtype |
| Prediction | Actual retained native label-file path, SHA-256/bytes, decoded size, geometry, label mapping, output restoration and postprocessing method |
| Assisted inputs | Provided pancreas mask identity and role in region selection; explicit declaration of every reference input used during prediction; separate lesion-reference use for coverage/metrics from inference |
| Region and coverage | Bound region/window plan, source transforms, output support, coverage report identity and case outcome; whether any reference repaired/expanded region selection |
| Availability | Whether those exact artifacts are immutable and can be copied without touching the running job; missing evidence must be listed explicitly |

Pancreas volume must identify the measured mask. A predicted label union (pancreas + lesion)
must not be substituted with the provided pancreas reference. The evaluator's pancreas-only
class metric is also not the union's volume. No aggregate score substitutes for an output file.

Current viewer budgets remain 32 million native voxels, 64 MiB per compressed image, 128 MiB per
decoded image and 1 MiB per JSON record. Check metadata against these limits before transfer;
an oversized native scan needs an explicit resource-design follow-up, not silent downsampling
or an unreviewed limit increase. Initially return metadata/paths only, not CT or reference arrays.

## Concrete message prepared for the training chat

> Continue owning the live training run without changing or interrupting it. The DAG/RAG chat
> needs one already-produced development prediction for the current-scan measurement viewer.
> Please inspect retained metadata for `pants_pancreas_region_24k_20261019` and report whether
> the latest completed native evaluation saved actual native prediction masks. If it did,
> select the first case by sorted case ID before inspecting quality and record its checkpoint
> identity, CT/prediction file paths, SHA-256/byte sizes, native geometry/units, label mapping,
> completed evaluation receipt, producer code identity, restoration/window-region records and
> linked coverage result. Explicitly disclose the provided pancreas mask used for region
> selection and all other reference-input roles. Distinguish predicted pancreas measurements
> from the provided mask. Report the original native voxel count and decoded image sizes against
> the viewer's 32-million-voxel/128-MiB decoded/64-MiB compressed limits. Missing files or evidence
> are a valid result: do not launch inference, rerun evaluation, inspect protected cases, alter
> the producer or copy arrays for this request. Leave the metadata handoff in this chat so the
> DAG/RAG chat can read it; no reply message to another chat is necessary.

This message has not been sent. The desktop messaging tool requires explicit human authorization
to message another chat. Preparing and reviewing the request does not authorize delivery.

## Integration sequence and completion evidence

1. Obtain the producer's metadata response and pin the actual schema and selected artifacts.
2. Implement an explicit assisted-result contract, preserving autonomous v2 rejection behavior.
   UI wording must say “Pancreas-assisted prediction” and disclose the provided outline's role.
3. Validate synthetic source/model/reference-role/geometry/coverage contradictions and successful
   arithmetic. Keep current boundary, resource and stale-study protections.
4. Copy the selected immutable files into a fresh private package only after metadata fits;
   verify original hashes, native geometry, label support and actual inference-region coverage.
5. Review the outline in the viewer with Quinton. Show a number only when calculation checks
   pass, with model/assistance provenance and unresolved accuracy limitations visible. A rejected
   case remains an honest integration result. No normal-range or disease conclusion follows.

AI-05 stays In Progress. Per-lesion components/defined diameter and reference-reviewed measurement
accuracy remain open. W03-04/05 and formal RAG acceptance remain in the weekly plan. This handoff
does not start training, inference, evaluation or data transfer. No runtime code or live UI policy
changed during discovery; documentation checks suffice for this planning checkpoint.
