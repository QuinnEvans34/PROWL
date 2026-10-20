# Current training output → measurement viewer handoff

**Status:** Quinton selected on-demand inference with optional caching. Retained training predictions are not a prerequisite.
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
The subsequent authorized handoff below confirms that it does not retain native prediction arrays.

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

Quinton explicitly answered “Yes, send the handoff request.” The message was sent and the training
chat completed its read-only inspection in turn `01a15acb-75e2-74f0-b94c-f52f76f23059`.

## Received result — missing export, not an intake failure

At inspection, the latest completed evaluation was step 6,000 (raw checkpoint, 70 development
cases). Neither the run directory nor its independent backup retained native prediction masks.
The producer reconstructs labels in memory, scores them and returns only `case_id`, `step`,
`scope`, `reconstruction` and `metrics`; the executor serializes those records as JSON.
There is no CT/prediction pair for this adapter to admit. No case was selected or quality screened.

| Retained evidence reported by training owner | Identity |
|---|---|
| `execution/native-006000.json` | 62,421 bytes; SHA-256 `c70d3fd952efbbec3dffb1dd7fb6428f243927761c6b21cdd921ec4a22b0398f` |
| Journal completion | `native_completed`, step 6000, variant `raw`, UTC milliseconds 1792509576893 |
| `execution/step-006000.pt` | 56,576,803 bytes; checkpoint hash **not computed**, weights not loaded |
| Run `ready.json` | SHA-256 `53b264490b2eb6e50b3e7b9c38e17ccf9e8b244b692b8edbf12fa3434edc1ffe` |
| `segmenter_pancreas_region_session_v1.py` | SHA-256 `105f4f75e2193559e714e66a0a7b87e55de0238a862761995a3ead4f5906b8f8`; reported matching frozen receipt |
| `segmenter_pancreas_region_executor_v1.py` | SHA-256 `26db95b7e47145f80e4731faf78c66b386992ea399137add9dc94769790eb67e`; reported matching frozen receipt |

These are the remote owner's reported identities, not a second local hash verification. Current
producer code is not present in this checkout. Coverage was reported in
`E:/PROWL/readiness/pancreas-region-20261019-a01/cohort-final/result.json` for all 1,403 cases;
`cuda/cold.json` is a restoration qualification, not a per-case prediction-export receipt.

Confirmed semantics: provided development pancreas masks select regions and support scoring;
fixed margins were derived from training annotations. Development lesion masks support coverage
auditing/scoring and do not select or repair inference regions. CT is the model's only image
channel, which does not remove the region's reference assistance. The class-1 predicted count
comes from the model, not the provided mask. Labels are 0 background, 1 pancreas, 2 lesion.
Per-case reconstruction records contain region bounds, spacing, tile count, gap/blending details,
assistance and outside-region background policy, but are not standalone spatial artifacts.

Viewer resource compliance remains **unassessed**: no candidate pair exists. No arrays/weights
were loaded, inference launched, artifacts copied, producer changed or training interrupted.

## Selected workflow — on-demand inference

Quinton selected on-demand inference on October 20 after reviewing this handoff. This supersedes
an export-first product workflow. The missing historical mask only prevents reusing an existing
prediction for the integration check; training does not need to save every prediction.

1. The user selects a scan and requests prediction, or reuses the matching prediction already
   produced by the viewer. Use an immutable, explicitly selected model checkpoint.
2. A bounded inference worker runs the current restoration/window logic once and returns a native
   prediction with source, model, geometry, label and assistance provenance. Temporary result files
   are permitted for transport; a permanent saved package is not required.
3. The viewer displays that exact prediction. Deterministic measurement code calculates volumes
   from the same native labels and affine. Asking another measurement question reuses the result;
   it does not trigger a second segmentation or ask the language model to estimate size.
4. Keep the result for the session. Persistent caching and explicit Save are optional. Cache keys
   bind CT content, checkpoint hash, preprocessing/restoration/postprocessing version, inference
   settings and any supplied region/reference-input identity. Never reuse on case name alone.
5. Switching scan, model or region invalidates the displayed answer. Cancel obsolete requests where
   supported and discard late results; pending/failed/cancelled output must not become a measurement.

The current pipeline is pancreas-assisted: the supplied pancreas mask defines its region. Model
output labels, not that reference, supply the measured volume. Expose the assistance in the UI;
a new CT without a provided region requires a qualified localization path. Preserve autonomous
v2's strict contract and implement a separate explicit assisted-result contract.

## Next implementation and completion evidence

- Inspect the actual current producer code and extract/reuse its inference and native restoration
  entry point behind a separate worker/API. Do not modify the running training evaluator.
- Define the job/result contract and UI states: queued, running, ready, failed and cancelled.
  Bind the displayed mask and measurement summary to one prediction identity. Enforce bounded
  memory, execution time and concurrency; reject unavailable/busy inference resources clearly.
- Qualify synthetic geometry, assistance/provenance, measurement arithmetic, stale-result handling
  and optional-cache invalidation. Existing source/region boundary and resource checks remain.
- Run one exposed development case in an available inference-resource window using a pinned
  checkpoint and the required assisted inputs. This does not require a training restart or a
  full evaluation run. Review the native outline with Quinton; retain this validation receipt
  even though routine application predictions need not be saved permanently.
- Compare the displayed outline, computed measurements and provenance. Keep coverage/accuracy
  limitations visible and withhold unsupported measurements. Individual-lesion measurements,
  reference accuracy, normal-range eligibility and disease explanations remain separate work.

Current viewer limits remain as recorded above; worker and transfer limits must be assessed against
actual native cases before implementation promotion. The selected architecture is approved; no
inference job, resource competition with training or automatic post-training execution was started
by this planning update. The metadata-only cross-chat request is complete; no further message was
sent to the training chat.

AI-05 stays In Progress. Per-lesion components/defined diameter and reference-reviewed measurement
accuracy remain open. W03-04/05 and formal RAG acceptance remain in the weekly plan. This handoff
does not start training, inference, evaluation or data transfer. No runtime code or live UI policy
changed during discovery; documentation checks suffice for this planning checkpoint.
