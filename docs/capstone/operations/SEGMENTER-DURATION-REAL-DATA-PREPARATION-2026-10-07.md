# Duration comparison preparation and tonight's decision — October 7

**Inactive draft; no scientific controls, grant, writer or request prepared.** The bounded diagnosis
is [complete](SEGMENTER-DURATION-RECOVERY-AUDIT-RESULTS-2026-10-07.md). The current native-readiness
guard still requires exact next-update state, so it correctly refuses scientific launch. This
packet proposes a narrower capability for one uninterrupted pilot; it does not silently amend it.

## The useful next question

Does increasing the frozen scratch recipe from48to192updates improve native lesion overlap while
preserving coverage and reducing false foreground? The192invented producer already completed;
one-step continuation showed small finite model/optimizer differences with exact progress/RNG.
We should finish saved-prediction recovery rather than repeat that full producer or rewrite
training mechanics without a demonstrated defect.

## DUR-06 proposal — qualify inference recovery; defer training resume

**Awaiting Quinton's decision.** Proposed change: allow a separately named
`qualified_duration_inference_v1` certificate for this fresh, uninterrupted scientific request.
It proves independently kept checkpoints can load and reproduce saved predictions/exports. It
does not certify optimizer continuation, exact replay or crash resumption. Keep N02's exact-replay
failure and both diagnostic failures of bit equality explicit. No new numerical tolerance is
chosen for optimizer/model continuation; no weights are altered and no deterministic-mode switch.

Closed producing implementation, if approved:

1. Amend only readiness-kind validation in `src/training/segmenter_duration_executor_v1.py`:
   admit the distinct inference-only certificate under the existing scientific no-restart policy.
   Keep kinds/domains, requests/grants, sampling, recipe, calls, cadence, quality and storage fixed.
2. Amend only `validate_readiness()` in `scripts/diagnostics/segmenter_duration_launch.py`:
   preserve the original full-readiness branch; validate a separate inference-only certificate
   with exact producer/recovery/test/source/runtime bindings and explicit resume denial. No change
   to `cold()` or its exact-update assertion and no manufactured full native acceptance.
3. New `tests/test_segmenter_duration_inference_readiness.py`: model-free positive/negative checks
   for the certificate, failed/incomplete cold evidence, missing checkpoints/exports, wrong source/
   runtime/provenance, old full-certificate substitution and any restart or role widening.
4. New `docs/capstone/imaging/SEGMENTER-DURATION-INFERENCE-READINESS-CONTRACT-V1.md`.

Snapshot the two amended paths and current400pins. Only those two function regions may differ;
retain every prior source version and historical qualification. Tests must authenticate the
permitted producing-lineage changes from N02's frozen source closure; no blanket hash exception.
Each new targeted invocation≤90seconds/2GiB sampled owned RSS, zero model/array/optimizer work;
no old-suite replay. Routine handback/tracking/local preservation included.

Conditional fresh actual qualification after these checks, also part of the proposed scope:

- **One new request**, suggested ID `DUR_INFERENCE_20261007_I01`, independently reviewed exact
  source/runtime/helper/receipt pins; N02 and D01/D02 controls stay consumed/immutable.
- Read only independently kept N02 invented artifacts: summary/screens, five checkpoints at
  0/48/96/144/192, stored image/probability bundles,25exports and25views. Derive the exact once-per-
  artifact read ledger from pinned metadata before dispatch. No original/cache/CT/third-party
  payloads, external primary reads or new keeper/restore payload copies.
- Restore each checkpoint with existing full-payload integrity validation. Compare five probe
  predictions using the **existing predeclared1e-6absolute probability limit**; reproduce all25
  native masks exactly and validate their paired view metadata. **30forwards/zero optimizer calls**.
  Do not run another192-update producer, resume training, or redefine the failed next-update test.
- ≤600seconds,12GiB sampled owned RSS/MPS driver ceiling,≤2GiB retained payload-member reads,
  ≤8MiB local controls/reports/logs,100GiB free floor. Exact retained-size admission must fit these
  bounds. AC, idle owner proof, continuous owned worker watchdog and shared MPS lock required.
  Preserve failure and stop; no retry, new capacity, deletion or external writer follows.
- Record a separate inference-only qualification certificate **only after all five checkpoint
  probes and25export/view checks pass**. It binds the historical producer proof, permitted source
  lineage, current source/runtime/test pins, exact read/call counts and primary-read denial.
  `training_resume_qualified=false`; record bit-exact continuation as failed, not waived-to-pass.

This scope adds a focused cold check, not a second full rehearsal or backup phase. Scientific
preparation and launch remain separate after success. If Quinton instead requires exact optimizer
continuation now, define a separate determinism investigation; no start-time promise is warranted.

## Prepared real-data comparison

