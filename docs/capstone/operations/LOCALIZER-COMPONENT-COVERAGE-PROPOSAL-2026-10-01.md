# Component-selection coverage diagnostic

October 1, 2026 — recommendation after D-314; not an authorized source-read job or selected ROI policy.

The retained audit shows that disconnected regions inflate boxes even though the largest component
contains a median 99.39% of CAP-EXP-012 foreground. Largest-only boxes would lower mean validation
crop fraction from 31.68% to 21.96%, but component reference retention is unmeasured. The largest
component remains a median 13.33 times the reference volume. Cleanup may improve localization crop
cost; it cannot by itself solve the broad connected overprediction or recover already missed anatomy.

## Proposed one-factor diagnostic

Use the same 46 paired cases as D-314: all 40 validation members plus train 150/756/6110/6822/7604/7684.
Freeze a new request for their 46 qualified original pancreas references, loaded once per case and
reused for raw/largest-only scoring from both retained 010 and 012 terminal masks. No CT, inference,
training, lesion target, threshold tuning or additional case selection. Old requests are consumed;
their descriptor evidence can be verified, their read allowances cannot be recycled.

Rule: 26-connectivity, descending component volume, deterministic discovery-order tie, largest
component only, unchanged 10 mm physical margin and acquired-scan clipping. Preserve raw outputs;
derived masks/results get separate identities. This is a deliberately simple diagnostic candidate,
not a hidden runtime cleanup or largest-lesion rule. No per-case exceptions or oracle enlargement.

Prepare/test a versioned diagnostic runner with exact retained export and reference pins, positive
role/purpose checks, source-unit/geometry verification, resource/read ceilings, one-shot consumption,
case-level failure records and completion-last receipt. Verify input immutability. Synthetic checks
must include a real fragment in a smaller component, a larger false region, ties, multiple components,
empty/dense predictions, anisotropic clipping, and a mask with high crop containment but poor recall.

Report raw/derived component overlap, visible-reference recall and false positives, box containment,
scan fraction and old size-plus-containment screen for every case. The primary paired development
readout is 010, whose raw boxes retain ≥.995 reference in all 40; 012 is a separate diagnostic arm
with its existing 3115 box failure. Do not pool models, choose components using ground truth, or
call a subset success representative of all requested cases.

Suggested prospective screen before considering further policy work: every 010 validation derived
box retains ≥.995 reference and mean crop fraction improves by at least .05 absolute. Record all
mask-recall changes as diagnostic evidence; the localizer mask is not the final reviewed contour.
These are **proposed diagnostic bars**, needing
review before the new request. Passing them is not policy adoption: actual Stage 2 normalization,
effective lesion containment and the frozen broader localization protocol remain required. If they
fail, retain the evidence and consider an explicitly frozen plausible-nearby union rule later; do
not tune distance/margin against these outcomes within the same experiment.

This can proceed alongside Stage 2 target qualification after a new bounded source-read decision.
Do not launch another loss-weight or long-duration experiment merely to avoid measuring this issue.
