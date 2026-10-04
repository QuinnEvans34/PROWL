# CAP-EXP-005 exact launch design

D-285 authorizes machinery and request preparation, not real launch. Experiment: expanded-cohort
pancreas-localizer smoke, 16 training and11 separate development-validation members frozen by D-282.
Case6350 remains held; no replacement. Validation lacks arterial/thin-slice coverage. Biological
patient identity remains an unverified study-as-subject fallback. No lesion or clinical claim.

Fresh seed42 two-output SegResNet; 96-cube patches, float32 native MPS with fallback disabled.
Balanced CE plus foreground soft Dice; AdamW LR0.0003,weight decay0.00001,cosine horizon288.
288 updates =18 frozen-order cycles over16 training members. Existing equal pancreas/background
center sampling. No old weights, adaptive stopping, threshold search or case filtering.

Full-volume sliding-window evaluation of both complete roles at0/144/288. Argmax mask; all-component
prediction-only box with fixed10mm margin. Report per-case Dice, precision/recall, volume ratio,
reference coverage and scan fraction, plus existing provisional fit/ROI screens. These screens are
diagnostics, not eligibility or clinical acceptance. Preserve empty predictions explicitly.
Detailed component diagnostics may report a budget-exceeded outcome if >4096 components; do not
change the prediction or omit the case. Report all-component box and voxel metrics regardless.

Checkpoint at0/96/192/288. At final step publish one source-grid binary NIfTI, processed-grid PNG,
transform record and metrics per case; terminal record references all27 case artifacts. Backup the
terminal checkpoint and its referenced case artifacts using existing independent registered stores.
Restore from backup without a primary-store argument and compare a fixed prediction probe.
No automatic restart; interruption preserves completed checkpoints and a durable failure journal.
A partial terminal/export set must never be marked complete. Completed requests are single-use.

Limits: total1200s from worker start (including loading), update phase600s wall time including its
checkpoint/intermediate-evaluation overhead; RSS16GiB;512MiB processed RAM;1GiB new data/domain;
96MiB per artifact;100GiB internal free floor. Source reads exact54 files once, using existing1GiB
compressed/4GiB expanded input budget. Native exports restored one at a time. AC power and a
cooperative accelerator lock are required. Failed attempts and bounded evidence remain retained.

Before launch: full native suite, complete synthetic CPU/MPS transaction, injected interruption,
export/terminal corruption refusal, independently verified backup/restore, frozen source/environment,
recipe/capability/input/plan pins. Approval is a separate record tied to the exact request digest.
Do not infer launch permission from preparing the request. Source/environment drift requires a new
reviewed request. Results are a learning experiment, never guaranteed to pass fit/ROI diagnostics.