| Item | Fixed scope |
|---|---|
| Baseline | D-335 / CAP-EXP-014, consumed and complete; compare retained results, never replay/extend it |
| Changed factor | Total updates48→192; fresh scratch initialization, seed42 |
| Model/recipe | SegResNet, v5 present-class mean CE + foreground Dice; AdamW LR0.0003, decay1e-5, constant schedule, batch1, fp32/MPS,144³ provided-pancreas ROI, zero jitter |
| Train | PanTS3,26,2232,2973,5821,6238;32exposures each if192updates complete |
| Report only | PanTS2514 at terminal192; never used to choose checkpoint/recipe/duration |
| Evidence cadence | Checkpoints0/48/96/144/192; all-six-case native screens48/96/144/192;2514only at192 |
| Primary result | Terminal192; interim checkpoints retain failures/trajectory, no best-score selection |
| Model calls | Producer253forwards/192updates; real cold30forwards/zero updates; no automatic restart |
| Resources |60minutes total:45producer/10cold/5preflight;12GiB RSS/driver; approved26GiB whole backup cap,100GiB free floor |
| Storage | New real phase≤2GiB per child/≤4GiB combined internal phase including64MiB controls;≤8GiB growth across the already-approved native+real allocation; preserve all evidence |
| Claim limits | Provided-ROI small positive pilot; no autonomous baseline, real-negative specificity or broad-generalization claim |

Initial weight hash remains `3ee49a533f03db4c2cea5c9cdec512004c7f904873149fa04002781980640add`.
Tiny2973 and boundary6238 remain in every training screen. All original membership/roles/holds
stay fixed; uncertain negatives do not become eligible because files exist.

**DUR-01 stays unchanged.** Complete valid outputs; nonzero pancreas TP in every case; pancreas
macro recall≥baseline−.03; lesion macro recall≥max(.8,baseline−.03); each class/case and lesion
component recall≥baseline−.10; all components TP>0; tiny components≥.95; each lesion FPmL≤1.25×
baseline. Terminal adds pancreas macro Dice≥baseline, lesion macro Dice≥1.20×baseline, mean lesion
FPmL≤.80×baseline and each case FPmL≤1.10×baseline. Missing/invalid outputs stop; zero-baseline FP
admits zero candidate FP only.2514quality is reported separately. See the
[accepted policy](../imaging/SEGMENTER-DURATION-POLICY-CONTRACT-V1.md).

## Retained-metadata target-read draft

Derived without arrays or current patient-file observations from the old approved request,
SHA256 `e63f5613085bf202bbb1157616afc7492f84e0855e81d243dd3981ed41ec4a10`.
The unchanged `original_scope()` adapter computes these stage envelopes. Full IDs are
`pants:study:PanTS_00000003`, `...00000026`, `...00002232`, `...00002973`, `...00005821`,
`...00006238` (train) and `...00002514` (validation/report-only), with no role changes.

| Stage | Logical pancreas/lesion target reads | Compressed hash bytes | Compressed decode bytes | Expanded bytes |
|---|---:|---:|---:|---:|
|48 |12 |1,173,533 |1,173,533 |253,698,624 |
|96 |12 |1,173,533 |1,173,533 |253,698,624 |
|144 |12 |1,173,533 |1,173,533 |253,698,624 |
|192 |14 |1,265,220 |1,265,220 |272,494,704 |
|Total |**50** |**4,785,819** |**4,785,819** |**1,033,590,576** |

Fourteen unique original targets are reread at the declared screens; **zero original CT reads**.
Qualified cached images/labels are separate permitted inputs for the future job; none were opened
by this preparation. The local JSON is explicitly `inactive_retained_metadata_draft`, not a fresh
source check, validated scientific request, reused capability or acquisition permission.

## Remaining launch work after the decision

1. If DUR-06 is selected, qualify its narrow guard amendment and focused cold evidence; preserve
   an inference-only certificate. Do not write a full native/replay acceptance.
2. Fresh registered drive/UUID/mount/device/AC/idle/free-space/backup-baseline proof; exact current
   source-metadata verification, accepted cache/source bindings and original-target read authority.
3. Freeze the new real request, policy/D-335/count evidence, target budgets, current producing pins,
   scientific storage capability, manifests and exclusive namespaces; review actual fit and all
   launch guards before enabling any job writer. Old approvals/consumed attempts remain fixed.
4. Present that concrete request for Quinton's scientific launch decision. One run≤192updates,
   stopping on the first failed quality/resource/fault limit. If interrupted, retain the checkpoint
   for evaluation; **do not resume or claim a complete192 result** under inference-only readiness.

There is no unbounded overnight queue in this proposal. Further experiments can reuse the qualified
workflow with fresh requests; new code is needed only for a changed capability, recipe or actual
defect. Dataset expansion and optimizer-resume qualification follow the first pilot separately.
